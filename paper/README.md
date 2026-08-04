<!--
SPDX-FileCopyrightText: 2026 Stanford University and the project authors (see CONTRIBUTORS.md)

SPDX-License-Identifier: MIT
-->

# Paper

This directory contains everything that controls the manuscript's scientific text and rendered presentation.

- `sections/` contains the numbered manuscript sections.
- `supplement/` contains supplementary manuscript text.
- `figures/` and `tables/` separate editable sources from reproducible exports.
- `setup/` contains metadata, semantic commands, acronyms, packages, and venue overrides.
- `venue/` contains licensed publisher files only when a selected venue requires them.

Write and review the paper here.
Keep evidence, analysis code, and workflow records under `research/` so manuscript content is not mixed with its provenance.
Compile the full paper from the root `main.tex` file.
Compile one section with `make subfile SUBFILE=paper/sections/<file>.tex` so the parent path resolves correctly and auxiliary files remain in `build/`.
