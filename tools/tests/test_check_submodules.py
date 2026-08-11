# SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import check_submodules


class SubmoduleCheckTests(unittest.TestCase):
    def make_project(self, manifest_row: str = "") -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        (root / "research/reproducibility").mkdir(parents=True)
        header = "\t".join(check_submodules.FIELDS) + "\n"
        (root / "research/reproducibility/submodules.tsv").write_text(header + manifest_row, encoding="utf-8")
        return root

    def test_empty_manifest_without_gitmodules_is_valid(self) -> None:
        root = self.make_project()
        errors, warnings, records = check_submodules.validate_project(root)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual(records, [])

    def test_manifest_entry_requires_gitmodules_section(self) -> None:
        row = (
            "research/analysis/external/example\thttps://example.org/repository.git\tevaluation\tv1.0\t"
            + "a" * 40
            + "\tMIT\tGenerate the primary evaluation\n"
        )
        root = self.make_project(row)
        errors, _, _ = check_submodules.validate_project(root)
        self.assertTrue(any("no matching .gitmodules section" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
