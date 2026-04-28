import requests

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Connection": "keep-alive"
}
url = "http://www.ccgp.gov.cn/cggg/dfgg/cjgg/202604/t20260428_26469101.htm"
try:
    print(f"Testing detail URL: {url}")
    r = requests.get(url, headers=headers, timeout=5)
    print(f"Status: {r.status_code}, Length: {len(r.text)}")
except Exception as e:
    print(f"Error: {e}")
