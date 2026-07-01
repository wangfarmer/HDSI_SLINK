# ORCID CSV grouping utility

Use `scripts/group_orcid_csv.py` to inspect `.csv` or `.csv.gz` ORCID exports.

The uploaded file currently has raw columns:

- `item`
- `content`
- `ORCID`

The script parses key/value fields inside `content`, such as:

- `role`
- `department`
- `organization`
- `institution`
- `title`
- `type`
- `journal`
- `doi`

It also derives `harvard_school` from organization/institution/department text.

## Show available fields

```bat
python scripts\group_orcid_csv.py harvard_orcid_complete_20251020_current_harvard_detail.csv.gz --show-columns
```

## Group by ORCID item type

```bat
python scripts\group_orcid_csv.py harvard_orcid_complete_20251020_current_harvard_detail.csv.gz --group-by item --top 20
```

## Group Harvard employment rows by normalized school

```bat
python scripts\group_orcid_csv.py harvard_orcid_complete_20251020_current_harvard_detail.csv.gz --harvard-only --field-contains item=Employment --group-by harvard_school --top 50
```

## Group Harvard employment rows by raw organization

```bat
python scripts\group_orcid_csv.py harvard_orcid_complete_20251020_current_harvard_detail.csv.gz --harvard-only --field-contains item=Employment --group-by organization --top 100
```

## Group by department within school

```bat
python scripts\group_orcid_csv.py harvard_orcid_complete_20251020_current_harvard_detail.csv.gz --harvard-only --field-contains item=Employment --group-by harvard_school,department --top 100
```

## Write a summary CSV

```bat
python scripts\group_orcid_csv.py harvard_orcid_complete_20251020_current_harvard_detail.csv.gz --harvard-only --field-contains item=Employment --group-by harvard_school --top 0 --output data\processed\orcid_harvard_school_counts.csv
```

Each summary reports:

- `rows`: number of CSV rows in that group
- `unique_orcids`: number of distinct ORCID IDs in that group
