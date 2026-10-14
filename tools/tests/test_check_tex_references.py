# SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)
#
# SPDX-License-Identifier: MIT

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from check_tex_references import EXPECTED_TYPES, check_reference_types
from package_arxiv import ArxivPackageError


class ReferenceTypeTests(unittest.TestCase):
    def specimen(self) -> str:
        return "\n".join(
            "\\newlabel{" + label + "@cref}{{[" + kind + "][1][]1}{[1][1][]1}}"
            for label, kind in EXPECTED_TYPES.items()
        )

    def test_expected_reference_types_pass(self) -> None:
        check_reference_types(self.specimen())

    def test_wrong_theorem_type_fails(self) -> None:
        with self.assertRaisesRegex(ArxivPackageError, "expected reference type theorem, found section"):
            check_reference_types(self.specimen().replace("[theorem]", "[section]"))

    def test_missing_labels_fail(self) -> None:
        with self.assertRaisesRegex(ArxivPackageError, "missing"):
            check_reference_types("")
