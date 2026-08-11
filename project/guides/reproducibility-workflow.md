<!--
SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)

SPDX-License-Identifier: MIT
-->

# Reproducibility Workflow

## 1. Freeze foundational inputs

1. Place repository-authorized immutable inputs in `research/data/source/`.
2. Place redistributable third-party inputs or retrieval instructions in `research/data/external/`.
3. Add every foundational and external asset to `research/data/manifest.tsv`.
4. Record the origin, immutable version or date, license or access route, sensitivity, checksum, and concise role.
5. Use `sha256:<digest>` for stored files and `git:<commit>` for a registered data submodule.
6. Add schemas, units, identifiers, and missing-value rules under `research/data/dictionaries/`.

Do not modify foundational files in place.
Create a new version or write a transformation to `research/data/interim/` or `research/data/derived/`.

## 2. Freeze the analysis environment

Add an exact dependency specification under `research/analysis/environment/`.
Record language and tool versions, random seeds, locale, time zone, hardware, and external service versions when they can affect results.
Keep scientific configuration under `research/analysis/config/`.
Keep credentials and machine-specific paths outside tracked configuration.

## 3. Declare the pipeline

Add each transformation or artifact-generation step to `research/reproducibility/pipeline.json`.
Declare its inputs, command, outputs, manuscript locations, and restricted-data status.
Use one top-level entry point, `make reproduce`, even when the underlying project uses R, Python, Julia, Swift, a workflow engine, or containers.

When a step depends on code from another repository, add that repository as a pinned submodule at its point of use.
Register it in `research/reproducibility/submodules.tsv` and reference the submodule paths directly in the pipeline inputs and command.
The superproject commit, not a floating branch, defines the version.

## 4. Generate artifacts

Write transient data to `research/data/interim/`.
Write reproducible analysis-ready data to `research/data/derived/`.
Write figure exports to `paper/figures/generated/`.
Write generated table exports to `paper/tables/generated/`.
Retain editable diagram sources in `paper/figures/source/` and declare their export commands.

Do not make manual changes to generated outputs.
Make the required change in the data, configuration, source asset, or generating code and rerun the pipeline.

## 5. Verify traceability

Run:

```bash
make reproducibility-check
make reproduce
make check
make pdf
```

Connect each reported claim, figure, and table to its pipeline step in `project/notes/02_evidence_inventory.md`.
Inspect the generated run record at `build/reproducibility-run.json`.
Confirm that the manuscript references the declared output rather than a stale copy.

## 6. Conduct an independent reproduction

Before submission, use a clean clone or clean worktree with the documented environment.
Ask a human or independent agent to follow only the repository instructions.
Record missing steps, ambiguous data fields, implicit dependencies, and nondeterministic behavior.
Resolve those defects before finalizing the availability statement.

## 7. Handle restricted or large data

Do not weaken privacy, consent, governance, or licensing to make a repository self-contained.
Retain a tracked manifest, expected schema, access procedure, immutable dataset version, and checksums when permitted.
Run the governed full pipeline in the authorized environment.
Use public or synthetic fixtures for CI when possible.
State precisely which results CI reproduces and which require controlled access.
