<!--
SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)

SPDX-License-Identifier: MIT
-->

# Tools

This directory contains workflow implementation rather than manuscript content.

- `scripts/` provides deterministic checks, reference management, and reproduction entry points.
- `tests/` protects those scripts and reference workflows.
- `skills/` defines bounded repository-local agent workflows.

Run the supported entry points through the root `Makefile` when possible.
Keep paper-specific analysis under `research/analysis/`, not in this directory.
