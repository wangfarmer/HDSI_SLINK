# Harvard people/researcher scraper

This is requirement 2 scaffolding for HUMA.I.N / S-Link:

> Collect Harvard school people/researcher profile data, mainly image, basic profile information, bio, and email.

The code is intentionally a configurable scraper framework. Harvard schools, departments, labs, and research groups use different CMS templates, so each source has its own seed URLs and link patterns in `harvard_faculty_scraper/config.py` or a custom JSON config file.

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

## Preferred person-folder output with profile pictures

Use this layout when you want each person to have their own folder:

```bat
python -m harvard_faculty_scraper.cli scrape --school harvard_education_school --max-pages 100 --max-profiles 10000 --delay-seconds 1 --continue-on-error --output-layout person-folders --output data\raw\harvard_education_school_people
```

Example output structure:

```text
data/raw/harvard_education_school_people/
  Danielle S. Allen/
    profile.jsonl
    profile_picture.jpg
  Drew Allen/
    profile.jsonl
    profile_picture.jpg
```

`profile.jsonl` contains the normalized profile record. If an image is downloaded successfully, the record's `local_image_path` field points to the saved image.

To create folders without downloading images:

```bat
python -m harvard_faculty_scraper.cli scrape --school harvard_education_school --max-pages 100 --max-profiles 10000 --delay-seconds 1 --continue-on-error --output-layout person-folders --skip-images --output data\raw\harvard_education_school_people
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

Use this when a school, department, lab, or research group has a more specific people page than the built-in default.

```bash
python -m harvard_faculty_scraper.cli scrape \
  --school harvard_law_school \
  --seed-url "https://hls.harvard.edu/faculty/" \
  --discover-only
```

## Use a custom school config

Copy `configs/example_school_config.json` or `configs/example_research_group_people_config.json`, update the URLs/patterns, then run:

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
  "role_category": "faculty",
  "affiliation": "Department or school",
  "email": "person@harvard.edu",
  "image_url": "https://...",
  "local_image_path": "data/raw/.../Jane Q. Scholar/profile_picture.jpg",
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

## Not just professors

The scraper does not intentionally filter to professors. It follows the profile links exposed by the configured seed pages. To include students, postdocs, technicians, lab managers, research scientists, and other research staff, configure seed URLs that list those people.

Examples:

- HGSE built-in config includes faculty, staff, PhD students, and EdLD students.
- GSD built-in config includes faculty, staff, and affiliates.
- Lab or department pages can be added through `--seed-url` or a custom config file.

The `role_category` field is inferred from title text when possible:

- `faculty`
- `postdoc`
- `student`
- `staff_or_technician`
- `research_staff`
- `fellow`
- `other`

## ORCID merge path

When the ORCID data arrives, use the scraped people/researcher output as the profile enrichment table. Recommended matching order:

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

## Robust mode for noisy runs

Use this mode when you see intermittent `403`, `429`, or `500` errors:

```bat
python -m harvard_faculty_scraper.cli scrape --school harvard_education_school --max-pages 100 --max-profiles 10000 --delay-seconds 3 --request-retries 5 --request-backoff-seconds 20 --image-delay-seconds 5 --image-retries 5 --image-backoff-seconds 20 --browser-fallback-on-403 --continue-on-error --write-failed-profile-records --output-layout person-folders --output data\raw\harvard_education_school_people
```

This does four things:

- retries transient `429` and `500` page/API requests;
- retries `403` once with the browser HTTP client;
- continues the run when one profile or image still fails;
- writes `_failures.jsonl` in the output folder and placeholder `profile.jsonl` records for failed profile pages.

## Windows Anaconda Prompt examples

Run all built-in schools and keep going if one school returns an HTTP error:

```bat
python -m pip install -e .

if not exist data\raw mkdir data\raw
if not exist logs mkdir logs

for /f "tokens=1 delims=	" %s in ('python -m harvard_faculty_scraper.cli list-schools') do (
  echo === scraping %s ===
  python -m harvard_faculty_scraper.cli scrape --school %s --max-pages 100 --max-profiles 10000 --delay-seconds 1 --continue-on-error --output-layout person-folders --output data\raw\%s_people > logs\%s.log 2>&1
)
```

If you save the command in a `.bat` file, change `%s` to `%%s`.

## Current built-in school status

Smoke-tested status as of the current scraper version:

| School key | Status | Notes |
| --- | --- | --- |
| `harvard_kennedy_school` | Works | Discovery finds 229 public faculty profile URLs from the current `/faculty-profiles` directory. |
| `harvard_business_school` | Works | Discovery finds 361 public faculty profile URLs from `pubwww.hbs.edu`. |
| `harvard_law_school` | Works | Discovery finds 387 public faculty profile URLs from the explicit `?page=1` paginated directory. |
| `harvard_graduate_school_of_design` | Works | Discovery finds about 128 public faculty/staff/affiliate `/person/...` profile URLs. |
| `harvard_medical_school` | Partial | Discovery finds 113 public profiles from the DBMI people directory; HMS does not expose a single master public people directory in this config. |
| `harvard_t_h_chan_school_public_health` | Works | Discovery finds 1548 public faculty/researcher profile URLs through the school's WordPress profiles API. |
| `harvard_education_school` | Works | Discovery finds about 679 public faculty/staff/PhD student/EdLD student directory profile URLs. |
| `harvard_divinity_school` | Blocked | Public people page currently returns HTTP 403 to scripted requests. |

## HTTP 403 Forbidden

Some Harvard school sites may reject non-browser-looking requests or require browser verification. The scraper now sends browser-like default headers, but a school can still block automated access.

If you see `403 Client Error: Forbidden`:

1. Try a smaller discovery run first:

   ```bat
   python -m harvard_faculty_scraper.cli scrape --school harvard_divinity_school --discover-only --max-pages 1 --delay-seconds 2
   ```

2. Try browser-impersonation mode:

   ```bat
   python -m harvard_faculty_scraper.cli scrape --school harvard_kennedy_school --discover-only --max-pages 20 --http-client browser --continue-on-error
   ```

   For full HKS folder output:

   ```bat
   python -m harvard_faculty_scraper.cli scrape --school harvard_kennedy_school --max-pages 100 --max-profiles 10000 --delay-seconds 1 --http-client browser --continue-on-error --output-layout person-folders --output data\raw\harvard_kennedy_school_people
   ```

3. For batch runs, add `--continue-on-error` so one school does not stop the whole run.

4. If your browser can open the page but Python cannot, pass your own current browser User-Agent:

   ```bat
   python -m harvard_faculty_scraper.cli scrape --school harvard_divinity_school --discover-only --user-agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36"
   ```

5. If the site still blocks access, use a school-specific public directory page with `--seed-url`, or collect that school manually.

## HTTP 429 Too Many Requests for profile pictures

Some image hosts rate-limit profile-picture downloads. If you see `429 Client Error: Too Many Requests`, slow down image downloads:

```bat
python -m harvard_faculty_scraper.cli scrape --school harvard_graduate_school_of_design --max-pages 100 --max-profiles 10000 --delay-seconds 1 --image-delay-seconds 5 --image-retries 5 --image-backoff-seconds 15 --continue-on-error --output-layout person-folders --output data\raw\harvard_gsd_people
```

If you only need the JSON profiles first, skip images and download them in a later rerun:

```bat
python -m harvard_faculty_scraper.cli scrape --school harvard_graduate_school_of_design --max-pages 100 --max-profiles 10000 --delay-seconds 1 --skip-images --continue-on-error --output-layout person-folders --output data\raw\harvard_gsd_people
```

For HBS, slow both profile-page and image requests if you see 429s:

```bat
python -m harvard_faculty_scraper.cli scrape --school harvard_business_school --max-pages 100 --max-profiles 10000 --delay-seconds 3 --request-retries 5 --request-backoff-seconds 20 --image-delay-seconds 5 --image-retries 5 --image-backoff-seconds 20 --continue-on-error --output-layout person-folders --output data\raw\harvard_business_school_people
```

If HBS still rate-limits, run JSON first without images:

```bat
python -m harvard_faculty_scraper.cli scrape --school harvard_business_school --max-pages 100 --max-profiles 10000 --delay-seconds 3 --request-retries 5 --request-backoff-seconds 20 --skip-images --continue-on-error --output-layout person-folders --output data\raw\harvard_business_school_people
```
