---
# SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)
#
# SPDX-License-Identifier: MIT

name: paper-reference-curator
description: Maintain a scientific paper's source-first citation assets, local abstracts, eligible full-text PDFs, and generated BibTeX bibliography. Use when adding a PMID, DOI, NBIB, RIS, or BibTeX record; auditing missing source assets; correcting metadata; or synchronizing references.bib with references folders.
---

# Paper Reference Curator

Read `../../../AGENTS.md` and `../../../research/literature/README.md` before changing citation assets.

## Workflow

1. Verify that the publication is the correct source for the intended claim.
2. Check for an existing key, DOI, PMID, PMCID, or title match before adding a folder.
3. Preserve stable existing keys.
4. Add new records through `python3 tools/scripts/add_reference.py --pmid`, `--doi`, or `--citation-file`.
5. Use `--pdf-file` for lawfully obtained local full text, `--pdf-url` for an authorized direct URL, or `--download-open-access-pdf` only for an eligible PMC record.
6. Inspect the resulting `research/literature/<key>/citation.*`, generated `abstract.md`, durable `claims.md`, and optional `source.pdf`.
7. Add claim-level source notes to `claims.md` without altering the generated source abstract.
8. Run `python3 tools/scripts/regenerate_bib_from_references.py --in-place`.
9. Run `python3 tools/scripts/organize_references.py --report-only` and `python3 tools/scripts/regenerate_bib_from_references.py --check`.
10. Rebuild the manuscript when cited keys changed.

Correct metadata at the source citation asset.
Do not patch generated `references.bib` directly.
Do not delete unknown reference folders during an audit.
Do not download or commit a publisher PDF without lawful access and appropriate redistribution rights.
Do not assign the repository's MIT license to source metadata, abstracts, or full text without verifying the asset's terms.

## Validation

Confirm:

- the folder name and BibTeX key agree;
- title, authors, venue, year, and identifiers match the primary record;
- duplicate DOI records are absent;
- `abstract.md` identifies its metadata source;
- `claims.md` preserves verified support notes across metadata refreshes;
- a missing PDF is reported as absent rather than treated as a citation failure;
- every tracked third-party citation or abstract asset has an appropriate SPDX annotation or sidecar;
- the generated bibliography round-trips cleanly;
- all manuscript citations resolve after compilation.

## Output

Report what changed, missing assets, metadata anomalies, bibliography synchronization, and build status.
