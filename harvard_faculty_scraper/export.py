from __future__ import annotations

import json
import mimetypes
import re
import time
from collections.abc import Callable, Iterable
from hashlib import sha1
from pathlib import Path
from urllib.parse import urlparse

import requests

from .models import FacultyRecord
from .utils import clean_text


FOLDER_SAFE_RE = re.compile(r"[^A-Za-z0-9._ -]+")


class PersonFolderWriter:
    """Incrementally write one folder per person."""

    def __init__(
        self,
        output_dir: Path,
        *,
        session: requests.Session | None = None,
        download_images: bool = True,
        continue_on_error: bool = False,
        on_error: Callable[[str, Exception], None] | None = None,
        timeout_seconds: float = 20.0,
        image_delay_seconds: float = 0.0,
        image_retries: int = 3,
        image_backoff_seconds: float = 5.0,
    ) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = session or requests.Session()
        self.download_images = download_images
        self.continue_on_error = continue_on_error
        self.on_error = on_error
        self.timeout_seconds = timeout_seconds
        self.image_delay_seconds = image_delay_seconds
        self.image_retries = image_retries
        self.image_backoff_seconds = image_backoff_seconds
        self.used_folder_names: set[str] = set()

    def write(self, record: FacultyRecord) -> Path:
        folder = _person_folder(self.output_dir, record, self.used_folder_names)
        folder.mkdir(parents=True, exist_ok=True)

        if self.download_images and record.image_url:
            if self.image_delay_seconds > 0:
                time.sleep(self.image_delay_seconds)
            try:
                record.local_image_path = str(
                    download_profile_image(
                        record.image_url,
                        folder,
                        session=self.session,
                        timeout_seconds=self.timeout_seconds,
                        retries=self.image_retries,
                        backoff_seconds=self.image_backoff_seconds,
                    )
                )
            except (Exception, ValueError, OSError) as exc:
                record.extraction_notes.append(f"image_download_failed: {exc}")
                if self.on_error:
                    self.on_error(record.image_url, exc)
                if not self.continue_on_error:
                    raise

        profile_path = folder / "profile.jsonl"
        profile_path.write_text(json.dumps(record.to_dict(), ensure_ascii=False) + "\n", encoding="utf-8")
        return folder


def write_person_folders(
    records: Iterable[FacultyRecord],
    output_dir: Path,
    *,
    session: requests.Session | None = None,
    download_images: bool = True,
    continue_on_error: bool = False,
    on_error: Callable[[str, Exception], None] | None = None,
    timeout_seconds: float = 20.0,
    image_delay_seconds: float = 0.0,
    image_retries: int = 3,
    image_backoff_seconds: float = 5.0,
) -> None:
    """Write one folder per person with profile JSONL and optional profile picture."""

    writer = PersonFolderWriter(
        output_dir,
        session=session,
        download_images=download_images,
        continue_on_error=continue_on_error,
        on_error=on_error,
        timeout_seconds=timeout_seconds,
        image_delay_seconds=image_delay_seconds,
        image_retries=image_retries,
        image_backoff_seconds=image_backoff_seconds,
    )
    for record in records:
        writer.write(record)


def download_profile_image(
    image_url: str,
    folder: Path,
    *,
    session: requests.Session,
    timeout_seconds: float = 20.0,
    retries: int = 3,
    backoff_seconds: float = 5.0,
) -> Path:
    response = None
    attempts = max(1, retries + 1)
    for attempt in range(attempts):
        response = session.get(image_url, timeout=timeout_seconds)
        status_code = getattr(response, "status_code", None)
        if status_code not in {429, 500, 502, 503, 504}:
            response.raise_for_status()
            break
        if attempt == attempts - 1:
            response.raise_for_status()
        time.sleep(_retry_sleep_seconds(response, attempt, backoff_seconds))

    if response is None:
        raise ValueError("No image response received")

    content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
    extension = _image_extension(image_url, content_type)
    image_path = folder / f"profile_picture{extension}"
    image_path.write_bytes(response.content)
    return image_path


def _retry_sleep_seconds(response: object, attempt: int, backoff_seconds: float) -> float:
    retry_after = getattr(response, "headers", {}).get("Retry-After")
    if retry_after:
        try:
            return max(0.0, float(retry_after))
        except ValueError:
            pass
    return max(0.0, backoff_seconds * (attempt + 1))


def _person_folder(output_dir: Path, record: FacultyRecord, used_folder_names: set[str]) -> Path:
    preferred_name = clean_text(record.full_name) or "unknown_person"
    base_name = sanitize_folder_name(preferred_name)
    suffix_source = record.profile_url or preferred_name
    candidate = base_name
    if candidate in used_folder_names:
        candidate = f"{base_name}__{sha1(suffix_source.encode('utf-8')).hexdigest()[:8]}"
    used_folder_names.add(candidate)
    return output_dir / candidate


def sanitize_folder_name(name: str) -> str:
    sanitized = FOLDER_SAFE_RE.sub("", name)
    sanitized = re.sub(r"\s+", " ", sanitized).strip(" .")
    if not sanitized:
        return "unknown_person"
    # Keep Windows paths short and avoid trailing dots/spaces.
    return sanitized[:120].rstrip(" .")


def _image_extension(image_url: str, content_type: str) -> str:
    extension = mimetypes.guess_extension(content_type) if content_type else None
    if extension in {".jpe"}:
        extension = ".jpg"
    if extension:
        return extension

    path_extension = Path(urlparse(image_url).path).suffix.lower()
    if path_extension in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
        return path_extension

    if content_type and not content_type.startswith("image/"):
        raise ValueError(f"URL did not return an image content type: {content_type}")
    return ".jpg"
