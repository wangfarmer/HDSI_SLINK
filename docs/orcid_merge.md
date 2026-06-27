# ORCID name merge

`harvard_orcid_unique_names.csv` provides one row per Harvard ORCID with:

- `ORCID`
- `full_name`
- `given_name`
- `family_name`
- `credit_name`

## Merge scraped profiles

```bash
python3 scripts/merge_orcid_to_profiles.py
```

This script:

1. Scans `data/raw/*/*/profile.jsonl`
2. Matches each person to ORCID using:
   - exact `full_name` / `credit_name`
   - missing-middle-name matches (`Andrea L. Roberts` ↔ `Andrea Roberts`)
   - fuzzy spelling matches when first+last agree and score ≥ 0.86
3. Writes `orcid`, `orcid_match_method`, and `orcid_match_score` into each local `profile.jsonl`
4. Builds `website/data/people.json` and `website/data/stats.json`

Radcliffe-style names with `| Radcliffe Institute ...` suffixes are cleaned before matching.

Ambiguous names with multiple equally likely ORCID records are left unmatched on purpose.

## Browse the website locally

```bash
python3 -m http.server 8080 --directory website
```

Open `http://localhost:8080`.
