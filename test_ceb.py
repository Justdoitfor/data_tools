import requests

url = "https://bulletin.cebpubservice.com/api/search"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Content-Type": "application/json"
}
data = '{"searchDateType":"1","keywords":"软件","page":1,"limit":10}'
try:
    response = requests.post(url, headers=headers, data=data, timeout=10)
    print("Status:", response.status_code)
    print("Snippet:", response.text[:500])
except Exception as e:
    print("Error:", e)
