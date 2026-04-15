from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExtractionRules:
    title_selectors: tuple[str, ...]
    publish_time_selectors: tuple[str, ...]
    content_selectors: tuple[str, ...]
    paragraph_selectors: tuple[str, ...]
    remove_selectors: tuple[str, ...]


@dataclass(frozen=True)
class SiteRules:
    seed_urls: tuple[str, ...]
    allowed_domains: tuple[str, ...]
    force_response_encoding: str
    min_uyghur_letters: int
    near_duplicate_hamming_distance: int
    simhash_band_count: int
    skip_crawl_url_patterns: tuple[str, ...]
    allow_article_url_patterns: tuple[str, ...]
    deny_article_url_patterns: tuple[str, ...]
    deny_title_keywords: tuple[str, ...]
    drop_text_patterns: tuple[str, ...]
    extraction: ExtractionRules


def _t(values) -> tuple[str, ...]:
    return tuple(v for v in (values or []) if isinstance(v, str) and v.strip())


def load_site_rules(path: str | None) -> SiteRules:
    config_path = Path(path or "config/site_rules.json")
    data = json.loads(config_path.read_text(encoding="utf-8"))
    extraction_data = data.get("extraction", {})
    extraction = ExtractionRules(
        title_selectors=_t(extraction_data.get("title_selectors")),
        publish_time_selectors=_t(extraction_data.get("publish_time_selectors")),
        content_selectors=_t(extraction_data.get("content_selectors")),
        paragraph_selectors=_t(extraction_data.get("paragraph_selectors")),
        remove_selectors=_t(extraction_data.get("remove_selectors")),
    )
    return SiteRules(
        seed_urls=_t(data.get("seed_urls")),
        allowed_domains=_t(data.get("allowed_domains")),
        force_response_encoding=data.get("force_response_encoding", ""),
        min_uyghur_letters=int(data.get("min_uyghur_letters", 60)),
        near_duplicate_hamming_distance=int(data.get("near_duplicate_hamming_distance", 6)),
        simhash_band_count=int(data.get("simhash_band_count", 8)),
        skip_crawl_url_patterns=_t(data.get("skip_crawl_url_patterns")),
        allow_article_url_patterns=_t(data.get("allow_article_url_patterns")),
        deny_article_url_patterns=_t(data.get("deny_article_url_patterns")),
        deny_title_keywords=_t(data.get("deny_title_keywords")),
        drop_text_patterns=_t(data.get("drop_text_patterns")),
        extraction=extraction,
    )
