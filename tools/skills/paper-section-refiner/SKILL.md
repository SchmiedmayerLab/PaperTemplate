---
# SPDX-FileCopyrightText: 2026 Stanford University and the project authors (see CONTRIBUTORS.md)
#
# SPDX-License-Identifier: MIT

name: paper-section-refiner
description: Revise one scientific manuscript section after its strategy and evidence are defined. Use for focused rewriting of an abstract, Introduction, Methods, Results, Discussion, availability statement, declaration, caption, or response text while preserving bounded claims, author voice, one-sentence-per-line LaTeX, and cross-document terminology.
---

# Paper Section Refiner

Read `../../../AGENTS.md`, the project brief, venue requirements, the complete target section, directly neighboring sections, and relevant evidence notes before editing.

## Workflow

1. State the section's job and the highest-risk weakness.
2. Distinguish missing evidence, missing method detail, weak logic, excess scope, and weak prose.
3. Resolve substantive gaps before polishing style.
4. Make the smallest edit that fixes the underlying problem.
5. Preserve approved language, source-trace notes, labels, citations, and semantic commands unless a change is necessary.
6. Prefer one idea and one evidentiary claim per sentence.
7. Prefer short adjacent sentences and one-purpose paragraphs over stacked clauses.
8. Keep the subject and main verb near the beginning.
9. Remove em dashes, avoid `because`, and replace vague evaluative language with the measured endpoint or evidence.
10. Put every prose sentence on its own physical source line.
11. Scan the complete section for any wording pattern the user identified as a general problem.
12. Keep Results factual and Discussion interpretive.
13. Propagate changed terminology, numbers, and framing to dependent artifacts.
14. Record project-specific feedback in the feedback ledger and cross-paper preferences in `AGENTS.md`.
15. Run `make check`, compile the paper, and inspect affected rendered pages.

Do not invent data, methods, citations, approvals, versions, dates, or author decisions.
Do not remove a TODO until the source or manuscript visibly resolves it.
Do not expand the paper's scope merely to make the prose sound more important.
Do not reintroduce wording that the author previously rejected or revise approved wording without a concrete precision or readability benefit.

## Output

When editing, return the revised source and a concise change summary.
When advising only, return the revision plan, evidence or author inputs needed, and remaining risks.
