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


if __name__ == "__main__":
    unittest.main()
