from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DomainDefinition:
    id: str
    name: str
    keywords: tuple[str, ...]


HUMAIN_DOMAINS: tuple[DomainDefinition, ...] = (
    DomainDefinition(
        "ai_foundations",
        "AI Foundations & Core Methods",
        (
            "machine learning",
            "deep learning",
            "neural network",
            "artificial intelligence",
            "nlp",
            "natural language processing",
            "computer vision",
            "reinforcement learning",
            "foundation model",
            "large language model",
            "llm",
            "algorithm",
            "optimization",
            "inference",
            "generative model",
            "transformer",
        ),
    ),
    DomainDefinition(
        "data_systems",
        "Data Systems & Infrastructure",
        (
            "data system",
            "database",
            "distributed system",
            "cloud computing",
            "data pipeline",
            "high performance computing",
            "hpc",
            "software engineering",
            "scalability",
            "data warehouse",
            "etl",
            "infrastructure",
            "data engineering",
            "storage system",
            "streaming data",
        ),
    ),
    DomainDefinition(
        "human_ai",
        "Human-AI Interaction & Cognition",
        (
            "human-computer interaction",
            "human computer interaction",
            "hci",
            "usability",
            "cognitive",
            "user experience",
            "explainability",
            "interpretability",
            "human-ai",
            "human ai",
            "interaction design",
            "behavioral science",
            "decision support",
            "trust in ai",
            "augmented cognition",
        ),
    ),
    DomainDefinition(
        "ai_science",
        "AI for Scientific Discovery",
        (
            "computational biology",
            "drug discovery",
            "materials science",
            "scientific discovery",
            "genomics",
            "proteomics",
            "bioinformatics",
            "astronomy",
            "physics simulation",
            "scientific computing",
            "molecular",
            "structural biology",
            "systems biology",
            "chemistry",
            "climate modeling",
        ),
    ),
    DomainDefinition(
        "ai_health_society",
        "AI for Health & Society",
        (
            "clinical",
            "health care",
            "healthcare",
            "public health",
            "epidemiology",
            "medicine",
            "patient",
            "hospital",
            "mental health",
            "global health",
            "health equity",
            "implementation science",
            "biomedical",
            "medical",
            "population health",
            "community health",
        ),
    ),
    DomainDefinition(
        "responsible_ai",
        "Responsible, Ethical & Policy AI",
        (
            "ethics",
            "fairness",
            "bias",
            "governance",
            "regulation",
            "policy",
            "privacy",
            "accountability",
            "transparency",
            "justice",
            "equity",
            "responsible ai",
            "algorithmic accountability",
            "human rights",
            "ai safety",
            "social impact",
        ),
    ),
    DomainDefinition(
        "ai_entrepreneurship",
        "AI Entrepreneurship & Translation",
        (
            "entrepreneurship",
            "commercialization",
            "startup",
            "venture",
            "innovation",
            "translation",
            "industry partnership",
            "product development",
            "business model",
            "go-to-market",
            "technology transfer",
            "spinout",
            "incubator",
        ),
    ),
)

DOMAIN_BY_ID = {domain.id: domain for domain in HUMAIN_DOMAINS}

METHODOLOGICAL_TAG_KEYWORDS: dict[str, tuple[str, ...]] = {
    "machine_learning": ("machine learning", "ml", "deep learning"),
    "nlp": ("natural language processing", "nlp", "text mining"),
    "computer_vision": ("computer vision", "image analysis", "imaging"),
    "statistics": ("statistics", "statistical", "biostatistics"),
    "simulation": ("simulation", "modeling", "computational model"),
    "qualitative_methods": ("qualitative", "ethnograph", "interview study"),
    "experimental": ("randomized", "clinical trial", "experiment"),
    "systems_building": ("software", "platform", "system design", "engineering"),
}

APPLICATION_TAG_KEYWORDS: dict[str, tuple[str, ...]] = {
    "healthcare": ("health", "clinical", "medical", "patient"),
    "education": ("education", "learning", "pedagogy", "student"),
    "climate": ("climate", "environment", "sustainability"),
    "finance": ("finance", "financial", "banking", "investment"),
    "law_policy": ("law", "legal", "policy", "regulation"),
    "governance": ("governance", "public sector", "civic"),
}

AI_ACTIVE_KEYWORDS = (
    "machine learning",
    "deep learning",
    "artificial intelligence",
    "neural network",
    "nlp",
    "computer vision",
    "large language model",
    "llm",
    "generative ai",
    "reinforcement learning",
)

AI_ADJACENT_KEYWORDS = (
    "data science",
    "computational",
    "informatics",
    "bioinformatics",
    "statistics",
    "statistical",
    "algorithm",
    "modeling",
    "simulation",
    "digital health",
)
