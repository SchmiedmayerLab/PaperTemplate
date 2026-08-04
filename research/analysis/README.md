<!--
SPDX-FileCopyrightText: 2026 Stanford University and the project authors (see CONTRIBUTORS.md)

SPDX-License-Identifier: MIT
-->

# Analysis

Keep the complete data-to-result implementation in this directory.
Provide one documented top-level execution path through `make reproduce` and `research/reproducibility/pipeline.json`.

## Layout

- `scripts/` contains versioned transformations, analyses, figure generation, and table generation.
- `config/` contains explicit parameters that should not be hidden in source code.
- `environment/` contains the dependency lock or exact environment specification.
- `external/` contains pinned submodules for evaluation or analysis code maintained elsewhere.

Record random seeds, locale, time zone, hardware, external service versions, and nondeterministic behavior when they can change a result.
Do not rely on notebook state or an undocumented manual command for a reported artifact.
If notebooks are used, add an output-stripping policy and a noninteractive reproduction path.
