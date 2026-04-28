import requests
from bs4 import BeautifulSoup
import urllib.parse

# Let's test with keyword "采购" or something very generic if no keyword provided
url = f"https://search.ccgp.gov.cn/bxsearch?searchtype=1&page_index=1&bidSort=0&buyerName=&projectId=&pinMu=&bidType=&dbselect=bidx&kw=%E9%A1%B9%E7%9B%AE&start_time=&end_time=&timeType=6&displayZone=&zoneId=&pppStatus=0&agentName="
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
print(f"With '项目' and timeType=6: Found {len(items)} items")

