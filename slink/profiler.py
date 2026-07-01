from __future__ import annotations

import json
from pathlib import Path

from .domains import (
    AI_ACTIVE_KEYWORDS,
    AI_ADJACENT_KEYWORDS,
    APPLICATION_TAG_KEYWORDS,
    DOMAIN_BY_ID,
    HUMAIN_DOMAINS,
    METHODOLOGICAL_TAG_KEYWORDS,
    domain_raw_score,
    keyword_hits,
)
from .models import DomainScore, ResearchFocus, ResearcherProfile

FOCUS_MIN_SCORE = 0.18
FOCUS_MERGE_RATIO = 0.72
MAX_FOCI = 3


def build_signal_text(payload: dict) -> str:
    parts: list[str] = []
    for field in ("title", "bio", "affiliation"):
        value = payload.get(field)
        if isinstance(value, str) and value.strip():
            parts.append(value)
    interests = payload.get("research_interests") or []
    if isinstance(interests, list):
        parts.extend(str(item) for item in interests if item)
    return " ".join(parts).lower()


def _count_hits(text: str, keywords: tuple[str, ...]) -> int:
    return keyword_hits(text, keywords)


def score_domains(text: str) -> list[DomainScore]:
    if not text.strip():
        return [DomainScore(domain.id, domain.name, 0.0) for domain in HUMAIN_DOMAINS]

    raw_scores = [domain_raw_score(text, domain) for domain in HUMAIN_DOMAINS]
    max_score = max(raw_scores) or 1.0
    return [
        DomainScore(domain.id, domain.name, round(raw / max_score, 4))
        for domain, raw in zip(HUMAIN_DOMAINS, raw_scores)
    ]


def extract_tags(text: str, mapping: dict[str, tuple[str, ...]]) -> list[str]:
    return sorted(tag for tag, keywords in mapping.items() if any(keyword in text for keyword in keywords))


def classify_ai_readiness(text: str, domain_scores: list[DomainScore]) -> str:
    if _count_hits(text, AI_ACTIVE_KEYWORDS) >= 2:
        return "ai_active"
    if _count_hits(text, AI_ACTIVE_KEYWORDS) == 1 or _count_hits(text, AI_ADJACENT_KEYWORDS) >= 2:
        return "ai_adjacent"

    top_domain = max(domain_scores, key=lambda score: score.score, default=None)
    if top_domain and top_domain.domain_id in {"ai_foundations", "data_systems", "human_ai"}:
        return "ai_adjacent"

    science_or_health = sum(
        score.score for score in domain_scores if score.domain_id in {"ai_science", "ai_health_society"}
    )
    if science_or_health >= 0.35:
        return "ai_opportunity"
    return "non_ai"


def _focus_keywords(text: str, domain_id: str) -> list[str]:
    domain = DOMAIN_BY_ID[domain_id]
    matched = [keyword for keyword in domain.core_keywords if keyword in text]
    if not matched:
        matched = [keyword for keyword in domain.secondary_keywords if keyword in text]
    return matched[:5]


def _focus_label(domain_id: str, keywords: list[str]) -> str:
    domain_name = DOMAIN_BY_ID[domain_id].name
    if not keywords:
        return domain_name
    return f"{domain_name}: {', '.join(keywords[:2])}"


def detect_research_foci(text: str, domain_scores: list[DomainScore]) -> list[ResearchFocus]:
    ranked = sorted(domain_scores, key=lambda item: item.score, reverse=True)
    candidates = [score for score in ranked if score.score >= FOCUS_MIN_SCORE]
    if not candidates:
        top = ranked[0]
        candidates = [top] if top.score > 0 else []

    foci: list[ResearchFocus] = []
    used_domains: set[str] = set()

    for index, candidate in enumerate(candidates):
        if candidate.domain_id in used_domains:
            continue
        supporting = [
            other.domain_id
            for other in candidates[index + 1 :]
            if other.domain_id not in used_domains and other.score >= candidate.score * FOCUS_MERGE_RATIO
        ]
        for domain_id in supporting:
            used_domains.add(domain_id)

        keywords = _focus_keywords(text, candidate.domain_id)
        foci.append(
            ResearchFocus(
                focus_id=f"focus_{len(foci) + 1}",
                label=_focus_label(candidate.domain_id, keywords),
                primary_domain_id=candidate.domain_id,
                primary_domain_name=candidate.domain_name,
                strength=round(candidate.score, 4),
                supporting_domains=supporting,
                keywords=keywords,
            )
        )
        used_domains.add(candidate.domain_id)
        if len(foci) >= MAX_FOCI:
            break

    return foci


def profile_from_payload(
    *,
    person_id: str,
    school_key: str,
    folder_name: str,
    payload: dict,
) -> ResearcherProfile:
    text = build_signal_text(payload)
    domain_scores = score_domains(text)
    return ResearcherProfile(
        person_id=person_id,
        full_name=(payload.get("full_name") or folder_name).strip(),
        school_key=school_key,
        orcid=payload.get("orcid"),
        title=payload.get("title"),
        profile_url=payload.get("profile_url"),
        domain_scores=domain_scores,
        research_foci=detect_research_foci(text, domain_scores),
        ai_readiness=classify_ai_readiness(text, domain_scores),
        methodological_tags=extract_tags(text, METHODOLOGICAL_TAG_KEYWORDS),
        application_tags=extract_tags(text, APPLICATION_TAG_KEYWORDS),
        collaboration_intent_tags=list(payload.get("collaboration_intent_tags") or []),
        signal_text_excerpt=text[:240] if text else None,
    )


def iter_scraped_profiles(raw_dir: Path):
    for school_dir in sorted(raw_dir.iterdir()):
        if not school_dir.is_dir() or school_dir.name.startswith("_"):
            continue
        for person_dir in sorted(school_dir.iterdir()):
            if not person_dir.is_dir():
                continue
            profile_path = person_dir / "profile.jsonl"
            if not profile_path.exists():
                continue
            try:
                payload = json.loads(profile_path.read_text(encoding="utf-8").splitlines()[0])
            except (json.JSONDecodeError, IndexError):
                continue
            person_id = f"{school_dir.name}/{person_dir.name}"
            yield person_id, school_dir.name, person_dir.name, payload
