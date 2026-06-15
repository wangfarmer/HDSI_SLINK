from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from .config import DEFAULT_SCHOOL_CONFIGS, get_school_config, load_school_config
from .crawler import HarvardFacultyCrawler, print_jsonl, with_seed_urls, write_csv, write_jsonl
from .export import PersonFolderWriter


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
    scrape_parser.add_argument(
        "--progress-every",
        type=int,
        default=25,
        help="Print progress every N profiles in person-folders mode. Use 0 to disable.",
    )
    scrape_parser.add_argument("--delay-seconds", type=float, default=1.0, help="Delay between HTTP requests.")
    scrape_parser.add_argument("--timeout-seconds", type=float, default=20.0, help="HTTP timeout.")
    scrape_parser.add_argument(
        "--request-retries",
        type=int,
        default=3,
        help="Number of retries for rate-limited or transient page/API requests.",
    )
    scrape_parser.add_argument(
        "--request-backoff-seconds",
        type=float,
        default=10.0,
        help="Base backoff between page/API retry attempts.",
    )
    scrape_parser.add_argument(
        "--http-client",
        choices=["requests", "browser"],
        default="requests",
        help="HTTP backend. Use browser for sites that block normal Python requests.",
    )
    scrape_parser.add_argument(
        "--browser-fallback-on-403",
        action="store_true",
        help="When using requests, retry HTTP 403 URLs once with the browser HTTP client.",
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
        "--write-failed-profile-records",
        action="store_true",
        help="For failed profile-page fetches, write placeholder profile.jsonl records with error metadata.",
    )
    scrape_parser.add_argument(
        "--skip-images",
        action="store_true",
        help="For person-folders output, write profile JSONL but do not download profile pictures.",
    )
    scrape_parser.add_argument(
        "--image-delay-seconds",
        type=float,
        default=None,
        help="Delay between profile-picture downloads. Defaults to --delay-seconds.",
    )
    scrape_parser.add_argument(
        "--image-retries",
        type=int,
        default=3,
        help="Number of retries for rate-limited or transient image downloads.",
    )
    scrape_parser.add_argument(
        "--image-backoff-seconds",
        type=float,
        default=5.0,
        help="Base backoff between image retry attempts.",
    )
    return parser


def scrape(args: argparse.Namespace) -> int:
    config = load_config_from_args(args)
    if args.seed_url:
        config = with_seed_urls(config, args.seed_url)
    failures: list[dict[str, str]] = []
    error_handler = make_error_handler(failures)

    crawler_kwargs = {
        "timeout_seconds": args.timeout_seconds,
        "delay_seconds": args.delay_seconds,
        "http_client": args.http_client,
        "request_retries": args.request_retries,
        "request_backoff_seconds": args.request_backoff_seconds,
        "browser_fallback_on_403": args.browser_fallback_on_403,
    }
    if args.user_agent:
        crawler_kwargs["user_agent"] = args.user_agent

    crawler = HarvardFacultyCrawler(config, **crawler_kwargs)
    profile_urls = crawler.discover_profile_urls(
        max_pages=args.max_pages,
        continue_on_error=args.continue_on_error,
        on_error=error_handler,
    )

    if args.discover_only:
        for url in profile_urls:
            print(url)
        return 0

    if args.output_layout == "person-folders":
        if not args.output:
            raise SystemExit("--output is required when --output-layout person-folders is used.")
        writer = PersonFolderWriter(
            args.output,
            session=crawler.session,
            download_images=not args.skip_images,
            continue_on_error=args.continue_on_error,
            on_error=error_handler,
            timeout_seconds=args.timeout_seconds,
            image_delay_seconds=args.image_delay_seconds if args.image_delay_seconds is not None else args.delay_seconds,
            image_retries=args.image_retries,
            image_backoff_seconds=args.image_backoff_seconds,
        )
        written = 0
        for record in crawler.iter_scrape_profiles(
            profile_urls,
            source_directory_url=", ".join(config.seed_urls),
            max_profiles=args.max_profiles,
            continue_on_error=args.continue_on_error,
            on_error=error_handler,
            write_failed_records=args.write_failed_profile_records,
        ):
            writer.write(record)
            written += 1
            if args.progress_every and written % args.progress_every == 0:
                print(f"[progress] wrote {written} profile folders", file=sys.stderr)
        write_failures_if_needed(failures, args.output / "_failures.jsonl")
    else:
        records = crawler.scrape_profiles(
            profile_urls,
            source_directory_url=", ".join(config.seed_urls),
            max_profiles=args.max_profiles,
            continue_on_error=args.continue_on_error,
            on_error=error_handler,
            write_failed_records=args.write_failed_profile_records,
        )
        if args.output:
            if args.format == "csv":
                write_csv(records, args.output)
            else:
                write_jsonl(records, args.output)
            write_failures_if_needed(failures, args.output.with_name(f"{args.output.stem}_failures.jsonl"))
        elif args.format == "csv":
            raise SystemExit("CSV output requires --output.")
        else:
            print_jsonl(records, sys.stdout)

    return 0


def make_error_handler(failures: list[dict[str, str]]):
    def handle(url: str, exc: Exception) -> None:
        failures.append(
            {
                "url": url,
                "error": str(exc),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        print_fetch_error(url, exc)

    return handle


def write_failures_if_needed(failures: list[dict[str, str]], output_path: Path) -> None:
    if not failures:
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for failure in failures:
            handle.write(json.dumps(failure, ensure_ascii=False) + "\n")


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
    if "429" in str(exc):
        print(
            "[fetch-error] Received HTTP 429 Too Many Requests. Slow page requests "
            "with --delay-seconds/--request-backoff-seconds, slow image downloads "
            "with --image-delay-seconds/--image-backoff-seconds, or use --skip-images "
            "and rerun images later.",
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
