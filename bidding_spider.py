import argparse
import csv
import datetime as dt
import os
import random
import re
import sqlite3
import time
import urllib.parse

import requests
from bs4 import BeautifulSoup


FIELDS = [
    "来源",
    "项目分类",
    "项目阶段",
    "项目名称",
    "发布时间",
    "招标人",
    "变更时间",
    "计划招标时间",
    "招标人联系人",
    "招标人联系方式",
    "招标代理机构",
    "招标代理机构联系人",
    "招标代理机构联系方式",
    "中标人",
    "中标人联系人",
    "中标人联系方式",
    "中标金额（元）",
    "招标内容",
    "项目地点",
    "招标文件",
]


def _clean_spaces(text):
    return re.sub(r"\s+", " ", text or "").strip()


def _date_range(start_date, end_date):
    cur = start_date
    while cur <= end_date:
        yield cur
        cur = cur + dt.timedelta(days=1)


def _parse_date(s):
    return dt.datetime.strptime(s, "%Y-%m-%d").date()


class HttpClient:
    def __init__(self, session, min_delay, max_delay, timeout, retries, backoff_base):
        self.session = session
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.timeout = timeout
        self.retries = retries
        self.backoff_base = backoff_base

    def _sleep(self):
        if self.max_delay <= 0:
            return
        time.sleep(random.uniform(self.min_delay, self.max_delay))

    def _is_blocked(self, text):
        if not text:
            return False
        return ("频繁访问" in text) or ("您的访问过于频繁" in text) or ("Forwarding error" in text)

    def request(self, method, url, headers=None, params=None, data=None):
        last_err = None
        for attempt in range(self.retries + 1):
            self._sleep()
            try:
                r = self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    data=data,
                    timeout=self.timeout,
                )
                r.encoding = r.apparent_encoding or "utf-8"
                if self._is_blocked(r.text):
                    event_id = ""
                    m = re.search(r"事件ID[:：]\s*([0-9a-fA-F]+)", r.text)
                    if m:
                        event_id = m.group(1)
                    last_err = BlockedError(url=url, event_id=event_id)
                    wait_s = self.backoff_base * (2 ** attempt) + random.uniform(0, 1)
                    print(f"触发频率限制，等待 {wait_s:.1f}s 后重试（{attempt+1}/{self.retries+1}）{(' 事件ID:'+event_id) if event_id else ''}", flush=True)
                    time.sleep(wait_s)
                    continue
                return r
            except Exception as e:
                last_err = e
                wait_s = self.backoff_base * (2 ** attempt) + random.uniform(0, 1)
                print(f"请求失败：{e}，等待 {wait_s:.1f}s 后重试（{attempt+1}/{self.retries+1}）", flush=True)
                time.sleep(wait_s)
        if last_err is None:
            raise RuntimeError("请求失败但未捕获到异常信息")
        raise last_err


class BlockedError(Exception):
    def __init__(self, url, event_id=""):
        self.url = url
        self.event_id = event_id
        super().__init__(f"触发频率限制: {url}{(' 事件ID:'+event_id) if event_id else ''}")


class SQLiteStore:
    def __init__(self, db_path):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init()

    def close(self):
        self.conn.close()

    def _init(self):
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tenders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                url TEXT NOT NULL,
                title TEXT,
                publish_time TEXT,
                region TEXT,
                category TEXT,
                stage TEXT,
                buyer TEXT,
                buyer_contact TEXT,
                buyer_phone TEXT,
                agent_name TEXT,
                agent_contact TEXT,
                agent_phone TEXT,
                winner_name TEXT,
                winner_contact TEXT,
                winner_phone TEXT,
                amount TEXT,
                change_time TEXT,
                plan_time TEXT,
                content TEXT,
                detail_fetched INTEGER NOT NULL DEFAULT 0,
                list_fetched_at TEXT,
                detail_fetched_at TEXT,
                UNIQUE(source, url)
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS checkpoints (
                source TEXT PRIMARY KEY,
                last_date TEXT
            )
            """
        )
        self.conn.commit()

    def upsert_list(self, source, item):
        now = dt.datetime.utcnow().isoformat()
        self.conn.execute(
            """
            INSERT INTO tenders (
                source, url, title, publish_time, region, category, stage, buyer, list_fetched_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source, url) DO UPDATE SET
                title=excluded.title,
                publish_time=excluded.publish_time,
                region=excluded.region,
                category=excluded.category,
                stage=excluded.stage,
                buyer=excluded.buyer,
                list_fetched_at=excluded.list_fetched_at
            """,
            (
                source,
                item.get("url"),
                item.get("title"),
                item.get("publish_time"),
                item.get("region"),
                item.get("category"),
                item.get("stage"),
                item.get("buyer"),
                now,
            ),
        )

    def update_detail(self, source, url, detail):
        now = dt.datetime.utcnow().isoformat()
        self.conn.execute(
            """
            UPDATE tenders SET
                buyer_contact=?,
                buyer_phone=?,
                agent_name=?,
                agent_contact=?,
                agent_phone=?,
                winner_name=?,
                winner_contact=?,
                winner_phone=?,
                amount=?,
                change_time=?,
                plan_time=?,
                content=?,
                detail_fetched=1,
                detail_fetched_at=?
            WHERE source=? AND url=?
            """,
            (
                detail.get("buyer_contact"),
                detail.get("buyer_phone"),
                detail.get("agent_name"),
                detail.get("agent_contact"),
                detail.get("agent_phone"),
                detail.get("winner_name"),
                detail.get("winner_contact"),
                detail.get("winner_phone"),
                detail.get("amount"),
                detail.get("change_time"),
                detail.get("plan_time"),
                detail.get("content"),
                now,
                source,
                url,
            ),
        )

    def commit(self):
        self.conn.commit()

    def set_checkpoint(self, source, last_date):
        self.conn.execute(
            """
            INSERT INTO checkpoints (source, last_date)
            VALUES (?, ?)
            ON CONFLICT(source) DO UPDATE SET last_date=excluded.last_date
            """,
            (source, last_date),
        )
        self.conn.commit()

    def get_checkpoint(self, source):
        row = self.conn.execute("SELECT last_date FROM checkpoints WHERE source=?", (source,)).fetchone()
        return row["last_date"] if row else None

    def iter_need_detail(self, source, limit):
        rows = self.conn.execute(
            """
            SELECT url, title FROM tenders
            WHERE source=? AND detail_fetched=0
            ORDER BY publish_time ASC, id ASC
            LIMIT ?
            """,
            (source, limit),
        ).fetchall()
        for r in rows:
            yield dict(r)

    def export_csv(self, output_path, sources=None, start_date=None, end_date=None):
        wh = []
        args = []
        if sources:
            wh.append("source IN (%s)" % ",".join(["?"] * len(sources)))
            args.extend(sources)
        if start_date:
            wh.append("publish_time >= ?")
            args.append(start_date)
        if end_date:
            wh.append("publish_time <= ?")
            args.append(end_date + " 23:59:59")
        where_sql = (" WHERE " + " AND ".join(wh)) if wh else ""
        rows = self.conn.execute(
            f"""
            SELECT * FROM tenders
            {where_sql}
            ORDER BY publish_time ASC, id ASC
            """,
            args,
        ).fetchall()
        with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            for r in rows:
                w.writerow(
                    {
                        "来源": r["source"],
                        "项目分类": r["category"] or "",
                        "项目阶段": r["stage"] or "",
                        "项目名称": r["title"] or "",
                        "发布时间": r["publish_time"] or "",
                        "招标人": r["buyer"] or "",
                        "变更时间": r["change_time"] or "",
                        "计划招标时间": r["plan_time"] or "",
                        "招标人联系人": r["buyer_contact"] or "",
                        "招标人联系方式": r["buyer_phone"] or "",
                        "招标代理机构": r["agent_name"] or "",
                        "招标代理机构联系人": r["agent_contact"] or "",
                        "招标代理机构联系方式": r["agent_phone"] or "",
                        "中标人": r["winner_name"] or "",
                        "中标人联系人": r["winner_contact"] or "",
                        "中标人联系方式": r["winner_phone"] or "",
                        "中标金额（元）": r["amount"] or "",
                        "招标内容": r["content"] or "",
                        "项目地点": r["region"] or "",
                        "招标文件": r["url"] or "",
                    }
                )


class CCGPSource:
    def __init__(self, client):
        self.client = client
        self.name = "中国政府采购网"
        self.category = "政府采购"

    def list_day(self, day, page, keyword):
        encoded_kw = urllib.parse.quote(keyword) if keyword else "%20"
        st = day.strftime("%Y:%m:%d")
        et = day.strftime("%Y:%m:%d")
        url = (
            "https://search.ccgp.gov.cn/bxsearch?"
            f"searchtype=1&page_index={page}&bidSort=0&buyerName=&projectId=&pinMu=&bidType=&dbselect=bidx"
            f"&kw={encoded_kw}&start_time={urllib.parse.quote(st)}&end_time={urllib.parse.quote(et)}"
            "&timeType=2&displayZone=&zoneId=&pppStatus=0&agentName="
        )
        r = self.client.request("GET", url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")
        items = soup.select(".vT-srch-result-list-bid li")
        out = []
        for item in items:
            a = item.select_one("a")
            title = a.get_text(strip=True) if a else ""
            href = a.get("href") if a else ""
            span = item.select_one("span")
            span_text = span.get_text(" ", strip=True) if span else ""
            publish_time = ""
            buyer = ""
            stage = ""
            region = ""
            time_match = re.search(r"(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})", span_text)
            if time_match:
                publish_time = time_match.group(1)
            buyer_match = re.search(r"采购人：([^|]+)", span_text)
            if buyer_match:
                buyer = buyer_match.group(1).strip()
            strongs = span.find_all("strong") if span else []
            if strongs:
                stage = strongs[0].get_text(strip=True)
            region_match = re.search(rf"{re.escape(stage)}\s*\|\s*([^|]+)\s*\|", span_text) if stage else None
            if region_match:
                region = region_match.group(1).strip()
            if href:
                out.append(
                    {
                        "url": href,
                        "title": title,
                        "publish_time": publish_time,
                        "region": region,
                        "category": self.category,
                        "stage": stage,
                        "buyer": buyer,
                    }
                )
        return out

    def _extract_section(self, text, start_marker, end_markers):
        if not text or not start_marker:
            return ""
        start_idx = text.find(start_marker)
        if start_idx < 0:
            return ""
        end_idx = len(text)
        for m in end_markers or []:
            i = text.find(m, start_idx + len(start_marker))
            if i >= 0 and i < end_idx:
                end_idx = i
        return text[start_idx:end_idx]

    def _extract_phones(self, text):
        if not text:
            return []
        matches = re.findall(r"(?:\d{3,4}-\d{7,8}|\d{11}|\d{7,8})", text)
        seen = set()
        out = []
        for m in matches:
            if m not in seen:
                seen.add(m)
                out.append(m)
        return out

    def _extract_contact_name(self, text):
        if not text:
            return ""
        m = re.search(r"项目联系人[：:\s]*([\u4e00-\u9fa5A-Za-z·•]{2,20})", text)
        return m.group(1).strip() if m else ""

    def _extract_body_text(self, html):
        soup = BeautifulSoup(html, "html.parser")
        content_div = soup.select_one(".vF_detail_content") or soup.select_one(".vT_detail_content")
        if not content_div:
            content_div = soup.select_one(".main") or soup.find("body")
        raw_text = content_div.get_text("\n") if content_div else soup.get_text("\n")
        raw_text = raw_text.replace("\r", "\n").replace("\t", "\n")
        text = _clean_spaces(raw_text)
        marker = "一、项目编号"
        idx = text.find(marker)
        if idx >= 0:
            text = text[idx:]
        return text

    def detail(self, url):
        r = self.client.request("GET", url, headers={"User-Agent": "Mozilla/5.0"})
        text = self._extract_body_text(r.text)

        buyer_sec = self._extract_section(
            text,
            "采购人信息",
            ["采购代理机构信息", "采购代理机构", "项目联系方式", "3.项目联系方式", "3. 项目联系方式"],
        )
        agent_sec = self._extract_section(
            text,
            "采购代理机构信息",
            ["项目联系方式", "3.项目联系方式", "3. 项目联系方式"],
        )
        project_sec = self._extract_section(
            text,
            "项目联系方式",
            ["十、", "十.", "附件", "附件：", "招标文件", "公告期限"],
        )

        buyer_contact = self._extract_contact_name(buyer_sec)
        buyer_phone = (self._extract_phones(buyer_sec) or [""])[0]
        agent_contact = self._extract_contact_name(agent_sec)
        agent_phone = (self._extract_phones(agent_sec) or [""])[0]

        if not agent_contact and not buyer_contact:
            agent_contact = self._extract_contact_name(project_sec)
        if not agent_phone and not buyer_phone:
            agent_phone = (self._extract_phones(project_sec) or [""])[0]

        if buyer_phone:
            buyer_phone = re.sub(r"[^\d\-]", "", buyer_phone)
        if agent_phone:
            agent_phone = re.sub(r"[^\d\-]", "", agent_phone)

        amount_m = re.search(r"(?:中标|成交)(?:总)?金额[：:\s]*([0-9.,]+(?:\s*万元|元|万|%))", text)
        amount = amount_m.group(1).strip() if amount_m else ""

        winner_m = re.search(r"(?:中标|成交)(?:人|供应商)(?:名称)?[：:\s]*([\u4e00-\u9fa5A-Za-z0-9_()（）]+(?:公司|中心|厂|院))", text)
        winner = winner_m.group(1).strip() if winner_m else ""

        change_time_m = re.search(r"更正日期[：:\s]*(\d{4}年\d{1,2}月\d{1,2}日|\d{4}-\d{1,2}-\d{1,2})", text)
        change_time = change_time_m.group(1).strip() if change_time_m else ""

        plan_time_m = re.search(r"预计采购时间[：:\s]*(\d{4}年\d{1,2}月|\d{4}-\d{1,2})", text)
        plan_time = plan_time_m.group(1).strip() if plan_time_m else ""

        agent_name_m = re.search(r"(?:代理机构|采购代理机构)(?:名称)?[：:\s]*([\u4e00-\u9fa5A-Za-z0-9_()（）]+(?:公司|中心|厂|院|局))", text)
        agent_name = agent_name_m.group(1).strip() if agent_name_m else ""

        return {
            "buyer_contact": buyer_contact,
            "buyer_phone": buyer_phone,
            "agent_name": agent_name,
            "agent_contact": agent_contact,
            "agent_phone": agent_phone,
            "winner_name": winner,
            "winner_contact": "",
            "winner_phone": "",
            "amount": amount,
            "change_time": change_time,
            "plan_time": plan_time,
            "content": text,
        }


class GGZYSource:
    def __init__(self, client):
        self.client = client
        self.name = "全国公共资源交易平台"

    def list_day(self, day, page, keyword):
        url = "http://deal.ggzy.gov.cn/ds/deal/dealList_find.jsp"
        data = {
            "TIMEBEGIN_SHOW": day.strftime("%Y-%m-%d"),
            "TIMEEND_SHOW": day.strftime("%Y-%m-%d"),
            "TIMEBEGIN": day.strftime("%Y-%m-%d"),
            "TIMEEND": day.strftime("%Y-%m-%d"),
            "SOURCE_TYPE": "1",
            "DEAL_TIME": "02",
            "DEAL_CLASSIFY": "01",
            "DEAL_STAGE": "0100",
            "DEAL_PROVINCE": "0",
            "DEAL_CITY": "0",
            "DEAL_PLATFORM": "0",
            "BID_PLATFORM": "0",
            "DEAL_TRADE": "0",
            "PAGENUMBER": str(page),
            "FINDTXT": keyword or "",
        }
        r = self.client.request("POST", url, headers={"User-Agent": "Mozilla/5.0"}, data=data)
        soup = BeautifulSoup(r.text, "html.parser")
        out = []
        for a in soup.select("a"):
            href = a.get("href") or ""
            title = a.get_text(" ", strip=True)
            if not href or not title:
                continue
            if "javascript" in href.lower():
                continue
            if href.startswith("/"):
                href = "http://deal.ggzy.gov.cn" + href
            if "ggzy.gov.cn" not in href:
                continue
            out.append(
                {
                    "url": href,
                    "title": title,
                    "publish_time": day.strftime("%Y-%m-%d") + " 00:00:00",
                    "region": "",
                    "category": "",
                    "stage": "",
                    "buyer": "",
                }
            )
        return out

    def detail(self, url):
        r = self.client.request("GET", url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")
        content_div = soup.select_one("article") or soup.select_one(".content") or soup.find("body")
        raw_text = content_div.get_text("\n") if content_div else soup.get_text("\n")
        raw_text = raw_text.replace("\r", "\n").replace("\t", "\n")
        text = _clean_spaces(raw_text)
        return {
            "buyer_contact": "",
            "buyer_phone": "",
            "agent_name": "",
            "agent_contact": "",
            "agent_phone": "",
            "winner_name": "",
            "winner_contact": "",
            "winner_phone": "",
            "amount": "",
            "change_time": "",
            "plan_time": "",
            "content": text,
        }


class Crawler:
    def __init__(self, store):
        self.store = store

    def crawl_list(self, source_obj, start_date, end_date, keyword, max_pages):
        for day in _date_range(start_date, end_date):
            inserted = 0
            for page in range(1, max_pages + 1):
                print(f"[{source_obj.name}] 列表采集 {day} 第{page}页", flush=True)
                try:
                    items = source_obj.list_day(day, page, keyword)
                except BlockedError as e:
                    print(str(e), flush=True)
                    print("建议：降低 max-pages、增大 min/max-delay，并等待一段时间后重试；已保存已完成日期的 checkpoint，可断点续跑。", flush=True)
                    return
                except Exception as e:
                    print(f"[{source_obj.name}] 列表采集失败：{e}", flush=True)
                    return
                if not items:
                    break
                for it in items:
                    self.store.upsert_list(source_obj.name, it)
                    inserted += 1
                self.store.commit()
                print(f"[{source_obj.name}] 已写入 {inserted} 条（截至 {day} 第{page}页）", flush=True)
            self.store.set_checkpoint(source_obj.name, day.strftime("%Y-%m-%d"))
            print(f"[{source_obj.name}] 完成日期 {day}，checkpoint 已更新", flush=True)

    def crawl_detail(self, source_obj, limit):
        for i, row in enumerate(self.store.iter_need_detail(source_obj.name, limit), start=1):
            url = row["url"]
            title = row.get("title") or ""
            print(f"  -> 正在抓取详情页 [{i}/{limit}]: {title[:20]}...")
            try:
                detail = source_obj.detail(url)
                self.store.update_detail(source_obj.name, url, detail)
                self.store.commit()
            except Exception:
                continue


def _map_source_names(keys):
    mp = {"ccgp": "中国政府采购网", "ggzy": "全国公共资源交易平台"}
    return [mp.get(k, k) for k in keys]


def main():
    parser = argparse.ArgumentParser(description="招投标信息自动化采集工具（SQLite落库/断点续跑/多源采集）")
    sub = parser.add_subparsers(dest="cmd")

    crawl_p = sub.add_parser("crawl", help="采集列表与详情并落库")
    crawl_p.add_argument("--db", default="data/tenders.db")
    crawl_p.add_argument("--sources", default="ccgp", help="ccgp,ggzy 或 ccgp,ggzy")
    crawl_p.add_argument("-k", "--keyword", default="")
    crawl_p.add_argument("--start-date", required=True)
    crawl_p.add_argument("--end-date", required=True)
    crawl_p.add_argument("--max-pages", type=int, default=50)
    crawl_p.add_argument("--detail", action="store_true")
    crawl_p.add_argument("--detail-limit", type=int, default=500)
    crawl_p.add_argument("--min-delay", type=float, default=1.0)
    crawl_p.add_argument("--max-delay", type=float, default=3.0)
    crawl_p.add_argument("--timeout", type=float, default=10.0)
    crawl_p.add_argument("--retries", type=int, default=2)
    crawl_p.add_argument("--backoff-base", type=float, default=5.0)

    export_p = sub.add_parser("export", help="从SQLite导出CSV")
    export_p.add_argument("--db", default="data/tenders.db")
    export_p.add_argument("-o", "--output", default="bidding_data.csv")
    export_p.add_argument("--sources", default="")
    export_p.add_argument("--start-date", default="")
    export_p.add_argument("--end-date", default="")

    legacy_p = sub.add_parser("run", help="兼容旧用法：采集并直接导出CSV")
    legacy_p.add_argument("--db", default="data/tenders.db")
    legacy_p.add_argument("--sources", default="ccgp")
    legacy_p.add_argument("-k", "--keyword", default="")
    legacy_p.add_argument("-p", "--pages", type=int, default=1)
    legacy_p.add_argument("-s", "--start_time", default="")
    legacy_p.add_argument("-e", "--end_time", default="")
    legacy_p.add_argument("-o", "--output", default="bidding_data.csv")
    legacy_p.add_argument("--min-delay", type=float, default=1.0)
    legacy_p.add_argument("--max-delay", type=float, default=3.0)
    legacy_p.add_argument("--timeout", type=float, default=10.0)
    legacy_p.add_argument("--retries", type=int, default=2)
    legacy_p.add_argument("--backoff-base", type=float, default=5.0)

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        return

    if args.cmd == "export":
        store = SQLiteStore(args.db)
        src_keys = [s.strip() for s in args.sources.split(",") if s.strip()]
        store.export_csv(
            args.output,
            sources=_map_source_names(src_keys) if src_keys else None,
            start_date=args.start_date or None,
            end_date=args.end_date or None,
        )
        store.close()
        print(f"导出完成：{args.output}")
        return

    session = requests.Session()
    client = HttpClient(
        session=session,
        min_delay=args.min_delay,
        max_delay=args.max_delay,
        timeout=args.timeout,
        retries=args.retries,
        backoff_base=args.backoff_base,
    )

    src_map = {"ccgp": CCGPSource(client), "ggzy": GGZYSource(client)}
    src_keys = [s.strip() for s in args.sources.split(",") if s.strip()]
    src_objs = [src_map[s] for s in src_keys if s in src_map]

    store = SQLiteStore(args.db)
    crawler = Crawler(store)

    if args.cmd == "run":
        if args.start_time and args.end_time:
            start_date = _parse_date(args.start_time)
            end_date = _parse_date(args.end_time)
        else:
            today = dt.date.today()
            start_date = today
            end_date = today
        for src in src_objs:
            crawler.crawl_list(src, start_date, end_date, args.keyword, args.pages)
            crawler.crawl_detail(src, limit=min(200, args.pages * 50))
        store.export_csv(args.output, sources=_map_source_names(src_keys) if src_keys else None)
        store.close()
        print(f"完成：{args.output}")
        return

    start_date = _parse_date(args.start_date)
    end_date = _parse_date(args.end_date)
    for src in src_objs:
        print(f"开始采集：{src.name} {start_date} -> {end_date}")
        crawler.crawl_list(src, start_date, end_date, args.keyword, args.max_pages)
        if args.detail:
            crawler.crawl_detail(src, args.detail_limit)
    store.close()


if __name__ == "__main__":
    main()
