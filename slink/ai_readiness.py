from __future__ import annotations

from dataclasses import dataclass

from .domains import keyword_hits
from .models import DomainScore


AI_NATIVE = "ai_native"
AI_ADJACENT = "ai_adjacent"
AI_BRIDGE = "ai_bridge"
DISCOVERY_CANDIDATE = "discovery_candidate"

AI_READINESS_LABELS = {
    AI_NATIVE: "AI-Native",
    AI_ADJACENT: "AI-Adjacent",
    AI_BRIDGE: "AI-Bridge / Domain Expert",
    DISCOVERY_CANDIDATE: "Non-AI / Discovery Candidate",
}

AI_NATIVE_KEYWORDS: tuple[str, ...] = (
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "neural networks",
    "neural network",
    "foundation models",
    "foundation model",
    "large language models",
    "large language model",
    "generative ai",
    "reinforcement learning",
    "computer vision",
    "natural language processing",
    "predictive modeling",
    "algorithmic decision-making",
    "algorithmic decision making",
    "representation learning",
    "multimodal ai",
    "multimodal learning",
    "bayesian machine learning",
    "bayesian learning",
    "causal machine learning",
    "ai agents",
    "agentic ai",
    "model evaluation",
    "model interpretability",
    "ai alignment",
)

AI_ADJACENT_KEYWORDS: tuple[str, ...] = (
    "computational methods",
    "statistical modeling",
    "data science",
    "data systems",
    "informatics",
    "simulation",
    "digital platforms",
    "quantitative methods",
    "network analysis",
    "geospatial analysis",
    "systems modeling",
    "behavioral measurement",
    "digital health",
    "computational social science",
    "bioinformatics",
    "data visualization",
    "research computing",
    "computational science",
    "computational biology",
    "scientific machine learning",
    "data engineering",
    "statistical",
    "statistics",
    "modeling",
    "computational",
)

AI_BRIDGE_KEYWORDS: tuple[str, ...] = (
    "clinical practice",
    "education",
    "public health",
    "policy",
    "humanities",
    "ethics",
    "law",
    "community engagement",
    "qualitative research",
    "fieldwork",
    "implementation science",
    "patient care",
    "youth development",
    "equity",
    "social behavior",
    "environment",
    "urban planning",
    "organizational practice",
    "community-based",
    "community health",
    "health equity",
    "social policy",
    "criminal justice",
    "primary care",
    "archival research",
    "program leadership",
    "institutional practice",
)

DISCOVERY_KEYWORDS: tuple[str, ...] = (
    "topic expertise",
    "traditional disciplinary",
    "descriptive field research",
    "archival research",
    "clinical expertise",
    "program leadership",
    "institutional practice",
    "community-based work",
    "field research",
    "historical research",
    "literary",
    "philosophy",
    "theology",
    "divinity",
)

BRIDGE_DOMAIN_IDS = frozenset({"ai_health_society", "responsible_ai", "human_ai", "ai_entrepreneurship"})
ADJACENT_DOMAIN_IDS = frozenset({"data_systems", "ai_science", "ai_foundations"})


@dataclass(frozen=True)
class AIReadinessResult:
    tag: str
    label: str
    native_hits: int
    adjacent_hits: int
    bridge_hits: int
    rationale: str


def _domain_strength(domain_scores: list[DomainScore], domain_ids: frozenset[str]) -> float:
    return max((score.score for score in domain_scores if score.domain_id in domain_ids), default=0.0)


def classify_ai_readiness(text: str, domain_scores: list[DomainScore]) -> str:
    return classify_ai_readiness_detailed(text, domain_scores).tag


def classify_ai_readiness_detailed(text: str, domain_scores: list[DomainScore]) -> AIReadinessResult:
    native_hits = keyword_hits(text, AI_NATIVE_KEYWORDS)
    adjacent_hits = keyword_hits(text, AI_ADJACENT_KEYWORDS)
    bridge_hits = keyword_hits(text, AI_BRIDGE_KEYWORDS)
    discovery_hits = keyword_hits(text, DISCOVERY_KEYWORDS)

    foundations_strength = _domain_strength(domain_scores, frozenset({"ai_foundations"}))
    adjacent_domain_strength = _domain_strength(domain_scores, ADJACENT_DOMAIN_IDS)
    bridge_domain_strength = _domain_strength(domain_scores, BRIDGE_DOMAIN_IDS)

    if native_hits >= 2 or (native_hits >= 1 and foundations_strength >= 0.45):
        return AIReadinessResult(
            AI_NATIVE,
            AI_READINESS_LABELS[AI_NATIVE],
            native_hits,
            adjacent_hits,
            bridge_hits,
            "Clear AI/ML development, use, evaluation, or study signals.",
        )

    if native_hits >= 1:
        return AIReadinessResult(
            AI_NATIVE,
            AI_READINESS_LABELS[AI_NATIVE],
            native_hits,
            adjacent_hits,
            bridge_hits,
            "At least one direct AI/ML method signal.",
        )

    if adjacent_hits >= 2 or (adjacent_hits >= 1 and adjacent_domain_strength >= 0.35):
        return AIReadinessResult(
            AI_ADJACENT,
            AI_READINESS_LABELS[AI_ADJACENT],
            native_hits,
            adjacent_hits,
            bridge_hits,
            "Data, computation, modeling, or analytics are central even if AI is not explicit.",
        )

    if adjacent_hits >= 1:
        return AIReadinessResult(
            AI_ADJACENT,
            AI_READINESS_LABELS[AI_ADJACENT],
            native_hits,
            adjacent_hits,
            bridge_hits,
            "Some data-intensive or computational research signals.",
        )

    if bridge_hits >= 2 or (bridge_hits >= 1 and bridge_domain_strength >= 0.35):
        return AIReadinessResult(
            AI_BRIDGE,
            AI_READINESS_LABELS[AI_BRIDGE],
            native_hits,
            adjacent_hits,
            bridge_hits,
            "Strong domain, population, or institutional expertise that could complement AI collaborators.",
        )

    if bridge_hits >= 1 or bridge_domain_strength >= 0.25:
        return AIReadinessResult(
            AI_BRIDGE,
            AI_READINESS_LABELS[AI_BRIDGE],
            native_hits,
            adjacent_hits,
            bridge_hits,
            "Domain expertise with potential to pair with AI-native or AI-adjacent partners.",
        )

    if discovery_hits >= 1 or not text.strip():
        return AIReadinessResult(
            DISCOVERY_CANDIDATE,
            AI_READINESS_LABELS[DISCOVERY_CANDIDATE],
            native_hits,
            adjacent_hits,
            bridge_hits,
            "No clear AI or data-intensive signal yet; may still be valuable for future AI collaboration.",
        )

    return AIReadinessResult(
        DISCOVERY_CANDIDATE,
        AI_READINESS_LABELS[DISCOVERY_CANDIDATE],
        native_hits,
        adjacent_hits,
        bridge_hits,
        "Limited automated signal; onboarding may reveal collaboration interest or domain relevance.",
    )
