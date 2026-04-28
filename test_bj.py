import requests

url = "http://www.ccgp-beijing.gov.cn/xxgg/qjzfcgxxgg/index.html"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
try:
    response = requests.get(url, headers=headers, timeout=10)
    response.encoding = 'utf-8'
    print("Status:", response.status_code)
    print("Snippet:", response.text[:500])
except Exception as e:
    print("Error:", e)
