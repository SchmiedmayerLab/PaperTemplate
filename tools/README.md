<!--
SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)

SPDX-License-Identifier: MIT
-->

# Tools

This directory contains workflow implementation rather than manuscript content.

- `scripts/` provides deterministic checks, reference management, reproduction entry points, and the arXiv source packager.
- `tests/` protects those scripts and reference workflows.
- `skills/` defines bounded repository-local agent workflows.

Run the supported entry points through the root `Makefile` when possible.
`make tex-check` compiles a specimen against the shared setup and verifies `cleveref` reference types, including shared theorem counters.
`make arxiv-check` runs that check and a temporary packaging/rebuild smoke test without publishing a ZIP.
`make arxiv` runs the strict final-readiness gate and publishes only a validated archive; `ARXIV_DATE=YYYY-MM-DD` fixes its release date.
Keep paper-specific analysis under `research/analysis/`, not in this directory.
