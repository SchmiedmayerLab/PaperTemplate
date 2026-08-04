---
# SPDX-FileCopyrightText: 2026 Stanford University and the project authors (see CONTRIBUTORS.md)
#
# SPDX-License-Identifier: MIT

name: paper-review-orchestrator
description: Coordinate a bounded multi-pass or permitted multi-agent review of a scientific paper. Use for a full manuscript review, revision campaign, submission-readiness pass, or parallel work spanning literature, references, methods, reproducibility, claims, consistency, and rendered layout.
---

# Paper Review Orchestrator

Read `../../../AGENTS.md`, the project brief, venue requirements, and the current manuscript before assigning or sequencing review work.

## Delegation Boundary

Follow the active platform and user authorization rules for sub-agents.
Use delegation only when independent, bounded tasks can run safely in parallel.
Run the same passes sequentially when delegation is unavailable or would create conflicting edits.
Do not broaden the task beyond the manuscript, evidence, and systems placed in scope.

## Orchestration Workflow

1. Define the requested outcome and current manuscript state.
2. Identify the story spine and highest-risk editorial issue.
3. Select only the specialist passes needed:
   - use `paper-reviewer` for scientific and editorial critique;
   - use `paper-literature-scout` for narrow evidence gaps;
   - use `paper-reference-curator` for source assets and bibliography changes;
   - use `paper-section-refiner` after strategy and evidence are resolved;
   - use `paper-consistency-auditor` after substantive changes.
4. Give each sub-agent a non-overlapping scope, raw artifact paths, relevant source paths, and a precise output contract.
5. Prevent concurrent edits to the same file.
6. Preserve independent review integrity by omitting the intended answer and other agents' conclusions.
7. Synthesize findings by evidence and severity rather than by vote.
8. Resolve conflicts against primary sources, current project decisions, and the user's stated intent.
9. Apply or recommend the smallest coherent revision set.
10. Run reference synchronization, reproducibility checks, declared artifact generation, repository checks, compilation, and rendered PDF inspection.
11. Update durable notes and report unresolved author decisions.

## Default Pass Order

1. Story and contribution.
2. Methods and reproducibility.
3. Results and quantitative integrity.
4. Data-to-artifact reproducibility.
5. Claims and literature support.
6. Terminology and cross-artifact consistency.
7. Venue compliance and declarations.
8. Rendered layout and final artifact inspection.

## Output

Return the synthesized findings, changes made, validation evidence, preserved scope decisions, and remaining author actions.
