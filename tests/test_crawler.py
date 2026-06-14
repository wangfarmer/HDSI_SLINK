import unittest
from importlib.util import find_spec

from harvard_faculty_scraper.models import SchoolConfig

if find_spec("bs4") is None or find_spec("requests") is None:
    HarvardFacultyCrawler = None
else:
    from harvard_faculty_scraper.crawler import HarvardFacultyCrawler


class FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text

    def raise_for_status(self) -> None:
        return None


class FakeSession:
    def __init__(self, pages: dict[str, str]) -> None:
        self.pages = pages
        self.headers: dict[str, str] = {}

    def get(self, url: str, timeout: float) -> FakeResponse:
        return FakeResponse(self.pages[url])


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


if __name__ == "__main__":
    unittest.main()
