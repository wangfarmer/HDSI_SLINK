from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import DEFAULT_SCHOOL_CONFIGS, get_school_config, load_school_config
from .crawler import HarvardFacultyCrawler, print_jsonl, with_seed_urls, write_csv, write_jsonl
from .export import write_person_folders


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "list-schools":
        for key, config in sorted(DEFAULT_SCHOOL_CONFIGS.items()):
            print(f"{key}\t{config.name}")
        return 0

    if args.command == "show-config":
        config = load_config_from_args(args)
        print_config(config)
        return 0

    if args.command == "scrape":
        return scrape(args)

    parser.error("Missing command")
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="harvard-faculty-scraper",
        description="Collect Harvard people/researcher profile data for HUMA.I.N S-Link experiments.",
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("list-schools", help="List built-in Harvard school/people configs.")

    show_config = subparsers.add_parser("show-config", help="Show one built-in school config.")
    show_config.add_argument("--school", choices=sorted(DEFAULT_SCHOOL_CONFIGS))
    show_config.add_argument("--config-file", type=Path, help="Path to a custom school config JSON file.")

    scrape_parser = subparsers.add_parser("scrape", help="Run a configured faculty scrape.")
    scrape_parser.add_argument("--school", choices=sorted(DEFAULT_SCHOOL_CONFIGS))
    scrape_parser.add_argument("--config-file", type=Path, help="Path to a custom school config JSON file.")
    scrape_parser.add_argument(
        "--seed-url",
        action="append",
        default=[],
        help="Override/add directory seed URL. Can be passed multiple times.",
    )
    scrape_parser.add_argument("--output", type=Path, help="Output file or person-folder root. Defaults to stdout for JSONL.")
    scrape_parser.add_argument(
        "--output-layout",
        choices=["flat", "person-folders"],
        default="flat",
        help="Flat writes one JSONL/CSV file. person-folders writes one folder per person.",
    )
    scrape_parser.add_argument("--format", choices=["jsonl", "csv"], default="jsonl")
    scrape_parser.add_argument("--max-pages", type=int, default=20, help="Max directory/list pages to scan.")
    scrape_parser.add_argument("--max-profiles", type=int, default=25, help="Max profiles to fetch.")
    scrape_parser.add_argument("--delay-seconds", type=float, default=1.0, help="Delay between HTTP requests.")
    scrape_parser.add_argument("--timeout-seconds", type=float, default=20.0, help="HTTP timeout.")
    scrape_parser.add_argument(
        "--http-client",
        choices=["requests", "browser"],
        default="requests",
        help="HTTP backend. Use browser for sites that block normal Python requests.",
    )
    scrape_parser.add_argument(
        "--discover-only",
        action="store_true",
        help="Only print discovered profile URLs; do not fetch profile pages.",
    )
    scrape_parser.add_argument(
        "--user-agent",
        default=None,
        help="Custom HTTP User-Agent for your run.",
    )
    scrape_parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Log HTTP errors and continue. Useful for all-school batch runs.",
    )
    scrape_parser.add_argument(
        "--skip-images",
        action="store_true",
        help="For person-folders output, write profile JSONL but do not download profile pictures.",
    )
    return parser


def scrape(args: argparse.Namespace) -> int:
    config = load_config_from_args(args)
    if args.seed_url:
        config = with_seed_urls(config, args.seed_url)

    crawler_kwargs = {
        "timeout_seconds": args.timeout_seconds,
        "delay_seconds": args.delay_seconds,
        "http_client": args.http_client,
    }
    if args.user_agent:
        crawler_kwargs["user_agent"] = args.user_agent

    crawler = HarvardFacultyCrawler(config, **crawler_kwargs)
    profile_urls = crawler.discover_profile_urls(
        max_pages=args.max_pages,
        continue_on_error=args.continue_on_error,
        on_error=print_fetch_error,
    )

    if args.discover_only:
        for url in profile_urls:
            print(url)
        return 0

    records = crawler.scrape_profiles(
        profile_urls,
        source_directory_url=", ".join(config.seed_urls),
        max_profiles=args.max_profiles,
        continue_on_error=args.continue_on_error,
        on_error=print_fetch_error,
    )

    if args.output_layout == "person-folders":
        if not args.output:
            raise SystemExit("--output is required when --output-layout person-folders is used.")
        write_person_folders(
            records,
            args.output,
            session=crawler.session,
            download_images=not args.skip_images,
            continue_on_error=args.continue_on_error,
            on_error=print_fetch_error,
            timeout_seconds=args.timeout_seconds,
        )
    elif args.output:
        if args.format == "csv":
            write_csv(records, args.output)
        else:
            write_jsonl(records, args.output)
    elif args.format == "csv":
        raise SystemExit("CSV output requires --output.")
    else:
        print_jsonl(records, sys.stdout)

    return 0


def print_fetch_error(url: str, exc: Exception) -> None:
    print(f"[fetch-error] {url}: {exc}", file=sys.stderr)
    if "403" in str(exc):
        print(
            "[fetch-error] Received HTTP 403 Forbidden. The site may block automated "
            "requests, require browser verification, or reject the current User-Agent. "
            "Try a smaller run, a school-specific seed URL, or --user-agent with a "
            "current browser User-Agent.",
            file=sys.stderr,
        )


def load_config_from_args(args: argparse.Namespace):
    if args.config_file:
        return load_school_config(args.config_file)
    if args.school:
        return get_school_config(args.school)
    raise SystemExit("Either --school or --config-file is required.")


def print_config(config: object) -> None:
    for field_name, value in vars(config).items():
        print(f"{field_name}: {value}")


if __name__ == "__main__":
    raise SystemExit(main())
