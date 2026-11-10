<!--
SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)
SPDX-License-Identifier: MIT
-->

# Word review and reconciliation

LaTeX remains the manuscript source.
Generate a Word copy for coauthors, preserve the exact export baseline, and reconcile returned changes into the original sections.
This avoids replacing citation keys, labels, macros, and subsequent local work with a lossy whole-document conversion.

## Export for coauthors

Install [Pandoc](https://pandoc.org/installing.html) 3.1 or newer; on macOS, `brew install pandoc` is sufficient.
The optional Word workflow uses Python's standard library and does not require a TeX installation, Microsoft Word, or a Python document library.
Run `make contributions` after changing the contributor assignments, and regenerate any figures or tables used by the manuscript.
Then run:

```bash
make word
# Or choose a new, descriptive directory:
make word WORD_OUTPUT=output/word/review-round-1
```

Each export creates a new directory containing:

- `manuscript.docx`, with native headings, editable equations and tables, numeric citations, and Track Changes enabled.
- `baseline.md`, the normalized text extracted from that exact DOCX, including title and author metadata.
- `sources/`, a snapshot of the included manuscript sources, bibliography, contribution assignments, Word adapters, citation style, and included images.
- `manifest.json`, recording source hashes, document and baseline hashes, conversion version, and export time.

Keep the complete bundle locally and send a **copy** of `manuscript.docx`.
Ask coauthors to leave Track Changes enabled, use comments for questions, and return the Word file.
Do not edit the retained baseline document or reuse an export directory.
Exports and returned reviews belong under ignored `output/` or `project/source-materials/`; do not commit private coauthor comments unintentionally.

The review layout uses Letter pages, one-inch margins, 12-point serif body text, black headings, and visible table borders.
It is intended for editing and reading rather than reproducing the preprint PDF's exact pagination.
The LaTeX PDF remains the authority for publication layout.
Open the actual Word copy and check all pages before circulation, especially dense tables, equations, figures, and long author lists.
LibreOffice can provide a local PDF preview if Word is unavailable; rendering in the recipient's Word version may differ.

## Conversion boundaries

The exporter follows the document body and literal `\input`, `\include`, and `\subfile` composition in `main.tex`.
It uses metadata and contributions from `paper/setup/`, with semantic conversion adapters in `paper/setup/word.tex`.
Presentation packages, venue class behavior, and arbitrary preamble definitions are not imported.
Put adapters for paper-specific semantic commands and acronyms in `word.tex` without duplicating scientific prose.
Dynamic include paths require an explicit adaptation.

Pandoc converts standard prose, citations, tables, images, and mathematical expressions to Word structures.
Its [manual](https://pandoc.org/MANUAL.html) documents that conversion from richer formats can lose information.
The exporter rejects remaining raw TeX and conversion warnings instead of silently omitting unsupported constructs.
This is a useful guard, not a proof of full fidelity; verify the rendered result against the manuscript.
Complex tables, TikZ, custom theorem packages, glossary state, equation numbering, and venue-specific cross-reference behavior may require adaptation and visual review.
Section, figure, and table references receive visible numbered targets in the review copy; unsupported reference types stop export and require an adapter.
Word figures must use local PNG/JPEG exports; PDF-only figures must be exported from their editable source to an appropriate Word-compatible image.
The included numeric CSL style preserves citation order; it is a review style, not a claim of exact equivalence to every journal's BibTeX style.
Rendered citations in Word are text, so citation changes must be mapped back to verified citation keys during reconciliation.

## Extract a returned review

```bash
make word-review REVIEWED="project/source-materials/returned.docx" BASELINE="output/word/review-round-1"
```

Optionally set `REVIEW_OUTPUT=output/word-reviews/reviewer-round-1` to choose a new extraction directory.
The command verifies the original baseline hashes and writes an extraction bundle without modifying any manuscript source:

- `accepted.md`, `rejected.md`, and `marked.md` show Pandoc's accepted, rejected, and annotated views.
- `changes.diff` compares proposed text against the original export, including edits made with tracking disabled.
- `untracked.diff` compares the rejected-changes view against the baseline; differences require attention and can also reflect structural or converter differences.
- `annotations.json` preserves revision and comment records with author, timestamp, raw XML, and paragraph context, including formatting and move records.
- `review.json` flags source drift, converter changes, changed DOCX parts, and changed image assets.
- `reviewed.docx` preserves the exact returned document for inspection.

Tracked paragraph boundaries, moved text, formatting, table structures, fields, images, and complex equations cannot be safely reduced to text replacement rules.
Inspect the original returned document for these changes.
Comment anchors can span paragraphs, and annotation context is a locator rather than an automatic source mapping.
Keep all three versions: exported source, returned review, and current source.
Never regenerate the missing original baseline from a manuscript that has since changed.

## Apply feedback to LaTeX

Use the repository-local [paper-word-review skill](../../tools/skills/paper-word-review/SKILL.md) with the returned document and its matching baseline.
The skill compares the three versions, applies clear edits within the requested scope, preserves citations and labels, and records unresolved scientific or conflicting changes for author decisions.
It does not treat every reviewer edit as an approved change.
For multiple reviewers, retain each review separately and reconcile against its corresponding export.
After merging feedback, run `make check`, rebuild and inspect the LaTeX PDF, then export a fresh Word bundle for the next round.

Automated integration tests exercise export, native math/tables/images, tracked insertion/deletion, comment attribution, untracked edits, changed title metadata, source drift, and immutable baseline checks.
Pandoc-dependent tests skip when Pandoc is absent locally; CI installs it for these tests.
