<!--
SPDX-FileCopyrightText: 2026 Stanford University and the project authors (see CONTRIBUTORS.md)

SPDX-License-Identifier: MIT
-->

# Evidence Inventory

Use one row per manuscript claim, result, figure, table, or release artifact that requires traceability.
Use stable identifiers so manuscript prose, pipeline steps, and review comments can refer to the same evidence item.

| ID | Claim or artifact | Foundational input and version | Code and configuration | Exact command | Environment and seed | Output or source location | Manuscript location | Verification status |
|---|---|---|---|---|---|---|---|---|
| EVID-001 | TODO | TODO | TODO | TODO | TODO | TODO | TODO | planned |

For empirical literature claims, record the citation key, the precise supported statement, and the relevant page, section, table, or figure.
For computed results, use the matching step identifier from `research/reproducibility/pipeline.json` and the matching data entry from `research/data/manifest.tsv`.
Record input and output checksums in the reproduction run record when feasible.
Do not mark an item verified until the cited source or generated output has been opened and checked.
