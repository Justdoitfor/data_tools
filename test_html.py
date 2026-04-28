import requests
from bs4 import BeautifulSoup
import urllib.parse

keyword = "软件"
encoded_kw = urllib.parse.quote(keyword)
url = f"https://search.ccgp.gov.cn/bxsearch?searchtype=1&page_index=1&bidSort=0&buyerName=&projectId=&pinMu=&bidType=&dbselect=bidx&kw={encoded_kw}&start_time=2026%3A04%3A21&end_time=2026%3A04%3A28&timeType=2&displayZone=&zoneId=&pppStatus=0&agentName="

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}
session = requests.Session()
r = session.get(url, headers=headers, timeout=10)
r.encoding = 'utf-8'
soup = BeautifulSoup(r.text, 'html.parser')
items = soup.select(".vT-srch-result-list-bid li")
for item in items[:2]:
    print(item.prettify())
