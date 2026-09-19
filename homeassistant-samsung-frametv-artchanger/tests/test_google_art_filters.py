import json
import os
import sys
import unittest


sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sources import google_art


class GoogleArtFilterTests(unittest.TestCase):
    def test_german_helper_values_are_normalized(self):
        self.assertEqual(google_art._normalize_museum("Musée d’Orsay"), "ORSAY")
        self.assertEqual(google_art._normalize_museum("MoMA"), "MOMA")
        self.assertEqual(google_art._normalize_style("Moderne Kunst"), "MODERN")
        self.assertEqual(
            google_art._normalize_style("Abstrakter Expressionismus"),
            "ABSTRACT_EXPRESSIONISM",
        )

    def test_google_dominant_colors_map_to_dashboard_groups(self):
        self.assertEqual(google_art._dominant_color_group("#607995"), "BLUE")
        self.assertEqual(google_art._dominant_color_group("#ff2020"), "RED")
        self.assertEqual(google_art._dominant_color_group("#f080b0"), "PINK")
        self.assertEqual(google_art._dominant_color_group("#777777"), "GRAY")

    def test_final_api_page_without_continuation_token_is_supported(self):
        query = [
            "stella.pr",
            "AssetsQuery:test",
            [
                [
                    "stella.common.cobject",
                    "The Starry Night",
                    "Vincent van Gogh",
                    "//lh3.googleusercontent.com/example",
                    "/asset/the-starry-night/test",
                    8,
                    None,
                    None,
                    "#607995",
                ]
            ],
            None,
            1,
        ]
        body = ")]}'\n" + json.dumps([[[*query], ["e", 2]]])
        assets, total, token = google_art._parse_search_api(body)
        self.assertEqual(total, 1)
        self.assertIsNone(token)
        self.assertEqual(assets[0]["color"], "#607995")
        self.assertTrue(assets[0]["url"].startswith("https://artsandculture.google.com/asset/"))

    def test_sent_urls_and_color_are_both_applied(self):
        catalog = {
            "assets": [
                {"url": "https://example/red-sent", "color": "#ff2020"},
                {"url": "https://example/red-new", "color": "#c03020"},
                {"url": "https://example/blue-new", "color": "#2040d0"},
            ]
        }
        candidates = google_art._filter_catalog_candidates(
            catalog,
            "RED",
            {"https://example/red-sent"},
        )
        self.assertEqual(candidates, ["https://example/red-new"])


if __name__ == "__main__":
    unittest.main()
