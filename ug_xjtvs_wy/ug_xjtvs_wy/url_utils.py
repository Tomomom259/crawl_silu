from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse, urlunparse

STATIC_SUFFIXES = (
    ".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg", ".ico",
    ".mp4", ".m3u8", ".mp3", ".wav", ".flv", ".avi", ".mov",
    ".css", ".js", ".json", ".xml", ".woff", ".woff2", ".ttf", ".map",
    ".zip", ".rar", ".7z", ".pdf",
)

SCRIPT_URL_RE = re.compile(r"['\"](/[^'\"\s]+(?:\.html?|/)[^'\"]*)['\"]")


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
    href = href.strip()
    if not href or href.startswith(("javascript:", "mailto:", "tel:", "#")):
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


def extract_follow_urls_from_scripts(base_url: str, script_texts: list[str], site_rules) -> set[str]:
    out: set[str] = set()
    for txt in script_texts:
        if not txt:
            continue
        for m in SCRIPT_URL_RE.findall(txt):
            next_url = build_follow_url(base_url, m, site_rules)
            if next_url:
                out.add(next_url)
    return out
