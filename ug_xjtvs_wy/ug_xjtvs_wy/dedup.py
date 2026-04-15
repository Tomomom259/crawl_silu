from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

TOKEN_RE = re.compile(r"[\u0600-\u06FF\w]{2,}")


def _hash64(text: str) -> int:
    h = hashlib.blake2b(text.encode("utf-8", errors="ignore"), digest_size=8).digest()
    return int.from_bytes(h, "big", signed=False)


def simhash(text: str) -> int:
    weights = [0] * 64
    for token in TOKEN_RE.findall(text.lower()):
        hv = _hash64(token)
        for i in range(64):
            weights[i] += 1 if ((hv >> i) & 1) else -1
    fingerprint = 0
    for i, w in enumerate(weights):
        if w > 0:
            fingerprint |= (1 << i)
    return fingerprint


def hamming_distance(a: int, b: int) -> int:
    return (a ^ b).bit_count()


@dataclass
class DedupDecision:
    keep: bool
    reason: str


class Deduplicator:
    def __init__(self, near_duplicate_hamming_distance: int = 6) -> None:
        self.url_seen: set[str] = set()
        self.text_seen: set[str] = set()
        self.simhash_seen: list[int] = []
        self.threshold = near_duplicate_hamming_distance

    def check(self, normalized_url: str, cleaned_text: str) -> DedupDecision:
        if normalized_url in self.url_seen:
            return DedupDecision(False, "duplicate_url")

        text_digest = hashlib.sha1(cleaned_text.encode("utf-8", errors="ignore")).hexdigest()
        if text_digest in self.text_seen:
            return DedupDecision(False, "duplicate_text_exact")

        fp = simhash(cleaned_text)
        for old_fp in self.simhash_seen:
            if hamming_distance(fp, old_fp) <= self.threshold:
                return DedupDecision(False, "duplicate_text_near")

        self.url_seen.add(normalized_url)
        self.text_seen.add(text_digest)
        self.simhash_seen.append(fp)
        return DedupDecision(True, "keep")
