#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)
#
# SPDX-License-Identifier: MIT

"""Compile the shared TeX setup and verify cleveref's recorded reference types."""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

from package_arxiv import ArxivPackageError, validate_compile_log


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_TYPES = {
    "sec:specimen": "section",
    "eq:specimen": "equation",
    "fig:specimen": "figure",
    "tab:specimen": "table",
    "thm:specimen": "theorem",
    "lem:specimen": "lemma",
    "thm:after-lemma": "theorem",
}


def check_reference_types(auxiliary: str) -> None:
    for label, expected in EXPECTED_TYPES.items():
        pattern = r"\\newlabel\{" + re.escape(label) + r"@cref\}\{\{\[([^\]]+)\]"
        match = re.search(pattern, auxiliary)
        actual = match[1] if match else "missing"
        if actual != expected:
            raise ArxivPackageError(f"{label}: expected reference type {expected}, found {actual}")


def main() -> int:
    try:
        with tempfile.TemporaryDirectory(prefix="paper-tex-references-") as temporary:
            output = Path(temporary)
            process = subprocess.run(
                [
                    "latexmk", "-norc", "-pdf", "-no-shell-escape",
                    "-interaction=nonstopmode", "-halt-on-error", "-file-line-error",
                    f"-outdir={output}", f"-auxdir={output}",
                    "tools/tests/fixtures/tex-references.tex",
                ],
                cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=300,
            )
            if process.returncode:
                raise ArxivPackageError((process.stdout + process.stderr)[-6000:])
            log = (output / "tex-references.log").read_text(encoding="utf-8")
            validate_compile_log(log)
            check_reference_types((output / "tex-references.aux").read_text(encoding="utf-8"))
            print(log.splitlines()[0])
            print("Verified section, equation, figure, table, theorem, and shared-counter lemma reference types.")
            return 0
    except (ArxivPackageError, OSError, subprocess.TimeoutExpired) as error:
        print(f"TeX reference check failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
