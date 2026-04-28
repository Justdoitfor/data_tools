import requests

url = "http://ggzyjy.sc.gov.cn/inteligentsearch/rest/inteligentSearch/getFullTextData"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Content-Type": "application/json"
}
data = '{"token":"","pn":10,"rn":1,"sdt":"","edt":"","wd":"软件","inc_wd":"","exc_wd":"","fields":"title","cnum":"","sort":"{\\"webdate\\":\\"0\\"}","ssort":"title","cl":500,"terminal":"","condition":[{"pn":10,"rn":1,"sdt":"","edt":"","wd":"软件","inc_wd":"","exc_wd":"","fields":"title","cnum":"","sort":"{\\"webdate\\":\\"0\\"}","ssort":"title","cl":500,"terminal":"","condition":null,"time":null,"highlights":null,"statistics":null,"unionCondition":null,"accuracy":"","noValue":null,"searchRange":null,"isBusiness":1}],"time":null,"highlights":null,"statistics":null,"unionCondition":null,"accuracy":"","noValue":null,"searchRange":null,"isBusiness":1}'
try:
    response = requests.post(url, headers=headers, data=data, timeout=10)
    print("Status:", response.status_code)
    print("Snippet:", response.text[:500])
except Exception as e:
    print("Error:", e)
