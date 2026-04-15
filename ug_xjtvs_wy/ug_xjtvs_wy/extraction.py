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
    uyghur_letters: int
    text_length: int
    text_lines: int
    content_selector: str
    reject_reason: str


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
        selected_by = ""

        if doc is not None:
            self._remove_noise_nodes(doc)
            title = clean_title(self._first_value(response, self.site_rules.extraction.title_selectors))
            publish_time = extract_publish_time(*self._all_values(response, self.site_rules.extraction.publish_time_selectors))
            content_node, selected_by = self._select_content_node(doc)
            has_content_node = content_node is not None
            extracted_text = self._extract_text(content_node)
            cleaned_text = clean_article_text(extracted_text, self.site_rules.drop_text_patterns)

        if not title:
            title = build_fallback_title(cleaned_text or extracted_text)

        is_article, reject_reason, uyghur_letters, text_length, text_lines = self._is_article_page(
            response.url,
            title,
            cleaned_text,
            has_content_node,
        )
        return PageExtractionResult(
            url=response.url,
            normalized_url=normalized,
            title=title,
            publish_time=publish_time,
            extracted_text=extracted_text,
            cleaned_text=cleaned_text,
            is_article=is_article,
            uyghur_letters=uyghur_letters,
            text_length=text_length,
            text_lines=text_lines,
            content_selector=selected_by,
            reject_reason=reject_reason,
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
        selector_candidates = list(self.site_rules.extraction.content_selectors) + [
            ".detail",
            ".detail-content",
            ".post-content",
            ".main-content",
            ".rich-text",
            "[class*='content']",
            "[class*='article']",
            "[class*='detail']",
            "[id*='content']",
            "[id*='article']",
            "[id*='detail']",
        ]
        nodes = self._collect_nodes(document, tuple(selector_candidates))
        best = self._pick_best_node(nodes)
        if best is not None:
            return best[0], best[1]

        generic = document.xpath(
            "//article | //main | //section[count(.//p)>=2] | //div[count(.//p)>=2] "
            "| //div[contains(@class,'content') or contains(@class,'article') or contains(@class,'detail')]"
        )
        picked = self._pick_best_node([(n, "generic_xpath") for n in generic])
        if picked is not None:
            return picked[0], picked[1]
        return None, ""

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
                    out.append((n, selector))
        return out

    def _pick_best_node(self, nodes: list):
        best = None
        best_score = -1
        for node, selector in nodes:
            text = self._extract_text(node)
            uy_letters = count_uyghur_letters(text)
            text_len = len(text)
            p_count = len([ln for ln in text.split("\n") if ln.strip()])
            score = uy_letters * 3 + text_len + p_count * 20
            if score > best_score:
                best = (node, selector)
                best_score = score
        return best

    def _extract_text(self, node) -> str:
        if node is None:
            return ""
        paras: list[str] = []
        paragraph_selectors = list(self.site_rules.extraction.paragraph_selectors) + [
            "p",
            "div > p",
            "section p",
            "article p",
            "li",
            "div[class*='paragraph']",
            "div[class*='text']",
        ]
        for selector in paragraph_selectors:
            try:
                texts = node.cssselect(selector)
            except Exception:
                texts = []
            for t in texts:
                txt = normalize_inline_whitespace(t.text_content())
                if txt and txt not in paras:
                    paras.append(txt)
        if paras:
            return "\n".join(paras)
        return normalize_inline_whitespace(node.text_content())

    def _is_article_page(self, url: str, title: str, cleaned_text: str, has_content_node: bool):
        text = cleaned_text.strip()
        text_length = len(text)
        uyghur_letters = count_uyghur_letters(text)
        lines = [ln for ln in text.split("\n") if ln.strip()]
        line_count = len(lines)

        if not has_content_node:
            return False, "no_content_node", uyghur_letters, text_length, line_count

        low_title = title.lower()
        if any(k.lower() in low_title for k in self.site_rules.deny_title_keywords):
            return False, "title_deny_keyword", uyghur_letters, text_length, line_count

        url_likely_article = is_likely_article_url(url, self.site_rules)
        min_letters = max(20, self.site_rules.min_uyghur_letters)
        relaxed_min_letters = max(20, min_letters // 2)

        if text_length < 60 or line_count < 2:
            return False, "text_too_short", uyghur_letters, text_length, line_count

        if uyghur_letters >= min_letters:
            return True, "", uyghur_letters, text_length, line_count

        content_first_pass = uyghur_letters >= relaxed_min_letters and text_length >= 120 and line_count >= 2
        if content_first_pass:
            return True, "", uyghur_letters, text_length, line_count

        if url_likely_article and uyghur_letters >= max(18, relaxed_min_letters - 10) and text_length >= 80:
            return True, "", uyghur_letters, text_length, line_count

        if not url_likely_article:
            return False, "url_not_article_and_content_weak", uyghur_letters, text_length, line_count
        return False, "uyghur_letters_too_few", uyghur_letters, text_length, line_count
