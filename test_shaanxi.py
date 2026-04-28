import requests
import json

url = "http://www.ccgp-shaanxi.gov.cn/freecms/rest/v1/notice/selectInfoMoreChannel.do"
params = {
    "siteId": "1",
    "channel": "c85d774f17784018861bb0529d8924b1",
    "currPage": "1",
    "pageSize": "10",
    "title": ""
}
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}
try:
    r = requests.get(url, params=params, headers=headers, timeout=10)
    print(r.status_code)
    data = r.json()
    print(json.dumps(data, indent=2, ensure_ascii=False)[:500])
except Exception as e:
    print(e)
