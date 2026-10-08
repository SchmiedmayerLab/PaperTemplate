<!--
SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)

SPDX-License-Identifier: MIT
-->

# Template Customization Checklist

The repository structure is generic.
Several LaTeX and manuscript choices are deliberate drafting defaults that must be reviewed for each paper.

## Replace for every project

- [ ] Update the optional brand or institution label, status, version, title, PDF title, authors, PDF authors, affiliations, date, short title, correspondence, repository display path, code license, DOI, DOI label, keywords, and subject fields in `paper/setup/metadata.tex`.
- [ ] Record a verified ORCID iD for each author who has one; leave the field empty rather than inventing an identifier.
- [ ] Update `CONTRIBUTORS.md`, copyright years, and project-specific licensing decisions.
- [ ] Select an article profile and remove irrelevant sections, subsections, declarations, and TODOs.
- [ ] Remove unused acronyms, semantic commands, packages, figures, tables, and supplement files.
- [ ] Replace the empty data and reproducibility manifests with the project's actual provenance.
- [ ] Register each external repository and pin its exact submodule commit.
- [ ] Verify the article's reporting guideline, authorship process, repository access, and release plan.

## Drafting defaults that are not universal

- The default presentation uses `article`, 11-point type, US letter paper, XCharter manuscript text, Source Sans Pro metadata, and pdfLaTeX.
- The default has no institutional logo and uses Stanford cardinal as a restrained accent; the standard green ORCID mark appears only for configured author identifiers.
- `paper/setup/profile.tex` selects the standalone preprint presentation independently of the scientific article profile.
- Geometry, typography, captions, headings, links, and running elements in the preprint profile are review defaults rather than publisher requirements.
- `natbib` with square-bracketed numeric citations, sorted and compressed grouped citations, and `unsrtnat` is a drafting bibliography choice; define `\papernatbiboptions` before loading `main.tex` and replace the bibliography style when a venue requires another convention.
- `glossaries-extra`, `hyperref`, `orcidlink`, `cleveref`, `geometry`, and caption-related packages may conflict with publisher classes.
- The default Methods and Results files provide a generic empirical or technical outline rather than a mandatory section taxonomy.
- Data and Code Availability, Declarations, Acknowledgments, a separate Conclusion, and a separate Related Work section depend on article type and venue.
- The repository's MIT license does not automatically cover instantiated manuscript text, publisher files, third-party data, publications, or figures.

## Venue migration

- [ ] Retrieve the current official class, style, and sample files from the venue.
- [ ] Verify the license of each publisher file before committing it.
- [ ] Define `\papervenuebuild` before inputting `main.tex` so the preprint package and style layers are disabled together.
- [ ] Disable conflicting drafting packages rather than loading duplicate implementations.
- [ ] Preserve scientific content in `paper/sections/` and isolate compatibility changes in `paper/setup/venue.tex`.
- [ ] Verify page size, fonts, bibliography backend, front matter, anonymity, PDF metadata, and supplement behavior in the rendered artifact.

## Final genericity audit

- [ ] Search for unused example language, placeholder names, old project identifiers, absolute paths, and stale venue names.
- [ ] Confirm that every retained section serves the selected article profile.
- [ ] Confirm that domain-specific terminology appears only when the paper uses it.
- [ ] Confirm that a new human or agent can identify the foundational data, analysis entry point, generated artifacts, and evidence boundary without oral context.
