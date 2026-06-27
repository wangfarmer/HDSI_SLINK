from __future__ import annotations

import unittest

from harvard_faculty_scraper.orcid_match import OrcidNameIndex, OrcidPerson, load_orcid_people, strip_folder_artifacts


class OrcidMatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.index = OrcidNameIndex(
            [
                OrcidPerson("0000-0001-5023-4399", "Andrea L. Roberts", "Andrea", "Roberts", "Andrea L. Roberts"),
                OrcidPerson("0000-0001-5007-193X", "Rui Wang", "Rui", "Wang", ""),
                OrcidPerson("0000-0001-5018-5419", "Zhiyu Yan", "Zhiyu (Roman)", "Yan", "Zhiyu Yan"),
            ]
        )

    def test_exact_full_name_match(self) -> None:
        match = self.index.match("Andrea L. Roberts")
        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.orcid, "0000-0001-5023-4399")
        self.assertEqual(match.method, "exact")

    def test_missing_middle_name_match(self) -> None:
        match = self.index.match("Andrea Roberts")
        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.orcid, "0000-0001-5023-4399")
        self.assertEqual(match.method, "core_name")

    def test_folder_suffix_is_stripped(self) -> None:
        folder = "Susan A. Murphy Radcliffe Institute for Advanced Study at Harvard University"
        self.assertEqual(
            strip_folder_artifacts(folder),
            "Susan A. Murphy",
        )

    def test_pipe_suffix_is_stripped(self) -> None:
        value = "Susan A. Murphy | Radcliffe Institute for Advanced Study at Harvard University"
        self.assertEqual(strip_folder_artifacts(value), "Susan A. Murphy")

    def test_ambiguous_core_name_returns_none(self) -> None:
        ambiguous = OrcidNameIndex(
            [
                OrcidPerson("0000-0001-0001-0001", "John Michael Smith", "John", "Smith", ""),
                OrcidPerson("0000-0001-0002-0002", "John Matthew Smith", "John", "Smith", ""),
            ]
        )
        self.assertIsNone(ambiguous.match("John Smith"))


class OrcidCsvLoadTests(unittest.TestCase):
    def test_load_orcid_csv_from_repo(self) -> None:
        from pathlib import Path

        csv_path = Path("harvard_orcid_unique_names.csv")
        if not csv_path.exists():
            self.skipTest("ORCID CSV not present in workspace")
        people = load_orcid_people(csv_path)
        self.assertGreater(len(people), 1000)
        self.assertTrue(all(person.orcid for person in people))


if __name__ == "__main__":
    unittest.main()
