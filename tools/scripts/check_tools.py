#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2026 Stanford University and the project authors (see CONTRIBUTORS.md)
#
# SPDX-License-Identifier: MIT

"""Report required and optional local tools for the publication workflow."""

from __future__ import annotations

import shutil


REQUIRED = ("python3", "latexmk", "bibtex")
OPTIONAL = ("texcount", "reuse", "linkspector")


def main() -> int:
    missing = []
    for command in REQUIRED:
        path = shutil.which(command)
        if path:
            print(f"FOUND required {command}: {path}")
        else:
            print(f"MISSING required {command}")
            missing.append(command)
    for command in OPTIONAL:
        path = shutil.which(command)
        if path:
            print(f"FOUND optional {command}: {path}")
        else:
            print(f"MISSING optional {command}")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
