import requests

url = "http://www.ccgp-hubei.gov.cn/macms/front/notice/noticeList"
headers = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/x-www-form-urlencoded"
}
data = {
    "pageNo": 1,
    "pageSize": 10,
    "queryType": 1,
    "title": "软件"
}
try:
    r = requests.post(url, headers=headers, data=data, timeout=10)
    print(r.status_code)
    print(r.text[:500])
except Exception as e:
    print(e)
