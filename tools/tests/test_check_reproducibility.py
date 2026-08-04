# SPDX-FileCopyrightText: 2026 Stanford University and the project authors (see CONTRIBUTORS.md)
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import csv
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import check_reproducibility


class ReproducibilityCheckTests(unittest.TestCase):
    def make_project(self) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        for directory in (
            "research/analysis/environment",
            "research/data/source",
            "research/data/external",
            "research/data/restricted",
            "paper/figures/generated",
            "paper/tables/generated",
            "research/reproducibility",
            "paper/sections",
            "paper/supplement",
        ):
            (root / directory).mkdir(parents=True, exist_ok=True)
        (root / "research/analysis/environment/README.md").write_text("environment\n", encoding="utf-8")
        for path in (
            "research/data/source/README.md",
            "research/data/external/README.md",
            "research/data/restricted/README.md",
            "paper/figures/generated/README.md",
            "paper/tables/generated/README.md",
        ):
            (root / path).write_text("placeholder\n", encoding="utf-8")
        (root / "research/data/manifest.tsv").write_text("\t".join(check_reproducibility.DATA_FIELDS) + "\n", encoding="utf-8")
        (root / "research/reproducibility/submodules.tsv").write_text(
            "path\trepository\trole\tversion_label\tpinned_commit\tlicense\tmanuscript_use\n",
            encoding="utf-8",
        )
        (root / "research/reproducibility/pipeline.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "environment": "research/analysis/environment/README.md",
                    "steps": [],
                }
            ),
            encoding="utf-8",
        )
        (root / "main.tex").write_text("", encoding="utf-8")
        return root

    def test_empty_template_is_valid(self) -> None:
        root = self.make_project()
        errors, warnings, _, _ = check_reproducibility.validate_project(root)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_foundational_data_requires_manifest_and_checksum(self) -> None:
        root = self.make_project()
        data_path = root / "research/data/source/example.csv"
        data_path.write_text("value\n1\n", encoding="utf-8")
        errors, _, _, _ = check_reproducibility.validate_project(root)
        self.assertTrue(any("absent from research/data/manifest.tsv" in error for error in errors))

        digest = hashlib.sha256(data_path.read_bytes()).hexdigest()
        with (root / "research/data/manifest.tsv").open("a", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
            writer.writerow(
                [
                    "research/data/source/example.csv",
                    "source",
                    "synthetic fixture",
                    "1",
                    "MIT",
                    "public",
                    f"sha256:{digest}",
                    "test data",
                ]
            )
        errors, _, _, _ = check_reproducibility.validate_project(root)
        self.assertEqual(errors, [])

    def test_undeclared_generated_artifact_is_an_error(self) -> None:
        root = self.make_project()
        (root / "paper/figures/generated/result.pdf").write_bytes(b"result")
        errors, _, _, _ = check_reproducibility.validate_project(root)
        self.assertTrue(any("generated artifact is not declared" in error for error in errors))

    def test_output_cannot_escape_generated_directories(self) -> None:
        root = self.make_project()
        pipeline = {
            "schema_version": 1,
            "environment": "research/analysis/environment/README.md",
            "steps": [
                {
                    "id": "unsafe-output",
                    "description": "Attempt an unsafe output.",
                    "inputs": ["research/analysis/environment/README.md"],
                    "command": ["python3", "research/analysis/scripts/example.py"],
                    "outputs": ["paper/sections/result.tex"],
                    "manuscript_locations": ["main.tex"],
                    "requires_restricted_data": False,
                }
            ],
        }
        (root / "research/reproducibility/pipeline.json").write_text(json.dumps(pipeline), encoding="utf-8")
        errors, _, _, _ = check_reproducibility.validate_project(root)
        self.assertTrue(any("outside an allowed generated directory" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
