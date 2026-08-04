<!--
SPDX-FileCopyrightText: 2026 Stanford University and the project authors (see CONTRIBUTORS.md)

SPDX-License-Identifier: MIT
-->

# Publication Workflow

## 1. Establish the paper

1. Complete the project brief before drafting prose.
2. Define the contribution, primary reader, evidence boundary, and non-goals.
3. Select an article profile from `project/guides/article-profiles.md` and record the sections to add, remove, or rename.
4. Record candidate venues, but keep the source journal-neutral until one is selected.
5. Select applicable reporting guidelines and identify protocol or preregistration commitments.
6. Triage unstructured local context in `project/source-materials/` and inventory verified protocols, repositories, analyses, and evidence in `project/notes/02_evidence_inventory.md`.

## 2. Establish authorship and governance

1. Verify author names, affiliations, ORCIDs, order, corresponding-author details, and CRediT roles.
2. Record who can approve scientific decisions, data access, software releases, and submission artifacts.
3. Confirm ethics, consent, privacy, licensing, and repository authorization before moving source material or data.
4. Define the coauthor circulation and final-approval process.

## 3. Freeze data and map the evidence

1. Inventory foundational inputs in `research/data/manifest.tsv` and document their schemas under `research/data/dictionaries/`.
2. Register external repositories in `research/reproducibility/submodules.tsv` and pin their exact commits.
3. Freeze the analysis environment, configuration, random seeds, and result-affecting versions.
4. Declare data-to-artifact steps in `research/reproducibility/pipeline.json`.
5. Convert each intended claim into an evidence need.
6. Separate background citations, methods authorities, present-study results, and future hypotheses.
7. Search for primary and authoritative sources.
8. Open each source and verify the exact claim, population or system, design, date, and limitations.
9. Add the source through the repository reference workflow and record claim-level support in `claims.md` and the evidence inventory.

## 4. Draft the story

1. Draft a section outline around problem, gap, contribution, evidence, limits, and next step.
2. Put one sentence on each physical line and one logical paragraph between blank lines.
3. Use stable terminology and semantic LaTeX commands.
4. Keep TODOs concrete and never replace missing evidence with plausible prose.
5. Build frequently so structural and citation failures stay local.

## 5. Run bounded review passes

Run separate passes for story, methods reproducibility, results integrity, claims and citations, terminology, figures and tables, venue fit, and rendered layout.
Use repository-local skills directly when helpful.
Follow the active platform's authorization rules for delegation.
Give each agent a non-overlapping scope, raw source paths, and an output contract.

## 6. Reproduce independently

1. Run `make reproducibility-check` and `make reproduce` from the documented environment.
2. Initialize submodules recursively and verify every checked-out revision against the superproject and dependency manifest.
3. Rebuild the manuscript from a clean state.
4. Ask a human or independent agent to follow only the repository instructions from a clean clone or clean worktree.
5. Resolve implicit dependencies, ambiguous data fields, undocumented manual steps, and stale outputs.
6. Record which results require controlled data and which public or synthetic checks CI reproduces.

## 7. Adapt to the venue

Verify the current official author instructions, record them in `project/notes/01_venue_requirements.md`, and follow `project/guides/venue-adaptation.md`.
Preserve the generic manuscript structure until the venue-specific build compiles and every section has a clear destination.

## 8. Freeze a submission candidate

1. Resolve all TODOs and switch `\paperdrafttrue` to `\paperdraftfalse`.
2. Run `make submission-check`, which reproduces declared artifacts and rebuilds from a clean state.
3. Render the PDF to images and inspect every page.
4. Check the exact exported files, not only the source repository.
5. Record the submitted commit, manuscript identifier, venue, date, and artifact checksums in the decision log.

## 9. Revise without losing context

1. Enter reviewer and coauthor feedback in `project/notes/04_feedback_ledger.md`.
2. Identify the underlying weakness before editing the local sentence.
3. Prefer minimal, high-value revisions and propagate terminology changes across every artifact.
4. Re-run the relevant review and layout passes.
5. Preserve a clean response-to-reviewers map of issue, change, location, and remaining scope boundary.

## 10. Release and archive

1. Create persistent releases for software, data, protocols, and analysis artifacts that the paper cites.
2. Record exact commits, release tags, archive identifiers, checksums, licenses, and access conditions.
3. Verify that preprint, journal, and repository versions use compatible copyright and licensing terms.
4. Record the submitted artifact set and manuscript identifier in the decision log.
5. Archive the accepted manuscript, final citation, correction history, and publication record when permitted.
