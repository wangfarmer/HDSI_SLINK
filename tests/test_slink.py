from __future__ import annotations

import unittest

from slink.domains import HUMAIN_DOMAINS, domain_raw_score
from slink.matcher import build_recommendations, enrich_with_recommendations
from slink.profiler import build_signal_text, detect_research_foci, profile_from_payload, score_domains


class SLinkProfilerTests(unittest.TestCase):
    def test_methods_researcher_scores_higher_than_application_only(self) -> None:
        methods_text = build_signal_text(
            {
                "title": "Professor of machine learning",
                "bio": "Develops foundation models, causal machine learning, and model evaluation methods.",
                "research_interests": ["representation learning", "uncertainty quantification"],
            }
        )
        application_text = build_signal_text(
            {
                "title": "Clinical researcher",
                "bio": "Uses existing machine learning tools for patient screening in hospitals.",
                "research_interests": ["patient outcomes"],
            }
        )
        methods_score = domain_raw_score(methods_text, HUMAIN_DOMAINS[0])
        application_score = domain_raw_score(application_text, HUMAIN_DOMAINS[0])
        self.assertGreater(methods_score, application_score)
    def test_domain_scores_cover_all_seven_domains(self) -> None:
        text = build_signal_text(
            {
                "title": "Professor of machine learning and clinical decision support",
                "bio": "Works on health equity, implementation science, and responsible AI governance.",
                "research_interests": ["public health", "ethics"],
            }
        )
        scores = score_domains(text)
        self.assertEqual(len(scores), len(HUMAIN_DOMAINS))
        top_ids = {score.domain_id for score in scores if score.score > 0}
        self.assertIn("ai_foundations", top_ids)
        self.assertIn("ai_health_society", top_ids)
        self.assertIn("responsible_ai", top_ids)

    def test_detects_multiple_distinct_foci(self) -> None:
        text = build_signal_text(
            {
                "title": "Machine learning for clinical decision support",
                "bio": "Also studies health equity, implementation science, and AI governance policy.",
                "research_interests": ["public health", "ethics", "fairness"],
            }
        )
        scores = score_domains(text)
        foci = detect_research_foci(text, scores)
        self.assertGreaterEqual(len(foci), 2)
        self.assertLessEqual(len(foci), 3)

    def test_single_focus_profile_gets_one_recommendation_track(self) -> None:
        profile = profile_from_payload(
            person_id="school/person",
            school_key="school",
            folder_name="Person",
            payload={
                "full_name": "Entrepreneurship Scholar",
                "title": "Professor of entrepreneurship and startup commercialization",
                "bio": "Focuses on venture creation and technology translation.",
                "research_interests": [],
            },
        )
        partner = profile_from_payload(
            person_id="school/other",
            school_key="other_school",
            folder_name="Other",
            payload={
                "full_name": "ML Health Researcher",
                "title": "Machine learning for healthcare",
                "bio": "Clinical AI and public health.",
                "research_interests": [],
            },
        )
        recs = build_recommendations(profile, [profile, partner])
        self.assertLessEqual(len(recs), 3)
        self.assertGreaterEqual(len(profile.research_foci), 1)

    def test_recommendations_never_exceed_three(self) -> None:
        profiles = [
            profile_from_payload(
                person_id=f"school/p{i}",
                school_key="school",
                folder_name=f"P{i}",
                payload={
                    "full_name": f"Researcher {i}",
                    "title": "machine learning healthcare ethics entrepreneurship genomics",
                    "bio": "public health policy governance implementation science startup",
                    "research_interests": ["clinical", "fairness", "data pipeline"],
                },
            )
            for i in range(5)
        ]
        enrich_with_recommendations(profiles)
        for profile in profiles:
            self.assertLessEqual(len(profile.slink_recommendations), 3)


if __name__ == "__main__":
    unittest.main()
