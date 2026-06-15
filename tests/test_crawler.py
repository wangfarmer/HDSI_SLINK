import unittest
from importlib.util import find_spec
from unittest.mock import patch

import requests

from harvard_faculty_scraper.models import SchoolConfig

if find_spec("bs4") is None or find_spec("requests") is None:
    HarvardFacultyCrawler = None
else:
    from harvard_faculty_scraper.crawler import HarvardFacultyCrawler


class FakeResponse:
    def __init__(
        self,
        text: str = "",
        json_payload=None,
        headers: dict[str, str] | None = None,
        status_code: int = 200,
    ) -> None:
        self.text = text
        self._json_payload = json_payload
        self.headers = headers or {}
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} Client Error")
        return None

    def json(self):
        if self._json_payload is None:
            raise ValueError("No JSON payload")
        return self._json_payload


class FakeSession:
    def __init__(self, pages: dict[str, str]) -> None:
        self.pages = pages
        self.headers: dict[str, str] = {}

    def get(self, url: str, timeout: float) -> FakeResponse:
        value = self.pages[url]
        if isinstance(value, list):
            return value.pop(0)
        if isinstance(value, FakeResponse):
            return value
        return FakeResponse(text=value)


class HarvardFacultyCrawlerTest(unittest.TestCase):
    @unittest.skipIf(HarvardFacultyCrawler is None, "beautifulsoup4/requests are not installed")
    def test_discover_profile_urls_from_seed_page(self) -> None:
        config = SchoolConfig(
            key="example",
            name="Example Harvard School",
            seed_urls=["https://example.harvard.edu/faculty"],
            allowed_domains=["example.harvard.edu"],
            profile_link_patterns=[r"/people/"],
            exclude_link_patterns=[r"#", r"/people/news"],
            profile_required_patterns=[r"/people/[^/]+$"],
        )
        session = FakeSession(
            {
                "https://example.harvard.edu/faculty": """
                <a href="/people/jane-scholar">Jane Scholar</a>
                <a href="https://example.harvard.edu/people/john-scholar#bio">John Scholar</a>
                <a href="/people/news">News</a>
                <a href="https://outside.example.com/people/person">Outside</a>
                """
            }
        )
        crawler = HarvardFacultyCrawler(config, session=session, delay_seconds=0)

        urls = crawler.discover_profile_urls()

        self.assertEqual(
            urls,
            [
                "https://example.harvard.edu/people/jane-scholar",
                "https://example.harvard.edu/people/john-scholar",
            ],
        )

    @unittest.skipIf(HarvardFacultyCrawler is None, "beautifulsoup4/requests are not installed")
    def test_follows_hls_query_style_pagination(self) -> None:
        config = SchoolConfig(
            key="hls",
            name="Harvard Law School",
            seed_urls=["https://hls.harvard.edu/faculty/?page=1"],
            allowed_domains=["hls.harvard.edu"],
            profile_link_patterns=[r"/faculty/"],
            exclude_link_patterns=[r"/faculty/$", r"#"],
            profile_required_patterns=[r"/faculty/[A-Za-z0-9][A-Za-z0-9-]*/?$"],
            list_page_patterns=[r"/faculty/\?(?:type=hls_faculty&)?page=\d+(?:&type=hls_faculty)?$"],
        )
        session = FakeSession(
            {
                "https://hls.harvard.edu/faculty/?page=1": """
                <a href="/faculty/william-p-alford/">William P. Alford</a>
                <a href="?page=2&type=hls_faculty">Next</a>
                """,
                "https://hls.harvard.edu/faculty/?page=2&type=hls_faculty": """
                <a href="/faculty/sabrineh-ardalan/">Sabrineh Ardalan</a>
                """
            }
        )
        crawler = HarvardFacultyCrawler(config, session=session, delay_seconds=0)

        urls = crawler.discover_profile_urls(max_pages=5)

        self.assertEqual(
            urls,
            [
                "https://hls.harvard.edu/faculty/william-p-alford",
                "https://hls.harvard.edu/faculty/sabrineh-ardalan",
            ],
        )

    @unittest.skipIf(HarvardFacultyCrawler is None, "beautifulsoup4/requests are not installed")
    def test_discovers_profile_urls_from_about_attributes(self) -> None:
        config = SchoolConfig(
            key="hks",
            name="Harvard Kennedy School",
            seed_urls=["https://www.hks.harvard.edu/faculty-profiles"],
            allowed_domains=["www.hks.harvard.edu"],
            profile_link_patterns=[r"/faculty/"],
            exclude_link_patterns=[r"/faculty-profiles"],
            profile_required_patterns=[r"/faculty/[A-Za-z0-9][A-Za-z0-9-]*/?$"],
        )
        session = FakeSession(
            {
                "https://www.hks.harvard.edu/faculty-profiles": """
                <article about="/faculty/khalil-abdur-rashid">Khalil Abdur-Rashid</article>
                """
            }
        )
        crawler = HarvardFacultyCrawler(config, session=session, delay_seconds=0)

        urls = crawler.discover_profile_urls(max_pages=1)

        self.assertEqual(urls, ["https://www.hks.harvard.edu/faculty/khalil-abdur-rashid"])

    @unittest.skipIf(HarvardFacultyCrawler is None, "beautifulsoup4/requests are not installed")
    def test_discovers_profile_urls_from_paginated_api(self) -> None:
        config = SchoolConfig(
            key="hsph",
            name="Harvard Chan School",
            seed_urls=[],
            api_seed_urls=["https://hsph.harvard.edu/wp-json/wp/v2/faculty_profiles?per_page=2&page=1"],
            allowed_domains=["hsph.harvard.edu"],
            profile_link_patterns=[r"/profile/"],
            profile_required_patterns=[r"/profile/[^/]+/?$"],
        )
        session = FakeSession(
            {
                "https://hsph.harvard.edu/wp-json/wp/v2/faculty_profiles?per_page=2&page=1": FakeResponse(
                    json_payload=[
                        {"link": "https://hsph.harvard.edu/profile/rifat-atun/"},
                        {"link": "https://hsph.harvard.edu/profile/andrea-baccarelli/"},
                    ],
                    headers={"X-WP-TotalPages": "2"},
                ),
                "https://hsph.harvard.edu/wp-json/wp/v2/faculty_profiles?per_page=2&page=2": FakeResponse(
                    json_payload=[
                        {"link": "https://hsph.harvard.edu/profile/jorge-e-chavarro/"},
                    ],
                    headers={"X-WP-TotalPages": "2"},
                ),
            }
        )
        crawler = HarvardFacultyCrawler(config, session=session, delay_seconds=0)

        urls = crawler.discover_profile_urls(max_pages=5)

        self.assertEqual(
            urls,
            [
                "https://hsph.harvard.edu/profile/rifat-atun",
                "https://hsph.harvard.edu/profile/andrea-baccarelli",
                "https://hsph.harvard.edu/profile/jorge-e-chavarro",
            ],
        )

    @unittest.skipIf(HarvardFacultyCrawler is None, "beautifulsoup4/requests are not installed")
    def test_fetch_text_retries_rate_limited_page(self) -> None:
        config = SchoolConfig(
            key="hbs",
            name="Harvard Business School",
            seed_urls=[],
            allowed_domains=["pubwww.hbs.edu"],
        )
        session = FakeSession(
            {
                "https://pubwww.hbs.edu/faculty/Pages/profile.aspx?facId=10653": [
                    FakeResponse(status_code=429, headers={"Retry-After": "0"}),
                    FakeResponse(text="<html>ok</html>"),
                ]
            }
        )
        crawler = HarvardFacultyCrawler(
            config,
            session=session,
            delay_seconds=0,
            request_retries=1,
            request_backoff_seconds=0,
        )

        with patch("harvard_faculty_scraper.crawler.time.sleep") as sleep:
            html = crawler.fetch_text("https://pubwww.hbs.edu/faculty/Pages/profile.aspx?facId=10653")

        self.assertEqual(html, "<html>ok</html>")
        sleep.assert_called_once_with(0.0)


if __name__ == "__main__":
    unittest.main()
