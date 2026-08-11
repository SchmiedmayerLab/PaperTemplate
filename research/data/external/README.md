<!--
SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)

SPDX-License-Identifier: MIT
-->

# External Data

Store redistributable third-party inputs here.
When redistribution is not permitted, retain a retrieval script or exact access instructions and declare the expected local path in `research/data/manifest.tsv`.
Preserve the original license and attribution.

A versioned data package may be a pinned submodule when Git is appropriate for its size and governance.
Register the submodule in `research/reproducibility/submodules.tsv` and use `git:<commit>` in the data manifest's checksum field.
