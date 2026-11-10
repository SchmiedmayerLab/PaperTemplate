<!--
SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)

SPDX-License-Identifier: MIT
-->

# Paper Skills

These repository-local skills turn recurring literature, reference, review, revision, and consistency tasks into bounded workflows.
Each skill has a narrow trigger and an explicit output contract.

| Skill | Purpose |
| --- | --- |
| [Review orchestrator](paper-review-orchestrator/SKILL.md) | Coordinate a bounded review across multiple passes or reviewers. |
| [Paper reviewer](paper-reviewer/SKILL.md) | Critique the manuscript from a journal reviewer's perspective. |
| [Literature scout](paper-literature-scout/SKILL.md) | Find and verify evidence for specific claims. |
| [Reference curator](paper-reference-curator/SKILL.md) | Maintain source citation assets and the generated bibliography. |
| [Section refiner](paper-section-refiner/SKILL.md) | Revise one section while preserving evidence and author voice. |
| [Consistency auditor](paper-consistency-auditor/SKILL.md) | Check terminology, numbers, claims, citations, and artifacts across the paper. |
| [Word review](paper-word-review/SKILL.md) | Reconcile returned edits against the export baseline and current LaTeX source. |

Automatic discovery depends on the active agent environment.
When a skill is not discovered, read its `SKILL.md` directly before using it.
Keep these skills repository-local; install them into a personal skill directory only at the user's request.
Follow current platform and user authorization for delegation.
Assign sub-agents only independent, non-overlapping work and keep final synthesis with the primary agent.
