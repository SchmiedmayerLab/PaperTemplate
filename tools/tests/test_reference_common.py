# SPDX-FileCopyrightText: 2026 Stanford University and the project authors (see CONTRIBUTORS.md)
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import sys
import io
import tarfile
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from reference_common import Citation, citation_to_bib, derive_key, ensure_claims, extract_pdf_from_oa_archive, parse_bib, parse_nbib, parse_ris, split_bib_entries, write_abstract


class ReferenceCommonTests(unittest.TestCase):
    def test_abstract_refresh_preserves_claim_notes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            citation = Citation(title="Example Source", year="2026", abstract="Initial abstract.")
            write_abstract(folder, citation, "example2026source", "citation.bib")
            ensure_claims(folder, citation, "example2026source")
            claims_path = folder / "claims.md"
            claims_path.write_text("durable manuscript note\n", encoding="utf-8")
            citation.abstract = "Refreshed abstract."
            write_abstract(folder, citation, "example2026source", "citation.bib")
            ensure_claims(folder, citation, "example2026source")
            self.assertEqual(claims_path.read_text(encoding="utf-8"), "durable manuscript note\n")

    def test_parse_nbib_and_generate_key(self) -> None:
        citation = parse_nbib(
            "PMID- 12345678\n"
            "TI  - A Reproducible Scientific Workflow\n"
            "FAU - Example, Alice B\n"
            "DP  - 2026 Jan\n"
            "JT  - Journal of Examples\n"
            "LID - 10.1000/example [doi]\n"
            "AB  - A structured abstract.\n"
        )
        self.assertEqual(citation.pmid, "12345678")
        self.assertEqual(citation.doi, "10.1000/example")
        self.assertEqual(derive_key(citation), "example2026reproducible")
        self.assertIn("doi = {10.1000/example}", citation_to_bib(citation, derive_key(citation)))

    def test_parse_ris(self) -> None:
        citation = parse_ris(
            "TY  - JOUR\n"
            "AU  - Example, Alice\n"
            "TI  - Transparent Methods\n"
            "PY  - 2025\n"
            "JO  - Testing Journal\n"
            "SP  - 10\n"
            "EP  - 20\n"
            "ER  -\n"
        )
        self.assertEqual(citation.pages, "10--20")
        self.assertEqual(citation.year, "2025")

    def test_bibtex_preserves_fields_and_rekeys(self) -> None:
        source = (
            "@inproceedings{oldKey,\n"
            "  author = {Example, Alice},\n"
            "  title = {A Tool for Reproducible Work},\n"
            "  booktitle = {Proceedings of Testing},\n"
            "  year = {2024},\n"
            "  eprint = {2401.00001}\n"
            "}\n"
        )
        citation = parse_bib(source)
        generated = citation_to_bib(citation, "example2024tool")
        self.assertIn("@inproceedings{example2024tool,", generated)
        self.assertIn("booktitle", generated)
        self.assertIn("eprint", generated)

    def test_single_line_crossref_bibtex(self) -> None:
        citation = parse_bib(
            "@article{Old, title={Single Line Metadata}, author={Example, Alice}, year={2026}, DOI={10.1000/single}}"
        )
        self.assertEqual(citation.title, "Single Line Metadata")
        self.assertEqual(citation.year, "2026")
        self.assertEqual(citation.doi, "10.1000/single")

    def test_split_multiple_bib_entries(self) -> None:
        entries = split_bib_entries(
            "@article{one, title={First}, year={2020}}\n"
            "@article{two, title={Second}, year={2021}}\n"
        )
        self.assertEqual(len(entries), 2)

    def test_extract_pdf_from_open_access_archive(self) -> None:
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
            payload = b"%PDF-1.4\nexample\n"
            member = tarfile.TarInfo("article/source.pdf")
            member.size = len(payload)
            archive.addfile(member, io.BytesIO(payload))
        self.assertEqual(extract_pdf_from_oa_archive(buffer.getvalue()), payload)


if __name__ == "__main__":
    unittest.main()
