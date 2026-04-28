import requests
from bs4 import BeautifulSoup
import urllib.parse

keyword = "软件"
encoded_kw = urllib.parse.quote(keyword)
url = f"https://search.ccgp.gov.cn/bxsearch?searchtype=1&page_index=1&bidSort=0&buyerName=&projectId=&pinMu=&bidType=&dbselect=bidx&kw={encoded_kw}&start_time=2026%3A04%3A21&end_time=2026%3A04%3A28&timeType=2&displayZone=&zoneId=&pppStatus=0&agentName="

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Cache-Control": "max-age=0",
    "Connection": "keep-alive",
    "Host": "search.ccgp.gov.cn",
    "Referer": "https://search.ccgp.gov.cn/",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

try:
    session = requests.Session()
    # first request to get cookies
    session.get("https://search.ccgp.gov.cn/", headers=headers, timeout=10)
    
    r = session.get(url, headers=headers, timeout=10)
    r.encoding = 'utf-8'
    print(r.status_code)
    
    soup = BeautifulSoup(r.text, 'html.parser')
    items = soup.select(".vT-srch-result-list-bid li")
    print(f"Found {len(items)} items")
    for item in items[:2]:
        a = item.select_one("a")
        print(a.text.strip() if a else "")
        print(item.text.strip().replace("\n", " "))
except Exception as e:
    print(e)
