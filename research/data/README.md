<!--
SPDX-FileCopyrightText: 2026 Stanford University and the project authors (see CONTRIBUTORS.md)

SPDX-License-Identifier: MIT
-->

# Data

This directory separates foundational inputs from reproducible transformations.
Do not treat all research data as interchangeable or apply one license to every file.

## Layout

- `source/` contains immutable foundational data that the repository is authorized to store.
- `external/` contains redistributable third-party inputs or retrieval instructions for inputs stored elsewhere.
- `dictionaries/` contains schemas, codebooks, units, identifiers, and missing-value conventions.
- `interim/` contains disposable intermediate files.
- `derived/` contains analysis-ready data recreated from foundational inputs.
- `manifest.tsv` is the machine-readable inventory of foundational and external inputs.

Track suitably small foundational data when their consent, governance, and license permit repository storage.
For large, controlled, sensitive, or nonredistributable data, keep the data outside Git and retain a manifest entry with the expected local path, access procedure, immutable version or checksum, schema, and reason for absence.
Use `sha256:<digest>` for a stored file.
Use `git:<commit>` for a data submodule that is also registered in `research/reproducibility/submodules.tsv`.

Never modify a file under `source/` in place.
Write transformations to `interim/` or `derived/` through versioned code under `research/analysis/`.
Do not place credentials, tokens, direct identifiers, or uncontrolled exports in this directory.

## Dataset registry

Replace this table with one row per dataset.

| Dataset | Purpose | Foundational path or access route | Data dictionary | License or governance | Maintainer |
|---|---|---|---|---|---|
| TODO | TODO | TODO | TODO | TODO | TODO |

Run `make reproducibility-check` after adding or moving data assets.
