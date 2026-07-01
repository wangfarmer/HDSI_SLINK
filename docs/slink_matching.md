# HUMA.I.N S-Link matching

This module implements the first version of the S-Link profiling and recommendation engine.

## Seven HUMA.I.N domains

1. AI Foundations & Core Methods
2. Data Systems & Infrastructure
3. Human-AI Interaction & Cognition
4. AI for Scientific Discovery
5. AI for Health & Society
6. Responsible, Ethical & Policy AI
7. AI Entrepreneurship & Translation

## Per-researcher outputs

Each profile includes:

- **Domain scores** across all seven domains
- **Research foci** (1–3 distinct tracks when warranted)
- **AI-readiness tag**: `ai_active`, `ai_adjacent`, `ai_opportunity`, or `non_ai`
- **Methodological tags**
- **Application/topic tags**
- **Collaboration-intent tags** (empty until onboarding is added)
- **Up to three S-Link recommendations**, one per distinct focus

The system does **not** force three S-Links. Researchers with one strong focus receive one recommendation.

## Build profiles

```bash
python3 scripts/build_slink_profiles.py
```

Outputs:

- `website/data/slink_profiles.json`
- `website/data/slink_stats.json`

## Browse in the website

```bash
python3 -m http.server 8080 --directory website
```

Open:

- `http://localhost:8080/slink.html` for domain scores, foci, and recommendations
- `http://localhost:8080/index.html` for the ORCID directory

## Matching logic (v1)

For each research focus:

1. Score candidate partners on domain overlap
2. Add complementarity from related domains
3. Reward cross-school bridges
4. Reward shared application tags
5. Reward mixed AI-readiness pairs (for example AI-active + AI-opportunity)

Recommendations are capped at three and only created for foci above the confidence threshold.

## Next steps

- Add onboarding collaboration-intent tags
- Enrich signals from ORCID detail CSV publications/abstracts
- Replace keyword rules with learned classifiers
- Add adaptive feedback loops after collaborations
