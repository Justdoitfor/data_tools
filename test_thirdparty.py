import requests
import time

def test_url(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        r = requests.get(url, headers=headers, timeout=5)
        print(f"[{r.status_code}] {url}")
    except Exception as e:
        print(f"[Error] {url}: {e}")

urls = [
    "https://www.chinabidding.cn/",
    "https://www.qianlima.com/",
    "https://www.bidcenter.com.cn/",
    "https://www.zbytb.com/",
    "https://www.weain.mil.cn/"
]

for u in urls:
    test_url(u)
    time.sleep(1)
