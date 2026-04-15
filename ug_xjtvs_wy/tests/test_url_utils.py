import unittest

from ug_xjtvs_wy.site_config import load_site_rules
from ug_xjtvs_wy.url_utils import is_likely_article_url, build_follow_url


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
