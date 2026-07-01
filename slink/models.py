from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class DomainScore:
    domain_id: str
    domain_name: str
    score: float


@dataclass
class ResearchFocus:
    focus_id: str
    label: str
    primary_domain_id: str
    primary_domain_name: str
    strength: float
    supporting_domains: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)


@dataclass
class SLinkPartner:
    person_id: str
    full_name: str
    school_key: str
    score: float
    rationale: str


@dataclass
class SLinkRecommendation:
    focus_id: str
    title: str
    primary_domain_id: str
    primary_domain_name: str
    rationale: str
    suggested_partners: list[SLinkPartner] = field(default_factory=list)


@dataclass
class ResearcherProfile:
    person_id: str
    full_name: str
    school_key: str
    orcid: str | None
    title: str | None
    profile_url: str | None
    domain_scores: list[DomainScore] = field(default_factory=list)
    research_foci: list[ResearchFocus] = field(default_factory=list)
    ai_readiness: str = "non_ai"
    methodological_tags: list[str] = field(default_factory=list)
    application_tags: list[str] = field(default_factory=list)
    collaboration_intent_tags: list[str] = field(default_factory=list)
    slink_recommendations: list[SLinkRecommendation] = field(default_factory=list)
    signal_text_excerpt: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
