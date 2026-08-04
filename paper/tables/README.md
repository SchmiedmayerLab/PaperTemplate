<!--
SPDX-FileCopyrightText: 2026 Stanford University and the project authors (see CONTRIBUTORS.md)

SPDX-License-Identifier: MIT
-->

# Tables

Use semantic LaTeX with `booktabs`, `tabularx`, and `threeparttable` for hand-authored tables.
Avoid vertical rules and screenshot-based tables.

Keep hand-authored structured inputs under `source/`.
Write data-derived LaTeX, CSV, or other table exports to `generated/`.
Declare every generated table in `research/reproducibility/pipeline.json` with its inputs, exact command, environment, and manuscript location.
