from pathlib import Path
import unittest

from ug_xjtvs_wy.site_config import load_site_rules


class TestSiteConfig(unittest.TestCase):
    def test_load_site_rules(self):
        rules = load_site_rules(str(Path("config/site_rules.json")))
        self.assertIn("wy.xjtvs.com.cn", rules.allowed_domains)
        self.assertGreaterEqual(rules.min_uyghur_letters, 100)
        self.assertTrue(rules.extraction.title_selectors)
