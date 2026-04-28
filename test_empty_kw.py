import requests
from bs4 import BeautifulSoup
import urllib.parse

# Test if we can search without keyword (e.g. wildcard or empty)
# Typically searchtype=1 requires some keyword, let's test kw=""
url = f"https://search.ccgp.gov.cn/bxsearch?searchtype=1&page_index=1&bidSort=0&buyerName=&projectId=&pinMu=&bidType=&dbselect=bidx&kw=&start_time=2026%3A04%3A21&end_time=2026%3A04%3A28&timeType=2&displayZone=&zoneId=&pppStatus=0&agentName="
headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Connection": "keep-alive"
}
try:
    session = requests.Session()
    session.get("https://search.ccgp.gov.cn/", headers=headers, timeout=10)
    
    r = session.get(url, headers=headers, timeout=10)
    r.encoding = 'utf-8'
    print(f"Status: {r.status_code}")
    
    soup = BeautifulSoup(r.text, 'html.parser')
    items = soup.select(".vT-srch-result-list-bid li")
    print(f"Found {len(items)} items with empty keyword")
    if items:
        a = items[0].select_one("a")
        print(a.text.strip() if a else "")
except Exception as e:
    print(e)
