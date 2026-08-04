<!--
SPDX-FileCopyrightText: 2026 Stanford University and the project authors (see CONTRIBUTORS.md)

SPDX-License-Identifier: MIT
-->

# External Repository Dependencies

Use Git submodules when analysis code, evaluation tools, software under study, or a versioned data package is maintained in another repository.
Place each submodule at the point where the paper consumes it:

- evaluation or analysis code under `research/analysis/external/<repository>/`;
- software or system source under `research/software/<repository>/`;
- Git-suitable external data under `research/data/external/<repository>/`.

Do not copy a source snapshot into the paper repository when a pinned submodule preserves provenance more clearly.
Do not use a submodule for a large data archive when an immutable archive identifier, governed data location, or specialized data tool is more appropriate.

Add every submodule to `submodules.tsv`.
The Git index pins the exact commit, and the manifest records its repository, role, human-readable version, license, and manuscript use.
Do not rely on a floating branch name as the reproducible version.

Initialize a clone with:

```bash
git submodule update --init --recursive
```

Update a dependency deliberately:

1. Fetch and check out the reviewed commit inside the submodule.
2. Run the dependency's tests and the paper's relevant reproduction steps.
3. Update `research/reproducibility/submodules.tsv` with the exact pinned commit and version label.
4. Review the superproject diff, which should show the submodule pointer change.
5. Record result changes and the reason for the update in `project/notes/03_decision_log.md`.

Do not edit reusable dependency code only inside the paper repository.
Commit the change in its source repository, review it there, and then update the pinned pointer.
