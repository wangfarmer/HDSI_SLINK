from __future__ import annotations

import json
import time
from collections.abc import Iterable
from dataclasses import replace
from pathlib import Path
from typing import Callable, TextIO
from urllib.parse import urldefrag

import requests
from bs4 import BeautifulSoup

from .extract import extract_faculty_record
from .models import FacultyRecord, SchoolConfig
from .utils import absolute_url, dedupe_preserve_order, domain_allowed, matches_any


DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36"

DEFAULT_HEADERS = {
    "User-Agent": DEFAULT_USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


class HarvardFacultyCrawler:
    """Small, configurable crawler for Harvard faculty directory pages."""

    def __init__(
        self,
        config: SchoolConfig,
        *,
        timeout_seconds: float = 20.0,
        delay_seconds: float = 1.0,
        user_agent: str = DEFAULT_USER_AGENT,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config
        self.timeout_seconds = timeout_seconds
        self.delay_seconds = delay_seconds
        self.session = session or requests.Session()
        self.session.headers.update(DEFAULT_HEADERS | {"User-Agent": user_agent})

    def discover_profile_urls(
        self,
        *,
        max_pages: int = 20,
        continue_on_error: bool = False,
        on_error: Callable[[str, Exception], None] | None = None,
    ) -> list[str]:
        """Discover profile links from configured seed/list pages."""

        queue = list(self.config.seed_urls)
        visited: set[str] = set()
        profile_urls: list[str] = []

        while queue and len(visited) < max_pages:
            url = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)
            try:
                html = self.fetch_text(url)
            except requests.RequestException as exc:
                if on_error:
                    on_error(url, exc)
                if continue_on_error:
                    continue
                raise
            soup = BeautifulSoup(html, "html.parser")

            for link in soup.select("a[href]"):
                href = str(link.get("href"))
                absolute = _normalize_url(absolute_url(url, href))
                if not absolute or not domain_allowed(absolute, self.config.allowed_domains):
                    continue
                if matches_any(absolute, self.config.exclude_link_patterns):
                    continue
                if self._is_profile_url(absolute):
                    profile_urls.append(absolute)
                elif self._is_list_page_url(absolute) and absolute not in visited and absolute not in queue:
                    queue.append(absolute)

            self.sleep()

        return dedupe_preserve_order(profile_urls)

    def scrape_profiles(
        self,
        profile_urls: Iterable[str],
        *,
        source_directory_url: str,
        max_profiles: int | None = None,
        continue_on_error: bool = False,
        on_error: Callable[[str, Exception], None] | None = None,
    ) -> list[FacultyRecord]:
        records: list[FacultyRecord] = []
        for index, profile_url in enumerate(profile_urls):
            if max_profiles is not None and index >= max_profiles:
                break
            try:
                html = self.fetch_text(profile_url)
            except requests.RequestException as exc:
                if on_error:
                    on_error(profile_url, exc)
                if continue_on_error:
                    continue
                raise
            records.append(
                extract_faculty_record(
                    html,
                    profile_url=profile_url,
                    source_school=self.config.name,
                    source_directory_url=source_directory_url,
                )
            )
            self.sleep()
        return records

    def fetch_text(self, url: str) -> str:
        response = self.session.get(url, timeout=self.timeout_seconds)
        response.raise_for_status()
        return response.text

    def sleep(self) -> None:
        if self.delay_seconds > 0:
            time.sleep(self.delay_seconds)

    def _is_profile_url(self, url: str) -> bool:
        if self.config.profile_required_patterns:
            return matches_any(url, self.config.profile_required_patterns)
        return matches_any(url, self.config.profile_link_patterns)

    def _is_list_page_url(self, url: str) -> bool:
        return matches_any(url, self.config.list_page_patterns)


def with_seed_urls(config: SchoolConfig, seed_urls: list[str]) -> SchoolConfig:
    return replace(config, seed_urls=seed_urls)


def write_jsonl(records: Iterable[FacultyRecord], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")


def write_csv(records: Iterable[FacultyRecord], output_path: Path) -> None:
    import csv

    rows = [record.to_dict() for record in records]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "source_school",
                "source_directory_url",
                "profile_url",
                "full_name",
                "title",
                "role_category",
                "affiliation",
                "email",
                "image_url",
                "local_image_path",
                "bio",
                "research_interests",
                "raw_text_excerpt",
                "scraped_at",
                "extraction_notes",
                "extra",
            ],
        )
        writer.writeheader()
        for row in rows:
            row["research_interests"] = "; ".join(row.get("research_interests") or [])
            row["extraction_notes"] = "; ".join(row.get("extraction_notes") or [])
            row["extra"] = json.dumps(row.get("extra") or {}, ensure_ascii=False)
            writer.writerow(row)


def print_jsonl(records: Iterable[FacultyRecord], handle: TextIO) -> None:
    for record in records:
        handle.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")


def _normalize_url(url: str | None) -> str | None:
    if not url:
        return None
    url, _fragment = urldefrag(url)
    return url.rstrip("/")
