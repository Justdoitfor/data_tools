import requests

# 尝试获取广东省政府采购网的公开接口
url = "https://gdgpo.czt.gd.gov.cn/freecms/rest/v1/notice/selectInfoMoreChannel.do?siteId=2771&channel=f10m01&limit=10&page=1&title=软件"

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
