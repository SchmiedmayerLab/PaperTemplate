# SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import sys
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from check_project import submission_metadata_sentinels


class CheckProjectTests(unittest.TestCase):
    def test_submission_metadata_sentinels_are_exact(self) -> None:
        metadata = (
            r"\newcommand{\papertitle}{Working Title: A Specific and Bounded Scientific Contribution}"
            "\n"
            r"\newcommand{\correspondingemail}{corresponding.author@stanford.edu}"
            "\n"
        )
        self.assertEqual(
            submission_metadata_sentinels(metadata),
            (
                "Working Title: A Specific and Bounded Scientific Contribution",
                "corresponding.author@stanford.edu",
            ),
        )
        self.assertEqual(
            submission_metadata_sentinels(
                r"\newcommand{\papertitle}{A completed manuscript title}"
            ),
            (),
        )


if __name__ == "__main__":
    unittest.main()
