BOT_NAME = "ug_xjtvs_wy"

SPIDER_MODULES = ["ug_xjtvs_wy.spiders"]
NEWSPIDER_MODULE = "ug_xjtvs_wy.spiders"

ROBOTSTXT_OBEY = False
CONCURRENT_REQUESTS = 8
DOWNLOAD_TIMEOUT = 20

SITE_RULES_PATH = "config/site_rules.json"
OUTPUT_FILE = "output/ug_xjtvs_wy_corpus.jsonl"
STATS_OUTPUT_FILE = "output/ug_xjtvs_wy_stats.json"
STATE_DB = "state/crawl_state.sqlite3"
JOBDIR = "state/job"
LOG_FILE = "logs/spider.log"
NEAR_DUPLICATE_HAMMING_DISTANCE = 6

ITEM_PIPELINES = {
    "ug_xjtvs_wy.pipelines.CorpusPipeline": 300,
}

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

DEBUG_PAGES_OUTPUT_FILE = "output/ug_xjtvs_wy_debug_pages.jsonl"
DEBUG_PAGES_OUTPUT_LIMIT = 300
