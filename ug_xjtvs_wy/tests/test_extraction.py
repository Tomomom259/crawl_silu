import importlib.util
import unittest

SCRAPY_OK = importlib.util.find_spec("scrapy") is not None
LXML_OK = importlib.util.find_spec("lxml") is not None

if SCRAPY_OK:
    from scrapy.http import HtmlResponse, Request

from ug_xjtvs_wy.extraction import PageExtractor
from ug_xjtvs_wy.site_config import load_site_rules


ARTICLE_HTML = """
<html><head><title>示例新闻</title></head>
<body>
<h1>شىنجاڭ خەۋەرلىرى بۈگۈن</h1>
<div class='publish-time'>2025-09-22 10:00</div>
<div class='article-content'>
  <p>بۇ بىر سىناق خەۋەرنىڭ بىرىنچى ئابزاسى بولۇپ، يېتەرلىك تېكىست مىقدارى بىلەن تەمىنلەيدۇ.</p>
  <p>بۇ ئىككىنچى ئابزاس، مەزمۇننىڭ داۋامى، سۈزۈك ۋە چۈشىنىشلىك بايان بىلەن يېزىلغان.</p>
  <div class='share'>分享到</div>
</div>
</body></html>
"""

IMAGE_ONLY_HTML = """
<html><body>
<h1>سۈرەتلىك خەۋەر</h1>
<div class='article-content'><img src='a.jpg'/></div>
</body></html>
"""

CONTENT_FIRST_HTML = """
<html><body>
<h1>تېما ئۇچۇرى</h1>
<div class='detail-content'>
  <p>بۇ بەتتە URL ئاددىي بولسىمۇ، مەزمۇن بۆلىكى ئېنىق بولۇپ، يېتەرلىك ئۇيغۇرچە ھەرپلەر بار.</p>
  <p>ئىككىنچى قۇر تېكىستى مەزمۇننىڭ داۋامى بولۇپ، ماقالە دەپ تونۇشقا ياردەم بېرىدۇ.</p>
</div>
</body></html>
"""


@unittest.skipUnless(SCRAPY_OK and LXML_OK, "requires scrapy and lxml")
class TestExtraction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = load_site_rules("config/site_rules.json")
        cls.extractor = PageExtractor(cls.rules)

    def _response(self, url: str, body: str):
        req = Request(url=url)
        return HtmlResponse(url=url, request=req, body=body.encode("utf-8"), encoding="utf-8")

    def test_article_extract(self):
        res = self._response("https://wy.xjtvs.com.cn/news/2025/09/22/1.html", ARTICLE_HTML)
        page = self.extractor.extract_page(res)
        self.assertTrue(page.is_article)
        self.assertIn("شىنجاڭ", page.title)
        self.assertIn("بىرىنچى", page.cleaned_text)

    def test_image_only_not_article(self):
        res = self._response("https://wy.xjtvs.com.cn/photo/1.html", IMAGE_ONLY_HTML)
        page = self.extractor.extract_page(res)
        self.assertFalse(page.is_article)

    def test_content_first_article_without_allowlist_url(self):
        res = self._response("https://wy.xjtvs.com.cn/channel/topic-page", CONTENT_FIRST_HTML)
        page = self.extractor.extract_page(res)
        self.assertTrue(page.is_article)
        self.assertGreaterEqual(page.uyghur_letters, 40)
