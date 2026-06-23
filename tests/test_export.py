import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import requests

from harvard_faculty_scraper.export import download_profile_image, sanitize_folder_name, write_person_folders
from harvard_faculty_scraper.models import FacultyRecord


class FakeImageResponse:
    def __init__(
        self,
        *,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        content: bytes = b"fake-jpeg-bytes",
    ) -> None:
        self.status_code = status_code
        self.headers = headers or {"Content-Type": "image/jpeg"}
        self.content = content

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} Client Error")
        return None


class FakeImageSession:
    def __init__(self) -> None:
        self.requested_urls: list[str] = []

    def get(self, url: str, timeout: float) -> FakeImageResponse:
        self.requested_urls.append(url)
        return FakeImageResponse()


class FakeSequenceImageSession:
    def __init__(self, responses: list[FakeImageResponse]) -> None:
        self.responses = responses
        self.requested_urls: list[str] = []

    def get(self, url: str, timeout: float) -> FakeImageResponse:
        self.requested_urls.append(url)
        return self.responses.pop(0)


class PersonFolderExportTest(unittest.TestCase):
    def test_sanitize_folder_name_keeps_windows_safe_name(self) -> None:
        self.assertEqual(sanitize_folder_name("Jane Q. Scholar, PhD"), "Jane Q. Scholar PhD")
        self.assertEqual(sanitize_folder_name("   ...   "), "unknown_person")

    def test_write_person_folders_downloads_image_and_jsonl(self) -> None:
        record = FacultyRecord(
            source_school="Example School",
            source_directory_url="https://example.harvard.edu/people",
            profile_url="https://example.harvard.edu/people/jane-scholar",
            full_name="Jane Q. Scholar",
            title="Postdoctoral Research Fellow",
            role_category="postdoc",
            email="jane@example.harvard.edu",
            image_url="https://example.harvard.edu/images/jane.jpg",
        )
        session = FakeImageSession()

        with tempfile.TemporaryDirectory() as tmp_dir:
            write_person_folders([record], Path(tmp_dir), session=session)

            folder = Path(tmp_dir) / "Jane Q. Scholar"
            profile_path = folder / "profile.jsonl"
            image_path = folder / "profile_picture.jpg"

            self.assertTrue(profile_path.exists())
            self.assertTrue(image_path.exists())
            self.assertEqual(image_path.read_bytes(), b"fake-jpeg-bytes")
            self.assertEqual(session.requested_urls, ["https://example.harvard.edu/images/jane.jpg"])

            payload = json.loads(profile_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["full_name"], "Jane Q. Scholar")
            self.assertEqual(payload["role_category"], "postdoc")
            self.assertTrue(payload["local_image_path"].endswith("profile_picture.jpg"))

    def test_download_profile_image_retries_rate_limit(self) -> None:
        session = FakeSequenceImageSession(
            [
                FakeImageResponse(status_code=429, headers={"Retry-After": "0"}),
                FakeImageResponse(status_code=200, headers={"Content-Type": "image/png"}, content=b"png"),
            ]
        )

        with tempfile.TemporaryDirectory() as tmp_dir, patch("harvard_faculty_scraper.export.time.sleep") as sleep:
            image_path = download_profile_image(
                "https://example.harvard.edu/images/jane.png",
                Path(tmp_dir),
                session=session,
                retries=1,
                backoff_seconds=0,
            )

            self.assertEqual(image_path.name, "profile_picture.png")
            self.assertEqual(image_path.read_bytes(), b"png")
            self.assertEqual(len(session.requested_urls), 2)
            sleep.assert_called_once_with(0.0)


if __name__ == "__main__":
    unittest.main()
