import requests
from bs4 import BeautifulSoup
import urllib.parse
import re
import csv
import time
import argparse
import sys

class BiddingSpider:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Connection": "keep-alive"
        }
        
    def scrape_ccgp(self, keyword, start_time, end_time, max_pages=1):
        """抓取中国政府采购网"""
        results = []
        # 初始化会话获取Cookie
        try:
            self.session.get("https://search.ccgp.gov.cn/", headers=self.headers, timeout=10)
        except:
            pass

        encoded_kw = urllib.parse.quote(keyword)
        # 将日期转换为url要求的格式 2023:01:01
        st = start_time.replace("-", "%3A") if start_time else ""
        et = end_time.replace("-", "%3A") if end_time else ""
        time_type = "6" if not st else "2" # 如果没有时间，默认近6个月（在CCGP中，timeType 6为近半年，2为自定义）
        if st and et:
            time_type = "2"
        
        print(f"正在从【中国政府采购网】抓取关键词：'{keyword}'，时间范围：{start_time} 至 {end_time}...")
        
        for page in range(1, max_pages + 1):
            print(f"正在抓取第 {page} 页...")
            url = f"https://search.ccgp.gov.cn/bxsearch?searchtype=1&page_index={page}&bidSort=0&buyerName=&projectId=&pinMu=&bidType=&dbselect=bidx&kw={encoded_kw}&start_time={st}&end_time={et}&timeType={time_type}&displayZone=&zoneId=&pppStatus=0&agentName="
            
            try:
                r = self.session.get(url, headers=self.headers, timeout=15)
                r.encoding = 'utf-8'
                
                if "频繁访问" in r.text:
                    print("检测到访问频率限制，暂停10秒...")
                    time.sleep(10)
                    r = self.session.get(url, headers=self.headers, timeout=15)
                    r.encoding = 'utf-8'
                    
                soup = BeautifulSoup(r.text, 'html.parser')
                items = soup.select(".vT-srch-result-list-bid li")
                if not items:
                    print("本页未发现数据或抓取已结束。")
                    break
                    
                for item in items:
                    a = item.select_one("a")
                    title = a.text.strip() if a else ""
                    href = a.get("href") if a else ""
                    
                    span = item.select_one("span")
                    span_text = span.text if span else ""
                    
                    publish_time, purchaser, notice_type, region, project_type = "", "", "", "", ""
                    
                    raw_span = span_text.replace("\n", " ").replace("\r", " ")
                    time_match = re.search(r"(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})", raw_span)
                    publish_time = time_match.group(1) if time_match else ""
                    
                    purchaser_match = re.search(r"采购人：([^|]+)", raw_span)
                    purchaser = purchaser_match.group(1).strip() if purchaser_match else ""
                    
                    strongs = span.find_all("strong")
                    if len(strongs) >= 1:
                        notice_type = strongs[0].text.strip()
                    if len(strongs) >= 2:
                        project_type = strongs[1].text.strip()
                        
                    region_match = re.search(rf"{notice_type}\s*\|\s*([^|]+)\s*\|", raw_span)
                    if region_match:
                        region = region_match.group(1).strip()
                        
                    p = item.select_one("p")
                    snippet = p.text.replace("\n", "").replace("\r", "") if p else ""
                    
                    winner, amount = "", ""
                    
                    winner_match = re.search(r"(?:中标|成交)供应商名称.*?([A-Za-z0-9\u4e00-\u9fa5_()（）]+(?:公司|中心|厂|院))", snippet)
                    if winner_match:
                        winner = winner_match.group(1)
                        
                    amt_match = re.search(r"(?:金额|预算)[：:]?([0-9.,]+(?:\s*万元|元|万))", snippet)
                    if amt_match:
                        amount = amt_match.group(1)
                        
                    results.append({
                        "项目名称": title,
                        "招标单位": purchaser,
                        "中标单位": winner,
                        "预算金额/中标金额": amount,
                        "发布时间": publish_time,
                        "地区": region,
                        "项目类型": project_type,
                        "公告类型": notice_type,
                        "信息来源网址": href
                    })
                    
            except Exception as e:
                print(f"解析第 {page} 页时出错: {e}")
                
            time.sleep(2)
            
        print(f"共收集到基本信息 {len(results)} 条，开始进一步抓取详情页提取中标信息...")
        
        # 针对中标公告进一步提取
        for idx, res in enumerate(results):
            if ("中标" in res["公告类型"] or "成交" in res["公告类型"]) and (not res["中标单位"] or not res["预算金额/中标金额"]):
                try:
                    det_headers = self.headers.copy()
                    parsed_href = urllib.parse.urlparse(res["信息来源网址"])
                    det_headers["Host"] = parsed_href.netloc
                    
                    det_r = self.session.get(res["信息来源网址"], headers=det_headers, timeout=10)
                    det_r.encoding = 'utf-8'
                    det_soup = BeautifulSoup(det_r.text, 'html.parser')
                    text_content = det_soup.text.replace("\n", " ").replace("\r", " ").replace("\t", " ")
                    
                    if not res["中标单位"]:
                        wm = re.search(r"(?:中标|成交)(?:人|供应商)(?:名称)?[：:\s]*([\u4e00-\u9fa5A-Za-z0-9_()（）]+(?:公司|中心|厂|院))", text_content)
                        if wm: res["中标单位"] = wm.group(1).strip()
                    if not res["预算金额/中标金额"]:
                        am = re.search(r"(?:中标|成交)(?:总)?金额[：:\s]*([0-9.,]+(?:\s*万元|元|万|%))", text_content)
                        if am: res["预算金额/中标金额"] = am.group(1).strip()
                except Exception as e:
                    pass
                time.sleep(1)
                
        return results

    def save_to_csv(self, data, filename="bidding_data.csv"):
        if not data:
            print("没有可保存的数据。")
            return
            
        keys = ["项目名称", "招标单位", "中标单位", "预算金额/中标金额", "发布时间", "地区", "项目类型", "公告类型", "信息来源网址"]
        with open(filename, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(data)
        print(f"成功将 {len(data)} 条数据保存至 {filename}")

def main():
    parser = argparse.ArgumentParser(description="招投标信息自动化采集工具")
    parser.add_argument("-k", "--keyword", required=True, help="搜索关键词，如：软件")
    parser.add_argument("-p", "--pages", type=int, default=1, help="采集页数，默认：1")
    parser.add_argument("-s", "--start_time", default="", help="开始时间，格式：YYYY-MM-DD")
    parser.add_argument("-e", "--end_time", default="", help="结束时间，格式：YYYY-MM-DD")
    parser.add_argument("-o", "--output", default="bidding_data.csv", help="导出CSV文件名")
    
    args = parser.parse_args()
    
    spider = BiddingSpider()
    data = spider.scrape_ccgp(args.keyword, args.start_time, args.end_time, args.pages)
    
    spider.save_to_csv(data, args.output)

if __name__ == "__main__":
    main()
