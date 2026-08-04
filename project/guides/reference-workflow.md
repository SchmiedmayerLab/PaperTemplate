<!--
SPDX-FileCopyrightText: 2026 Stanford University and the project authors (see CONTRIBUTORS.md)

SPDX-License-Identifier: MIT
-->

# Reference Workflow

## Design

The reference folder is the durable evidence layer and `references.bib` is a generated manuscript interface.
Each citation key owns its official metadata export, generated searchable abstract, durable claim notes, and optional local full text.
This separation makes citation metadata reviewable, lets agents inspect sources without searching the entire workspace, and prevents manual BibTeX changes from drifting away from source records.

## Add metadata

Use one source per command:

```bash
python3 tools/scripts/add_reference.py --citation-file ~/Downloads/export.ris
python3 tools/scripts/add_reference.py --doi 10.1000/example
python3 tools/scripts/add_reference.py --pmid 12345678
```

Use `--key` to preserve a chosen stable key.
Use `--replace` only after verifying that the existing folder represents the same publication.
The importer accepts one BibTeX, NBIB, or RIS record per file and regenerates `references.bib` after a successful addition.

## Attach authorized full text

Copy a lawfully obtained PDF:

```bash
python3 tools/scripts/add_reference.py --doi 10.1000/example --pdf-file ~/Downloads/article.pdf
```

Download from a direct authorized URL:

```bash
python3 tools/scripts/add_reference.py --doi 10.1000/example --pdf-url https://example.org/article.pdf
```

As an optional biomedical convenience, retrieve an eligible PMC open-access PDF:

```bash
python3 tools/scripts/add_reference.py --pmid 12345678 --download-open-access-pdf
python3 tools/scripts/organize_references.py --keys example2026paper --download-missing-pdfs
```

The PMC path uses the [official unsigned open-data S3 service](https://pmc.ncbi.nlm.nih.gov/tools/pmcaws/) and retains a legacy open-access-package fallback during the service transition.
Automatic retrieval still requires a PMCID and an article record exposed through PMC's open datasets.
A missing PDF is not a citation error.

For other fields, attach a lawfully obtained local PDF or use an authorized direct URL.

Downloaded PDFs remain ignored by Git.
Before redistributing any full text, inspect its article-level license and the destination repository's access controls.
Before committing a citation export or source abstract, verify its metadata and text-reuse terms and add the corresponding SPDX metadata.
Do not assign MIT to third-party source content by default.

## Verify a claim

1. Open the primary source, preferably `source.pdf` when available.
2. Confirm the population or system, design, date, metric, denominator, and limitation relevant to the manuscript claim.
3. Add a claim-level note to the reference folder's `claims.md`.
4. Add the citation to the exact sentence it supports.
5. Record high-risk or quantitative support in `project/notes/02_evidence_inventory.md`.

Do not edit the source abstract.
`abstract.md` is generated and may be overwritten by `--refresh-abstracts` or `--replace`.
`claims.md` is never overwritten by those operations.
Do not turn a thematic citation into support for an exact number or causal claim.

## Regenerate and audit

```bash
python3 tools/scripts/regenerate_bib_from_references.py --in-place
python3 tools/scripts/organize_references.py --report-only
python3 tools/scripts/regenerate_bib_from_references.py --check
```

The audit reports missing citation exports, missing abstracts, optional full-text status, invalid metadata, and duplicate DOI records.
It never prunes unrecognized reference folders.

## Troubleshooting

- If DOI metadata is incomplete, download an official publisher or database citation export and import it with the stable key.
- If a PMID has no PMCID, attach a lawfully obtained PDF or retain metadata and abstract assets without full text.
- If the generated key is undesirable, remove the newly created folder before citing it and add the record again with `--key`.
- If metadata are semantically wrong, replace the source export and regenerate rather than patching `references.bib`.
- If a venue suppresses DOI, URL, or identifier fields, change the venue bibliography style instead of deleting source metadata.
