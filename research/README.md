<!--
SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)

SPDX-License-Identifier: MIT
-->

# Research

This directory contains the evidence and computation behind the paper.

- `literature/` stores source-first citation assets and durable claim notes.
- `data/` separates foundational, external, restricted, interim, and derived data.
- `analysis/` contains versioned code, configuration, environments, and external evaluation tooling.
- `software/` contains pinned source repositories for systems documented or evaluated by the paper.
- `reproducibility/` maps inputs and pinned dependencies to commands and manuscript artifacts.

Place an external repository where it is consumed.
Use `analysis/external/` for evaluation code, `software/` for software under study, and `data/external/` for Git-suitable versioned data.
Register every submodule and exact pinned commit in `reproducibility/submodules.tsv`.
Keep unstructured drafts, coauthor files, and other inbound context under `project/source-materials/` until they are converted into a durable note or verified research asset.
