from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class SchoolConfig:
    """Configuration for one Harvard school people/researcher directory."""

    key: str
    name: str
    seed_urls: list[str]
    allowed_domains: list[str]
    profile_link_patterns: list[str] = field(default_factory=list)
    exclude_link_patterns: list[str] = field(default_factory=list)
    profile_required_patterns: list[str] = field(default_factory=list)
    list_page_patterns: list[str] = field(default_factory=list)
    api_seed_urls: list[str] = field(default_factory=list)


@dataclass
class FacultyRecord:
    """Normalized Harvard person/researcher profile record used by requirement 2."""

    source_school: str
    source_directory_url: str
    profile_url: str
    full_name: str | None = None
    title: str | None = None
    role_category: str | None = None
    affiliation: str | None = None
    email: str | None = None
    image_url: str | None = None
    local_image_path: str | None = None
    bio: str | None = None
    research_interests: list[str] = field(default_factory=list)
    raw_text_excerpt: str | None = None
    scraped_at: str | None = None
    extraction_notes: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
