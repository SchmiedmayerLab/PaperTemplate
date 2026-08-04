---
# SPDX-FileCopyrightText: 2026 Stanford University and the project authors (see CONTRIBUTORS.md)
#
# SPDX-License-Identifier: MIT

name: paper-literature-scout
description: Find, compare, and verify claim-specific primary literature for a scientific manuscript. Use when a section has unsupported claims, weak quantitative grounding, outdated citations, a related-work gap, or a need for exact source support before prose or BibTeX assets are added.
---

# Paper Literature Scout

Read `../../../AGENTS.md`, `../../../project/notes/00_project_brief.md`, `../../../project/notes/01_venue_requirements.md`, the target section, and its current citations before searching.

## Workflow

1. Convert the target prose or outline into narrow evidence questions.
2. Separate claims needing primary evidence from claims needing a review, guideline, standard, or official source.
3. Search authoritative databases and official sources, prioritizing peer-reviewed primary records.
4. Open each candidate source and verify title, authors, venue, year, study object or population, design, exact result, and limitations.
5. Prefer the published record over a preprint unless the preprint is the current primary record or contains necessary additional detail.
6. Extract the exact numeric value, denominator, time window, and population context for quantitative claims.
7. Record where the support occurs, including page, section, table, figure, or quoted clause when needed for traceability.
8. Compare the source with the proposed manuscript wording and flag any overstatement.
9. Recommend the smallest source set that supports the paper without turning the section into a review article.

Do not add a citation because it is merely adjacent to the topic.
Do not rely on search-result snippets, secondary summaries, or unverified metadata.
Respect source quotation and copyright limits.

## Repository Changes

If the user asks to add source assets, use the workflow in `../../../research/literature/README.md` and hand off each verified identifier to `paper-reference-curator`.
Update `../../../research/literature/<key>/claims.md` and `../../../project/notes/02_evidence_inventory.md` when the work establishes claim-level support.
Do not hand-edit generated `../../../references.bib`.

## Output

Return:

1. Evidence gaps ordered by importance.
2. Best candidate sources with stable identifiers and source type.
3. Exact findings, denominators, and limitations relevant to each claim.
4. Recommended manuscript location and wording boundary.
5. Sources rejected and the reason.
6. Reference assets that should be added or refreshed.
