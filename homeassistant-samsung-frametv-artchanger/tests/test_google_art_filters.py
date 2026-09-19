import json
import os
import sys
import unittest
from unittest import mock


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

    def test_asset_page_parser_keeps_original_image_url(self):
        parser = google_art.GoogleAssetImageParser()
        parser.feed(
            '<html><head><meta property="og:image" '
            'content="https://lh3.googleusercontent.com/example"></head></html>'
        )
        self.assertEqual(
            parser.image_url,
            "https://lh3.googleusercontent.com/example",
        )

    @mock.patch.object(google_art, "_save_orientation_cache")
    @mock.patch.object(google_art, "_load_orientation_cache", return_value={})
    @mock.patch.object(google_art.random, "shuffle")
    @mock.patch.object(
        google_art,
        "_probe_asset_dimensions",
        side_effect=[(600, 900), (1600, 900)],
    )
    def test_landscape_selector_skips_portrait_before_high_res_download(
        self,
        probe_dimensions,
        _shuffle,
        _load_cache,
        save_cache,
    ):
        selected = google_art._select_landscape_candidate(
            ["https://example/portrait", "https://example/landscape"]
        )

        self.assertEqual(selected, "https://example/landscape")
        self.assertEqual(probe_dimensions.call_count, 2)
        saved_cache = save_cache.call_args.args[0]
        self.assertEqual(
            saved_cache["https://example/portrait"]["orientation"],
            "portrait_or_square",
        )
        self.assertEqual(
            saved_cache["https://example/landscape"]["orientation"],
            "landscape",
        )

    @mock.patch.object(google_art, "_save_orientation_cache")
    @mock.patch.object(
        google_art,
        "_load_orientation_cache",
        return_value={
            "https://example/portrait": {"orientation": "portrait_or_square"},
            "https://example/landscape": {"orientation": "landscape"},
        },
    )
    @mock.patch.object(google_art.random, "shuffle")
    @mock.patch.object(google_art, "_probe_asset_dimensions")
    def test_landscape_selector_reuses_cached_orientation(
        self,
        probe_dimensions,
        _shuffle,
        _load_cache,
        save_cache,
    ):
        selected = google_art._select_landscape_candidate(
            ["https://example/portrait", "https://example/landscape"]
        )

        self.assertEqual(selected, "https://example/landscape")
        probe_dimensions.assert_not_called()
        save_cache.assert_not_called()


if __name__ == "__main__":
    unittest.main()
