from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

import scrapy

from ug_xjtvs_wy.extraction import PageExtractor
from ug_xjtvs_wy.items import XjtvsDocumentItem
from ug_xjtvs_wy.pagination import extract_pagination_urls
from ug_xjtvs_wy.site_config import load_site_rules
from ug_xjtvs_wy.url_utils import (
    build_follow_url,
    extract_follow_urls_from_scripts,
    extract_follow_urls_from_text,
    is_allowed_domain,
)


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
        spider.debug_pages_output = Path(crawler.settings.get("DEBUG_PAGES_OUTPUT_FILE", "output/ug_xjtvs_wy_debug_pages.jsonl"))
        spider.debug_pages_limit = int(crawler.settings.get("DEBUG_PAGES_OUTPUT_LIMIT", 300))
        spider._debug_pages_written = 0
        spider._debug_fp = None
        crawler.signals.connect(spider._open_debug_file, signal=scrapy.signals.spider_opened)
        crawler.signals.connect(spider._close_debug_file, signal=scrapy.signals.spider_closed)
        return spider

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.site_rules = None
        self.allowed_domains = []
        self.start_urls = []
        self.extractor = None

    def _open_debug_file(self, spider):
        self.debug_pages_output.parent.mkdir(parents=True, exist_ok=True)
        self._debug_fp = self.debug_pages_output.open("w", encoding="utf-8")

    def _close_debug_file(self, spider, reason):
        if self._debug_fp:
            self._debug_fp.close()

    def parse(self, response, **kwargs):
        response = self.extractor.force_response_encoding(response)
        if response.status != 200:
            self.crawler.stats.inc_value("pages/skipped/non_200")
            return
        if not is_allowed_domain(response.url, self.site_rules.allowed_domains):
            self.crawler.stats.inc_value("pages/skipped/disallowed_domain")
            return

        self.crawler.stats.inc_value("pages/raw_total")
        is_html_like = self._is_html_like_response(response)

        if is_html_like:
            page = self.extractor.extract_page(response)
            if page.is_article:
                self.crawler.stats.inc_value("pages/article_total")
                self.crawler.stats.inc_value("pages/kept")
                item = XjtvsDocumentItem()
                item["url"] = page.url
                item["normalized_url"] = page.normalized_url
                item["title"] = page.title
                item["publish_time"] = page.publish_time
                item["extracted_text"] = page.extracted_text
                item["cleaned_text"] = page.cleaned_text
                yield item
            else:
                reason = page.reject_reason or "unknown"
                self.crawler.stats.inc_value(f"pages/rejected/{reason}")
            self._log_debug_page(page)
        else:
            self.crawler.stats.inc_value("pages/non_html_total")

        script_texts = response.css("script::text").getall() if is_html_like else []
        pagination_urls = extract_pagination_urls(response.url, script_texts) if is_html_like else set()
        next_urls: set[str] = set()

        if is_html_like:
            for href in response.css("a::attr(href)").getall():
                next_url = build_follow_url(response.url, href, self.site_rules)
                if next_url:
                    next_urls.add(next_url)

            next_urls.update(extract_follow_urls_from_scripts(response.url, script_texts, self.site_rules))

            app_json_texts = response.css("script[type='application/json']::text").getall()
            for txt in app_json_texts:
                next_urls.update(extract_follow_urls_from_text(response.url, txt, self.site_rules))

        next_urls.update(extract_follow_urls_from_text(response.url, response.text, self.site_rules))

        for next_url in sorted(pagination_urls):
            yield response.follow(next_url, callback=self.parse, priority=10)

        follow_urls = sorted(next_urls.difference(pagination_urls))
        self.crawler.stats.inc_value("links/follow_extracted_total", len(follow_urls))
        self.crawler.stats.inc_value(f"links/follow_extracted_by_page/{min(len(follow_urls), 20)}")
        if response.url in self.start_urls:
            self.logger.info("Seed %s extracted %d follow links", response.url, len(follow_urls))
            self.crawler.stats.inc_value("links/from_seed_total", len(follow_urls))

        for next_url in follow_urls:
            yield response.follow(next_url, callback=self.parse)

    def _log_debug_page(self, page):
        if not self._debug_fp or self._debug_pages_written >= self.debug_pages_limit:
            return
        payload = {
            "url": page.url,
            "title": page.title,
            "is_article": page.is_article,
            "content_selector": page.content_selector,
            "text_length": page.text_length,
            "uyghur_letters": page.uyghur_letters,
            "text_lines": page.text_lines,
            "reject_reason": page.reject_reason,
        }
        self._debug_fp.write(json.dumps(payload, ensure_ascii=False) + "\n")
        self._debug_pages_written += 1

    def _is_html_like_response(self, response) -> bool:
        content_type = response.headers.get(b"Content-Type", b"").decode("latin-1", errors="ignore").lower()
        if "html" in content_type:
            return True
        path = (urlparse(response.url).path or "").lower()
        if path.endswith((".html", ".htm", ".shtml")) or path == "/" or path.endswith("/"):
            return True
        return response.text.lstrip().startswith("<")
