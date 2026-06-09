# Harvard faculty scraper

This is requirement 2 scaffolding for HUMA.I.N / S-Link:

> Collect Harvard school faculty profile data, mainly image, basic profile information, bio, and email.

The code is intentionally a configurable scraper framework. Harvard schools use different CMS templates, so each school has its own seed URLs and link patterns in `harvard_faculty_scraper/config.py`.

## Install locally

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

## List configured schools

```bash
python -m harvard_faculty_scraper.cli list-schools
```

## Inspect one config

```bash
python -m harvard_faculty_scraper.cli show-config --school harvard_kennedy_school
```

## Discover profile URLs only

This scans directory/list pages and prints candidate profile URLs. It does not fetch profile pages.

```bash
python -m harvard_faculty_scraper.cli scrape \
  --school harvard_kennedy_school \
  --discover-only \
  --max-pages 3 \
  --delay-seconds 1
```

## Scrape profiles to JSONL

```bash
python -m harvard_faculty_scraper.cli scrape \
  --school harvard_kennedy_school \
  --max-pages 3 \
  --max-profiles 50 \
  --delay-seconds 1 \
  --format jsonl \
  --output data/raw/harvard_kennedy_school_faculty.jsonl
```

## Scrape profiles to CSV

```bash
python -m harvard_faculty_scraper.cli scrape \
  --school harvard_business_school \
  --max-pages 3 \
  --max-profiles 50 \
  --delay-seconds 1 \
  --format csv \
  --output data/raw/harvard_business_school_faculty.csv
```

## Override seed URLs

Use this when a school has a more specific faculty page than the built-in default.

```bash
python -m harvard_faculty_scraper.cli scrape \
  --school harvard_law_school \
  --seed-url "https://hls.harvard.edu/faculty/" \
  --discover-only
```

## Use a custom school config

Copy `configs/example_school_config.json`, update the URLs/patterns, then run:

```bash
python -m harvard_faculty_scraper.cli scrape \
  --config-file configs/example_school_config.json \
  --discover-only
```

## Output schema

Each JSONL row is a `FacultyRecord`:

```json
{
  "source_school": "Harvard Kennedy School",
  "source_directory_url": "https://www.hks.harvard.edu/faculty-research/faculty-directory",
  "profile_url": "https://...",
  "full_name": "Jane Q. Scholar",
  "title": "Professor ...",
  "affiliation": "Department or school",
  "email": "person@harvard.edu",
  "image_url": "https://...",
  "bio": "Biography text...",
  "research_interests": ["network science", "collective intelligence"],
  "raw_text_excerpt": "First 1000 chars of page text...",
  "scraped_at": "UTC timestamp",
  "extraction_notes": ["used_json_ld"],
  "extra": {}
}
```

## Extraction strategy

The extractor tries fields in this order:

1. JSON-LD `Person` structured data.
2. Open Graph / meta tags.
3. Common Harvard/CMS CSS selectors.
4. `mailto:` links and plain-text email regex.
5. Headings such as `Biography`, `Bio`, `Research`, `Expertise`, and nearby paragraphs.

This should produce usable first-pass data, but each school may need custom tuning after you run samples.

## ORCID merge path

When the ORCID data arrives, use the scraped faculty output as the profile enrichment table. Recommended matching order:

1. Exact ORCID if available in a profile or ORCID table.
2. Exact institutional email.
3. Normalized full name plus school/affiliation.
4. Normalized full name plus research topic similarity.

Do not overwrite a high-confidence ORCID field with lower-confidence scraped text. Keep provenance columns so the grouping algorithm can know which source supplied each attribute.

## Notes for polite runs

- Start with `--discover-only`.
- Use small `--max-pages` and `--max-profiles` values while tuning.
- Keep `--delay-seconds` at 1 or higher unless you have explicit permission.
- Do not commit files under `data/raw` or `data/processed`; the repository ignores them by default.

## Windows Anaconda Prompt examples

Run all built-in schools and keep going if one school returns an HTTP error:

```bat
python -m pip install -e .

if not exist data\raw mkdir data\raw
if not exist logs mkdir logs

for /f "tokens=1 delims=	" %s in ('python -m harvard_faculty_scraper.cli list-schools') do (
  echo === scraping %s ===
  python -m harvard_faculty_scraper.cli scrape --school %s --max-pages 100 --max-profiles 10000 --delay-seconds 1 --continue-on-error --format jsonl --output data\raw\%s_faculty.jsonl > logs\%s.log 2>&1
)
```

If you save the command in a `.bat` file, change `%s` to `%%s`.

## Current built-in school status

Smoke-tested status as of the current scraper version:

| School key | Status | Notes |
| --- | --- | --- |
| `harvard_law_school` | Works | Discovery finds about 83 public faculty profile URLs. |
| `harvard_graduate_school_of_design` | Works | Discovery finds about 53 public faculty profile URLs. |
| `harvard_education_school` | Works | Discovery finds about 252 public faculty profile URLs. |
| `harvard_kennedy_school` | Blocked | Public directory currently returns HTTP 403 to scripted requests. |
| `harvard_divinity_school` | Blocked | Public people page currently returns HTTP 403 to scripted requests. |
| `harvard_business_school` | Needs tuning | Seed page returns no static profile links in the current HTML response. |
| `harvard_medical_school` | Needs tuning | Current seed/config does not discover profile links yet. |
| `harvard_t_h_chan_school_public_health` | Needs tuning | Current seed/config does not discover profile links yet. |

## HTTP 403 Forbidden

Some Harvard school sites may reject non-browser-looking requests or require browser verification. The scraper now sends browser-like default headers, but a school can still block automated access.

If you see `403 Client Error: Forbidden`:

1. Try a smaller discovery run first:

   ```bat
   python -m harvard_faculty_scraper.cli scrape --school harvard_kennedy_school --discover-only --max-pages 1 --delay-seconds 2
   ```

2. For batch runs, add `--continue-on-error` so one school does not stop the whole run.

3. If your browser can open the page but Python cannot, pass your own current browser User-Agent:

   ```bat
   python -m harvard_faculty_scraper.cli scrape --school harvard_kennedy_school --discover-only --user-agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36"
   ```

4. If the site still blocks access, use a school-specific public directory page with `--seed-url`, or collect that school manually.
