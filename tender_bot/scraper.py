import requests
from bs4 import BeautifulSoup
import time
import random
import pandas as pd
from datetime import datetime

class TenderScraper:
    def __init__(self):
        # 初始化反爬配置
        self.headers_list = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        ]
        self.session = requests.Session()
        
    def _get_random_header(self):
        return {
            "User-Agent": random.choice(self.headers_list),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        }

    def _sleep(self):
        # 模拟请求限速与抖动
        time.sleep(random.uniform(0.5, 1.5))

    def fetch_mock_data(self, keyword: str, region: str, limit: int = 10):
        """
        为了演示，模拟抓取数据逻辑。
        真实环境应当使用 self.session.get(url) 获取网页内容，
        并利用 BeautifulSoup 提取项目名称、招标单位、金额等。
        """
        print(f"[*] 正在采集关键字: '{keyword}', 地区: '{region}' 的招投标数据...")
        self._sleep()
        
        results = []
        for i in range(limit):
            # 模拟页面解析过程
            notice_type = random.choice(["招标公告", "中标结果", "变更公告"])
            item = {
                "project_name": f"{region}关于{keyword}的采购项目批次{i}",
                "tenderer": f"{region}某行政单位",
                "winner": f"{region}某科技有限公司" if notice_type != "招标公告" else "",
                "amount": round(random.uniform(10_0000, 1000_0000), 2),
                "publish_date": datetime.now().strftime("%Y-%m-%d"),
                "region": region,
                "project_type": random.choice(["工程", "服务", "货物"]),
                "notice_type": notice_type,
                "source_url": f"http://example-gov-bidding.com/article/new_{i}"
            }
            results.append(item)
            
        df = pd.DataFrame(results)
        return df

    def run(self, keyword: str, region: str, limit: int = 10, output_csv: str = "scraped_data.csv"):
        """
        运行采集任务并保存到文件
        """
        df = self.fetch_mock_data(keyword, region, limit)
        df.to_csv(output_csv, index=False, encoding='utf-8')
        print(f"[+] 采集完成，共获取 {len(df)} 条数据，已保存至 {output_csv}")
        return df

if __name__ == "__main__":
    scraper = TenderScraper()
    scraper.run(keyword="大数据", region="北京", limit=5)
