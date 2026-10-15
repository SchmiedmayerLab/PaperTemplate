# SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)
#
# SPDX-License-Identifier: MIT

import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from check_latex_log import main


class LatexLogTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("latexmk"), "latexmk is needed for the standalone regression")
    def test_standalone_subfile_resolves_bibliography_from_separate_output_directory(self) -> None:
        self.assert_standalone_build(citation=True)

    @unittest.skipUnless(shutil.which("latexmk"), "latexmk is needed for the standalone regression")
    def test_standalone_without_citations_does_not_require_bibtex(self) -> None:
        self.assert_standalone_build(citation=False)

    def assert_standalone_build(self, citation: bool) -> None:
        commands = Path(__file__).resolve().parents[2] / "paper/setup/commands.tex"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            section = root / "paper/sections"
            section.mkdir(parents=True)
            (root / "build").mkdir()
            (root / "main.tex").write_text(
                "\\documentclass{article}\n"
                "\\usepackage{subfiles,natbib,xcolor,etoolbox,hyperref}\n"
                + "\\input{" + commands.as_posix() + "}\n"
                + "\\begin{document}\n\\subfile{paper/sections/intro}\n\\end{document}\n",
                encoding="utf-8",
            )
            (root / "references.bib").write_text(
                "@article{example,author={Example, A.},title={A test},journal={Test},year={2026}}\n",
                encoding="utf-8",
            )
            (section / "intro.tex").write_text(
                "\\documentclass[../../main.tex]{subfiles}\n"
                "\\begin{document}\n"
                + ("A citation \\citep{example}." if citation else "No citations in this section.")
                + "\n\\end{document}\n",
                encoding="utf-8",
            )
            environment = os.environ.copy()
            environment["BIBINPUTS"] = str(root) + os.pathsep + environment.get("BIBINPUTS", "")
            result = subprocess.run(
                ["latexmk", "-norc", "-cd", "-pdf", "-halt-on-error",
                 "-interaction=nonstopmode", "-auxdir=../../build", "-outdir=../../build",
                 "paper/sections/intro.tex"],
                cwd=root, env=environment, capture_output=True, text=True, timeout=120,
            )
            self.assertEqual(result.returncode, 0, (result.stdout + result.stderr)[-5000:])
            auxiliary = (root / "build/intro.aux").read_text(encoding="utf-8")
            if citation:
                self.assertIn("\\bibdata{references}", auxiliary)
                self.assertIn("\\bibcite{example}", auxiliary)
            else:
                self.assertNotIn("\\bibdata", auxiliary)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main([str(root / "build/intro.log")]), 0)

    def test_final_log_passes_despite_unrelated_layout_warning(self) -> None:
        self.assert_log_result("Overfull \\hbox (1.0pt too wide)\nOutput written on main.pdf", 0)

    def test_unresolved_citations_and_references_fail_despite_pdf(self) -> None:
        for warning in (
            "Package natbib Warning: There were undefined citations.",
            "LaTeX Warning: Reference `missing' on page 1 undefined on input line 12.",
            "LaTeX Warning: There were undefined references.",
            "No file main.bbl.",
        ):
            with self.subTest(warning=warning):
                self.assert_log_result(warning + "\nOutput written on main.pdf", 1)

    def test_missing_log_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main([str(Path(temporary) / "missing.log")]), 1)

    def assert_log_result(self, content: str, expected: int) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "main.log"
            path.write_text(content, encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main([str(path)]), expected)
