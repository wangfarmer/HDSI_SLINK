#!/usr/bin/env python3
"""Classify AI-readiness tags for scraped researcher profiles."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from slink.ai_readiness import AI_READINESS_LABELS, classify_ai_readiness_detailed
from slink.profiler import (
    build_signal_text,
    iter_scraped_profiles,
    score_domains,
)

DEFAULT_RAW_DIR = ROOT / "data" / "raw"
DEFAULT_STATS = ROOT / "website" / "data" / "ai_readiness_stats.json"


def classify_profiles(
    raw_dir: Path,
    *,
    write_profiles: bool,
) -> tuple[list[dict], dict[str, int]]:
    rows: list[dict] = []
    stats: Counter[str] = Counter()

    for person_id, school_key, folder_name, payload in iter_scraped_profiles(raw_dir):
        stats["profiles_seen"] += 1
        text = build_signal_text(payload)
        domain_scores = score_domains(text)
        readiness = classify_ai_readiness_detailed(text, domain_scores)
        previous = payload.get("ai_readiness")

        payload["ai_readiness"] = readiness.tag
        payload["ai_readiness_label"] = readiness.label
        payload["ai_readiness_rationale"] = readiness.rationale
        stats[f"tag_{readiness.tag}"] += 1
        if previous and previous != readiness.tag:
            stats["changed"] += 1
        elif previous == readiness.tag:
            stats["unchanged"] += 1
        else:
            stats["new"] += 1

        if write_profiles:
            profile_path = raw_dir / school_key / folder_name / "profile.jsonl"
            profile_path.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")

        rows.append(
            {
                "person_id": person_id,
                "school_key": school_key,
                "full_name": payload.get("full_name") or folder_name,
                "ai_readiness": readiness.tag,
                "ai_readiness_label": readiness.label,
                "previous_ai_readiness": previous,
            }
        )

    return rows, dict(stats)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--stats", type=Path, default=DEFAULT_STATS)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not rewrite profile.jsonl files; only compute stats.",
    )
    args = parser.parse_args()

    if not args.raw_dir.is_dir():
        raise SystemExit(f"Raw data directory not found: {args.raw_dir}")

    rows, stats = classify_profiles(args.raw_dir, write_profiles=not args.dry_run)
    args.stats.parent.mkdir(parents=True, exist_ok=True)
    args.stats.write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")

    print(f"Profiles scanned: {stats.get('profiles_seen', 0):,}")
    for tag in AI_READINESS_LABELS:
        count = stats.get(f"tag_{tag}", 0)
        if count:
            print(f"  {tag:16s} {count:,}")
    if stats.get("changed"):
        print(f"Changed:          {stats['changed']:,}")
    if stats.get("new"):
        print(f"Newly tagged:     {stats['new']:,}")
    print(f"Stats:            {args.stats}")
    if args.dry_run:
        print("Dry run: profile.jsonl files were not modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
