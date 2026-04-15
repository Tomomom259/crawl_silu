from __future__ import annotations

import json
import re
from urllib.parse import urljoin, urlparse, urlunparse

STATIC_SUFFIXES = (
    ".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg", ".ico",
    ".mp4", ".m3u8", ".mp3", ".wav", ".flv", ".avi", ".mov",
    ".css", ".js", ".xml", ".woff", ".woff2", ".ttf", ".map",
    ".zip", ".rar", ".7z", ".pdf",
)

SCRIPT_URL_RE = re.compile(
    r"(?P<raw>(?:https?:\\/\\/|https?://|\\/|/|\\./|\.\./|[a-zA-Z0-9_-]+/)[^'\"\s<>]{3,})"
)
WINDOW_STATE_RE = re.compile(
    r"(?:window\\.)?(?:__INITIAL_STATE__|__NEXT_DATA__|INITIAL_STATE)\\s*=\\s*(\{.*?\})\\s*;",
    flags=re.S,
)


def normalize_url(url: str) -> str:
    p = urlparse(url.strip())
    scheme = p.scheme.lower() if p.scheme else "https"
    netloc = p.netloc.lower()
    path = p.path or "/"
    if path != "/" and path.endswith("/"):
        path = path[:-1]
    return urlunparse((scheme, netloc, path, "", p.query, ""))


def is_allowed_domain(url: str, allowed_domains: tuple[str, ...]) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return any(host == d or host.endswith(f".{d}") for d in allowed_domains)


def is_static_resource_url(url: str) -> bool:
    path = (urlparse(url).path or "").lower()
    return any(path.endswith(s) for s in STATIC_SUFFIXES)


def build_follow_url(base_url: str, href: str, site_rules) -> str | None:
    if not href:
        return None
    href = href.strip().replace("\\/", "/")
    if not href or href.startswith(("javascript:", "mailto:", "tel:")):
        return None
    if href.startswith("#/"):
        href = href[1:]
    elif href.startswith("#"):
        return None

    u = urljoin(base_url, href)
    if not is_allowed_domain(u, site_rules.allowed_domains):
        return None
    nu = normalize_url(u)
    low = nu.lower()
    if is_static_resource_url(nu):
        return None
    if any(re.search(pat, low, flags=re.I) for pat in site_rules.skip_crawl_url_patterns):
        return None
    return nu


def is_likely_article_url(url: str, site_rules) -> bool:
    low = normalize_url(url).lower()
    if any(re.search(p, low, flags=re.I) for p in site_rules.deny_article_url_patterns):
        return False
    if any(re.search(p, low, flags=re.I) for p in site_rules.allow_article_url_patterns):
        return True
    return False


def _extract_urls_from_obj(value, out: set[str]) -> None:
    if isinstance(value, dict):
        for v in value.values():
            _extract_urls_from_obj(v, out)
    elif isinstance(value, list):
        for v in value:
            _extract_urls_from_obj(v, out)
    elif isinstance(value, str):
        if "/" in value or value.startswith("http"):
            out.add(value)


def extract_follow_urls_from_scripts(base_url: str, script_texts: list[str], site_rules) -> set[str]:
    out: set[str] = set()

    def add_candidate(raw_url: str):
        next_url = build_follow_url(base_url, raw_url, site_rules)
        if next_url:
            out.add(next_url)

    for txt in script_texts:
        if not txt:
            continue

        raw = txt.replace("\\/", "/")
        for m in SCRIPT_URL_RE.finditer(raw):
            add_candidate(m.group("raw").strip("\"'"))

        for jm in WINDOW_STATE_RE.findall(raw):
            try:
                obj = json.loads(jm)
            except Exception:
                continue
            json_urls: set[str] = set()
            _extract_urls_from_obj(obj, json_urls)
            for candidate in json_urls:
                add_candidate(candidate)

        if 'type="application/json"' in raw or "application/json" in raw:
            start = raw.find("{")
            end = raw.rfind("}")
            if start >= 0 and end > start:
                try:
                    obj = json.loads(raw[start : end + 1])
                except Exception:
                    obj = None
                if obj is not None:
                    json_urls: set[str] = set()
                    _extract_urls_from_obj(obj, json_urls)
                    for candidate in json_urls:
                        add_candidate(candidate)

    return out


def extract_follow_urls_from_text(base_url: str, raw_text: str, site_rules) -> set[str]:
    out: set[str] = set()
    if not raw_text:
        return out
    normalized = raw_text.replace("\\/", "/")
    for m in SCRIPT_URL_RE.finditer(normalized):
        next_url = build_follow_url(base_url, m.group("raw").strip("\"'"), site_rules)
        if next_url:
            out.add(next_url)
    return out
