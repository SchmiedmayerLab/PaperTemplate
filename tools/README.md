<!--
SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)

SPDX-License-Identifier: MIT
-->

# Tools

This directory contains workflow implementation rather than manuscript content.

- [scripts/](scripts/) provides deterministic checks, reference management, reproduction entry points, and the arXiv source packager.
- [tests/](tests/) protects those scripts and reference workflows.
- [skills/](skills/README.md) defines bounded repository-local agent workflows.

Run the supported entry points through the root [Makefile](../Makefile) when possible.
`make contributions` generates the CRediT statement from [contributors.json](../project/contributors.json); `make check` verifies synchronization.
`make word` exports an immutable Word review bundle using Pandoc; `make word-review` extracts returned feedback without editing manuscript source.
See the [Word review guide](../project/guides/word-review.md) for conversion limits and reconciliation.
`make tex-check` compiles a specimen against the shared setup and verifies `cleveref` reference types, including shared theorem counters.
`make arxiv-check` runs that check and a temporary packaging/rebuild smoke test without publishing a ZIP.
`make arxiv` runs the strict final-readiness gate and publishes only a validated archive; `ARXIV_DATE=YYYY-MM-DD` fixes its release date.
Keep paper-specific analysis under [research/analysis/](../research/analysis/).

## Continuous integration

The [validation workflow](../.github/workflows/validate.yml) runs repository checks, TeX Live 2026 PDF builds, and TeX Live 2025 arXiv validation in parallel with independent checkouts.
The [Repository Standards workflow](../.github/workflows/repository-standards.yml) runs licensing, Markdown link, workflow lint, and repository-surface checks once.
Require `Repository Checks`, `Build LaTeX Manuscript`, `Validate arXiv Package`, and all four `Standards / ...` checks in the main-branch ruleset.
When renaming or consolidating jobs, update the required check names without weakening the corresponding validation or other merge protections.
