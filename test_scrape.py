import requests

url = "http://search.ccgp.gov.cn/bxsearch?searchtype=1&page_index=1&bidSort=0&buyerName=&projectId=&pinYin=0&displayZone=&zoneId=&pppStatus=0&agentName=&timeType=2&keyword=软件"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
try:
    response = requests.get(url, headers=headers, timeout=10)
    print("Status:", response.status_code)
    print("Content length:", len(response.text))
    print("Snippet:", response.text[:500])
except Exception as e:
    print("Error:", e)
