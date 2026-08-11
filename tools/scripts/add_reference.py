#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)
#
# SPDX-License-Identifier: MIT

"""Add one source-derived reference by citation file, PMID, or DOI."""

from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path

from reference_common import (
    BIB_PATH,
    REFERENCES_DIR,
    derive_key,
    download_pmc_pdf,
    download_pdf,
    ensure_claims,
    generated_bibliography,
    http_get,
    parse_citation,
    validate_pdf,
    write_abstract,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--citation-file", type=Path, help="Official citation export in BibTeX, NBIB, or RIS format.")
    source.add_argument("--pmid", help="PubMed PMID to retrieve as citation.nbib.")
    source.add_argument("--doi", help="DOI to retrieve as citation.bib.")
    parser.add_argument("--key", help="Stable citation key; otherwise derive surname + year + title word.")
    parser.add_argument("--pdf-file", type=Path, help="Lawfully obtained full-text PDF to copy as source.pdf.")
    parser.add_argument("--pdf-url", help="Direct, authorized PDF URL to download as source.pdf.")
    parser.add_argument(
        "--download-open-access-pdf",
        action="store_true",
        help="Download a PDF when the metadata contains a PMC open-access identifier.",
    )
    parser.add_argument("--replace", action="store_true", help="Replace source metadata in an existing key folder.")
    parser.add_argument("--timeout", type=int, default=30)
    return parser.parse_args()


def retrieve_citation(args: argparse.Namespace, temporary: Path) -> Path:
    if args.citation_file:
        source = args.citation_file.expanduser().resolve()
        if source.suffix.lower() not in {".bib", ".nbib", ".ris"}:
            raise ValueError("Citation file must use .bib, .nbib, or .ris")
        if not source.exists():
            raise FileNotFoundError(source)
        destination = temporary / f"citation{source.suffix.lower()}"
        shutil.copy2(source, destination)
        return destination
    if args.pmid:
        destination = temporary / "citation.nbib"
        destination.write_bytes(
            http_get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
                f"?db=pubmed&id={args.pmid}&rettype=medline&retmode=text",
                timeout=args.timeout,
            )
        )
        return destination
    destination = temporary / "citation.bib"
    doi = args.doi.removeprefix("https://doi.org/").removeprefix("http://doi.org/")
    destination.write_bytes(
        http_get(f"https://doi.org/{doi}", accept="application/x-bibtex", timeout=args.timeout)
    )
    return destination


def main() -> int:
    args = parse_args()
    REFERENCES_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="paper-reference-") as temporary_name:
        temporary = Path(temporary_name)
        citation_path = retrieve_citation(args, temporary)
        citation = parse_citation(citation_path)
        key = args.key or derive_key(citation)
        target = REFERENCES_DIR / key
        if target.exists() and not args.replace:
            raise FileExistsError(f"{target} already exists; use --replace only after verifying the stable key")
        target.mkdir(parents=True, exist_ok=True)
        if args.replace:
            for existing in target.glob("citation.*"):
                if existing.suffix.lower() in {".bib", ".nbib", ".ris"}:
                    existing.unlink()
        destination = target / citation_path.name
        shutil.copy2(citation_path, destination)
        write_abstract(target, citation, key, destination.name)
        ensure_claims(target, citation, key)

        pdf_target = target / "source.pdf"
        if args.pdf_file:
            pdf_source = args.pdf_file.expanduser().resolve()
            if not validate_pdf(pdf_source):
                raise ValueError(f"Not a valid PDF: {pdf_source}")
            shutil.copy2(pdf_source, pdf_target)
        elif args.pdf_url:
            download_pdf(args.pdf_url, pdf_target, timeout=max(args.timeout, 60))
        elif args.download_open_access_pdf and citation.pmcid:
            download_pmc_pdf(citation.pmcid, pdf_target, timeout=max(args.timeout, 60))
        elif args.download_open_access_pdf:
            print("WARNING: citation metadata contains no PMCID; no PDF was downloaded")

    bibliography, problems = generated_bibliography()
    if problems:
        for problem in problems:
            print(f"ERROR: {problem}")
        return 1
    BIB_PATH.write_text(bibliography, encoding="utf-8")
    print(f"Added {key} and regenerated {BIB_PATH.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
