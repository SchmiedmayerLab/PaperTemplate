<!--
SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)

SPDX-License-Identifier: MIT
-->

# Source-first references

Each citation key has one durable asset directory:

```text
research/literature/<citation-key>/
  citation.bib | citation.nbib | citation.ris
  abstract.md            # generated source content
  claims.md              # durable manuscript support notes
  source.pdf            # optional and ignored by Git
```

Citation keys use lowercase first-author surname, four-digit year, and the first meaningful title word, for example `example2026reproducible`.
Keep a stable existing key when updating metadata.

Use `tools/scripts/add_reference.py` to import an official citation export or retrieve metadata by PMID or DOI.
Use `tools/scripts/organize_references.py` to audit assets, regenerate abstracts, and retrieve eligible open-access PDFs.
Use `tools/scripts/regenerate_bib_from_references.py --in-place` to rebuild `references.bib`.

Treat the raw downloaded `citation.*` file as the metadata source of truth.
Do not hand-edit generated `references.bib` when correcting the source asset is possible.
Treat `abstract.md` as generated content that may be replaced during a metadata refresh.
Record verified manuscript support, source locations, and limitations in `claims.md` and the evidence inventory.

Only download and retain full-text PDFs when access is lawful.
Do not commit publisher PDFs by default.
Verify the terms of every tracked citation export or abstract.
Add an appropriate SPDX header, `.license` sidecar, or narrow `REUSE.toml` annotation rather than applying the repository's MIT license automatically.
