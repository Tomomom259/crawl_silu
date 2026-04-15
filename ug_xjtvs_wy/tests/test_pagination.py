import unittest

from ug_xjtvs_wy.pagination import extract_pagination_urls


class TestPagination(unittest.TestCase):
    def test_extract_from_script(self):
        scripts = ["var html = pageHtml(12, '/news/index_', '.html'); var currentPage=3;"]
        urls = extract_pagination_urls("https://wy.xjtvs.com.cn/news/index.html", scripts)
        self.assertIn("https://wy.xjtvs.com.cn/news/index_1.html", urls)
        self.assertIn("https://wy.xjtvs.com.cn/news/index_2.html", urls)
