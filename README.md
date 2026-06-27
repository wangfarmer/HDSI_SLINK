# HDSI_SLINK

Research workspace for HUMA.I.N S-Link data collection and grouping experiments.

## Current focus

Requirement 2 is implemented as a configurable Harvard people/researcher scraper scaffold:

- Built-in configs for several Harvard school people/faculty directories.
- Profile URL discovery from school directory pages.
- Profile extraction for name, title, role category, affiliation, email, image, bio, and research interests.
- JSONL/CSV output, or one folder per person with `profile.jsonl` and a downloaded profile picture.
- Output suitable for later ORCID merge and S-Link grouping experiments.

See `docs/harvard_faculty_scraper.md` for usage.

## ORCID name merge + website

Match scraped person folders to `harvard_orcid_unique_names.csv` (exact, missing-middle-name, and fuzzy spelling matches), update local `profile.jsonl` files, and build a static people directory:

```bash
python3 scripts/merge_orcid_to_profiles.py
python3 -m http.server 8080 --directory website
```

Open `http://localhost:8080` to browse matched ORCID links. Generated data lives in `website/data/people.json`.
