from __future__ import annotations

import argparse
import csv
import gzip
import re
from collections import Counter, defaultdict
from collections.abc import Iterable
from pathlib import Path


MISSING = "(missing)"
KNOWN_CONTENT_KEYS = {
    "date",
    "degree",
    "department",
    "doi",
    "email",
    "institution",
    "journal",
    "organization",
    "period",
    "pmid",
    "role",
    "title",
    "type",
}
DERIVED_FIELDS = ["harvard_school"]
HARVARD_SCHOOL_PATTERNS = [
    ("Harvard T.H. Chan School of Public Health", ["t.h. chan", "t h chan", "chan school", "school of public health", "hsph"]),
    ("Harvard Medical School", ["harvard medical school", "hms.harvard", " hms", "hms "]),
    ("Harvard Business School", ["harvard business school", "hbs.harvard", " hbs", "hbs "]),
    ("Harvard Law School", ["harvard law school", "hls.harvard", " hls", "hls "]),
    ("Harvard Kennedy School", ["harvard kennedy school", "john f kennedy school", "kennedy school", "hks.harvard"]),
    ("Harvard Graduate School of Design", ["graduate school of design", "gsd.harvard", " gsd", "gsd "]),
    ("Harvard Graduate School of Education", ["graduate school of education", "gse.harvard", "hgse"]),
    ("Harvard Divinity School", ["harvard divinity school", "hds.harvard", " hds", "hds "]),
    ("Harvard School of Dental Medicine", ["school of dental medicine", "hsdm"]),
    ("Harvard SEAS", ["paulson school", "engineering and applied sciences", "seas.harvard"]),
    ("Harvard Faculty of Arts and Sciences", ["faculty of arts and sciences", "harvard college", " fas", "fas "]),
    ("Harvard Radcliffe Institute", ["radcliffe"]),
    ("Harvard Wyss Institute", ["wyss institute"]),
]


def main() -> int:
    args = parse_args()
    group_fields = parse_group_fields(args.group_by)

    if args.show_columns:
        columns, parsed_fields = inspect_columns(args.input)
        print("Raw columns:")
        for column in columns:
            print(f"  {column}")
        print("Parsed content fields:")
        for field in parsed_fields:
            print(f"  {field}")
        return 0

    summary = summarize(
        args.input,
        group_fields=group_fields,
        harvard_only=args.harvard_only,
        contains=args.contains,
        field_contains=parse_field_contains(args.field_contains),
    )

    rows = sorted(
        summary.items(),
        key=lambda item: (item[1]["rows"], item[1]["unique_orcids"]),
        reverse=True,
    )
    if args.top > 0:
        rows = rows[: args.top]

    if args.output:
        write_summary_csv(args.output, group_fields, rows)
    else:
        print_summary(group_fields, rows)

    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Group a Harvard ORCID CSV/CSV.GZ by raw columns or parsed fields inside "
            "the content column."
        )
    )
    parser.add_argument("input", type=Path, help="Input .csv or .csv.gz file.")
    parser.add_argument(
        "--group-by",
        default="item",
        help=(
            "Comma-separated fields to group by. Supports raw columns like item/ORCID "
            "and parsed content fields like role, department, organization, institution, "
            "title, type, journal, doi, plus derived field harvard_school. Default: item."
        ),
    )
    parser.add_argument("--top", type=int, default=50, help="Show top N groups. Use 0 for all.")
    parser.add_argument(
        "--harvard-only",
        action="store_true",
        help="Only include rows where any raw or parsed value contains 'harvard'.",
    )
    parser.add_argument(
        "--contains",
        help="Only include rows where any raw or parsed value contains this text.",
    )
    parser.add_argument(
        "--field-contains",
        action="append",
        default=[],
        help="Filter as field=value. Can be repeated, e.g. --field-contains item=Employment.",
    )
    parser.add_argument("--output", type=Path, help="Optional output CSV path.")
    parser.add_argument(
        "--show-columns",
        action="store_true",
        help="Print raw columns and parsed content fields, then exit.",
    )
    return parser.parse_args()


def read_rows(path: Path) -> Iterable[dict[str, str]]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            yield normalize_row(row)


def normalize_row(row: dict[str, str | None]) -> dict[str, str]:
    normalized = {str(key): (value or "").strip() for key, value in row.items()}
    parsed = parse_content(normalized.get("content", ""))
    for key, value in parsed.items():
        normalized.setdefault(key, value)
    normalized["harvard_school"] = derive_harvard_school(normalized)
    return normalized


def parse_content(content: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for part in content.split(" | "):
        if ":" not in part:
            continue
        key, value = part.split(":", 1)
        normalized_key = slugify_field(key)
        if normalized_key not in KNOWN_CONTENT_KEYS:
            continue
        parsed[normalized_key] = value.strip()
    return parsed


def derive_harvard_school(row: dict[str, str]) -> str:
    text = " ".join(
        row.get(field, "")
        for field in ["organization", "institution", "department", "content"]
    ).lower()
    if "harvard" not in text and not any(marker in text for marker in [" hbs", " hks", " hls", " hds", " hms", " hgse", " gsd", "hsph"]):
        return MISSING
    for school, patterns in HARVARD_SCHOOL_PATTERNS:
        if any(pattern in text for pattern in patterns):
            return school
    if "harvard" in text:
        return "Harvard University / unspecified"
    return MISSING


def slugify_field(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def inspect_columns(path: Path) -> tuple[list[str], list[str]]:
    parsed_fields: Counter[str] = Counter()
    raw_columns: list[str] = []
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        raw_columns = list(reader.fieldnames or [])
        for index, row in enumerate(reader):
            parsed_fields.update(parse_content(row.get("content") or "").keys())
            if index >= 10_000:
                break
    return raw_columns, sorted(parsed_fields) + DERIVED_FIELDS


def summarize(
    path: Path,
    *,
    group_fields: list[str],
    harvard_only: bool,
    contains: str | None,
    field_contains: list[tuple[str, str]],
) -> dict[tuple[str, ...], dict[str, object]]:
    row_counts: Counter[tuple[str, ...]] = Counter()
    orcids_by_group: dict[tuple[str, ...], set[str]] = defaultdict(set)

    for row in read_rows(path):
        if harvard_only and not row_contains(row, "harvard"):
            continue
        if contains and not row_contains(row, contains):
            continue
        if field_contains and not all(field_value_contains(row, field, value) for field, value in field_contains):
            continue

        key = tuple(row.get(field, "").strip() or MISSING for field in group_fields)
        row_counts[key] += 1
        orcid = row.get("ORCID", "").strip()
        if orcid:
            orcids_by_group[key].add(orcid)

    return {
        key: {"rows": rows, "unique_orcids": len(orcids_by_group.get(key, set()))}
        for key, rows in row_counts.items()
    }


def row_contains(row: dict[str, str], needle: str) -> bool:
    needle_lower = needle.lower()
    return any(needle_lower in value.lower() for value in row.values())


def field_value_contains(row: dict[str, str], field: str, needle: str) -> bool:
    return needle.lower() in row.get(field, "").lower()


def parse_group_fields(value: str) -> list[str]:
    fields = [normalize_field_name(part) for part in value.split(",")]
    fields = [field for field in (field.strip() for field in fields) if field]
    if not fields:
        raise SystemExit("--group-by must include at least one field.")
    return fields


def parse_field_contains(values: list[str]) -> list[tuple[str, str]]:
    filters: list[tuple[str, str]] = []
    for value in values:
        if "=" not in value:
            raise SystemExit(f"Invalid --field-contains value '{value}'. Expected field=value.")
        field, needle = value.split("=", 1)
        filters.append((normalize_field_name(field), needle))
    return filters


def normalize_field_name(value: str) -> str:
    value = value.strip()
    if value.lower() == "orcid":
        return "ORCID"
    return slugify_field(value)


def print_summary(group_fields: list[str], rows: list[tuple[tuple[str, ...], dict[str, object]]]) -> None:
    header = group_fields + ["rows", "unique_orcids"]
    print("\t".join(header))
    for key, counts in rows:
        print("\t".join([*key, str(counts["rows"]), str(counts["unique_orcids"])]))


def write_summary_csv(
    path: Path,
    group_fields: list[str],
    rows: list[tuple[tuple[str, ...], dict[str, object]]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=group_fields + ["rows", "unique_orcids"])
        writer.writeheader()
        for key, counts in rows:
            writer.writerow(
                {
                    **dict(zip(group_fields, key, strict=True)),
                    "rows": counts["rows"],
                    "unique_orcids": counts["unique_orcids"],
                }
            )


if __name__ == "__main__":
    raise SystemExit(main())
