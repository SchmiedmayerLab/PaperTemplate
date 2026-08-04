<!--
SPDX-FileCopyrightText: 2026 Stanford University and the project authors (see CONTRIBUTORS.md)

SPDX-License-Identifier: MIT
-->

# Template Customization Checklist

The repository structure is generic.
Several LaTeX and manuscript choices are deliberate drafting defaults that must be reviewed for each paper.

## Replace for every project

- [ ] Update the title, authors, date, short title, and corresponding-author details in `paper/setup/metadata.tex`.
- [ ] Update `CONTRIBUTORS.md`, copyright years, and project-specific licensing decisions.
- [ ] Select an article profile and remove irrelevant sections, subsections, declarations, and TODOs.
- [ ] Remove unused acronyms, semantic commands, packages, figures, tables, and supplement files.
- [ ] Replace the empty data and reproducibility manifests with the project's actual provenance.
- [ ] Register each external repository and pin its exact submodule commit.
- [ ] Verify the article's reporting guideline, authorship process, repository access, and release plan.

## Drafting defaults that are not universal

- `article`, 11-point type, US letter paper, one-inch margins, Latin Modern, and pdfLaTeX are local drafting choices.
- `natbib` with author-year citations and `unsrtnat` is a drafting bibliography choice.
- `glossaries-extra`, `hyperref`, `cleveref`, `geometry`, and caption-related packages may conflict with publisher classes.
- The default Methods and Results files provide a generic empirical or technical outline rather than a mandatory section taxonomy.
- Data and Code Availability, Declarations, Acknowledgments, a separate Conclusion, and a separate Related Work section depend on article type and venue.
- The repository's MIT license does not automatically cover instantiated manuscript text, publisher files, third-party data, publications, or figures.

## Venue migration

- [ ] Retrieve the current official class, style, and sample files from the venue.
- [ ] Verify the license of each publisher file before committing it.
- [ ] Disable conflicting drafting packages rather than loading duplicate implementations.
- [ ] Preserve scientific content in `paper/sections/` and isolate compatibility changes in `paper/setup/venue.tex`.
- [ ] Verify page size, fonts, bibliography backend, front matter, anonymity, PDF metadata, and supplement behavior in the rendered artifact.

## Final genericity audit

- [ ] Search for unused example language, placeholder names, old project identifiers, absolute paths, and stale venue names.
- [ ] Confirm that every retained section serves the selected article profile.
- [ ] Confirm that domain-specific terminology appears only when the paper uses it.
- [ ] Confirm that a new human or agent can identify the foundational data, analysis entry point, generated artifacts, and evidence boundary without oral context.
