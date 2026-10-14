#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)
#
# SPDX-License-Identifier: MIT

"""Report required and optional local tools for the publication workflow."""

from __future__ import annotations

import shutil
import subprocess


REQUIRED = ("python3", "latexmk", "bibtex", "kpsewhich", "gs")
OPTIONAL = ("texcount", "reuse", "linkspector")
REQUIRED_TEX_FILES = (
    "XCharter.sty",
    "newtxmath.sty",
    "sourcesanspro.sty",
    "caption.sty",
    "fancyhdr.sty",
    "needspace.sty",
    "ragged2e.sty",
    "titlesec.sty",
    "xurl.sty",
    "orcidlink.sty",
)


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
    kpsewhich = shutil.which("kpsewhich")
    if kpsewhich:
        for tex_file in REQUIRED_TEX_FILES:
            result = subprocess.run(
                [kpsewhich, tex_file],
                check=False,
                capture_output=True,
                text=True,
            )
            path = result.stdout.strip()
            if result.returncode == 0 and path:
                print(f"FOUND required TeX file {tex_file}: {path}")
            else:
                print(f"MISSING required TeX file {tex_file}")
                missing.append(tex_file)
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
