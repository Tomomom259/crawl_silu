from __future__ import annotations

import re
from urllib.parse import urlparse

PAGE_HINT_RE = re.compile(r"index_(\d+)\.html", flags=re.I)
GENERIC_PAGE_RE = re.compile(r"(?:page|pageno|currentPage)\s*[:=]\s*(\d+)", flags=re.I)
PAGE_HTML_RE = re.compile(r"pageHtml\(\s*(\d+)", flags=re.I)


def extract_pagination_urls(current_url: str, script_texts: list[str]) -> set[str]:
    out: set[str] = set()
    parsed = urlparse(current_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    prefix = parsed.path.rsplit("/", 1)[0]

    for txt in script_texts:
        if not txt:
            continue
        for m in PAGE_HINT_RE.findall(txt):
            try:
                idx = int(m)
            except ValueError:
                continue
            for i in range(1, min(idx + 1, 50)):
                out.add(f"{base}{prefix}/index_{i}.html")
        for m in PAGE_HTML_RE.findall(txt):
            try:
                idx = int(m)
            except ValueError:
                continue
            for i in range(1, min(idx + 1, 50)):
                out.add(f"{base}{prefix}/index_{i}.html")

        for m in GENERIC_PAGE_RE.findall(txt):
            try:
                idx = int(m)
            except ValueError:
                continue
            if idx > 1:
                out.add(f"{base}{prefix}/index_{idx}.html")
    return out
