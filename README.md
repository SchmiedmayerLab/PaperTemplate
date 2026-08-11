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

The default `article` class and package set form a generic pdfLaTeX drafting profile.
They are not a guarantee of compatibility with every publisher class.
The paper's article profile, domain guidance, section structure, and venue adapter should be selected explicitly for each project.

## Quick start

1. Copy this repository or publish it as a GitHub template repository.
2. Update `CONTRIBUTORS.md`, `paper/setup/metadata.tex`, and the repository licensing metadata.
3. Complete `project/notes/00_project_brief.md` and select a profile from `project/guides/article-profiles.md`.
4. Verify candidate venue rules in `project/notes/01_venue_requirements.md`.
5. Run `make submodules` when the project uses external repositories.
6. Inventory foundational data in `research/data/manifest.tsv` and define the environment under `research/analysis/environment/`.
7. Declare generated figures and tables in `research/reproducibility/pipeline.json`.
8. Draft one sentence per physical source line in `paper/sections/`.
9. Add references through `tools/scripts/add_reference.py` rather than editing generated `references.bib`.
10. Run `make all` while drafting and `make submission-check` before final circulation.

Required local tools are Python 3.10 or newer and a current TeX distribution with `latexmk` and BibTeX.
The repository scripts use only the Python standard library.
REUSE and Linkspector are optional locally and enforced by CI when the repository is hosted in the SchmiedmayerLab organization.

## Repository map

The repository has four working areas around two visible manuscript entry points:

```text
main.tex                 Full-manuscript entry point
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
make clean
```

The PDF is written to `build/main.pdf`.
The `subfile` target changes into the source directory before compiling and writes its output to `build/`.
Use that target rather than invoking `latexmk paper/sections/<file>.tex` from the repository root.
Build outputs, derived artifacts, local source material, restricted data, and downloaded article PDFs are ignored to avoid stale results, repository bloat, and accidental redistribution.

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
