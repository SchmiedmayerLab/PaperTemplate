<!--
SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)

SPDX-License-Identifier: MIT
-->

# Conditional Domain Checklists

Apply only the checklists relevant to the selected article profile and contribution.
Do not retain their terminology in an unrelated paper.

## Human-participant or clinical work

- Record ethics review, consent, privacy, data governance, recruitment, eligibility, dates, and sample accounting.
- Distinguish usability, retrospective analysis, human validation, prospective evaluation, and clinical effectiveness.
- Do not use `safe`, `clinical`, `diagnostic`, or `therapeutic` beyond the evaluated endpoint and approved scope.
- Select the applicable reporting guideline and record it in `project/notes/01_venue_requirements.md`.

## Software or systems work

- Identify the released version, repository, archive, license, dependencies, supported environments, and maintenance status.
- Separate architecture description from evidence that the implementation works as claimed.
- Report tests, representative use, deployment evidence, performance, failure modes, and reuse instructions appropriate to the contribution.
- State what a new institution can reuse directly and what requires local configuration, governance, or collaboration.

## Machine learning or AI work

- Define training, tuning, evaluation, and runtime inputs separately.
- Record model versions, prompts, sampling settings, seeds, tools, retrieval sources, output limits, and evaluation rubrics.
- Check leakage, overlap, circularity, grader dependence, comparator fairness, uncertainty, and subgroup behavior.
- Do not infer privacy, security, clinical readiness, autonomy, or cost savings from local execution or benchmark performance alone.
- Use `agentic`, `reference-free`, and similar labels only after defining the implemented mechanism and withheld information.

## Review or evidence-synthesis work

- Preserve database queries, dates, eligibility criteria, deduplication, screening decisions, extraction schemas, and synthesis code.
- Record protocol registration and deviations.
- Follow the applicable reporting checklist.

## Protocol or design work

- Use planned or conditional language until procedures and analyses are complete.
- Separate prespecified decisions from open design questions.
- Report study status without presenting planned outcomes as findings.

## Qualitative work

- Describe sampling, researcher roles, data collection, coding, reflexivity, saturation or information power, disagreement resolution, and software.
- Preserve the approved de-identification and quotation workflow.
- Follow the selected qualitative reporting standard.
