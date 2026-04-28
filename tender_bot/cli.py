import argparse
from scraper import TenderScraper
import os

def main():
    parser = argparse.ArgumentParser(description="招投标信息自动化采集与分析工具 CLI")
    
    # 采集任务参数
    parser.add_argument("--scrape", action="store_true", help="执行采集任务")
    parser.add_argument("-k", "--keyword", type=str, default="", help="搜索关键字")
    parser.add_argument("-r", "--region", type=str, default="全国", help="搜索地区")
    parser.add_argument("-l", "--limit", type=int, default=10, help="采集条数限制")
    parser.add_argument("-o", "--output", type=str, default="scraped_data.csv", help="输出CSV文件路径")
    
    args = parser.parse_args()
    
    if args.scrape:
        if not args.keyword:
            print("错误: 采集模式必须指定关键字 (-k)")
            return
            
        scraper = TenderScraper()
        scraper.run(keyword=args.keyword, region=args.region, limit=args.limit, output_csv=args.output)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
