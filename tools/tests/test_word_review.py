# SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)
# SPDX-License-Identifier: MIT

import hashlib
import json
import shutil
import struct
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile, ZIP_DEFLATED

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import credit_contributions as credit
import word_review as word

ROOT = Path(__file__).resolve().parents[2]


def fixture(root: Path) -> None:
    for name in ("paper/setup/word.tex", "references.bib", "tools/word/numeric.csl"):
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
    shutil.copy2(ROOT / "tools/tests/fixtures/word-review.tex", root / "main.tex")
    (root / "paper/setup/metadata.tex").write_text(r"""
\newcommand{\papertitle}{Manuscript review workflow specimen}
\newcommand{\paperauthors}{Alex Example and Robin Example}
\newcommand{\paperaffiliations}{Example Research Group}
\newcommand{\correspondingauthor}{Alex Example}
\newcommand{\correspondingemail}{alex@example.org}
\newcommand{\paperdate}{November 4, 2026}
""", encoding="utf-8")
    data = {"schema_version": 1, "authors": [
        {"name": "Alex Example", "roles": ["Conceptualization", "Writing – original draft"], "confirmed": True},
        {"name": "Robin Example", "roles": ["Software", "Validation", "Writing – review & editing"], "confirmed": True},
    ]}
    (root / "project").mkdir()
    (root / "project/contributors.json").write_text(json.dumps(data), encoding="utf-8")
    (root / "paper/setup/contributions.tex").write_text(credit.generate(data), encoding="utf-8")
    # Deterministic illustrative graphic, independent of plotting libraries.
    def chunk(kind, payload):
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload))
    rows = []
    for y in range(240):
        row = bytearray([0])
        for x in range(600):
            bar = next((i for i in range(4) if 60 + i * 130 <= x < 125 + i * 130 and 200 - (i + 1) * 40 <= y < 200), None)
            row.extend((75, 100, 120) if bar is not None else (255, 255, 255))
        rows.append(row)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 600, 240, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(b"".join(rows))) + chunk(b"IEND", b"")
    image = root / "paper/figures/generated/review-bars.png"
    image.parent.mkdir(parents=True, exist_ok=True)
    image.write_bytes(png)


def tracked_review(original: Path, reviewed: Path) -> None:
    with ZipFile(original) as archive:
        parts = {name: archive.read(name) for name in archive.namelist()}
    document = ET.fromstring(parts["word/document.xml"])
    paragraph = next(p for p in document.findall(".//w:p", word.NS) if word.xml_text(p) == "The measured value was 10 units.")
    for child in list(paragraph):
        if child.tag != f"{{{word.W}}}pPr":
            paragraph.remove(child)
    def add_run(parent, text, deleted=False):
        run = ET.SubElement(parent, f"{{{word.W}}}r")
        item = ET.SubElement(run, f"{{{word.W}}}{'delText' if deleted else 't'}")
        item.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        item.text = text
    add_run(paragraph, "The measured value was ")
    for tag, value, number in (("del", "10", "101"), ("ins", "12", "102")):
        change = ET.SubElement(paragraph, f"{{{word.W}}}{tag}", {
            f"{{{word.W}}}id": number, f"{{{word.W}}}author": "Robin Example", f"{{{word.W}}}date": "2026-11-04T12:00:00Z"})
        add_run(change, value, tag == "del")
    add_run(paragraph, " units.")
    start = ET.Element(f"{{{word.W}}}commentRangeStart", {f"{{{word.W}}}id": "103"})
    paragraph.insert(1 if paragraph.find("w:pPr", word.NS) is not None else 0, start)
    ET.SubElement(paragraph, f"{{{word.W}}}commentRangeEnd", {f"{{{word.W}}}id": "103"})
    ref = ET.SubElement(paragraph, f"{{{word.W}}}r")
    ET.SubElement(ref, f"{{{word.W}}}commentReference", {f"{{{word.W}}}id": "103"})
    for node in document.findall(".//w:t", word.NS):
        if node.text == "Notes for reviewers.":
            node.text = "Notes for coauthors."
        if node.text == "Manuscript review workflow specimen":
            node.text = "Revised manuscript review workflow specimen"
    parts["word/document.xml"] = word.serialize_xml(document, parts["word/document.xml"])
    comments = ET.Element(f"{{{word.W}}}comments")
    comment = ET.SubElement(comments, f"{{{word.W}}}comment", {
        f"{{{word.W}}}id": "103", f"{{{word.W}}}author": "Robin Example", f"{{{word.W}}}date": "2026-11-04T12:00:00Z"})
    p = ET.SubElement(comment, f"{{{word.W}}}p")
    add_run(p, "Verify this against the source data.")
    parts["word/comments.xml"] = ET.tostring(comments, encoding="utf-8", xml_declaration=True)
    rels = ET.fromstring(parts["word/_rels/document.xml.rels"])
    ET.SubElement(rels, "{http://schemas.openxmlformats.org/package/2006/relationships}Relationship", {
        "Id": "rIdReviewComment", "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments", "Target": "comments.xml"})
    parts["word/_rels/document.xml.rels"] = word.serialize_xml(rels, parts["word/_rels/document.xml.rels"])
    types = ET.fromstring(parts["[Content_Types].xml"])
    ET.SubElement(types, "{http://schemas.openxmlformats.org/package/2006/content-types}Override", {
        "PartName": "/word/comments.xml", "ContentType": "application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"})
    parts["[Content_Types].xml"] = word.serialize_xml(types, parts["[Content_Types].xml"])
    with ZipFile(reviewed, "w", ZIP_DEFLATED) as archive:
        for name, content in parts.items():
            archive.writestr(name, content)


class WordSafetyTests(unittest.TestCase):
    def test_unsupported_content_is_not_silently_lost(self):
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            word.validate_ast({"blocks": [{"t": "RawInline", "c": ["latex", r"\unknown{Important text}"]}]}, set())

    def test_paths_cannot_escape_snapshot(self):
        with self.assertRaises(ValueError):
            word.inside(ROOT, "../private.tex")

    def test_comments_keep_escaped_percent(self):
        self.assertEqual(word.uncomment("Value 10\\% % private\n"), "Value 10\\% \n")

    def test_literal_percent_and_include_commands_are_preserved(self):
        literal = r"""\verb|total % count \input{missing}| \verb*+10%+
\begin{verbatim}
remainder = total % count
\input {missing}
\end{verbatim}
"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            main = root / "main.tex"
            main.write_text("% ignore \\verb|misleading\n" + literal + "% trailing comment\n")
            with patch.object(word, "ROOT", root):
                sources = set()
                result = word.flatten(main, sources)
            self.assertEqual(result, "\n" + literal + "\n")
            self.assertEqual(sources, {main})
        self.assertEqual(word.uncomment(literal), literal)

    def test_whitespace_and_parent_relative_includes_are_snapshotted(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            section = root / "sections" / "methods.tex"
            section.parent.mkdir()
            table = root / "tables" / "results.tex"
            table.parent.mkdir()
            table.write_text("Recorded result.")
            section.write_text("\\input \n {../tables/results}")
            main = root / "main.tex"
            main.write_text(r"\input {sections/methods}")
            with patch.object(word, "ROOT", root):
                sources = set()
                self.assertEqual(word.flatten(main, sources), "Recorded result.")
                self.assertEqual(sources, {main, section, table})
                section.write_text(r"\input {../../private}")
                with self.assertRaisesRegex(ValueError, "outside the project"):
                    word.flatten(main, set())

    def test_citation_metadata_is_validated_but_fallback_is_exempt(self):
        fallback = [{"t": "RawInline", "c": ["latex", r"\cite{example}"]}]
        for field in ("citationPrefix", "citationSuffix"):
            citation = {"t": "Cite", "c": [[{field: fallback}], fallback]}
            with self.assertRaisesRegex(ValueError, "Unsupported"):
                word.validate_ast(citation, set())
        word.validate_ast({"t": "Cite", "c": [[{"citationPrefix": [], "citationSuffix": []}], fallback]}, set())

    def test_cycles_and_missing_includes_fail(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            (root / "main.tex").write_text(r"\input{main}")
            with patch.object(word, "ROOT", root), self.assertRaisesRegex(ValueError, "Cyclic"):
                word.flatten(root / "main.tex", set())

    def test_reference_targets_are_explicit_and_unknown_targets_fail(self):
        ast = {"blocks": [
            {"t": "Header", "c": [1, ["sec:methods", [], []], [{"t": "Str", "c": "Methods"}]]},
            {"t": "Link", "c": [["", [], [["reference", "sec:methods"], ["reference-type", "ref+label"]]], [], ["#sec:methods", ""]]},
        ]}
        word.number_references(ast)
        self.assertEqual(ast["blocks"][1]["c"][1][0]["c"], "Section 1")
        ast["blocks"][1]["c"][0][2][0][1] = "eq:missing"
        with self.assertRaisesRegex(ValueError, "needs an adapter"):
            word.number_references(ast)

    def test_formatting_revisions_are_retained_for_manual_review(self):
        with tempfile.TemporaryDirectory() as temporary:
            docx = Path(temporary) / "formatting.docx"
            with ZipFile(docx, "w") as archive:
                archive.writestr("word/document.xml", f'''<w:document xmlns:w="{word.W}"><w:body><w:p>
                    <w:pPr><w:pPrChange w:id="7" w:author="Reviewer"><w:pPr><w:jc w:val="center"/></w:pPr></w:pPrChange></w:pPr>
                    <w:r><w:t>Review context</w:t></w:r></w:p></w:body></w:document>''')
            records = word.review_annotations(docx)
            self.assertEqual(records[0]["kind"], "pPrChange")
            self.assertEqual(records[0]["paragraph"], "Review context")
            self.assertIn("center", records[0]["xml"])


@unittest.skipUnless(shutil.which("pandoc"), "Pandoc is required for Word integration tests")
class WordIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        fixture(self.root)
        for target, name, value in ((word, "ROOT", self.root),
                                    (credit, "SOURCE", self.root / "project/contributors.json"),
                                    (credit, "OUTPUT", self.root / "paper/setup/contributions.tex")):
            patcher = patch.object(target, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.bundle = self.root / "bundle"
        word.export_bundle(self.bundle)

    def test_native_content_and_tracked_review_with_source_drift(self):
        original = self.bundle / "manuscript.docx"
        with ZipFile(original) as archive:
            document = archive.read("word/document.xml")
            self.assertIn(b"oMath", document)
            self.assertIn(b":tbl>", document)
            self.assertIn(b":drawing>", document)
            self.assertIn(b"trackRevisions", archive.read("word/settings.xml"))
        baseline = (self.bundle / "baseline.md").read_text()
        self.assertIn("Manuscript review workflow specimen", baseline)
        self.assertIn("Example Research Group", baseline)
        self.assertIn("Writing", baseline)
        self.assertIn("Section 1", baseline)
        self.assertIn("Table 1.", baseline)
        self.assertIn("Figure 1.", baseline)
        reviewed = self.root / "returned.docx"
        tracked_review(original, reviewed)
        main = self.root / "main.tex"
        main.write_text(main.read_text() + "\n% Later local work\n")
        before = hashlib.sha256(main.read_bytes()).hexdigest()
        output = self.root / "review"
        word.import_review(reviewed, self.bundle, output)
        self.assertEqual(hashlib.sha256(main.read_bytes()).hexdigest(), before)
        self.assertIn("12 units", (output / "accepted.md").read_text())
        self.assertIn("10 units", (output / "rejected.md").read_text())
        self.assertIn("Notes for coauthors", (output / "untracked.diff").read_text())
        self.assertIn("Revised manuscript", (output / "changes.diff").read_text())
        records = json.loads((output / "annotations.json").read_text())
        self.assertTrue(any(r["kind"] == "comment" and r["attributes"]["author"] == "Robin Example" for r in records))
        self.assertTrue(any(r["kind"] == "del" and r["text"] == "10" for r in records))
        self.assertEqual(json.loads((output / "review.json").read_text())["source_drift"], ["main.tex"])

    def test_baseline_tampering_and_overwrite_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "immutable"):
            word.export_bundle(self.bundle)
        (self.bundle / "baseline.md").write_text("Changed baseline")
        with self.assertRaisesRegex(ValueError, "modified"):
            word.import_review(self.bundle / "manuscript.docx", self.bundle, self.root / "review")

    def test_citation_locator_types_and_plurals(self):
        text = word.run_pandoc([
            "-f", "markdown", "-t", "plain", "--citeproc", "--bibliography", str(self.root / "references.bib"),
            "--csl", str(self.root / "tools/word/numeric.csl"),
        ], "[@schmiedmayer2026papertemplate, p. 2]\n\n"
           "[@schmiedmayer2026papertemplate, pp. 2-3]\n\n"
           "[@schmiedmayer2026papertemplate, sec. 2]\n\n"
           "[@schmiedmayer2026papertemplate, chap. 3]\n")
        self.assertIn("[1, p. 2]", text)
        self.assertIn("[1, pp. 2–3]", text)
        self.assertIn("[1, sec. 2]", text)
        self.assertIn("[1, chap. 3]", text)


if __name__ == "__main__":
    unittest.main()
