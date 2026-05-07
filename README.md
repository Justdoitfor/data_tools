# 招投标信息自动化采集工具

这是一个基于 Python 编写的自动化招投标信息采集脚本工具。工具支持从多个真实招投标信息平台同步采集（当前内置：中国政府采购网 CCGP、全国公共资源交易平台 GGZY），并将数据统一落库去重后导出 CSV。

## 功能特性

- **多字段全覆盖**：支持提取包含来源、项目分类、项目阶段、项目名称、发布时间、招标人、招标代理机构及其联系方式、中标人及联系方式、中标金额、项目地点、招标文件链接等 **20 个关键业务字段**。
- **无关键词全网采集**：支持按指定关键词搜索，或不填关键词直接拉取全网最新公开的招投标信息。
- **深度信息下探**：针对结果性或变更性公告，脚本会自动进入公告详情页进行深度解析，使用正则表达式智能提取招标人及代理机构的联系人与电话、计划时间等数据。
- **断点续跑与去重**：默认写入 SQLite（按 `来源 + URL` 去重），可中断后继续跑，不重复抓取已落库的数据。
- **两阶段采集**：先采集列表入库（只抓标题/时间/URL），再单独批量补全详情页正文与联系方式字段，降低对详情页的压力。
- **限速与退避**：内置随机延时、重试与频控检测（出现“频繁访问”会指数退避），用于降低触发频率限制概率。

## 环境要求

- Python 3.6 或以上版本

## 安装依赖

在使用本工具前，请确保安装以下第三方库：

```bash
pip install requests beautifulsoup4
```

## 使用方法

脚本基于命令行参数运行。直接在终端执行 `python bidding_spider.py -h` 查看完整帮助。

### 子命令

#### 1) crawl：采集并落库（SQLite）

必填参数：
- `--start-date` / `--end-date`：日期范围（YYYY-MM-DD）

常用参数：
- `--sources`：`ccgp` 或 `ccgp,ggzy`
- `-k/--keyword`：可选关键词，不填表示尽量全量（平台可能仍有自身限制）
- `--db`：SQLite 路径，默认 `data/tenders.db`
- `--max-pages`：每一天最多翻页数
- `--detail`：是否在同一次运行中补全详情页
- `--detail-limit`：每次最多补全多少条详情
- `--min-delay` / `--max-delay`：每次请求的随机延时范围（秒）
- `--timeout` / `--retries` / `--backoff-base`：超时、重试与指数退避设置

#### 2) export：从 SQLite 导出 CSV

- `--db`：SQLite 路径
- `-o/--output`：导出 CSV 文件名
- `--sources`：可选过滤来源（如 `ccgp`）
- `--start-date` / `--end-date`：可选过滤日期范围（YYYY-MM-DD）

#### 3) run：兼容旧用法（采集并直接导出 CSV）

保留了早期示例的行为，但底层同样会写入 SQLite 并去重。

### 使用示例

1. **采集 2025 年（建议按月/按周分片跑）**

   以 2025 年 1 月为例，先采集列表落库：

   ```bash
   python bidding_spider.py crawl --sources ccgp,ggzy --start-date 2025-01-01 --end-date 2025-01-31 --max-pages 200 --db data/tenders.db --min-delay 2 --max-delay 6 --retries 3 --backoff-base 30
   ```

   再分批补全详情页（多次执行直到补全完毕）：

   ```bash
   python bidding_spider.py crawl --sources ccgp,ggzy --start-date 2025-01-01 --end-date 2025-01-31 --detail --detail-limit 2000 --db data/tenders.db --min-delay 2 --max-delay 8 --retries 3 --backoff-base 30
   ```

   最后导出 CSV：

   ```bash
   python bidding_spider.py export --db data/tenders.db -o tenders_2025_01.csv --start-date 2025-01-01 --end-date 2025-01-31
   ```

2. **按关键词采集（列表+详情）**

   ```bash
   python bidding_spider.py crawl --sources ccgp -k "软件" --start-date 2026-04-01 --end-date 2026-04-07 --max-pages 50 --detail --detail-limit 500 --db data/tenders.db
   python bidding_spider.py export --db data/tenders.db -o software.csv --start-date 2026-04-01 --end-date 2026-04-07
   ```

3. **兼容旧用法（run）**

   ```bash
   python bidding_spider.py run -k "工程" -s "2026-04-01" -e "2026-04-28" -p 2 -o engineering.csv --db data/tenders.db
   ```

## 输出说明

导出的 CSV 文件采用 `utf-8-sig` 编码格式（带有 BOM 头），直接使用 Microsoft Excel 打开不会出现中文乱码问题。

包含的字段列表：
- 来源、项目分类、项目阶段、项目名称、发布时间
- 招标人、变更时间、计划招标时间、招标人联系人、招标人联系方式
- 招标代理机构、招标代理机构联系人、招标代理机构联系方式
- 中标人、中标人联系人、中标人联系方式、中标金额（元）
- 招标内容、项目地点、招标文件

## 免责声明

本工具仅供学习、研究及内部测试使用，抓取数据时请严格遵守目标网站的 `robots.txt` 协议及相关法律法规。请勿进行高并发恶意爬取，以免对目标服务器造成影响。
