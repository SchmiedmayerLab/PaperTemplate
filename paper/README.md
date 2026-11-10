<!--
SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)

SPDX-License-Identifier: MIT
-->

# Paper

This directory contains everything that controls the manuscript's scientific text and rendered presentation.

- `sections/` contains the numbered manuscript sections.
- `supplement/` contains supplementary manuscript text.
- `figures/` and `tables/` separate editable sources from reproducible exports.
- `setup/` contains metadata, semantic commands, acronyms, shared packages, the default preprint presentation, and venue overrides.
- `venue/` contains licensed publisher files only when a selected venue requires them.
- `preprint-preview.tex` is a self-contained visual specimen with illustrative content.

Write and review the paper here.
Keep evidence, analysis code, and workflow records under `research/` so manuscript content is not mixed with its provenance.
Compile the full paper from the root `main.tex` file.
Compile the visual specimen with `make preview-pdf` and inspect `build/preprint-preview.pdf`.
Compile one section with `make subfile SUBFILE=paper/sections/<file>.tex` so the parent path resolves correctly and auxiliary files remain in `build/`.

## Preprint presentation

[main.tex](../main.tex) selects the standalone preprint profile by default.
[preprint-packages.tex](setup/preprint-packages.tex) isolates its visual dependencies, and [preprint.tex](setup/preprint.tex) controls the layout.
XCharter carries the manuscript text and headings; Source Sans Pro is limited to metadata, running elements, and figure labels.
The near-monochrome palette uses Stanford cardinal for small navigational cues and links, with no institutional logos or publisher assets.
The title and abstract share a dedicated opening page; the main text and references each start on a new page.
The `\paperstartmaintext` hook leaves pagination unchanged in venue-controlled builds.

Edit [metadata.tex](setup/metadata.tex) rather than the title block.
Supply verified ORCID identifiers; empty fields render no icon.
Use optional brand, version, code-license, and DOI fields only for actual manuscript metadata, and use a readable repository path as the link label.
[commands.tex](setup/commands.tex) provides semantic hooks for front matter, the abstract, keywords, and bibliography style.
The drafting default uses square-bracketed numeric citations, sorts and compresses groups, and orders references by first citation.
See [venue adaptation](../project/guides/venue-adaptation.md) to change the class or citation mode without duplicating scientific sections.

Run `make preview-pdf` to build the [design specimen](preprint-preview.tex) locally at `build/preprint-preview.pdf`.
Its prose, figure, and table are illustrative; the generated PDF is not a submission file.
The root README uses separate [documentation snapshots](../project/assets/previews/README.md), regenerated with `make readme-previews`.
