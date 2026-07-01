#!/usr/bin/env python3
"""Build HUMA.I.N S-Link researcher profiles and recommendations."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from slink.matcher import enrich_with_recommendations
from slink.profiler import iter_scraped_profiles, profile_from_payload

DEFAULT_RAW_DIR = ROOT / "data" / "raw"
DEFAULT_OUTPUT = ROOT / "website" / "data" / "slink_profiles.json"
DEFAULT_STATS = ROOT / "website" / "data" / "slink_stats.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--stats", type=Path, default=DEFAULT_STATS)
    args = parser.parse_args()

    if not args.raw_dir.is_dir():
        raise SystemExit(f"Raw data directory not found: {args.raw_dir}")

    profiles = [
        profile_from_payload(
            person_id=person_id,
            school_key=school_key,
            folder_name=folder_name,
            payload=payload,
        )
        for person_id, school_key, folder_name, payload in iter_scraped_profiles(args.raw_dir)
    ]
    enrich_with_recommendations(profiles)

    stats = Counter()
    stats["profiles"] = len(profiles)
    for profile in profiles:
        stats[f"foci_{len(profile.research_foci)}"] += 1
        stats[f"recs_{len(profile.slink_recommendations)}"] += 1
        stats[f"ai_{profile.ai_readiness}"] += 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps([profile.to_dict() for profile in profiles], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    args.stats.write_text(json.dumps(dict(stats), indent=2) + "\n", encoding="utf-8")

    print(f"Profiles built: {stats['profiles']:,}")
    print(f"1 focus:  {stats.get('foci_1', 0):,}")
    print(f"2 foci:   {stats.get('foci_2', 0):,}")
    print(f"3 foci:   {stats.get('foci_3', 0):,}")
    print(f"0 recs:   {stats.get('recs_0', 0):,}")
    print(f"1 rec:    {stats.get('recs_1', 0):,}")
    print(f"2 recs:   {stats.get('recs_2', 0):,}")
    print(f"3 recs:   {stats.get('recs_3', 0):,}")
    print(f"Output:   {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
