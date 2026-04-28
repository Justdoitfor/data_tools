import sys
import csv
import urllib.parse
import re
from playwright.sync_api import sync_playwright

def scrape_ccgp(keyword, max_pages=1):
    results = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        encoded_kw = urllib.parse.quote(keyword)
        # Using timeType=6 for last 6 months
        url = f"https://search.ccgp.gov.cn/bxsearch?searchtype=1&page_index=1&bidSort=0&buyerName=&projectId=&pinMu=&bidType=&dbselect=bidx&kw={encoded_kw}&start_time=&end_time=&timeType=6&displayZone=&zoneId=&pppStatus=0&agentName="
        
        print(f"Navigating to search page for keyword: {keyword}...")
        page.goto(url)
        page.wait_for_timeout(2000)
        
        for i in range(max_pages):
            print(f"Scraping list page {i+1}/{max_pages}...")
            try:
                page.wait_for_selector(".vT-srch-result-list-bid", timeout=10000)
            except:
                print("No results found or timeout waiting for list.")
                break
                
            items = page.query_selector_all(".vT-srch-result-list-bid li")
            for item in items:
                try:
                    title_el = item.query_selector("a")
                    title = title_el.inner_text().strip() if title_el else ""
                    href = title_el.get_attribute("href") if title_el else ""
                    
                    info_text = item.inner_text()
                    
                    publish_time = ""
                    purchaser = ""
                    notice_type = ""
                    region = ""
                    project_type = ""
                    
                    if " | " in info_text:
                        lines = info_text.split("\n")
                        for line in lines:
                            if "采购人：" in line:
                                parts = line.split("|")
                                if len(parts) >= 2:
                                    publish_time = parts[0].strip()
                                    purchaser = parts[1].replace("采购人：", "").strip()
                            elif "公告 | " in line or "公示 | " in line:
                                parts = line.split("|")
                                if len(parts) >= 2:
                                    notice_type = parts[0].strip()
                                    region = parts[1].strip()
                                if len(parts) >= 3:
                                    project_type = parts[2].strip()
                                    
                    results.append({
                        "项目名称": title,
                        "招标单位": purchaser,
                        "发布时间": publish_time,
                        "地区": region,
                        "项目类型": project_type,
                        "公告类型": notice_type,
                        "信息来源网址": href,
                        "中标单位": "",
                        "预算金额/中标金额": ""
                    })
                except Exception as e:
                    print("Error parsing item:", e)
            
            if i < max_pages - 1:
                next_btn = page.query_selector("a.next")
                if next_btn:
                    next_btn.click()
                    page.wait_for_timeout(3000)
                else:
                    break
        
        print(f"Total basic items collected: {len(results)}. Extracting detailed info (Winning Provider/Amount)...")
        for idx, res in enumerate(results):
            if "中标" in res["公告类型"] or "成交" in res["公告类型"]:
                print(f"[{idx+1}/{len(results)}] Extracting details for: {res['项目名称'][:20]}...")
                try:
                    page.goto(res["信息来源网址"], timeout=15000)
                    page.wait_for_timeout(1000)
                    content = page.inner_text("body")
                    
                    # Regex to find winner
                    winner_match = re.search(r"(?:中标|成交)(?:人|供应商)(?:名称)?[：:\s]*([\u4e00-\u9fa5A-Za-z0-9_()（）]+公司)", content)
                    if winner_match:
                        res["中标单位"] = winner_match.group(1).strip()
                        
                    # Regex to find amount
                    amount_match = re.search(r"(?:中标|成交)金额[：:\s]*([0-9.,]+(?:\s*万元|元|万|%))", content)
                    if amount_match:
                        res["预算金额/中标金额"] = amount_match.group(1).strip()
                        
                except Exception as e:
                    print(f"Failed to load detail page: {e}")
                    
        browser.close()
    
    return results

if __name__ == "__main__":
    keyword = sys.argv[1] if len(sys.argv) > 1 else "软件"
    pages = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    data = scrape_ccgp(keyword, pages)
    
    if data:
        keys = ["项目名称", "招标单位", "中标单位", "预算金额/中标金额", "发布时间", "地区", "项目类型", "公告类型", "信息来源网址"]
        filename = "bidding_data.csv"
        with open(filename, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictReader(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(data)
        print(f"Saved {len(data)} records to {filename}")
    else:
        print("No data found.")
