<!--
SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)

SPDX-License-Identifier: MIT
-->

# Article Profiles

Use these profiles as structural starting points, then follow the selected venue's official article-type instructions.
Record the selected profile and section changes in `project/notes/00_project_brief.md`.
Delete unused sections rather than leaving empty headings or irrelevant terminology.

## Empirical research article

Use the default order:

1. Abstract
2. Introduction
3. Methods
4. Results
5. Discussion
6. Conclusion when required
7. Availability and declarations

Merge Related Work into the Introduction or Discussion unless the field or venue expects a separate section.

## Software or systems paper

Retain the standard evidence boundary while adapting Methods and Results:

1. Introduction and unmet use case
2. Related software and differentiating gap
3. Software architecture and design rationale
4. Core functionality and user workflows
5. Installation, configuration, and deployment
6. Reuse, extension, interoperability, privacy, and governance
7. Verification through tests, deployment evidence, performance, or representative use
8. Limitations and roadmap
9. Code, documentation, version, archive, license, and support statement

Treat architecture description as Methods and tested behavior as Results.
Do not substitute implementation description for evidence that the software works as claimed.

## Application note or short communication

Compress the story without removing the evidence chain:

1. Problem and contribution
2. Focused implementation or method
3. A concise result or worked use case
4. Availability
5. Bounded limitations and implications

Move secondary implementation detail into documentation or a supplement while retaining enough information to evaluate the main claim.

## Protocol or design paper

Replace completed-results language with prespecified plans:

1. Background and rationale
2. Objectives or hypotheses
3. Design, setting, eligibility, intervention or system, outcomes, and analysis
4. Ethics, governance, dissemination, and status
5. Strengths and limitations of the design

Do not present planned analyses or enrollment as completed findings.

## Review or landscape paper

Add a reproducible search and screening workflow, eligibility criteria, extraction schema, synthesis method, and reporting checklist.
Keep included-source selection and evidence grading distinct from narrative interpretation.

## Qualitative or mixed-methods paper

Describe sampling, researcher roles, data collection, analysis, reflexivity, disagreement handling, and reporting guidance.
Separate qualitative themes from quantitative estimates when the design combines methods.
Retain enough de-identified source and coding provenance to support an audit without exposing participants.
