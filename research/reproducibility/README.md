<!--
SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)

SPDX-License-Identifier: MIT
-->

# Reproducibility Manifest

`pipeline.json` is the machine-readable source-to-artifact map.
It keeps exact commands and dependencies visible to humans, agents, and CI without requiring a workflow engine.

Declare one object per step in the `steps` array:

```json
{
  "id": "figure-primary-outcome",
  "description": "Generate the primary-outcome figure from the frozen analysis table.",
  "inputs": [
    "research/data/source/observations.csv",
    "research/analysis/config/primary-outcome.json",
    "research/analysis/scripts/plot_primary_outcome.py"
  ],
  "command": [
    "python3",
    "research/analysis/scripts/plot_primary_outcome.py",
    "--config",
    "research/analysis/config/primary-outcome.json"
  ],
  "outputs": [
    "paper/figures/generated/primary-outcome.pdf"
  ],
  "manuscript_locations": [
    "paper/sections/40_results.tex"
  ],
  "requires_restricted_data": false
}
```

Use argument arrays rather than shell strings.
Paths must be repository-relative.
Inputs must exist before execution.
Outputs must remain inside `research/data/interim/`, `research/data/derived/`, `paper/figures/generated/`, `paper/tables/generated/`, `build/`, or `output/`.

External analysis or evaluation code may be referenced inside a registered Git submodule.
Place it under `research/analysis/external/`, register its exact revision in `research/reproducibility/submodules.tsv`, and list the relevant submodule files as pipeline inputs.
The runner verifies the checked-out revision and records recursive submodule status in `build/reproducibility-run.json`.

Run `make reproducibility-check` to validate the manifest and declared paths.
Run `make reproduce` to execute the steps in order and verify that every output exists.
The runner writes checksums and execution details to the ignored `build/reproducibility-run.json` file.

Restricted data may remain unavailable to CI.
Set `requires_restricted_data` to `true`, retain the governed access record in `research/data/manifest.tsv`, and provide a synthetic smoke-test step when it can test the same code path without exposing protected information.
Do not describe a CI smoke test as a recomputation of protected-data results.
