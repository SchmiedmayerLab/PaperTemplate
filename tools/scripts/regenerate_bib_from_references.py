#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2026 Stanford University and the project authors (see CONTRIBUTORS.md)
#
# SPDX-License-Identifier: MIT

"""Regenerate the LaTeX-facing bibliography from reference source folders."""

from __future__ import annotations

import argparse
import difflib

from reference_common import BIB_PATH, generated_bibliography


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--in-place", action="store_true", help="Write the generated bibliography to references.bib.")
    mode.add_argument("--check", action="store_true", help="Fail when references.bib is not synchronized.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    generated, problems = generated_bibliography()
    if problems:
        for problem in problems:
            print(f"ERROR: {problem}")
        return 1
    current = BIB_PATH.read_text(encoding="utf-8") if BIB_PATH.exists() else ""
    if args.check:
        if current == generated:
            print(f"OK: {BIB_PATH.name} is synchronized")
            return 0
        print(f"ERROR: {BIB_PATH.name} is not synchronized")
        for line in difflib.unified_diff(
            current.splitlines(),
            generated.splitlines(),
            fromfile=str(BIB_PATH),
            tofile="generated",
            lineterm="",
        ):
            print(line)
        return 1
    if args.in_place:
        BIB_PATH.write_text(generated, encoding="utf-8")
        print(f"Wrote {BIB_PATH}")
    else:
        print(generated, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
