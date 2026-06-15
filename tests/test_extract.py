import unittest
from importlib.util import find_spec

if find_spec("bs4") is None:
    extract_faculty_record = None
else:
    from harvard_faculty_scraper.extract import extract_faculty_record


class ExtractFacultyRecordTest(unittest.TestCase):
    @unittest.skipIf(extract_faculty_record is None, "beautifulsoup4 is not installed")
    def test_extract_faculty_record_from_profile_html(self) -> None:
        html = """
        <html>
          <head>
            <meta property="og:title" content="Jane Q. Scholar | Harvard Example">
            <meta property="og:image" content="/images/jane.jpg">
            <script type="application/ld+json">
              {
                "@context": "https://schema.org",
                "@type": "Person",
                "name": "Jane Q. Scholar",
                "jobTitle": "Professor of Collective Intelligence",
                "email": "jane_scholar@example.harvard.edu",
                "knowsAbout": ["collective intelligence", "network science"]
              }
            </script>
          </head>
          <body>
            <main>
              <h1>Jane Q. Scholar</h1>
              <p class="department">Example School</p>
              <h2>Biography</h2>
              <p>
                Jane studies how people and AI systems collaborate across adaptive
                networks. Her work focuses on team learning, social sensitivity,
                and group decision processes in complex organizations.
              </p>
            </main>
          </body>
        </html>
        """

        record = extract_faculty_record(
            html,
            profile_url="https://example.harvard.edu/people/jane-scholar",
            source_school="Example School",
            source_directory_url="https://example.harvard.edu/people",
        )

        self.assertEqual(record.full_name, "Jane Q. Scholar")
        self.assertEqual(record.title, "Professor of Collective Intelligence")
        self.assertEqual(record.role_category, "faculty")
        self.assertEqual(record.email, "jane_scholar@example.harvard.edu")
        self.assertEqual(record.image_url, "https://example.harvard.edu/images/jane.jpg")
        self.assertEqual(record.affiliation, "Example School")
        self.assertIn("people and AI systems collaborate", record.bio or "")
        self.assertEqual(record.research_interests, ["collective intelligence", "network science"])

    @unittest.skipIf(extract_faculty_record is None, "beautifulsoup4 is not installed")
    def test_infers_postdoc_role_category(self) -> None:
        html = """
        <html>
          <body>
            <main>
              <h1>Robin Researcher</h1>
              <p class="profile-title">Postdoctoral Fellow in Education</p>
              <p>Robin studies collaboration and learning systems.</p>
            </main>
          </body>
        </html>
        """

        record = extract_faculty_record(
            html,
            profile_url="https://example.harvard.edu/people/robin-researcher",
            source_school="Example School",
            source_directory_url="https://example.harvard.edu/people",
        )

        self.assertEqual(record.role_category, "postdoc")

    @unittest.skipIf(extract_faculty_record is None, "beautifulsoup4 is not installed")
    def test_prefers_hbs_headshot_over_publication_images(self) -> None:
        html = """
        <html>
          <body>
            <main>
              <h1>Max H. Scholar</h1>
              <img src="https://www.hbs.edu/ris/Profile%20Files/book%20cover.jpg" alt="Book cover">
              <img src="http://harvardbusiness.org/products/1023-HBK-ENG/thumbnail/thumbnail.gif" alt="Product">
              <img src="https://www.hbs.edu/Style%20Library/api/headshot.aspx?id=10653&amp;size=medium" alt="Max H. Scholar">
            </main>
          </body>
        </html>
        """

        record = extract_faculty_record(
            html,
            profile_url="https://pubwww.hbs.edu/faculty/Pages/profile.aspx?facId=10653",
            source_school="Harvard Business School",
            source_directory_url="https://pubwww.hbs.edu/faculty/Pages/browse.aspx",
        )

        self.assertEqual(
            record.image_url,
            "https://www.hbs.edu/Style%20Library/api/headshot.aspx?id=10653&size=medium",
        )


if __name__ == "__main__":
    unittest.main()
