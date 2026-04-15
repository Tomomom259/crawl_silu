import unittest

from ug_xjtvs_wy.site_config import load_site_rules
from ug_xjtvs_wy.url_utils import (
    build_follow_url,
    extract_follow_urls_from_scripts,
    extract_follow_urls_from_text,
    is_likely_article_url,
)


class TestUrlUtils(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = load_site_rules("config/site_rules.json")

    def test_article_url_match(self):
        self.assertTrue(is_likely_article_url("https://wy.xjtvs.com.cn/news/2025/09/21/12345.html", self.rules))

    def test_non_article_url(self):
        self.assertFalse(is_likely_article_url("https://wy.xjtvs.com.cn/video/123", self.rules))

    def test_skip_media_resource(self):
        self.assertIsNone(build_follow_url("https://wy.xjtvs.com.cn/", "/assets/a.mp4", self.rules))

    def test_extract_urls_from_window_state(self):
        scripts = [
            "window.__INITIAL_STATE__={\"items\":[{\"url\":\"/news/2026/01/01/1001.html\"}]};"
        ]
        found = extract_follow_urls_from_scripts("https://wy.xjtvs.com.cn/news", scripts, self.rules)
        self.assertIn("https://wy.xjtvs.com.cn/news/2026/01/01/1001.html", found)

    def test_extract_urls_from_json_text(self):
        text = '{"list":[{"link":"/xinjiang/2026/02/03/abc.html"}]}'
        found = extract_follow_urls_from_text("https://wy.xjtvs.com.cn/", text, self.rules)
        self.assertIn("https://wy.xjtvs.com.cn/xinjiang/2026/02/03/abc.html", found)
