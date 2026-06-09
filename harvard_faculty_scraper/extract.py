from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from bs4 import BeautifulSoup, Tag

from .models import FacultyRecord
from .utils import absolute_url, clean_text, dedupe_preserve_order, first_email


TITLE_HINTS = (
    "professor",
    "lecturer",
    "dean",
    "fellow",
    "research scientist",
    "instructor",
    "faculty",
    "chair",
    "director",
)

BIO_HEADING_RE = re.compile(
    r"\b(biography|bio|about|profile|overview|background)\b",
    re.IGNORECASE,
)
RESEARCH_HEADING_RE = re.compile(
    r"\b(research|interests|expertise|areas of interest|topics)\b",
    re.IGNORECASE,
)


def extract_faculty_record(
    html: str,
    profile_url: str,
    source_school: str,
    source_directory_url: str,
) -> FacultyRecord:
    soup = BeautifulSoup(html, "html.parser")
    for element in soup(["script", "style", "noscript"]):
        element.decompose()

    json_ld_people = _extract_json_ld_people(html)
    json_ld = json_ld_people[0] if json_ld_people else {}
    notes: list[str] = []
    if json_ld:
        notes.append("used_json_ld")

    name = _first_nonempty(
        _json_value(json_ld, "name"),
        _meta_content(soup, "og:title"),
        _select_text(soup, ["h1", ".field--name-title", ".profile-name", ".person-name"]),
    )
    name = _clean_name(name)

    title = _first_nonempty(
        _json_value(json_ld, "jobTitle"),
        _select_text(
            soup,
            [
                ".field--name-field-title",
                ".field--name-field-job-title",
                ".profile-title",
                ".person-title",
                ".views-field-title",
                "[class*=title]",
                "[class*=position]",
            ],
            predicate=_looks_like_title,
        ),
        _title_from_near_header(soup),
    )

    affiliation = _first_nonempty(
        _json_value(json_ld, "affiliation"),
        _select_text(
            soup,
            [
                ".field--name-field-department",
                ".field--name-field-affiliation",
                ".department",
                ".affiliation",
                "[class*=department]",
                "[class*=affiliation]",
            ],
        ),
    )

    email = _first_nonempty(_json_value(json_ld, "email"), _email_from_mailto(soup), first_email(soup.get_text(" ")))
    if email:
        email = email.removeprefix("mailto:").strip()

    image_url = _first_nonempty(
        _json_value(json_ld, "image"),
        _meta_content(soup, "og:image"),
        _select_image(soup, profile_url),
    )
    if image_url:
        image_url = absolute_url(profile_url, image_url)

    bio = _first_nonempty(
        _meta_content(soup, "description"),
        _bio_from_selectors(soup),
        _section_after_heading(soup, BIO_HEADING_RE),
    )

    research_interests = dedupe_preserve_order(
        _research_from_json_ld(json_ld)
        + _research_from_selectors(soup)
        + _split_interests(_section_after_heading(soup, RESEARCH_HEADING_RE))
    )

    raw_text_excerpt = clean_text(soup.get_text(" "))
    if raw_text_excerpt and len(raw_text_excerpt) > 1000:
        raw_text_excerpt = raw_text_excerpt[:1000].rstrip()

    return FacultyRecord(
        source_school=source_school,
        source_directory_url=source_directory_url,
        profile_url=profile_url,
        full_name=name,
        title=title,
        affiliation=affiliation,
        email=email,
        image_url=image_url,
        bio=bio,
        research_interests=research_interests,
        raw_text_excerpt=raw_text_excerpt,
        scraped_at=datetime.now(timezone.utc).isoformat(),
        extraction_notes=notes,
    )


def _extract_json_ld_people(html: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    people: list[dict[str, Any]] = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        text = script.string or script.get_text()
        if not text:
            continue
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            continue
        for item in _flatten_json_ld(payload):
            item_type = item.get("@type")
            if isinstance(item_type, list):
                is_person = any(str(value).lower() == "person" for value in item_type)
            else:
                is_person = str(item_type).lower() == "person"
            if is_person:
                people.append(item)
    return people


def _flatten_json_ld(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        values = [payload]
        graph = payload.get("@graph")
        if isinstance(graph, list):
            values.extend(item for item in graph if isinstance(item, dict))
        return values
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def _json_value(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if isinstance(value, str):
        return clean_text(value)
    if isinstance(value, dict):
        return _first_nonempty(value.get("name"), value.get("@id"))
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("name"), str):
                parts.append(item["name"])
        return clean_text(", ".join(parts))
    return None


def _meta_content(soup: BeautifulSoup, name: str) -> str | None:
    selectors = [
        {"property": name},
        {"name": name},
    ]
    if name == "description":
        selectors.extend([{"property": "og:description"}, {"name": "twitter:description"}])
    for attrs in selectors:
        tag = soup.find("meta", attrs=attrs)
        if tag and tag.get("content"):
            return clean_text(str(tag["content"]))
    return None


def _select_text(
    soup: BeautifulSoup,
    selectors: list[str],
    predicate: Any | None = None,
) -> str | None:
    for selector in selectors:
        for tag in soup.select(selector):
            text = clean_text(tag.get_text(" "))
            if text and (predicate is None or predicate(text)):
                return text
    return None


def _select_image(soup: BeautifulSoup, base_url: str) -> str | None:
    selectors = [
        ".profile img",
        ".person img",
        ".faculty img",
        "article img",
        "main img",
        "img",
    ]
    for selector in selectors:
        for tag in soup.select(selector):
            src = tag.get("src") or tag.get("data-src")
            if src:
                return absolute_url(base_url, str(src))
    return None


def _email_from_mailto(soup: BeautifulSoup) -> str | None:
    for tag in soup.select('a[href^="mailto:"]'):
        href = tag.get("href")
        if href:
            return href.split("?", 1)[0].removeprefix("mailto:")
    return None


def _bio_from_selectors(soup: BeautifulSoup) -> str | None:
    selectors = [
        ".field--name-body",
        ".field--name-field-bio",
        ".field--name-field-biography",
        ".profile-bio",
        ".person-bio",
        ".bio",
        ".biography",
        "article",
        "main",
    ]
    for selector in selectors:
        for tag in soup.select(selector):
            text = _paragraph_text(tag)
            if text and len(text) >= 120:
                return text
    return None


def _paragraph_text(tag: Tag) -> str | None:
    paragraphs = [clean_text(p.get_text(" ")) for p in tag.find_all(["p", "li"])]
    paragraphs = [p for p in paragraphs if p]
    if paragraphs:
        return clean_text(" ".join(paragraphs[:6]))
    return clean_text(tag.get_text(" "))


def _section_after_heading(soup: BeautifulSoup, heading_re: re.Pattern[str]) -> str | None:
    for heading in soup.find_all(re.compile("^h[1-6]$")):
        heading_text = clean_text(heading.get_text(" "))
        if not heading_text or not heading_re.search(heading_text):
            continue
        parts: list[str] = []
        for sibling in heading.find_next_siblings():
            if isinstance(sibling, Tag) and re.match(r"^h[1-6]$", sibling.name or ""):
                break
            if isinstance(sibling, Tag):
                text = _paragraph_text(sibling)
                if text:
                    parts.append(text)
            if len(" ".join(parts)) > 800:
                break
        text = clean_text(" ".join(parts))
        if text:
            return text
    return None


def _research_from_json_ld(payload: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for key in ("knowsAbout", "keywords"):
        value = payload.get(key)
        if isinstance(value, str):
            values.extend(_split_interests(value))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    values.extend(_split_interests(item))
    return values


def _research_from_selectors(soup: BeautifulSoup) -> list[str]:
    selectors = [
        ".field--name-field-research-interests",
        ".field--name-field-areas-of-expertise",
        ".research-interests",
        ".expertise",
        "[class*=research-interest]",
        "[class*=expertise]",
    ]
    values: list[str] = []
    for selector in selectors:
        for tag in soup.select(selector):
            values.extend(_split_interests(tag.get_text(" ")))
    return values


def _split_interests(text: str | None) -> list[str]:
    text = clean_text(text)
    if not text:
        return []
    text = re.sub(r"^(research interests?|expertise|areas of interest)\s*:?", "", text, flags=re.IGNORECASE)
    parts = re.split(r"[,;|]\s*|\n+", text)
    return [part for part in (clean_text(part) for part in parts) if part and len(part) <= 80]


def _title_from_near_header(soup: BeautifulSoup) -> str | None:
    header = soup.find("h1")
    if not header:
        return None
    for tag in header.find_all_next(["p", "div", "span"], limit=8):
        text = clean_text(tag.get_text(" "))
        if text and _looks_like_title(text):
            return text
    return None


def _looks_like_title(text: str) -> bool:
    lowered = text.lower()
    return any(hint in lowered for hint in TITLE_HINTS) and len(text) <= 220


def _clean_name(value: str | None) -> str | None:
    value = clean_text(value)
    if not value:
        return None
    value = re.sub(r"\s*\|\s*Harvard.*$", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\s*-\s*Harvard.*$", "", value, flags=re.IGNORECASE)
    return clean_text(value)


def _first_nonempty(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str):
            cleaned = clean_text(value)
            if cleaned:
                return cleaned
    return None
