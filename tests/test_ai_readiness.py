from __future__ import annotations

import unittest

from slink.ai_readiness import (
    AI_ADJACENT,
    AI_BRIDGE,
    AI_NATIVE,
    DISCOVERY_CANDIDATE,
    classify_ai_readiness_detailed,
)
from slink.profiler import build_signal_text, score_domains


class AIReadinessTests(unittest.TestCase):
    def test_ai_native_for_methods_researcher(self) -> None:
        text = build_signal_text(
            {
                "title": "Professor of machine learning",
                "bio": "Develops foundation models, causal machine learning, and model evaluation.",
                "research_interests": ["representation learning"],
            }
        )
        result = classify_ai_readiness_detailed(text, score_domains(text))
        self.assertEqual(result.tag, AI_NATIVE)

    def test_ai_adjacent_for_data_science_profile(self) -> None:
        text = build_signal_text(
            {
                "title": "Biostatistician",
                "bio": "Uses statistical modeling, data visualization, and research computing.",
                "research_interests": ["informatics"],
            }
        )
        result = classify_ai_readiness_detailed(text, score_domains(text))
        self.assertEqual(result.tag, AI_ADJACENT)

    def test_ai_bridge_for_domain_expert(self) -> None:
        text = build_signal_text(
            {
                "title": "Professor of public health",
                "bio": "Community engagement, health equity, qualitative research, and implementation science.",
                "research_interests": ["patient care", "youth development"],
            }
        )
        result = classify_ai_readiness_detailed(text, score_domains(text))
        self.assertEqual(result.tag, AI_BRIDGE)

    def test_discovery_candidate_for_low_signal_profile(self) -> None:
        text = build_signal_text(
            {
                "title": "Program director",
                "bio": "Leads institutional practice and community-based work.",
                "research_interests": [],
            }
        )
        result = classify_ai_readiness_detailed(text, score_domains(text))
        self.assertIn(result.tag, {AI_BRIDGE, DISCOVERY_CANDIDATE})


if __name__ == "__main__":
    unittest.main()
