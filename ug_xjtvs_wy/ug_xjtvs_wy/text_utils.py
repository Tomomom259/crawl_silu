from __future__ import annotations

import re
from datetime import datetime

UYGHUR_LETTER_RE = re.compile(r"[\u0621-\u064A\u067E\u0686\u0698\u06AD\u06AF\u06BE\u06C6\u06C7\u06C8\u06CB\u06D0\u06D5]")
INLINE_WS_RE = re.compile(r"\s+")


def normalize_inline_whitespace(text: str) -> str:
    if not text:
        return ""
    return INLINE_WS_RE.sub(" ", text.replace("\u00a0", " ")).strip()


def count_uyghur_letters(text: str) -> int:
    if not text:
        return 0
    return len(UYGHUR_LETTER_RE.findall(text))


def clean_title(text: str) -> str:
    return normalize_inline_whitespace(text)


def clean_article_text(text: str, drop_patterns: tuple[str, ...]) -> str:
    normalized = normalize_inline_whitespace(text)
    if not normalized:
        return ""
    lines = [normalize_inline_whitespace(line) for line in normalized.split("\n")]
    out: list[str] = []
    for line in lines:
        if not line:
            continue
        lowered = line.lower()
        if any(pat and re.search(pat, lowered, flags=re.I) for pat in drop_patterns):
            continue
        out.append(line)
    return "\n".join(out)


def extract_publish_time(*candidates: str) -> str:
    text = " ".join(c for c in candidates if c)
    if not text:
        return ""
    # common numeric forms
    for pat in [
        r"(20\d{2}[-/.年]\s*\d{1,2}[-/.月]\s*\d{1,2}(?:日)?)",
        r"(20\d{2}\s*[-/]\s*\d{1,2}\s*[-/]\s*\d{1,2})",
        r"(20\d{2}年\d{1,2}月\d{1,2}日)",
    ]:
        m = re.search(pat, text)
        if m:
            return normalize_inline_whitespace(m.group(1))
    return normalize_inline_whitespace(text)[:64]


def build_fallback_title(text: str) -> str:
    if not text:
        return ""
    first = normalize_inline_whitespace(text).split(" ")
    return " ".join(first[:16])
