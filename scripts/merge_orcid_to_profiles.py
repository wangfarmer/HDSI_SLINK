#!/usr/bin/env python3
"""Match scraped person folders to ORCID IDs and build website data."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harvard_faculty_scraper.orcid_match import (
    OrcidNameIndex,
    load_orcid_people,
    normalize_name_key,
    strip_folder_artifacts,
)
from harvard_faculty_scraper.utils import clean_text
DEFAULT_ORCID_CSV = ROOT / "harvard_orcid_unique_names.csv"
DEFAULT_RAW_DIR = ROOT / "data" / "raw"
DEFAULT_WEBSITE_DATA = ROOT / "website" / "data" / "people.json"
DEFAULT_STATS = ROOT / "website" / "data" / "stats.json"


def iter_profiles(raw_dir: Path):
    for school_dir in sorted(raw_dir.iterdir()):
        if not school_dir.is_dir() or school_dir.name.startswith("_"):
            continue
        for person_dir in sorted(school_dir.iterdir()):
            if not person_dir.is_dir():
                continue
            profile_path = person_dir / "profile.jsonl"
            if not profile_path.exists():
                continue
            try:
                payload = json.loads(profile_path.read_text(encoding="utf-8").splitlines()[0])
            except (json.JSONDecodeError, IndexError):
                continue
            yield school_dir.name, person_dir.name, profile_path, payload


def profile_query_names(folder_name: str, payload: dict) -> list[str]:
    candidates = [
        payload.get("full_name") or "",
        strip_folder_artifacts(folder_name),
    ]
    deduped: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        cleaned = strip_folder_artifacts(clean_text(candidate) or "")
        key = normalize_name_key(cleaned)
        if cleaned and key not in seen:
            seen.add(key)
            deduped.append(cleaned)
    return deduped


def merge_profiles(
    raw_dir: Path,
    index: OrcidNameIndex,
    *,
    write_profiles: bool,
    fuzzy_threshold: float,
) -> tuple[list[dict], dict[str, int]]:
    people: list[dict] = []
    stats: Counter[str] = Counter()

    for school_key, folder_name, profile_path, payload in iter_profiles(raw_dir):
        stats["profiles_seen"] += 1
        match = None
        query_name = ""
        for candidate_name in profile_query_names(folder_name, payload):
            query_name = candidate_name
            match = index.match(candidate_name, fuzzy_threshold=fuzzy_threshold)
            if match:
                break

        if match:
            stats["matched"] += 1
            stats[f"method_{match.method}"] += 1
            payload["orcid"] = match.orcid
            payload["orcid_match_method"] = match.method
            payload["orcid_match_score"] = match.score
            payload["orcid_matched_name"] = match.matched_name
            if write_profiles:
                profile_path.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
        else:
            stats["unmatched"] += 1
            payload.pop("orcid", None)
            payload.pop("orcid_match_method", None)
            payload.pop("orcid_match_score", None)
            payload.pop("orcid_matched_name", None)

        people.append(
            {
                "school_key": school_key,
                "folder_name": folder_name,
                "full_name": payload.get("full_name") or query_name,
                "title": payload.get("title"),
                "email": payload.get("email"),
                "profile_url": payload.get("profile_url"),
                "orcid": payload.get("orcid"),
                "orcid_match_method": payload.get("orcid_match_method"),
                "orcid_match_score": payload.get("orcid_match_score"),
                "orcid_matched_name": payload.get("orcid_matched_name"),
            }
        )

    return people, dict(stats)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--orcid-csv", type=Path, default=DEFAULT_ORCID_CSV)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--website-data", type=Path, default=DEFAULT_WEBSITE_DATA)
    parser.add_argument("--stats", type=Path, default=DEFAULT_STATS)
    parser.add_argument("--fuzzy-threshold", type=float, default=0.86)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not rewrite profile.jsonl files; only build website JSON.",
    )
    args = parser.parse_args()

    if not args.orcid_csv.exists():
        raise SystemExit(f"ORCID CSV not found: {args.orcid_csv}")
    if not args.raw_dir.is_dir():
        raise SystemExit(f"Raw data directory not found: {args.raw_dir}")

    index = OrcidNameIndex(load_orcid_people(args.orcid_csv))
    people, stats = merge_profiles(
        args.raw_dir,
        index,
        write_profiles=not args.dry_run,
        fuzzy_threshold=args.fuzzy_threshold,
    )
    people.sort(key=lambda row: ((row.get("full_name") or "").lower(), row["school_key"]))

    stats["orcid_records"] = len(index.people)
    stats["match_rate_pct"] = round(
        100.0 * stats.get("matched", 0) / max(stats.get("profiles_seen", 1), 1),
        2,
    )

    write_json(args.website_data, people)
    write_json(args.stats, stats)

    print(f"ORCID records loaded: {stats['orcid_records']:,}")
    print(f"Profiles scanned:     {stats['profiles_seen']:,}")
    print(f"Matched:              {stats.get('matched', 0):,} ({stats['match_rate_pct']}%)")
    print(f"Unmatched:            {stats.get('unmatched', 0):,}")
    for method in ("exact", "core_name", "fuzzy"):
        key = f"method_{method}"
        if stats.get(key):
            print(f"  {method:10s} {stats[key]:,}")
    print(f"Website data:         {args.website_data}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
