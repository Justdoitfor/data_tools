import requests

url = "https://www.qianlima.com/zb/area_0/bidd_0/zhaobiao_0/kw_%E8%BD%AF%E4%BB%B6/search.html"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
try:
    response = requests.get(url, headers=headers, timeout=10)
    print("Status:", response.status_code)
    print("Content length:", len(response.text))
    print("Snippet:", response.text[:500])
except Exception as e:
    print("Error:", e)
