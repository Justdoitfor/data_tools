import requests
from bs4 import BeautifulSoup
import urllib.parse

# try default timeType=2 without dates
url = f"https://search.ccgp.gov.cn/bxsearch?searchtype=1&page_index=1&bidSort=0&buyerName=&projectId=&pinMu=&bidType=&dbselect=bidx&kw=%20&start_time=&end_time=&timeType=2&displayZone=&zoneId=&pppStatus=0&agentName="
headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Connection": "keep-alive"
}
session = requests.Session()
session.get("https://search.ccgp.gov.cn/", headers=headers, timeout=10)
r = session.get(url, headers=headers, timeout=15)
r.encoding = 'utf-8'
soup = BeautifulSoup(r.text, 'html.parser')
items = soup.select(".vT-srch-result-list-bid li")
print(f"With timeType=2: Found {len(items)} items")

