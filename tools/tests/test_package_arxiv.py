# SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import patch


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from package_arxiv import (
    ArxivPackageError,
    PackageResult,
    RecorderData,
    audit_isolated_recorder_inputs,
    clear_package_outputs,
    discover_archive_files,
    extract_validated_zip,
    find_internal_source_constructs,
    freeze_submission_date,
    load_config,
    main as package_main,
    package_from_recorder,
    parse_recorder,
    publish_package,
    report_paths,
    sha256,
    strip_latex_comments,
    submission_build_environment,
    validate_rendered_equivalence,
)


class PackageArxivTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.root = self.base / "project"
        self.root.mkdir()
        (self.root / "paper").mkdir()
        (self.root / "build").mkdir()
        (self.root / "project" / "submission").mkdir(parents=True)
        self.system_root = self.base / "texmf"
        self.system_root.mkdir()
        (self.system_root / "article.cls").write_text("system class\n", encoding="utf-8")

    def _write_config(
        self,
        *,
        allowed_roots: list[str] | None = None,
        extra_files: list[dict[str, str]] | None = None,
        strip_extensions: list[str] | None = None,
        copy_extensions: list[str] | None = None,
    ) -> Path:
        config = {
            "schema_version": 1,
            "entrypoint": "main.tex",
            "compiler": ["latexmk", "-pdf", "-halt-on-error"],
            "texlive_version": "2025",
            "recorder": "build/main.fls",
            "allowed_roots": allowed_roots or ["main.tex", "paper"],
            "generated_files": [
                {"source": "build/main.bbl", "destination": "main.bbl"}
            ],
            "extra_files": extra_files or [],
            "strip_comment_extensions": strip_extensions or [".tex", ".bbl"],
            "copy_extensions": copy_extensions or [".pdf", ".png", ".jpg", ".jpeg"],
            "archive": "output/arxiv/manuscript.zip",
            "max_archive_bytes": 1_000_000,
            "max_uncompressed_bytes": 5_000_000,
            "compile_timeout_seconds": 30,
        }
        path = self.root / "project" / "submission" / "arxiv.json"
        path.write_text(json.dumps(config), encoding="utf-8")
        return path.relative_to(self.root)

    def _write_standard_sources(self) -> None:
        (self.root / "main.tex").write_text(
            "% private header\n"
            "\\documentclass{article}\n"
            "\\begin{document}\n"
            "\\input{paper/section}\n"
            "\\bibliography{references}\n"
            "\\end{document}\n",
            encoding="utf-8",
        )
        (self.root / "paper" / "section.tex").write_text(
            "Visible% remove me\n"
            " text with 50\\% retained.\n",
            encoding="utf-8",
        )
        (self.root / "build" / "main.bbl").write_text(
            "% generated note\n\\begin{thebibliography}{1}\n\\end{thebibliography}\n",
            encoding="utf-8",
        )
        (self.root / "build" / "main.aux").write_text("generated\n", encoding="utf-8")

    def _write_recorder(self, extra_inputs: list[Path] | None = None) -> None:
        inputs = [
            self.root / "main.tex",
            self.root / "paper" / "section.tex",
            self.root / "build" / "main.bbl",
            self.root / "build" / "main.aux",
            self.system_root / "article.cls",
        ]
        inputs.extend(extra_inputs or [])
        lines = [f"PWD {self.root.resolve()}"]
        for path in inputs:
            if path == self.system_root / "article.cls":
                recorded = path.resolve()
            else:
                recorded = Path(os.path.relpath(path, self.root))
            lines.append(f"INPUT {recorded}")
        lines.append("OUTPUT build/main.aux")
        (self.root / "build" / "main.fls").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )

    def test_strip_comments_preserves_tex_semantics_and_literal_percent(self) -> None:
        source = (
            "% full-line private note\n"
            "First% inline private note\n"
            "Second 50\\% complete.\n"
            "Indented% remove indentation too\n"
            "    continuation.\n"
            "\\newcommand{\\joined}{left% macro note\n"
            "    right}\n"
            "\\verb|literal%value|\n"
            "\\url{https://example.org/a%20b}\n"
            "\\href{https://example.org/a%20b}{label% remove href-label note\n"
            "continued}\n"
            "\\begin{verbatim}\n"
            "literal % value\n"
            "\\end{verbatim}\n"
        )
        cleaned = strip_latex_comments(source)
        self.assertNotIn("private note", cleaned)
        self.assertNotIn("macro note", cleaned)
        self.assertNotIn("href-label note", cleaned)
        self.assertIn("FirstSecond 50\\% complete.", cleaned)
        self.assertIn("Indentedcontinuation.", cleaned)
        self.assertIn(r"\newcommand{\joined}{leftright}", cleaned)
        self.assertIn(r"\verb|literal%value|", cleaned)
        self.assertIn(r"\url{https://example.org/a%20b}", cleaned)
        self.assertIn(r"\href{https://example.org/a%20b}{labelcontinued}", cleaned)
        self.assertIn("literal % value", cleaned)

    def test_public_cli_is_strict_and_smoke_test_never_publishes(self) -> None:
        config = load_config(self.root, self._write_config())
        with (
            patch("package_arxiv.load_config", return_value=config),
            patch("package_arxiv.clear_package_outputs") as clear_outputs,
            patch(
                "package_arxiv.run_submission_checks",
                side_effect=ArxivPackageError("blocked by submission gate"),
            ) as submission_checks,
            patch("package_arxiv.run_source_build") as source_build,
            patch("builtins.print"),
        ):
            self.assertEqual(
                package_main(["--project-root", str(self.root)]),
                1,
            )
        clear_outputs.assert_called_once_with(config)
        submission_checks.assert_called_once_with(config)
        source_build.assert_not_called()

        candidate = PackageResult(
            archive=self.base / "candidate.zip",
            contents_report=self.base / "candidate.contents.txt",
            checksum_report=self.base / "candidate.sha256",
            members=("main.tex",),
            sha256="digest",
        )
        with (
            patch("package_arxiv.load_config", return_value=config),
            patch("package_arxiv.clear_package_outputs") as clear_outputs,
            patch("package_arxiv.run_submission_checks") as submission_checks,
            patch("package_arxiv.run_source_build") as source_build,
            patch("package_arxiv.package_from_recorder", return_value=candidate),
            patch("package_arxiv.validate_archive"),
            patch("package_arxiv.publish_package") as publish,
            patch("builtins.print"),
        ):
            self.assertEqual(
                package_main(["--project-root", str(self.root), "--smoke-test"]),
                0,
            )
        clear_outputs.assert_not_called()
        submission_checks.assert_not_called()
        source_build.assert_called_once_with(config, submission_date=date.today())
        publish.assert_not_called()

    def test_submission_date_is_frozen_without_touching_literal_examples(self) -> None:
        source = (
            r"\newcommand{\paperdate}{\today}" "\n"
            r"\verb|\today|" "\n"
            r"\begin{verbatim}\newcommand{\paperdate}{\today}\end{verbatim}"
        )
        frozen = freeze_submission_date(source, date(2025, 1, 2))
        self.assertIn(r"\newcommand{\paperdate}{January 2, 2025}", frozen)
        self.assertIn(r"\verb|\today|", frozen)
        self.assertIn(r"\begin{verbatim}\newcommand{\paperdate}{\today}\end{verbatim}", frozen)
        self.assertIn(r"\newcommand{\paperdate}{\today}", source)
        fixed = r"\newcommand{\paperdate}{A fixed author-selected date}"
        self.assertEqual(freeze_submission_date(fixed, date(2025, 1, 2)), fixed)

    def test_unsupported_dynamic_date_fails_instead_of_rewriting_macros(self) -> None:
        for source in (r"\date{\today}", r"\renewcommand{\today}{custom}"):
            with self.subTest(source=source), self.assertRaisesRegex(ArxivPackageError, "unfrozen"):
                freeze_submission_date(source, date(2025, 1, 2))

    def test_submission_clock_uses_the_requested_date(self) -> None:
        environment = submission_build_environment(date(2025, 1, 2))
        timestamp = datetime.fromtimestamp(int(environment["SOURCE_DATE_EPOCH"]), timezone.utc)
        self.assertEqual(timestamp.date(), date(2025, 1, 2))
        self.assertEqual(environment["FORCE_SOURCE_DATE"], "1")
        self.assertEqual(environment["TZ"], "UTC")

    def test_archive_freezes_date_and_removes_editor_directives_without_source_edits(self) -> None:
        self._write_standard_sources()
        section = self.root / "paper" / "section.tex"
        source = (
            "%%begin novalidate\n"
            r"\newcommand{\paperdate}{\today}" "\n"
            "%%end novalidate\n"
        )
        section.write_text(source, encoding="utf-8")
        self._write_recorder()
        config = load_config(self.root, self._write_config())
        result = package_from_recorder(
            config, (self.system_root,), submission_date=date(2025, 1, 2),
        )
        with zipfile.ZipFile(result.archive) as archive:
            staged = archive.read("paper/section.tex").decode("utf-8")
        self.assertEqual(staged.strip(), r"\newcommand{\paperdate}{January 2, 2025}")
        self.assertEqual(section.read_text(encoding="utf-8"), source)
        repeated = package_from_recorder(
            config, (self.system_root,), submission_date=date(2025, 1, 2),
        )
        self.assertEqual(result.sha256, repeated.sha256)

    def test_comments_cannot_hide_in_protected_arguments_or_literal_openers(self) -> None:
        source = (
            "\\href{https://example.org/a%20b}{label}\n"
            "\\url{https://example.org/c%20d}\n"
            "\\detokenize{left% SECRET DETOKENIZE\nright}\n"
        )
        cleaned = strip_latex_comments(source)
        self.assertNotIn("SECRET", cleaned)
        self.assertIn("https://example.org/a%20b", cleaned)
        self.assertIn("https://example.org/c%20d", cleaned)
        self.assertIn(r"\detokenize{leftright}", cleaned)
        with self.assertRaisesRegex(ArxivPackageError, "ambiguous percent"):
            strip_latex_comments("\\href{% SECRET HREF\nhttps://example.org}{label}\n")
        with self.assertRaisesRegex(ArxivPackageError, "ambiguous percent"):
            strip_latex_comments("\\url{https://example.org/100%coverage}\n")
        with self.assertRaisesRegex(ArxivPackageError, "literal-environment opening"):
            strip_latex_comments(
                "\\begin{minted}{python}% SECRET\nprint('visible')\n\\end{minted}\n"
            )

    def test_internal_hidden_constructs_are_rejected_by_scanner(self) -> None:
        self.assertEqual(find_internal_source_constructs("% \\iffalse hidden\ntext\n"), ())
        self.assertIn(
            r"TeX ^^ character notation",
            find_internal_source_constructs("Visible^^25 PRIVATE NOTE\nNext\n"),
        )
        self.assertIn(
            r"TeX ^^ character notation",
            find_internal_source_constructs("Visible^^e PRIVATE NOTE\nNext\n"),
        )
        self.assertIn(r"\iffalse", find_internal_source_constructs("\\iffalse hidden\\fi\n"))
        self.assertIn(
            r"\begin{comment}",
            find_internal_source_constructs("\\begin{comment}hidden\\end{comment}\n"),
        )
        self.assertIn(r"\catcode", find_internal_source_constructs(r"\catcode`\%=12"))
        self.assertIn(
            r"content after \end{document}",
            find_internal_source_constructs(
                "\\begin{document}Visible\\end{document}\nprivate material\n"
            ),
        )
        self.assertNotIn(
            r"content after \end{document}",
            find_internal_source_constructs(
                "\\begin{document}Visible\\end{document}\n% private comment\n"
            ),
        )
        self.assertIn(
            r"content after \end{document}",
            find_internal_source_constructs(
                "\\begin{document}Visible\\end{document}\n\\verb|PRIVATE|\n"
            ),
        )
        self.assertIn(
            r"content after \end{document}",
            find_internal_source_constructs(
                "\\begin{document}Visible\\end{document}\n"
                "\\begin{verbatim}\nPRIVATE\n\\end{verbatim}\n"
            ),
        )
        self.assertEqual(
            find_internal_source_constructs(
                "\\begin{verbatim}\n\\iffalse \\catcode \\end{document}\n\\end{verbatim}\n"
            ),
            (),
        )
        self.assertIn(
            r"content after \endinput",
            find_internal_source_constructs("visible\\endinput\nprivate material\n"),
        )
        self.assertIn(
            r"content after \endinput",
            find_internal_source_constructs("visible\\endinput\n\\verb|PRIVATE|\n"),
        )

    def test_exact_contents_comment_removal_reports_and_determinism(self) -> None:
        self._write_standard_sources()
        (self.root / "references.bib").write_text("must not upload\n", encoding="utf-8")
        (self.root / "LICENSE.md").write_text("License notice\n", encoding="utf-8")
        self._write_recorder()
        config_path = self._write_config(
            extra_files=[
                {
                    "source": "LICENSE.md",
                    "destination": "LICENSE.txt",
                    "purpose": "Required source license notice",
                }
            ]
        )
        config = load_config(self.root, config_path)

        first = package_from_recorder(config, [self.system_root])
        first_digest = sha256(first.archive)
        with zipfile.ZipFile(first.archive) as bundle:
            self.assertEqual(
                bundle.namelist(),
                ["LICENSE.txt", "main.bbl", "main.tex", "paper/section.tex"],
            )
            self.assertNotIn("private header", bundle.read("main.tex").decode())
            self.assertNotIn("remove me", bundle.read("paper/section.tex").decode())
            self.assertNotIn("generated note", bundle.read("main.bbl").decode())
            self.assertIn(r"50\% retained", bundle.read("paper/section.tex").decode())
            self.assertNotIn("references.bib", bundle.namelist())

        second = package_from_recorder(config, [self.system_root])
        self.assertEqual(first_digest, sha256(second.archive))
        contents_report, checksum_report = report_paths(second.archive)
        self.assertEqual(
            contents_report.read_text(encoding="utf-8"),
            "LICENSE.txt\nmain.bbl\nmain.tex\npaper/section.tex\n",
        )
        self.assertEqual(
            checksum_report.read_text(encoding="utf-8"),
            f"{sha256(second.archive)}  manuscript.zip\n",
        )

    def test_path_traversal_input_fails(self) -> None:
        self._write_standard_sources()
        secret = self.base / "secret.tex"
        secret.write_text("secret\n", encoding="utf-8")
        self._write_recorder([self.root / ".." / "secret.tex"])
        config = load_config(self.root, self._write_config())
        recorder = parse_recorder(self.root / config.recorder, self.root)
        with self.assertRaisesRegex(ArxivPackageError, "escapes|outside"):
            discover_archive_files(config, recorder, [self.system_root])

    def test_symlink_input_fails(self) -> None:
        self._write_standard_sources()
        target = self.root / "paper" / "target.tex"
        target.write_text("target\n", encoding="utf-8")
        link = self.root / "paper" / "linked.tex"
        try:
            os.symlink(target, link)
        except OSError as error:
            self.skipTest(f"symbolic links unavailable: {error}")
        self._write_recorder([link])
        config = load_config(self.root, self._write_config())
        recorder = parse_recorder(self.root / config.recorder, self.root)
        with self.assertRaisesRegex(ArxivPackageError, "symbolic link"):
            discover_archive_files(config, recorder, [self.system_root])

    def test_hidden_input_fails(self) -> None:
        self._write_standard_sources()
        hidden = self.root / "paper" / ".internal.tex"
        hidden.write_text("private\n", encoding="utf-8")
        self._write_recorder([hidden])
        config = load_config(self.root, self._write_config())
        recorder = parse_recorder(self.root / config.recorder, self.root)
        with self.assertRaisesRegex(ArxivPackageError, "hidden"):
            discover_archive_files(config, recorder, [self.system_root])

    def test_input_outside_allowlist_fails(self) -> None:
        self._write_standard_sources()
        private = self.root / "private.tex"
        private.write_text("private\n", encoding="utf-8")
        self._write_recorder([private])
        config = load_config(self.root, self._write_config())
        recorder = parse_recorder(self.root / config.recorder, self.root)
        with self.assertRaisesRegex(ArxivPackageError, "outside allowed_roots"):
            discover_archive_files(config, recorder, [self.system_root])

    def test_missing_and_forbidden_inputs_fail(self) -> None:
        self._write_standard_sources()
        missing = self.root / "paper" / "missing.tex"
        self._write_recorder([missing])
        config = load_config(self.root, self._write_config())
        recorder = parse_recorder(self.root / config.recorder, self.root)
        with self.assertRaisesRegex(ArxivPackageError, "does not exist"):
            discover_archive_files(config, recorder, [self.system_root])

        bibliography = self.root / "references.bib"
        bibliography.write_text("@misc{private}\n", encoding="utf-8")
        self._write_recorder([bibliography])
        recorder = parse_recorder(self.root / config.recorder, self.root)
        with self.assertRaisesRegex(ArxivPackageError, "forbidden"):
            discover_archive_files(config, recorder, [self.system_root])

        alternate_bibliography = self.root / "paper" / "refs.bib"
        alternate_bibliography.write_text("@misc{private}\n", encoding="utf-8")
        self._write_recorder([alternate_bibliography])
        recorder = parse_recorder(self.root / config.recorder, self.root)
        with self.assertRaisesRegex(ArxivPackageError, "forbidden"):
            discover_archive_files(config, recorder, [self.system_root])

    def test_config_rejects_path_traversal_and_unreviewed_strip_extension(self) -> None:
        path = self._write_config()
        payload = json.loads((self.root / path).read_text(encoding="utf-8"))
        payload["archive"] = "../manuscript.zip"
        (self.root / path).write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(ArxivPackageError, "without '..'"):
            load_config(self.root, path)

        path = self._write_config(strip_extensions=[".tex", ".py"])
        with self.assertRaisesRegex(ArxivPackageError, "TeX-language"):
            load_config(self.root, path)

        path = self._write_config()
        payload = json.loads((self.root / path).read_text(encoding="utf-8"))
        payload["archive"] = "main.tex"
        (self.root / path).write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(ArxivPackageError, "below output/arxiv"):
            load_config(self.root, path)

        path = self._write_config(
            extra_files=[
                {"source": "NOTICE", "destination": "NOTICE.txt", "purpose": "notice"},
                {"source": "notice", "destination": "notice.txt", "purpose": "notice"},
            ]
        )
        with self.assertRaisesRegex(ArxivPackageError, "case-insensitive"):
            load_config(self.root, path)

    def test_local_style_can_be_explicitly_sanitized(self) -> None:
        self._write_standard_sources()
        style = self.root / "paper" / "local.sty"
        style.write_text("% internal note\n\\ProvidesPackage{local}\n", encoding="utf-8")
        self._write_recorder([style])
        config = load_config(
            self.root,
            self._write_config(strip_extensions=[".tex", ".bbl", ".sty"]),
        )
        result = package_from_recorder(config, [self.system_root])
        with zipfile.ZipFile(result.archive) as bundle:
            self.assertEqual(bundle.read("paper/local.sty"), b"\\ProvidesPackage{local}\n")

    def test_tex_source_extensions_are_sanitized_and_unknown_inputs_fail(self) -> None:
        self._write_standard_sources()
        font_definition = self.root / "paper" / "local.fd"
        font_definition.write_text("% private note\n\\ProvidesFile{local.fd}\n", encoding="utf-8")
        self._write_recorder([font_definition])
        config = load_config(
            self.root,
            self._write_config(strip_extensions=[".tex", ".bbl", ".fd"]),
        )
        result = package_from_recorder(config, [self.system_root])
        with zipfile.ZipFile(result.archive) as bundle:
            self.assertEqual(bundle.read("paper/local.fd"), b"\\ProvidesFile{local.fd}\n")

        data_file = self.root / "paper" / "runtime.dat"
        data_file.write_text("private process data\n", encoding="utf-8")
        self._write_recorder([data_file])
        with self.assertRaisesRegex(ArxivPackageError, "unclassified extension"):
            package_from_recorder(config, [self.system_root])

    def test_rendered_equivalence_detects_changed_pages(self) -> None:
        reference_pdf = self.base / "reference.pdf"
        packaged_pdf = self.base / "packaged.pdf"
        reference_pdf.write_bytes(b"reference")
        packaged_pdf.write_bytes(b"packaged")
        reference_page = self.base / "reference.png"
        packaged_page = self.base / "packaged.png"
        reference_page.write_bytes(b"same pixels")
        packaged_page.write_bytes(b"same pixels")
        with patch(
            "package_arxiv._render_pdf_pages",
            side_effect=[(reference_page,), (packaged_page,)],
        ):
            validate_rendered_equivalence(reference_pdf, packaged_pdf, self.base / "render")

        packaged_page.write_bytes(b"changed pixels")
        with patch(
            "package_arxiv._render_pdf_pages",
            side_effect=[(reference_page,), (packaged_page,)],
        ):
            with self.assertRaisesRegex(ArxivPackageError, "changed rendered manuscript pages"):
                validate_rendered_equivalence(reference_pdf, packaged_pdf, self.base / "render")

    def test_output_symlinks_are_rejected_and_validated_results_publish_last(self) -> None:
        self._write_standard_sources()
        self._write_recorder()
        config = load_config(self.root, self._write_config())
        outside = self.base / "outside"
        outside.mkdir()
        try:
            os.symlink(outside, self.root / "output")
        except OSError as error:
            self.skipTest(f"symbolic links unavailable: {error}")
        with self.assertRaisesRegex(ArxivPackageError, "symbolic link"):
            package_from_recorder(config, [self.system_root])
        (self.root / "output").unlink()

        final_archive = self.root / config.archive
        final_archive.parent.mkdir(parents=True)
        final_contents, final_checksum = report_paths(final_archive)
        for path in (final_archive, final_contents, final_checksum):
            path.write_text("stale\n", encoding="utf-8")
        clear_package_outputs(config)
        self.assertTrue(all(not path.exists() for path in (final_archive, final_contents, final_checksum)))

        candidate_archive = self.base / final_archive.name
        candidate_archive.write_bytes(b"zip")
        candidate_contents, candidate_checksum = report_paths(candidate_archive)
        candidate_contents.write_text("main.tex\n", encoding="utf-8")
        candidate_checksum.write_text("digest  manuscript.zip\n", encoding="utf-8")
        candidate = PackageResult(
            candidate_archive,
            candidate_contents,
            candidate_checksum,
            ("main.tex",),
            "digest",
        )
        published = publish_package(candidate, config)
        self.assertEqual(published.archive.read_bytes(), b"zip")
        self.assertEqual(published.contents_report.read_text(encoding="utf-8"), "main.tex\n")

    def test_zip_validation_rejects_noncanonical_paths_and_expansion(self) -> None:
        archive = self.base / "malformed.zip"
        with zipfile.ZipFile(archive, "w") as bundle:
            bundle.writestr("./main.tex", b"content")
        destination = self.base / "extract-noncanonical"
        destination.mkdir()
        with self.assertRaisesRegex(ArxivPackageError, "noncanonical"):
            extract_validated_zip(archive, destination, 1_000)

        with zipfile.ZipFile(archive, "w") as bundle:
            bundle.writestr("main.tex", b"x" * 1_001)
        destination = self.base / "extract-oversized"
        destination.mkdir()
        with self.assertRaisesRegex(ArxivPackageError, "uncompressed-size"):
            extract_validated_zip(archive, destination, 1_000)

    def test_isolated_recorder_rejects_external_non_tex_inputs(self) -> None:
        extraction_root = self.base / "isolated"
        extraction_root.mkdir()
        included = extraction_root / "main.tex"
        included.write_text("content\n", encoding="utf-8")
        trusted = self.system_root / "article.cls"
        external = self.base / "private.tex"
        external.write_text("private\n", encoding="utf-8")
        recorder = RecorderData(
            inputs=frozenset({included, trusted, external}),
            outputs=frozenset(),
        )
        with self.assertRaisesRegex(ArxivPackageError, "undeclared external file"):
            audit_isolated_recorder_inputs(recorder, extraction_root, [self.system_root])

        recorder = RecorderData(
            inputs=frozenset({included, trusted}),
            outputs=frozenset(),
        )
        self.assertEqual(
            audit_isolated_recorder_inputs(recorder, extraction_root, [self.system_root]),
            frozenset({Path("main.tex")}),
        )


if __name__ == "__main__":
    unittest.main()
