from __future__ import annotations

from dataclasses import dataclass

try:
    from lxml import html as lxml_html
except Exception:
    lxml_html = None

from ug_xjtvs_wy.site_config import SiteRules
from ug_xjtvs_wy.text_utils import (
    build_fallback_title,
    clean_article_text,
    clean_title,
    count_uyghur_letters,
    extract_publish_time,
    normalize_inline_whitespace,
)
from ug_xjtvs_wy.url_utils import is_likely_article_url, normalize_url


@dataclass
class PageExtractionResult:
    url: str
    normalized_url: str
    title: str
    publish_time: str
    extracted_text: str
    cleaned_text: str
    is_article: bool


class PageExtractor:
    def __init__(self, site_rules: SiteRules) -> None:
        self.site_rules = site_rules

    def force_response_encoding(self, response):
        if not self.site_rules.force_response_encoding:
            return response
        if response.encoding and response.encoding.lower() == self.site_rules.force_response_encoding.lower():
            return response
        return response.replace(body=response.body, encoding=self.site_rules.force_response_encoding)

    def extract_page(self, response) -> PageExtractionResult:
        normalized = normalize_url(response.url)
        doc = self._build_document(response.text)
        title = ""
        publish_time = ""
        extracted_text = ""
        cleaned_text = ""
        has_content_node = False

        if doc is not None:
            self._remove_noise_nodes(doc)
            title = clean_title(self._first_value(response, self.site_rules.extraction.title_selectors))
            publish_time = extract_publish_time(*self._all_values(response, self.site_rules.extraction.publish_time_selectors))
            content_node = self._select_content_node(doc)
            has_content_node = content_node is not None
            extracted_text = self._extract_text(content_node)
            cleaned_text = clean_article_text(extracted_text, self.site_rules.drop_text_patterns)

        if not title:
            title = build_fallback_title(cleaned_text or extracted_text)

        is_article = self._is_article_page(response.url, title, cleaned_text, has_content_node)
        return PageExtractionResult(
            url=response.url,
            normalized_url=normalized,
            title=title,
            publish_time=publish_time,
            extracted_text=extracted_text,
            cleaned_text=cleaned_text,
            is_article=is_article,
        )

    def _build_document(self, raw_html: str):
        if not raw_html:
            return None
        if lxml_html is None:
            return None
        try:
            return lxml_html.fromstring(raw_html)
        except (ValueError, TypeError):
            return None

    def _all_values(self, response, selectors: tuple[str, ...]) -> list[str]:
        values: list[str] = []
        for selector in selectors:
            try:
                extracted = response.css(selector).getall()
            except ValueError:
                extracted = []
            values.extend(v for v in extracted if v)
        return values

    def _first_value(self, response, selectors: tuple[str, ...]) -> str:
        for v in self._all_values(response, selectors):
            n = normalize_inline_whitespace(v)
            if n:
                return n
        return ""

    def _remove_noise_nodes(self, document) -> None:
        for selector in self.site_rules.extraction.remove_selectors:
            try:
                nodes = document.cssselect(selector)
            except Exception:
                continue
            for n in nodes:
                parent = n.getparent()
                if parent is not None:
                    parent.remove(n)

    def _select_content_node(self, document):
        nodes = self._collect_nodes(document, self.site_rules.extraction.content_selectors)
        best = self._pick_best_node(nodes)
        if best is not None:
            return best
        generic = document.xpath("//article | //main | //section[count(.//p)>=2] | //div[count(.//p)>=2]")
        return self._pick_best_node(generic)

    def _collect_nodes(self, document, selectors: tuple[str, ...]) -> list:
        out = []
        seen = set()
        for selector in selectors:
            try:
                nodes = document.cssselect(selector)
            except Exception:
                nodes = []
            for n in nodes:
                nid = id(n)
                if nid not in seen:
                    seen.add(nid)
                    out.append(n)
        return out

    def _pick_best_node(self, nodes: list):
        best = None
        best_score = 0
        for node in nodes:
            score = count_uyghur_letters(self._extract_text(node))
            if score > best_score:
                best = node
                best_score = score
        return best

    def _extract_text(self, node) -> str:
        if node is None:
            return ""
        paras: list[str] = []
        for selector in self.site_rules.extraction.paragraph_selectors:
            try:
                texts = node.cssselect(selector)
            except Exception:
                texts = []
            for t in texts:
                txt = normalize_inline_whitespace(t.text_content())
                if txt:
                    paras.append(txt)
        if paras:
            return "\n".join(paras)
        return normalize_inline_whitespace(node.text_content())

    def _is_article_page(self, url: str, title: str, cleaned_text: str, has_content_node: bool) -> bool:
        if not has_content_node:
            return False
        if not is_likely_article_url(url, self.site_rules):
            return False
        low_title = title.lower()
        if any(k.lower() in low_title for k in self.site_rules.deny_title_keywords):
            return False
        if count_uyghur_letters(cleaned_text) < self.site_rules.min_uyghur_letters:
            return False
        lines = [ln for ln in cleaned_text.split("\n") if ln.strip()]
        if len(lines) < 2:
            return False
        return True
