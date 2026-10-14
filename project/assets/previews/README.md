<!--
SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)

SPDX-License-Identifier: MIT
-->

# Documentation previews

The root README displays pages 1 and 2 of [the design specimen](../../../paper/preprint-preview.tex) and links to its complete PDF.
The specimen uses the shared files in `paper/setup/` and the generated `references.bib`.
Its prose, diagram, and table illustrate formatting rather than research results.

From the repository root, regenerate all three snapshots with:

```bash
make readme-previews
```

The command uses PDFLaTeX through `latexmk`, then Ghostscript to render 96-dpi PNGs.
It fixes the documentation date to October 14, 2026 through `SOURCE_DATE_EPOCH`, leaving manuscript source and ordinary builds unchanged.
Build intermediates stay in the ignored `build/readme-preview/` directory.
Rendering can vary across TeX and Ghostscript releases; inspect both pages after regeneration.
For a disposable check, run `make readme-previews README_PREVIEW_DIR=build/readme-assets`.

Only `page-1.png`, `page-2.png`, and `preprint-preview.pdf` are committed exports.
This documentation-only exception lets GitHub display previews in a private repository without an external host, public release, or expiring build artifact.
The assets are outside the arXiv package allowlist and are not manuscript submission files.
