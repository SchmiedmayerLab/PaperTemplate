<!--
SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)

SPDX-License-Identifier: MIT
-->

# Venue Adaptation

## Principles

- Use the current official template and author instructions as the authority.
- Keep scientific section files stable while adapting the document class, front matter, bibliography, and declarations.
- Put compatibility commands in `paper/setup/venue.tex` and explain non-obvious changes in the venue requirements note.
- Do not carry package choices from an old submission when the official class already provides the same capability.

## Adaptation sequence

1. Save the official class, style, bibliography, and sample files under `paper/venue/` when their license permits reuse.
2. Record source URL, access date, template version, and license.
3. Preserve third-party attribution with a file header, `.license` sidecar, or narrow `REUSE.toml` annotation.
4. Create a branch for venue adaptation when the generic manuscript must remain available.
5. Create a thin venue root that defines `\papervenuebuild`, `\paperdocumentclass`, `\paperclassoptions`, and any venue-specific `\papernatbiboptions` before it inputs `main.tex`.
6. Adapt the standard `\maketitle` command and `abstract` environment through the official class and `paper/setup/venue.tex`; keep title and author metadata in their standard commands.
7. Disable conflicting shared packages in `paper/setup/packages.tex`; do not silently load two competing implementations.
8. Map the abstract, section order, declarations, references, figures, tables, and supplement to venue requirements.
9. Replace the drafting bibliography style with the official style.
10. Build the venue artifact and the standalone preprint from a clean state when both versions remain active.
11. Inspect warnings and every rendered page for each artifact.
12. Run the venue checklist and confirm the exact upload package.

## Common migration risks

- Publisher classes may load `natbib`, `hyperref`, caption packages, fonts, or geometry internally.
- Double-blind venues may require a separate anonymous title page and sanitized PDF metadata.
- Some venues require Methods after Discussion or declarations before references.
- Bibliography backends, accepted entry fields, and citation commands vary.
- Official templates may redefine theorem, figure, table, and appendix behavior.
- Preprint and accepted-manuscript policies may differ from copyright and repository-deposit rules.
- Presentation-profile metadata that is appropriate for a public preprint may violate double-blind review requirements.
