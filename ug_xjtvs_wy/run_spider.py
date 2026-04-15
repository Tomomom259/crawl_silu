from __future__ import annotations

import argparse
import os

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


def parse_args():
    p = argparse.ArgumentParser(description="Run xjtvs uyghur scrapy spider")
    p.add_argument("--site-rules", default="config/site_rules.json")
    p.add_argument("--output", default="output/ug_xjtvs_wy_corpus.jsonl")
    p.add_argument("--state-db", default="state/crawl_state.sqlite3")
    p.add_argument("--stats-output", default="output/ug_xjtvs_wy_stats.json")
    p.add_argument("--jobdir", default="state/job")
    p.add_argument("--log-file", default="logs/spider.log")
    p.add_argument("--obey-robots", action="store_true")
    return p.parse_args()


def ensure_parent(path: str):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def main():
    args = parse_args()
    for p in [args.output, args.state_db, args.stats_output, args.log_file]:
        ensure_parent(p)
    os.makedirs(args.jobdir, exist_ok=True)

    settings = get_project_settings()
    settings.set("SITE_RULES_PATH", args.site_rules, priority="cmdline")
    settings.set("OUTPUT_FILE", args.output, priority="cmdline")
    settings.set("STATE_DB", args.state_db, priority="cmdline")
    settings.set("STATS_OUTPUT_FILE", args.stats_output, priority="cmdline")
    settings.set("JOBDIR", args.jobdir, priority="cmdline")
    settings.set("LOG_FILE", args.log_file, priority="cmdline")
    settings.set("ROBOTSTXT_OBEY", bool(args.obey_robots), priority="cmdline")

    process = CrawlerProcess(settings)
    process.crawl("xjtvs_wy_uyghur", site_rules_path=args.site_rules)
    process.start()


if __name__ == "__main__":
    main()
