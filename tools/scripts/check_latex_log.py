#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)
#
# SPDX-License-Identifier: MIT

"""Reject unresolved citations/references in the final pass of a LaTeX build."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from package_arxiv import ArxivPackageError, validate_compile_log


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("logs", nargs="+", type=Path)
    args = parser.parse_args(argv)
    for path in args.logs:
        try:
            validate_compile_log(path.read_text(encoding="utf-8", errors="replace"))
        except (OSError, ArxivPackageError) as error:
            print(f"LaTeX log check failed for {path}: {error}", file=sys.stderr)
            return 1
    print("Verified final LaTeX logs: " + ", ".join(map(str, args.logs)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
