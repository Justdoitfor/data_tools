import requests

url = "http://www.ccgp-hunan.gov.cn/mvc/getNoticeList4More.do"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Content-Type": "application/x-www-form-urlencoded"
}
data = {
    "nType": "prcmNotices",
    "pType": "",
    "prcmPrjName": "软件",
    "prcmItemCode": "",
    "prcmOrgName": "",
    "startDate": "2023-01-01",
    "endDate": "2023-12-31",
    "page": 1,
    "pageSize": 10
}
try:
    response = requests.post(url, headers=headers, data=data, timeout=10)
    print("Status:", response.status_code)
    print("Snippet:", response.text[:500])
except Exception as e:
    print("Error:", e)
