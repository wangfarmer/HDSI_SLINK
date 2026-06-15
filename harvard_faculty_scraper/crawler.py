from __future__ import annotations

import json
import time
from collections.abc import Iterable
from dataclasses import replace
from pathlib import Path
from typing import Callable, TextIO
from urllib.parse import parse_qs, urlencode, urldefrag, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

from .extract import extract_faculty_record
from .models import FacultyRecord, SchoolConfig
from .utils import absolute_url, dedupe_preserve_order, domain_allowed, matches_any

try:
    from curl_cffi import requests as curl_requests
except ImportError:  # pragma: no cover - exercised only when optional dependency is missing.
    curl_requests = None


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
        http_client: str = "requests",
        request_retries: int = 3,
        request_backoff_seconds: float = 10.0,
        browser_fallback_on_403: bool = False,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config
        self.timeout_seconds = timeout_seconds
        self.delay_seconds = delay_seconds
        self.request_retries = request_retries
        self.request_backoff_seconds = request_backoff_seconds
        self.http_client = http_client
        self.browser_fallback_on_403 = browser_fallback_on_403
        self._fallback_session = None
        self.session = session or _make_session(http_client)
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
        profile_urls: list[str] = self.discover_api_profile_urls(
            max_pages=max_pages,
            continue_on_error=continue_on_error,
            on_error=on_error,
        )

        while queue and len(visited) < max_pages:
            url = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)
            try:
                html = self.fetch_text(url)
            except Exception as exc:
                if on_error:
                    on_error(url, exc)
                if continue_on_error:
                    continue
                raise
            soup = BeautifulSoup(html, "html.parser")

            for candidate_url in _html_candidate_urls(soup):
                absolute = _normalize_url(absolute_url(url, candidate_url))
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

    def discover_api_profile_urls(
        self,
        *,
        max_pages: int = 20,
        continue_on_error: bool = False,
        on_error: Callable[[str, Exception], None] | None = None,
    ) -> list[str]:
        """Discover profile URLs from JSON APIs such as WordPress REST endpoints."""

        profile_urls: list[str] = []
        pages_seen = 0
        for seed_url in self.config.api_seed_urls:
            next_url: str | None = seed_url
            while next_url and pages_seen < max_pages:
                pages_seen += 1
                try:
                    response = self.fetch_response(next_url)
                    payload = response.json()
                except (Exception, ValueError) as exc:
                    if on_error:
                        on_error(next_url, exc)
                    if continue_on_error:
                        break
                    raise

                for profile_url in _profile_urls_from_api_payload(payload):
                    normalized = _normalize_url(profile_url)
                    if not normalized or not domain_allowed(normalized, self.config.allowed_domains):
                        continue
                    if matches_any(normalized, self.config.exclude_link_patterns):
                        continue
                    if self._is_profile_url(normalized):
                        profile_urls.append(normalized)
                total_pages = _safe_int(response.headers.get("X-WP-TotalPages"))
                current_page = _query_page(next_url)
                if total_pages and current_page and current_page < total_pages:
                    next_url = _with_query_page(next_url, current_page + 1)
                    self.sleep()
                else:
                    next_url = None

        return profile_urls

    def scrape_profiles(
        self,
        profile_urls: Iterable[str],
        *,
        source_directory_url: str,
        max_profiles: int | None = None,
        continue_on_error: bool = False,
        on_error: Callable[[str, Exception], None] | None = None,
        write_failed_records: bool = False,
    ) -> list[FacultyRecord]:
        records: list[FacultyRecord] = []
        for index, profile_url in enumerate(profile_urls):
            if max_profiles is not None and index >= max_profiles:
                break
            try:
                html = self.fetch_text(profile_url)
            except Exception as exc:
                if on_error:
                    on_error(profile_url, exc)
                if continue_on_error:
                    if write_failed_records:
                        records.append(_failed_profile_record(self.config.name, source_directory_url, profile_url, exc))
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
        response = self.fetch_response(url)
        return response.text

    def fetch_response(self, url: str):
        attempts = max(1, self.request_retries + 1)
        response = None
        for attempt in range(attempts):
            response = self.session.get(url, timeout=self.timeout_seconds)
            status_code = getattr(response, "status_code", None)
            if status_code == 403 and self.browser_fallback_on_403 and self.http_client != "browser":
                fallback_response = self._get_fallback_session().get(url, timeout=self.timeout_seconds)
                fallback_status_code = getattr(fallback_response, "status_code", None)
                if fallback_status_code != 403:
                    response = fallback_response
                    status_code = fallback_status_code
            if status_code not in {429, 500, 502, 503, 504}:
                response.raise_for_status()
                return response
            if attempt == attempts - 1:
                response.raise_for_status()
                return response
            time.sleep(_retry_sleep_seconds(response, attempt, self.request_backoff_seconds))
        if response is None:
            raise ValueError("No response received")
        return response

    def _get_fallback_session(self):
        if self._fallback_session is None:
            self._fallback_session = _make_session("browser")
            self._fallback_session.headers.update(self.session.headers)
        return self._fallback_session

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


def _failed_profile_record(source_school: str, source_directory_url: str, profile_url: str, exc: Exception) -> FacultyRecord:
    return FacultyRecord(
        source_school=source_school,
        source_directory_url=source_directory_url,
        profile_url=profile_url,
        extraction_notes=[f"profile_fetch_failed: {exc}"],
        extra={"fetch_failed": True, "error": str(exc)},
    )


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


def _make_session(http_client: str):
    if http_client == "requests":
        return requests.Session()
    if http_client == "browser":
        if curl_requests is None:
            raise RuntimeError("curl_cffi is required for --http-client browser. Run: python -m pip install -e .")
        return curl_requests.Session(impersonate="chrome")
    raise ValueError(f"Unknown HTTP client: {http_client}")


def _html_candidate_urls(soup: BeautifulSoup) -> list[str]:
    values: list[str] = []
    for element in soup.select("a[href], [about]"):
        href = element.get("href")
        about = element.get("about")
        if href:
            values.append(str(href))
        if about:
            values.append(str(about))
    return values


def _profile_urls_from_api_payload(payload: object) -> list[str]:
    if not isinstance(payload, list):
        return []
    urls: list[str] = []
    for item in payload:
        if isinstance(item, dict) and isinstance(item.get("link"), str):
            urls.append(item["link"])
    return urls


def _query_page(url: str) -> int | None:
    query = parse_qs(urlparse(url).query)
    values = query.get("page")
    if not values:
        return None
    return _safe_int(values[0])


def _with_query_page(url: str, page: int) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    query["page"] = [str(page)]
    encoded_query = urlencode(query, doseq=True)
    return urlunparse(parsed._replace(query=encoded_query))


def _safe_int(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _retry_sleep_seconds(response: object, attempt: int, backoff_seconds: float) -> float:
    retry_after = getattr(response, "headers", {}).get("Retry-After")
    if retry_after:
        try:
            return max(0.0, float(retry_after))
        except ValueError:
            pass
    return max(0.0, backoff_seconds * (attempt + 1))
