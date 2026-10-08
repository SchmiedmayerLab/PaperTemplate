#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)
#
# SPDX-License-Identifier: MIT

"""Run lightweight, deterministic manuscript repository checks."""

from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

from reference_common import BIB_PATH, PROJECT_ROOT, bib_keys


TEX_ROOTS = (
    PROJECT_ROOT / "main.tex",
    PROJECT_ROOT / "paper" / "preprint-preview.tex",
    PROJECT_ROOT / "paper" / "setup",
    PROJECT_ROOT / "paper" / "sections",
    PROJECT_ROOT / "paper" / "supplement",
)
TODO_PATTERN = re.compile(r"\b(?:TODO|TBD|PLACEHOLDER)\b|\\(?:papertodo|placeholder)\s*\{", re.IGNORECASE)
ABSOLUTE_PATH_PATTERN = re.compile(r"(?:/Users/|/home/|[A-Za-z]:\\\\)")
CITE_PATTERN = re.compile(r"\\(?:cite|citep|citet|citealp|citeauthor|citeyear)\*?(?:\[[^]]*\]){0,2}\{([^}]+)\}")
LABEL_PATTERN = re.compile(r"\\label\{([^}]+)\}")
REF_PATTERN = re.compile(r"\\(?:ref|cref|Cref|autoref|pageref)\{([^}]+)\}")
INCLUDE_PATTERN = re.compile(r"\\(?:input|include|subfile)\{([^}]+)\}")
EM_DASH_PATTERN = re.compile(r"—|---")
BECAUSE_PATTERN = re.compile(r"\bbecause\b", re.IGNORECASE)
FORMULAIC_PATTERN = re.compile(
    r"\b(?:unlock|game-changing|paradigm shift|seamlessly|at scale)\b|\bthis creates a gap\b",
    re.IGNORECASE,
)
WORD_PATTERN = re.compile(r"\b[\w'-]+\b")
LONG_SENTENCE_REVIEW_WORDS = 35


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission", action="store_true", help="Treat draft markers as errors.")
    return parser.parse_args()


def tex_files() -> list[Path]:
    files: set[Path] = set()
    for root in TEX_ROOTS:
        if root.is_file():
            files.add(root)
        elif root.exists():
            files.update(root.rglob("*.tex"))
    return sorted(files)


def source_location(path: Path, line_number: int) -> str:
    return f"{path.relative_to(PROJECT_ROOT)}:{line_number}"


def resolve_include(source: Path, include: str) -> Path:
    candidate = PROJECT_ROOT / include
    if not candidate.suffix:
        candidate = candidate.with_suffix(".tex")
    if candidate.exists():
        return candidate
    candidate = source.parent / include
    if not candidate.suffix:
        candidate = candidate.with_suffix(".tex")
    return candidate


def main() -> int:
    args = parse_args()
    errors: list[str] = []
    warnings: list[str] = []
    labels: list[tuple[str, str]] = []
    references: list[tuple[str, str]] = []
    citations: list[tuple[str, str]] = []

    files = tex_files()
    for path in files:
        for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("%"):
                continue
            location = source_location(path, line_number)
            if TODO_PATTERN.search(raw_line) and path.name != "commands.tex":
                message = f"{location}: unresolved draft marker"
                (errors if args.submission else warnings).append(message)
            if ABSOLUTE_PATH_PATTERN.search(raw_line):
                errors.append(f"{location}: committed absolute path")
            prose = re.sub(r"\\[A-Za-z@]+\*?(?:\[[^]]*\])?(?:\{[^{}]*\})?", "", raw_line)
            sentence_starts = re.findall(r"[.!?]\s+[A-Z]", prose)
            if sentence_starts and not stripped.startswith(("\\item", "\\newcommand", "\\placeholder", "\\papertodo")):
                message = f"{location}: possible multiple prose sentences on one physical line"
                (errors if args.submission else warnings).append(message)
            if EM_DASH_PATTERN.search(prose):
                message = f"{location}: em dash or triple hyphen in manuscript prose"
                (errors if args.submission else warnings).append(message)
            if BECAUSE_PATTERN.search(prose):
                message = f"{location}: 'because' in manuscript prose; state the rationale directly"
                (errors if args.submission else warnings).append(message)
            if FORMULAIC_PATTERN.search(prose):
                message = f"{location}: formulaic or promotional phrase requires a concrete replacement"
                (errors if args.submission else warnings).append(message)
            word_count = len(WORD_PATTERN.findall(prose))
            if (
                word_count > LONG_SENTENCE_REVIEW_WORDS
                and not stripped.startswith(("\\item", "\\newcommand", "\\placeholder", "\\papertodo"))
            ):
                warnings.append(
                    f"{location}: {word_count}-word prose line exceeds the {LONG_SENTENCE_REVIEW_WORDS}-word review trigger"
                )
            labels.extend((match, location) for match in LABEL_PATTERN.findall(raw_line))
            references.extend((match, location) for match in REF_PATTERN.findall(raw_line))
            for group in CITE_PATTERN.findall(raw_line):
                citations.extend((key.strip(), location) for key in group.split(",") if key.strip())
            for include in INCLUDE_PATTERN.findall(raw_line):
                if "\\" in include:
                    continue
                included_path = resolve_include(path, include)
                if not included_path.exists():
                    errors.append(f"{location}: included file does not exist: {include}")

    counts = Counter(label for label, _ in labels)
    for label, count in sorted(counts.items()):
        if count > 1:
            errors.append(f"duplicate label {label!r} appears {count} times")
    label_names = set(counts)
    for reference, location in references:
        if reference not in label_names:
            errors.append(f"{location}: unresolved LaTeX reference {reference!r}")

    bibliography_keys = bib_keys(BIB_PATH.read_text(encoding="utf-8")) if BIB_PATH.exists() else set()
    for citation, location in citations:
        if citation not in bibliography_keys:
            errors.append(f"{location}: citation key {citation!r} is absent from {BIB_PATH.name}")

    metadata = (PROJECT_ROOT / "paper" / "setup" / "metadata.tex").read_text(encoding="utf-8")
    if args.submission and "\\paperdrafttrue" in metadata:
        errors.append("paper/setup/metadata.tex: switch \\paperdrafttrue to \\paperdraftfalse for submission")

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    print(f"Checked {len(files)} TeX files: {len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
