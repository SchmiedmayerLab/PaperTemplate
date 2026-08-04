#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2026 Stanford University and the project authors (see CONTRIBUTORS.md)
#
# SPDX-License-Identifier: MIT

"""Audit source assets, refresh summaries, and retrieve eligible OA PDFs."""

from __future__ import annotations

import argparse
from reference_common import (
    INVENTORY_PATH,
    all_reference_folders,
    choose_citation_file,
    download_pmc_pdf,
    ensure_claims,
    parse_citation,
    validate_pdf,
    write_abstract,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--keys", help="Comma-separated citation keys; default is every reference folder.")
    parser.add_argument("--report-only", action="store_true", help="Audit and rewrite only the inventory report.")
    parser.add_argument("--refresh-abstracts", action="store_true", help="Regenerate abstract.md from citation exports.")
    parser.add_argument(
        "--download-missing-pdfs",
        action="store_true",
        help="Retrieve missing PDFs only for citation exports containing a PMC open-access identifier.",
    )
    parser.add_argument("--timeout", type=int, default=30)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    requested = {key.strip() for key in args.keys.split(",")} if args.keys else None
    folders = [folder for folder in all_reference_folders() if requested is None or folder.name in requested]
    if requested:
        found = {folder.name for folder in folders}
        for missing in sorted(requested - found):
            print(f"ERROR: unknown reference key {missing}")
        if requested - found:
            return 1

    rows: list[str] = []
    problems: list[str] = []
    for folder in folders:
        citation_file = choose_citation_file(folder)
        if not citation_file:
            rows.append(f"| `{folder.name}` | missing | missing | missing | missing |")
            problems.append(f"{folder.name}: missing citation export")
            continue
        try:
            citation = parse_citation(citation_file)
        except (OSError, ValueError) as error:
            rows.append(f"| `{folder.name}` | invalid | unknown | unknown | unknown |")
            problems.append(f"{folder.name}: {error}")
            continue
        abstract_path = folder / "abstract.md"
        claims_path = folder / "claims.md"
        if args.refresh_abstracts and not args.report_only:
            write_abstract(folder, citation, folder.name, citation_file.name)
            ensure_claims(folder, citation, folder.name)
        pdf_path = folder / "source.pdf"
        if args.download_missing_pdfs and not args.report_only and not validate_pdf(pdf_path):
            if citation.pmcid:
                try:
                    download_pmc_pdf(citation.pmcid, pdf_path, timeout=max(args.timeout, 60))
                except (OSError, ValueError) as error:
                    problems.append(f"{folder.name}: PDF download failed: {error}")
            else:
                problems.append(f"{folder.name}: no PMCID for automatic open-access PDF retrieval")
        citation_status = citation_file.name
        abstract_status = "present" if abstract_path.exists() else "missing"
        claims_status = "present" if claims_path.exists() else "missing"
        pdf_status = "present" if validate_pdf(pdf_path) else "missing or intentionally absent"
        rows.append(
            f"| `{folder.name}` | `{citation_status}` | {abstract_status} | {claims_status} | {pdf_status} |"
        )
        if not citation.title or not citation.year:
            problems.append(f"{folder.name}: citation is missing title or year")
        if not abstract_path.exists():
            problems.append(f"{folder.name}: missing abstract.md")
        if not claims_path.exists():
            problems.append(f"{folder.name}: missing claims.md")

    report = [
        "# Reference Asset Inventory",
        "",
        "| Citation key | Metadata | Abstract | Claim notes | Full text |",
        "|---|---|---|---|---|",
        *rows,
        "",
        "## Findings",
        "",
    ]
    report.extend(f"- {problem}" for problem in problems)
    if not problems:
        report.append("- No structural problems found.")
    INVENTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    INVENTORY_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Audited {len(folders)} references and wrote {INVENTORY_PATH}")
    for problem in problems:
        print(f"WARNING: {problem}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
