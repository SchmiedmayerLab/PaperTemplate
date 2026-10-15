<!--
SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)

SPDX-License-Identifier: MIT
-->

# Submission Checklist

## Scientific integrity

- [ ] The title, abstract, main text, figures, tables, supplement, and availability statements use the same terminology.
- [ ] Every primary claim is supported by a result, citation, protocol feature, governance mechanism, or clearly marked hypothesis.
- [ ] The Results report findings without interpretation that belongs in the Discussion.
- [ ] Limitations bound the claims and future work follows from the evidence.
- [ ] All sample sizes, denominators, dates, versions, and confidence intervals agree across artifacts.

## Reproducibility and references

- [ ] `make submission-check` succeeds.
- [ ] `research/data/manifest.tsv` inventories every foundational and external input.
- [ ] Foundational data are immutable, licensed or governed, documented, and checksummed where permitted.
- [ ] The analysis environment and all result-affecting versions, configurations, and seeds are recorded.
- [ ] Every external repository is a registered submodule or has another justified immutable reference.
- [ ] Every submodule is initialized at the exact superproject commit recorded in `research/reproducibility/submodules.tsv`.
- [ ] All affected results were regenerated after the last submodule pointer update.
- [ ] Every generated figure and table is declared in `research/reproducibility/pipeline.json`.
- [ ] A clean reproduction generated every available artifact from foundational inputs and tracked code.
- [ ] Restricted-data steps were run in the governed environment and are distinguished from public or synthetic CI checks.
- [ ] No manually edited generated exports, notebook outputs, caches, or stale derived files are manuscript inputs.
- [ ] `references.bib` is synchronized with the source folders.
- [ ] Every cited source was opened and verified against the supported claim.
- [ ] Durable source support is recorded in `claims.md`, not generated `abstract.md`.
- [ ] Code, data, software, model, protocol, and license statements use persistent identifiers where available.
- [ ] Figure and table generation is reproducible from documented inputs and commands.

## Venue and administration

- [ ] Current official venue requirements are recorded with access dates.
- [ ] Word, page, reference, figure, and supplement limits are satisfied.
- [ ] Reporting guidelines and checklists are complete.
- [ ] Ethics, consent, funding, conflicts, author contributions, acknowledgments, and AI-assistance statements are correct.
- [ ] All authors approved the final manuscript and author order.
- [ ] Names, affiliations, ORCIDs, author order, CRediT roles, and corresponding-author details are verified.
- [ ] Double-blind submissions contain no identifying text, PDF metadata, repository links, acknowledgments, or file names.
- [ ] The preprint, software, data, and archival-release plan is consistent with venue and funder policies.

## Rendered artifacts

- [ ] The final PDF was rebuilt from a clean state and visually inspected page by page.
- [ ] No TODOs, placeholders, comments, tracked changes, clipped content, broken references, or missing glyphs remain.
- [ ] Headings, floats, captions, equations, references, and page breaks are readable.
- [ ] The exact upload files were opened after export.
- [ ] The arXiv ZIP, when applicable, contains only recorder-derived dependencies allowed by `project/submission/arxiv.json` and compiles after isolated extraction.
- [ ] The arXiv-generated PDF and processing log were reviewed before submission completion.
- [ ] The archived date is fixed and reference names are correct.
- [ ] The manuscript license is selected in arXiv; any input-specific notice obligations are reviewed and required extras explicitly configured.
- [ ] Every packaged source file, binary asset, embedded metadata field, and link was reviewed for internal or private content; PDF equivalence is not a privacy audit.
- [ ] Meaningful figures have alt text, and arXiv HTML was reviewed when available; PDF compilation alone does not verify accessibility.
- [ ] The submitted commit, release identifiers, artifact checksums, venue, date, and manuscript identifier are recorded.
- [ ] The accepted-manuscript and publication-record archival plan is documented.
