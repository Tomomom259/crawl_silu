from __future__ import annotations

from urllib.parse import urlparse

import scrapy

from ug_xjtvs_wy.extraction import PageExtractor
from ug_xjtvs_wy.items import XjtvsDocumentItem
from ug_xjtvs_wy.pagination import extract_pagination_urls
from ug_xjtvs_wy.site_config import load_site_rules
from ug_xjtvs_wy.url_utils import build_follow_url, extract_follow_urls_from_scripts, is_allowed_domain


class XjtvsWyUyghurSpider(scrapy.Spider):
    name = "xjtvs_wy_uyghur"

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        config_path = kwargs.get("site_rules_path") or crawler.settings.get("SITE_RULES_PATH")
        spider.site_rules = load_site_rules(config_path)
        spider.allowed_domains = list(spider.site_rules.allowed_domains)
        spider.start_urls = list(spider.site_rules.seed_urls)
        spider.extractor = PageExtractor(spider.site_rules)
        return spider

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.site_rules = None
        self.allowed_domains = []
        self.start_urls = []
        self.extractor = None

    def parse(self, response, **kwargs):
        response = self.extractor.force_response_encoding(response)
        if response.status != 200:
            return
        if not is_allowed_domain(response.url, self.site_rules.allowed_domains):
            return
        if not self._is_html_like_response(response):
            return

        self.crawler.stats.inc_value("pages/raw_total")
        page = self.extractor.extract_page(response)
        if page.is_article:
            self.crawler.stats.inc_value("pages/article_total")
            item = XjtvsDocumentItem()
            item["url"] = page.url
            item["normalized_url"] = page.normalized_url
            item["title"] = page.title
            item["publish_time"] = page.publish_time
            item["extracted_text"] = page.extracted_text
            item["cleaned_text"] = page.cleaned_text
            yield item

        script_texts = response.css("script::text").getall()
        pagination_urls = extract_pagination_urls(response.url, script_texts)
        next_urls: set[str] = set()

        for href in response.css("a::attr(href)").getall():
            next_url = build_follow_url(response.url, href, self.site_rules)
            if next_url:
                next_urls.add(next_url)

        next_urls.update(extract_follow_urls_from_scripts(response.url, script_texts, self.site_rules))

        for next_url in sorted(pagination_urls):
            yield response.follow(next_url, callback=self.parse, priority=10)

        for next_url in sorted(next_urls.difference(pagination_urls)):
            yield response.follow(next_url, callback=self.parse)

    def _is_html_like_response(self, response) -> bool:
        content_type = response.headers.get(b"Content-Type", b"").decode("latin-1", errors="ignore").lower()
        if "html" in content_type:
            return True
        path = (urlparse(response.url).path or "").lower()
        if path.endswith((".html", ".htm", ".shtml")) or path == "/" or path.endswith("/"):
            return True
        return response.text.lstrip().startswith("<")
