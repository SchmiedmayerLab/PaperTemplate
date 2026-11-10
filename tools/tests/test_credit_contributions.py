# SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)
# SPDX-License-Identifier: MIT

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from credit_contributions import generate, ROLES


class ContributionsTests(unittest.TestCase):
    def setUp(self):
        self.data = {"schema_version": 1, "authors": [{
            "name": "A. Example & B_Example", "roles": ["Software", "Conceptualization"], "confirmed": True,
        }]}

    def test_escape_and_canonical_order(self):
        text = generate(self.data, submission=True)
        self.assertIn(r"A. Example \& B\_Example", text)
        self.assertIn("Conceptualization; Software", text)
        self.assertNotIn("placeholder", text)
        self.assertEqual(len(ROLES), 14)

    def test_unconfirmed_assignments_stay_visible_and_block_submission(self):
        self.data["authors"][0]["confirmed"] = False
        self.assertIn(r"\placeholder{Confirm", generate(self.data))
        with self.assertRaisesRegex(ValueError, "not been confirmed"):
            generate(self.data, submission=True)

    def test_no_invented_assignments_in_empty_template(self):
        data = {"schema_version": 1, "authors": []}
        self.assertIn("placeholder", generate(data))
        with self.assertRaises(ValueError):
            generate(data, submission=True)

    def test_invalid_assignments_fail(self):
        for field, value in (("roles", ["Editing"]), ("roles", []), ("roles", ["Software", "Software"]),
                             ("roles", [None]), ("confirmed", "true"), ("name", "\n")):
            with self.subTest(field=field, value=value):
                data = copy.deepcopy(self.data)
                data["authors"][0][field] = value
                with self.assertRaises(ValueError):
                    generate(data)
        self.data["authors"].append(copy.deepcopy(self.data["authors"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            generate(self.data)


if __name__ == "__main__":
    unittest.main()
