<!--

This source file is part of the Paper Template open-source project

SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)

SPDX-License-Identifier: MIT

-->

# Paper Template

[![Build and Test](https://github.com/SchmiedmayerLab/PaperTemplate/actions/workflows/validate.yml/badge.svg)](https://github.com/SchmiedmayerLab/PaperTemplate/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE.md)

This repository is a reusable starting point for scientific and technical papers written in LaTeX.
It combines modular manuscript source, source-first references, a declared data-to-artifact pipeline, durable editorial context, repository-local agent skills, and submission checks.

The default standalone build uses a quiet contemporary-journal presentation with a compact title block, readable single-column typography, and restrained running elements.
This presentation profile is distinct from the scientific article profiles in `project/guides/article-profiles.md` and is not a guarantee of compatibility with a publisher class.
The paper's article profile, domain guidance, section structure, and venue adapter should still be selected explicitly for each project.

## Quick start

1. Copy this repository or publish it as a GitHub template repository.
2. Update `CONTRIBUTORS.md`, every field in `paper/setup/metadata.tex`, and the repository licensing metadata.
3. Complete `project/notes/00_project_brief.md` and select a profile from `project/guides/article-profiles.md`.
4. Verify candidate venue rules in `project/notes/01_venue_requirements.md`.
5. Run `make submodules` when the project uses external repositories.
6. Inventory foundational data in `research/data/manifest.tsv` and define the environment under `research/analysis/environment/`.
7. Declare generated figures and tables in `research/reproducibility/pipeline.json`.
8. Draft one sentence per physical source line in `paper/sections/`.
9. Add references through `tools/scripts/add_reference.py` rather than editing generated `references.bib`.
10. Run `make all` while drafting, `make submission-check` before final circulation, and `make arxiv` for a checked arXiv source ZIP.

Required local tools are Python 3.10 or newer, a current TeX distribution with `latexmk` and BibTeX, and Ghostscript for arXiv render comparison.
Run `make doctor` to verify the TeX Live packages used by the default preprint presentation.
The repository scripts use only the Python standard library.
REUSE and Linkspector are optional locally and enforced by CI when the repository is hosted in the SchmiedmayerLab organization.

## Repository map

The repository has four working areas around two visible manuscript entry points:

```text
main.tex                 Full-manuscript entry point
paper/preprint-preview.tex
                         Self-contained visual specimen for the preprint profile
references.bib           Generated LaTeX bibliography
paper/                   Manuscript content and presentation
research/                Evidence, computation, and reproducibility records
project/                 Paper-specific decisions and reusable guidance
tools/                   Automation, tests, and agent workflows
```

Start in `paper/` when writing or reviewing the manuscript.
Use `research/` when tracing a claim or regenerating an artifact.
Use `project/` for planning and publication decisions.
Use `tools/` only when running or maintaining the workflow.
Each area has a short README that defines its internal structure and boundary.

## Reproducible figures and tables

Track authorized foundational data under `research/data/source/` and redistributable external data under `research/data/external/`.
Keep restricted data outside Git under the ignored `research/data/restricted/` path or another governed location.
Record every foundational or external input in `research/data/manifest.tsv`.

Every data-derived figure and table must identify its input files, generating command, environment, outputs, and manuscript locations in `research/reproducibility/pipeline.json`.
Conceptual diagrams must retain editable source and a documented export command.
Generated outputs belong under `paper/figures/generated/`, `paper/tables/generated/`, `research/data/interim/`, or `research/data/derived/` and remain ignored by default.

Run:

```bash
make reproducibility-check
make reproduce
make pdf
make preview-pdf
make subfile SUBFILE=paper/sections/10_introduction.tex
```

The runner writes input and output checksums to the ignored `build/reproducibility-run.json` record.
The full policy and clean-clone verification process are documented in `project/guides/reproducibility-workflow.md`.

## External evaluation and software repositories

Use Git submodules when analysis scripts, evaluation tooling, software under study, or a versioned data package is maintained elsewhere.
Place each submodule where it is consumed, such as `research/analysis/external/<repository>/`, `research/software/<repository>/`, or `research/data/external/<repository>/`.
Register its repository URL, role, version label, exact commit, license, and manuscript use in `research/reproducibility/submodules.tsv`.

The superproject pins the exact commit.
Do not use a floating branch as the reproducible version.
Initialize and verify dependencies with:

```bash
make submodules
make submodule-check
```

Pipeline steps should reference the pinned submodule files directly.
CI checks out submodules recursively and records their revisions in the reproduction run record.

## Build and validation commands

```bash
make doctor
make submodules
make submodule-check
make check
make reproducibility-check
make reproduce
make pdf
make subfile SUBFILE=paper/sections/10_introduction.tex
make references
make compliance
make submission-check
make arxiv
make clean
```

The PDF is written to `build/main.pdf`.
The design specimen is written to `build/preprint-preview.pdf`.
The `subfile` target changes into the source directory before compiling and writes its output to `build/`.
Use that target rather than invoking `latexmk paper/sections/<file>.tex` from the repository root.
Build outputs, derived artifacts, local source material, restricted data, and downloaded article PDFs are ignored to avoid stale results, repository bloat, and accidental redistribution.

## arXiv source package

Run `make arxiv` after the manuscript passes the final submission checks.
The command builds a minimal ZIP from the compiler's recorded manuscript dependencies and the explicit path policy in `project/submission/arxiv.json`.
It strips manuscript comments only in a temporary staged copy, includes the matching `main.bbl` instead of the full bibliography database, recompiles the extracted ZIP in isolation, and requires its rendered pages to match the repository build pixel for pixel.
The resulting archive, inventory, and SHA-256 checksum are written under `output/arxiv/`.
The staged source freezes the default `\today` date; use `make arxiv ARXIV_DATE=2026-10-13` to select an explicit release date without editing the manuscript.
Use `make arxiv-check` for a nonpublishing packaging and reference-label smoke test, including while the template contains draft placeholders.

The allowlist is intentionally narrower than the repository.
Project notes, research material, tools, CI configuration, editable figure sources, unused figures, and build artifacts cannot enter the ZIP merely because they exist in the checkout.
See `project/guides/arxiv-submission.md` for current arXiv requirements, configuration, licensing cautions, and the final upload review steps.

## Preprint presentation

`main.tex` uses the standalone preprint presentation by default.
The visual packages are isolated in `paper/setup/preprint-packages.tex`, and the style rules are isolated in `paper/setup/preprint.tex`.
The profile uses XCharter for the title, headings, manuscript body, and captions.
Source Sans Pro is limited to metadata, running elements, and figure labels.
The near-monochrome palette uses Stanford cardinal for small navigational cues and links.
The standard green ORCID mark appears only beside authors with a configured ORCID iD.
The presentation contains no institutional logos, decorative icons, proprietary fonts, or copied publisher assets.
The title and abstract occupy a dedicated opening page, with a date header and rule aligned to the running headers on later pages.
`\paperstartmaintext` starts the main text on a new page in the preprint profile and leaves pagination unchanged in venue-controlled builds.
References also start on a new page in the preprint profile, after any pending figures and tables.

Edit the semantic fields in `paper/setup/metadata.tex` rather than changing the title block directly.
Record a verified ORCID iD for each author who has one; an empty ORCID field remains available as a placeholder and renders no icon.
Use the optional brand, version, code-license, and DOI-label fields only when they communicate real manuscript metadata.
The repository label should show a readable path such as `github.com/organization/repository` rather than generic linked text.
The front matter, abstract, keywords, and bibliography style use hooks defined in `paper/setup/commands.tex` so a venue adapter can replace them without editing scientific section files.
The journal-neutral drafting default uses square-bracketed numeric citations, sorts and compresses grouped citations, and orders the bibliography by first citation.
Define `\papernatbiboptions` before loading `main.tex` when a venue requires another `natbib` citation mode.
Run `make preview-pdf` to render a complete design specimen with illustrative content, a figure, and a table.
The preview is an ignored review artifact rather than a submission file.

## Reference workflow

Add a reference from a citation export, DOI, or PubMed identifier:

```bash
python3 tools/scripts/add_reference.py --citation-file ~/Downloads/citation.ris --key example2026reproducible
python3 tools/scripts/add_reference.py --doi 10.1000/example
python3 tools/scripts/add_reference.py --pmid 12345678
```

Attach full text only when access is lawful:

```bash
python3 tools/scripts/add_reference.py --doi 10.1000/example --pdf-file ~/Downloads/article.pdf
python3 tools/scripts/organize_references.py --keys example2026paper --download-missing-pdfs
```

Each reference folder contains the citation export, generated `abstract.md`, durable `claims.md`, and optionally an ignored `source.pdf`.
Metadata refreshes replace `abstract.md` but preserve `claims.md`.
Run `make references` to rebuild `references.bib` and update `project/notes/06_reference_inventory.md`.

## Adapting to a journal

Draft with the generic class until a venue is selected.
Record verified author instructions in `project/notes/01_venue_requirements.md`.
Download official class or template files into `paper/venue/` only when their license permits repository storage.
Adapt the document class and front matter without moving scientific section content.
Keep compatibility code in `paper/setup/venue.tex` so venue adaptation remains reviewable and reversible.
Define `\papervenuebuild` in a thin venue root before inputting `main.tex` to bypass the preprint presentation as a single unit.
The same root can set `\paperdocumentclass` and `\paperclassoptions` before it inputs `main.tex`.

```tex
\def\papervenuebuild{}
\def\paperdocumentclass{publisher-class}
\def\paperclassoptions{}
\def\papernatbiboptions{round,authoryear}
\input{main.tex}
```

Do not infer current venue requirements from an old example submission.
Do not apply the repository's MIT license to publisher files, external data, downloaded publications, or other third-party assets.

## Repository-local paper skills

The folders under `tools/skills/` use the Codex skill format.
Automatic discovery depends on the active agent environment.
When a skill is not discovered automatically, read its `SKILL.md` directly and follow its bounded workflow.
Do not install these skills into a personal skill directory without the user's request.

## Documentation

- `project/guides/publication-workflow.md` covers the publication lifecycle.
- `project/guides/reproducibility-workflow.md` covers data, analysis, and artifact traceability.
- `project/guides/reference-workflow.md` covers citation assets and lawful full text.
- `project/guides/article-profiles.md` maps common manuscript structures.
- `project/guides/domain-checklists.md` contains conditional clinical, software, AI, review, protocol, and qualitative guidance.
- `project/guides/customization-checklist.md` identifies drafting defaults that each paper must replace or verify.
- `project/guides/venue-adaptation.md` covers the final journal migration.

## Contributing

Contributions to this project are welcome. Please make sure to read the [contribution guidelines](https://github.com/SchmiedmayerLab/.github/blob/main/CONTRIBUTING.md) and the [contributor covenant code of conduct](https://github.com/SchmiedmayerLab/.github/blob/main/CODE_OF_CONDUCT.md) first. You can find a list of contributors in the [CONTRIBUTORS.md](CONTRIBUTORS.md) file.

## License

This project is licensed under the MIT License. See [LICENSE.md](LICENSE.md) for more information.

## Citation

If you use this software, please cite it using the metadata in [CITATION.cff](CITATION.cff), which GitHub surfaces through the [*Cite this repository*](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-citation-files) button.

## Our Research

For more information, visit the [Schmiedmayer Lab GitHub organization](https://github.com/SchmiedmayerLab).

![Schmiedmayer Lab](https://raw.githubusercontent.com/SchmiedmayerLab/.github/main/assets/footer-light.png#gh-light-mode-only)
![Schmiedmayer Lab](https://raw.githubusercontent.com/SchmiedmayerLab/.github/main/assets/footer-dark.png#gh-dark-mode-only)
