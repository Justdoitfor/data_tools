import requests

url = "http://deal.ggzy.gov.cn/ds/deal/dealList_find.jsp"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
data = {
    "TIMEBEGIN_SHOW": "2023-01-01",
    "TIMEEND_SHOW": "2023-12-31",
    "TIMEBEGIN": "2023-01-01",
    "TIMEEND": "2023-12-31",
    "SOURCE_TYPE": "1",
    "DEAL_TIME": "02",
    "DEAL_CLASSIFY": "01",
    "DEAL_STAGE": "0100",
    "DEAL_PROVINCE": "0",
    "DEAL_CITY": "0",
    "DEAL_PLATFORM": "0",
    "BID_PLATFORM": "0",
    "DEAL_TRADE": "0",
    "PAGENUMBER": "1",
    "FINDTXT": "测试"
}
try:
    response = requests.post(url, headers=headers, data=data, timeout=10)
    print("Status:", response.status_code)
    print("Content length:", len(response.text))
    print("Snippet:", response.text[:500])
except Exception as e:
    print("Error:", e)
