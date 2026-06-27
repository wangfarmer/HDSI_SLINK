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
