# ug_xjtvs_wy

基于 Scrapy 的 `wy.xjtvs.com.cn` 维吾尔语新闻爬虫项目，整体风格对齐 `ug_guangbo`：站内递归发现、正文抽取、URL 去重、正文精确去重、近重复去重、断点续爬，输出面向大模型预训练的 `jsonl`。

## 站点特性（探测结论）

- 首页提供多个维吾尔语新闻与节目入口（如：باش بەت / خەۋەرلەر / شىنجاڭ خەۋەرلىرى / مەخسۇس پروگرامما）。
- 首页同时混有“看电视/听广播”等媒体播放入口，需强排除。
- 搜索抓取样本显示页面大量卡片化内容，文章列表与详情可能同时存在传统 HTML 路径和前端路由路径，因此规则采用“允许 + 拒绝”双层约束。
- 当前实现优先抓取 HTML 文本正文；若页面只有图片/视频，不做 OCR，直接丢弃。

## 实际文章页规律（当前规则）

> 由于站点外网访问存在环境限制，规则基于已抓取快照文本与站点命名习惯保守配置；建议先跑 smoke 再微调。

- 优先判定文章 URL 模式：
  - `/20xx/xx/xx/` 日期路径
  - `/detail` / `/article` / `/content`
  - `/news/<id>`
  - `.html`
- 强排除 URL 模式：`/live` `/video` `/audio` `/radio` `/tv` `/watch` `/listen` `/player` `/photo` `/gallery` 及媒体资源后缀。

## 默认输出

- 语料：`output/ug_xjtvs_wy_corpus.jsonl`
- 统计：`output/ug_xjtvs_wy_stats.json`
- 预览：`output/ug_xjtvs_wy_corpus.preview.txt`
- 状态库：`state/crawl_state.sqlite3`
- 断点目录：`state/job`

## 运行

```bash
cd ug_xjtvs_wy
python run_spider.py
```

带参数运行：

```bash
python run_spider.py \
  --site-rules config/site_rules.json \
  --output output/ug_xjtvs_wy_corpus.jsonl \
  --state-db state/crawl_state.sqlite3 \
  --stats-output output/ug_xjtvs_wy_stats.json \
  --jobdir state/job \
  --log-file logs/spider.log
```

## 预览

```bash
python preview_jsonl.py --limit 20
```

## 测试

```bash
python -m unittest discover -s tests -v
```

## 断点续爬

- 启用 `--jobdir state/job` 后，Scrapy 会自动保存请求队列和去重指纹。
- 重启同一命令时会从上次进度继续。

## 抽取范围声明

- 本项目仅抓取“可提取文本正文”的维吾尔语文章页。
- 图片新闻若无可用文本会跳过。
- 视频/音频/播放页默认排除。
- **不做 OCR。**
