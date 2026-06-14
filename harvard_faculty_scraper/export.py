from __future__ import annotations

import json
import mimetypes
import re
from collections.abc import Callable, Iterable
from hashlib import sha1
from pathlib import Path
from urllib.parse import urlparse

import requests

from .models import FacultyRecord
from .utils import clean_text


FOLDER_SAFE_RE = re.compile(r"[^A-Za-z0-9._ -]+")


def write_person_folders(
    records: Iterable[FacultyRecord],
    output_dir: Path,
    *,
    session: requests.Session | None = None,
    download_images: bool = True,
    continue_on_error: bool = False,
    on_error: Callable[[str, Exception], None] | None = None,
    timeout_seconds: float = 20.0,
) -> None:
    """Write one folder per person with profile JSONL and optional profile picture."""

    output_dir.mkdir(parents=True, exist_ok=True)
    http = session or requests.Session()
    used_folder_names: set[str] = set()

    for record in records:
        folder = _person_folder(output_dir, record, used_folder_names)
        folder.mkdir(parents=True, exist_ok=True)

        if download_images and record.image_url:
            try:
                record.local_image_path = str(
                    download_profile_image(
                        record.image_url,
                        folder,
                        session=http,
                        timeout_seconds=timeout_seconds,
                    )
                )
            except (requests.RequestException, ValueError, OSError) as exc:
                record.extraction_notes.append(f"image_download_failed: {exc}")
                if on_error:
                    on_error(record.image_url, exc)
                if not continue_on_error:
                    raise

        profile_path = folder / "profile.jsonl"
        profile_path.write_text(json.dumps(record.to_dict(), ensure_ascii=False) + "\n", encoding="utf-8")


def download_profile_image(
    image_url: str,
    folder: Path,
    *,
    session: requests.Session,
    timeout_seconds: float = 20.0,
) -> Path:
    response = session.get(image_url, timeout=timeout_seconds)
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
    extension = _image_extension(image_url, content_type)
    image_path = folder / f"profile_picture{extension}"
    image_path.write_bytes(response.content)
    return image_path


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
