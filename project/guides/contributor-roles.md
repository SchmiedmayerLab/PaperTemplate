<!--
SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)
SPDX-License-Identifier: MIT
-->

# Contributor roles

Edit `project/contributors.json` to assign CRediT roles in manuscript author order, then run `make contributions`.
The generated `paper/setup/contributions.tex` supplies the Author Contributions subsection in Declarations and is committed with its source JSON.
Direct LaTeX builds and Overleaf therefore do not require Python.
`make check` rejects stale generated text; `make submission-check` also requires a nonempty roster and confirmed assignments for every listed author.

The template starts with an empty roster to avoid assigning work or approval to real people.
For a new paper, replace it with the actual authors and their agreed contributions:

```json
{
  "schema_version": 1,
  "authors": [
    {
      "name": "Alex Example",
      "roles": ["Conceptualization", "Writing – original draft"],
      "confirmed": false
    },
    {
      "name": "Robin Example",
      "roles": ["Software", "Validation", "Writing – review & editing"],
      "confirmed": false
    }
  ]
}
```

Names are plain text and are escaped for LaTeX.
Use the exact official role names, including the en dash in the two writing roles.
List accepted names with `python3 tools/scripts/credit_contributions.py --roles`.
The generator orders roles consistently, rejects duplicate authors and roles, and leaves a visible draft marker for unconfirmed assignments.
Set `confirmed` to true only after that author confirms the current assignments; reset it to false when revising their roles.
Verify that the roster matches the authors in `paper/setup/metadata.tex`; the generator does not infer an author list from arbitrary LaTeX formatting or establish authorship eligibility.

CRediT has 14 roles and permits multiple roles per person and multiple people per role.
It describes contributions and does not determine who qualifies as an author.
The corresponding author should coordinate assignments and give every contributor an opportunity to confirm them.
These principles follow [NISO's contributor guidance](https://credit.niso.org/contributor-roles/) and [ANSI/NISO Z39.104-2022](https://www.niso.org/publications/z39104-2022-credit), checked November 4, 2026.

Keep non-author thanks and the template attribution in `paper/sections/90_acknowledgments.tex`.
If the venue includes contributions in Acknowledgments, move `\papercontributions` to that section and remove the original occurrence.
The taxonomy can also describe non-author contributions, but this file intentionally represents the manuscript author roster; record non-author contributions separately with any required permission.
This workflow implements the core role assignments without optional contribution-degree labels.
