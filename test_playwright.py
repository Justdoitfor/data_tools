from playwright.sync_api import sync_playwright
import csv
import urllib.parse
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        kw = "软件"
        encoded_kw = urllib.parse.quote(kw)
        url = f"https://search.ccgp.gov.cn/bxsearch?searchtype=1&page_index=1&bidSort=0&buyerName=&projectId=&pinMu=&bidType=&dbselect=bidx&kw={encoded_kw}&start_time=2026%3A04%3A21&end_time=2026%3A04%3A28&timeType=2&displayZone=&zoneId=&pppStatus=0&agentName="
        
        print(f"Navigating to {url}")
        page.goto(url)
        page.wait_for_selector(".vT-srch-result-list-bid", timeout=10000)
        
        items = page.query_selector_all(".vT-srch-result-list-bid li")
        print(f"Found {len(items)} items")
        
        for item in items[:2]:
            title_el = item.query_selector("a")
            title = title_el.inner_text().strip() if title_el else ""
            href = title_el.get_attribute("href") if title_el else ""
            
            info_text = item.inner_text()
            print(f"Title: {title}\nHref: {href}\nInfo: {info_text}\n---")
            
        browser.close()

if __name__ == "__main__":
    run()
