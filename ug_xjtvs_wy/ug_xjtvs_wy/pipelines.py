from __future__ import annotations

import json
from pathlib import Path

from scrapy.exceptions import DropItem

from ug_xjtvs_wy.dedup import Deduplicator


class CorpusPipeline:
    def __init__(self, output_path: str, stats_output_path: str, near_duplicate_hamming_distance: int = 6):
        self.output_path = Path(output_path)
        self.stats_output_path = Path(stats_output_path)
        self.output_fp = None
        self.dedup = Deduplicator(near_duplicate_hamming_distance=near_duplicate_hamming_distance)
        self.stats = {
            "kept": 0,
            "dropped_duplicate_url": 0,
            "dropped_duplicate_text_exact": 0,
            "dropped_duplicate_text_near": 0,
        }

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            output_path=crawler.settings.get("OUTPUT_FILE"),
            stats_output_path=crawler.settings.get("STATS_OUTPUT_FILE"),
            near_duplicate_hamming_distance=int(crawler.settings.get("NEAR_DUPLICATE_HAMMING_DISTANCE", 6)),
        )

    def open_spider(self, spider):
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.stats_output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_fp = self.output_path.open("a", encoding="utf-8")

    def close_spider(self, spider):
        if self.output_fp:
            self.output_fp.close()
        self.stats_output_path.write_text(json.dumps(self.stats, ensure_ascii=False, indent=2), encoding="utf-8")

    def process_item(self, item, spider):
        decision = self.dedup.check(item["normalized_url"], item.get("cleaned_text", ""))
        if not decision.keep:
            key = f"dropped_{decision.reason}"
            if key in self.stats:
                self.stats[key] += 1
            raise DropItem(decision.reason)

        self.stats["kept"] += 1
        self.output_fp.write(json.dumps(dict(item), ensure_ascii=False) + "\n")
        return item
