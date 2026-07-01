from __future__ import annotations

from .models import ResearchFocus, ResearcherProfile, SLinkPartner, SLinkRecommendation

MAX_PARTNERS = 6
MAX_RECOMMENDATIONS = 3
MIN_FOCUS_STRENGTH = 0.18
MIN_PARTNER_SCORE = 0.28

COMPLEMENTARY_DOMAINS: dict[str, tuple[str, ...]] = {
    "ai_foundations": ("ai_health_society", "ai_science", "human_ai", "data_systems"),
    "data_systems": ("ai_foundations", "ai_science", "ai_health_society"),
    "human_ai": ("ai_foundations", "ai_health_society", "responsible_ai"),
    "ai_science": ("ai_foundations", "data_systems", "ai_health_society"),
    "ai_health_society": ("ai_foundations", "responsible_ai", "human_ai", "data_systems"),
    "responsible_ai": ("ai_health_society", "human_ai", "ai_foundations"),
    "ai_entrepreneurship": ("ai_foundations", "ai_health_society", "data_systems"),
}

AI_MIX_BONUS = {
    ("ai_native", "ai_bridge"): 0.14,
    ("ai_native", "discovery_candidate"): 0.12,
    ("ai_adjacent", "ai_bridge"): 0.10,
    ("ai_native", "ai_adjacent"): 0.06,
    ("ai_adjacent", "discovery_candidate"): 0.08,
}


def _domain_score_map(profile: ResearcherProfile) -> dict[str, float]:
    return {score.domain_id: score.score for score in profile.domain_scores}


def _shared_application_tags(left: ResearcherProfile, right: ResearcherProfile) -> list[str]:
    return sorted(set(left.application_tags) & set(right.application_tags))


def _complementarity_score(focus: ResearchFocus, candidate: ResearcherProfile) -> float:
    domain_map = _domain_score_map(candidate)
    related = COMPLEMENTARY_DOMAINS.get(focus.primary_domain_id, ())
    if not related:
        return 0.0
    return max(domain_map.get(domain_id, 0.0) for domain_id in related)


def _ai_mix_bonus(left: ResearcherProfile, right: ResearcherProfile) -> float:
    pair = tuple(sorted((left.ai_readiness, right.ai_readiness)))
    return AI_MIX_BONUS.get(pair, 0.0)


def score_partner(subject: ResearcherProfile, focus: ResearchFocus, candidate: ResearcherProfile) -> tuple[float, str]:
    if subject.person_id == candidate.person_id:
        return 0.0, ""

    domain_map = _domain_score_map(candidate)
    domain_fit = domain_map.get(focus.primary_domain_id, 0.0)
    for supporting in focus.supporting_domains:
        domain_fit = max(domain_fit, domain_map.get(supporting, 0.0) * 0.85)

    complementarity = _complementarity_score(focus, candidate)
    cross_school = 0.08 if subject.school_key != candidate.school_key else 0.0
    shared_apps = _shared_application_tags(subject, candidate)
    application_bonus = min(0.12, 0.04 * len(shared_apps))
    ai_bonus = _ai_mix_bonus(subject, candidate)

    total = (
        domain_fit * 0.42
        + complementarity * 0.28
        + cross_school
        + application_bonus
        + ai_bonus
    )

    rationale_parts: list[str] = []
    if domain_fit >= 0.25:
        rationale_parts.append(f"strong overlap in {focus.primary_domain_name}")
    if complementarity >= 0.25:
        rationale_parts.append("complementary domain expertise")
    if cross_school:
        rationale_parts.append("cross-school bridge")
    if shared_apps:
        rationale_parts.append(f"shared application focus ({', '.join(shared_apps)})")
    if ai_bonus:
        rationale_parts.append("mixed AI-readiness collaboration potential")
    if not rationale_parts:
        rationale_parts.append("related research signals")

    return round(total, 4), "; ".join(rationale_parts)


def build_recommendations(
    subject: ResearcherProfile,
    candidates: list[ResearcherProfile],
) -> list[SLinkRecommendation]:
    recommendations: list[SLinkRecommendation] = []

    for focus in subject.research_foci:
        if focus.strength < MIN_FOCUS_STRENGTH:
            continue

        scored_partners: list[SLinkPartner] = []
        for candidate in candidates:
            score, rationale = score_partner(subject, focus, candidate)
            if score < MIN_PARTNER_SCORE:
                continue
            scored_partners.append(
                SLinkPartner(
                    person_id=candidate.person_id,
                    full_name=candidate.full_name,
                    school_key=candidate.school_key,
                    score=score,
                    rationale=rationale,
                )
            )

        scored_partners.sort(key=lambda partner: partner.score, reverse=True)
        partners = scored_partners[:MAX_PARTNERS]
        if not partners:
            continue

        recommendations.append(
            SLinkRecommendation(
                focus_id=focus.focus_id,
                title=focus.label,
                primary_domain_id=focus.primary_domain_id,
                primary_domain_name=focus.primary_domain_name,
                rationale=(
                    f"Distinct collaboration track anchored in {focus.primary_domain_name}. "
                    "Suggested mix balances domain overlap, complementarity, and cross-school bridges."
                ),
                suggested_partners=partners,
            )
        )
        if len(recommendations) >= MAX_RECOMMENDATIONS:
            break

    return recommendations


def enrich_with_recommendations(profiles: list[ResearcherProfile]) -> None:
    for profile in profiles:
        profile.slink_recommendations = build_recommendations(profile, profiles)
