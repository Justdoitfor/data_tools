import requests

url = "http://gzpublic.gzfinance.gov.cn/gzlc/notice/queryNoticeList"
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Content-Type": "application/x-www-form-urlencoded"
}
data = {
    "noticeType": "2",
    "keyword": "软件",
    "pageNo": 1,
    "pageSize": 10
}
try:
    r = requests.post(url, headers=headers, data=data, timeout=10)
    print(r.status_code)
    print(r.text[:500])
except Exception as e:
    print(e)
