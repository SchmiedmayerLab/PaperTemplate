<!--
SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)

SPDX-License-Identifier: MIT
-->

# Feedback Ledger

Treat user, coauthor, editor, and reviewer feedback as durable context.
Record the underlying issue rather than only the marked sentence.

| Date | Source | Scope | Category | Underlying issue | Resolution | Durable destination | Remaining action |
|---|---|---|---|---|---|---|---|
| 2026-10-13 | Author | preprint opening page | layout | Larger main-text margins are approved, but the first-page title sits too low and the rule does not align with later headers. Main content should start on a new page. | Move the date and rule into the first-page header; move the title upward and add a preprint-only main-text page break. Keep the approved main-text geometry. | `paper/setup/preprint.tex`, `paper/setup/commands.tex`, main root, preview, decision log | Author review of the rebuilt opening page. |
| 2026-10-13 | Author | preprint layout | author decision | Later pages feel cramped at the top and bottom. | Increase vertical text margins and header separation uniformly; preserve side margins, type, and line spacing. Keep consecutive section and subsection headings together during repagination. | `paper/setup/preprint-packages.tex`, `paper/setup/preprint.tex`, decision log | Author review of the rebuilt PDFs. |
| YYYY-MM-DD | TODO | local, section, manuscript, or cross-paper | wording, structure, evidence, fact, or author decision | TODO | TODO | section, note, `AGENTS.md`, or paper skill | TODO |

Use `AGENTS.md` for a cross-paper writing preference.
Use this ledger for project-specific feedback and decisions.
Update a paper skill only when the feedback establishes a reusable procedure for that skill's bounded task.
After recording a recurring wording issue, audit the complete affected section or manuscript for the same pattern.
