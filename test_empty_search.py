import requests
from bs4 import BeautifulSoup
import urllib.parse

# try kw=" "
url = f"https://search.ccgp.gov.cn/bxsearch?searchtype=1&page_index=1&bidSort=0&buyerName=&projectId=&pinMu=&bidType=&dbselect=bidx&kw=%20&start_time=2026%3A04%3A21&end_time=2026%3A04%3A28&timeType=2&displayZone=&zoneId=&pppStatus=0&agentName="
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
print(f"With space: Found {len(items)} items")

# try kw="*"
url = f"https://search.ccgp.gov.cn/bxsearch?searchtype=1&page_index=1&bidSort=0&buyerName=&projectId=&pinMu=&bidType=&dbselect=bidx&kw=*&start_time=2026%3A04%3A21&end_time=2026%3A04%3A28&timeType=2&displayZone=&zoneId=&pppStatus=0&agentName="
r = session.get(url, headers=headers, timeout=15)
r.encoding = 'utf-8'
soup = BeautifulSoup(r.text, 'html.parser')
items = soup.select(".vT-srch-result-list-bid li")
print(f"With *: Found {len(items)} items")

# try generic search keyword like "采购"
url = f"https://search.ccgp.gov.cn/bxsearch?searchtype=1&page_index=1&bidSort=0&buyerName=&projectId=&pinMu=&bidType=&dbselect=bidx&kw=%E9%87%87%E8%B4%AD&start_time=2026%3A04%3A21&end_time=2026%3A04%3A28&timeType=2&displayZone=&zoneId=&pppStatus=0&agentName="
r = session.get(url, headers=headers, timeout=15)
r.encoding = 'utf-8'
soup = BeautifulSoup(r.text, 'html.parser')
items = soup.select(".vT-srch-result-list-bid li")
print(f"With '采购': Found {len(items)} items")

