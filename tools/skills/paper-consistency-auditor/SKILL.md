---
# SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)
#
# SPDX-License-Identifier: MIT

name: paper-consistency-auditor
description: Audit a scientific paper across LaTeX sections, supplement, notes, data, analysis, references, figures, tables, and declarations for inconsistent terminology, numbers, versions, claims, citations, artifact provenance, cross-references, and submission metadata. Use after substantive revisions, before coauthor circulation, for reproducibility review, or before submission.
---

# Paper Consistency Auditor

Read `../../../AGENTS.md`, the project brief, venue requirements, manuscript, supplement, evidence inventory, data manifest, reproducibility manifest, and reference inventory.

## Audit Sequence

1. Identify the canonical contribution, population or system, primary outcomes, versions, dates, and terminology.
2. Trace each item across title, abstract, sections, figures, tables, supplement, availability statements, and declarations.
3. Compare Methods definitions with Results denominators and Discussion claims.
4. Compare every reported number, unit, interval, sample size, and version across locations.
5. Check acronym expansion, labels, citations, figure and table callouts, and bibliography keys.
6. Check that availability, ethics, funding, conflicts, and author-contribution statements agree with known project facts.
7. Trace each generated figure and table from manuscript callout to declared output, exact command, versioned code, environment, and foundational data.
8. Confirm that foundational inputs are inventoried, immutable, checksummed when permitted, and distinct from interim and derived files.
9. Confirm that generated exports have no undocumented manual edits and that restricted-data steps are described honestly.
10. Run `make check`, `make reproducibility-check`, and `python3 tools/scripts/regenerate_bib_from_references.py --check`.
11. Run `make reproduce` from a clean clone or clean worktree when the audit includes independent reproducibility.
12. Compile and inspect the rendered PDF when the audit includes submission readiness.

Do not silently choose between conflicting scientific values.
Report the conflict, identify the candidate sources of truth, and request an author decision when the repository does not resolve it.

## Output

Return a table with severity, inconsistent item, locations, likely source of truth, and required action.
Add a source-to-artifact traceability table when reproducibility is in scope.
End with automated-check status, skipped restricted-data steps, unresolved author decisions, and a prioritized repair order.
