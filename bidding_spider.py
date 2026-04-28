import requests
from bs4 import BeautifulSoup
import urllib.parse
import re
import csv
import time
import argparse
import sys

class BiddingSpider:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Connection": "keep-alive"
        }
        
    def _extract_detail(self, text_content):
        """从详情页正文提取联系人和额外信息"""
        detail_info = {
            "招标人联系人": "",
            "招标人联系方式": "",
            "招标代理机构": "",
            "招标代理机构联系人": "",
            "招标代理机构联系方式": "",
            "中标人": "",
            "中标人联系人": "",
            "中标人联系方式": "",
            "中标金额（元）": "",
            "项目地点": "",
            "变更时间": "",
            "计划招标时间": ""
        }
        
        # 中标金额
        am = re.search(r"(?:中标|成交)(?:总)?金额[：:\s]*([0-9.,]+(?:\s*万元|元|万|%))", text_content)
        if am: detail_info["中标金额（元）"] = am.group(1).strip()
            
        # 中标人
        wm = re.search(r"(?:中标|成交)(?:人|供应商)(?:名称)?[：:\s]*([\u4e00-\u9fa5A-Za-z0-9_()（）]+(?:公司|中心|厂|院))", text_content)
        if wm: detail_info["中标人"] = wm.group(1).strip()
            
        # 招标代理机构
        agent_m = re.search(r"(?:代理机构|采购代理机构)(?:名称)?[：:\s]*([\u4e00-\u9fa5A-Za-z0-9_()（）]+(?:公司|中心|厂|院|局))", text_content)
        if agent_m: detail_info["招标代理机构"] = agent_m.group(1).strip()
            
        # 招标人联系人 / 联系方式
        buyer_contact_m = re.search(r"采购人信息.*?联系方式[：:\s]*([\d\-、\s]+)", text_content)
        if buyer_contact_m:
            detail_info["招标人联系方式"] = buyer_contact_m.group(1).strip()
            
        buyer_name_m = re.search(r"采购人信息.*?项目联系人[：:\s]*([\u4e00-\u9fa5]{2,5})", text_content)
        if buyer_name_m:
            detail_info["招标人联系人"] = buyer_name_m.group(1).strip()
            
        # 代理机构联系人 / 联系方式
        agent_contact_m = re.search(r"采购代理机构信息.*?联系方式[：:\s]*([\d\-、\s]+)", text_content)
        if agent_contact_m:
            detail_info["招标代理机构联系方式"] = agent_contact_m.group(1).strip()
            
        agent_name_m = re.search(r"采购代理机构信息.*?项目联系人[：:\s]*([\u4e00-\u9fa5]{2,5})", text_content)
        if agent_name_m:
            detail_info["招标代理机构联系人"] = agent_name_m.group(1).strip()
            
        # 中标人联系人 / 联系方式
        winner_contact_m = re.search(r"(?:中标|成交)人.*?联系方式[：:\s]*([\d\-、\s]+)", text_content)
        if winner_contact_m:
            detail_info["中标人联系方式"] = winner_contact_m.group(1).strip()
            
        winner_name_m = re.search(r"(?:中标|成交)人.*?项目联系人[：:\s]*([\u4e00-\u9fa5]{2,5})", text_content)
        if winner_name_m:
            detail_info["中标人联系人"] = winner_name_m.group(1).strip()
            
        # 粗略提取地址
        addr_m = re.search(r"项目地点[：:\s]*([\u4e00-\u9fa5A-Za-z0-9_()（）]+)", text_content)
        if addr_m:
            detail_info["项目地点"] = addr_m.group(1).strip()
            
        # 变更时间/计划招标时间 匹配 (针对更正公告、意向公告)
        change_time_m = re.search(r"更正日期[：:\s]*(\d{4}年\d{1,2}月\d{1,2}日|\d{4}-\d{1,2}-\d{1,2})", text_content)
        if change_time_m:
            detail_info["变更时间"] = change_time_m.group(1).strip()
            
        plan_time_m = re.search(r"预计采购时间[：:\s]*(\d{4}年\d{1,2}月|\d{4}-\d{1,2})", text_content)
        if plan_time_m:
            detail_info["计划招标时间"] = plan_time_m.group(1).strip()
            
        return detail_info
        
    def scrape_ccgp(self, keyword, start_time, end_time, max_pages=1):
        """抓取中国政府采购网"""
        results = []
        try:
            self.session.get("https://search.ccgp.gov.cn/", headers=self.headers, timeout=10)
        except:
            pass

        # Use %20 (space) if no keyword is provided. CCGP requires at least a space to search all
        encoded_kw = urllib.parse.quote(keyword) if keyword else "%20"
        
        st = start_time.replace("-", "%3A") if start_time else ""
        et = end_time.replace("-", "%3A") if end_time else ""
        
        # CCGP API logic: timeType=2 is 'custom time' or 'today'. It works well with space keyword.
        time_type = "2" 
        
        kw_display = keyword if keyword else "【全部招标(无关键词)】"
        print(f"正在抓取，关键词：'{kw_display}'，时间：{start_time} 至 {end_time}...")
        
        for page in range(1, max_pages + 1):
            print(f"正在抓取第 {page} 页...")
            url = f"https://search.ccgp.gov.cn/bxsearch?searchtype=1&page_index={page}&bidSort=0&buyerName=&projectId=&pinMu=&bidType=&dbselect=bidx&kw={encoded_kw}&start_time={st}&end_time={et}&timeType={time_type}&displayZone=&zoneId=&pppStatus=0&agentName="
            
            try:
                r = self.session.get(url, headers=self.headers, timeout=15)
                r.encoding = 'utf-8'
                
                if "频繁访问" in r.text:
                    print("检测到访问频率限制，暂停10秒...")
                    time.sleep(10)
                    r = self.session.get(url, headers=self.headers, timeout=15)
                    r.encoding = 'utf-8'
                    
                soup = BeautifulSoup(r.text, 'html.parser')
                items = soup.select(".vT-srch-result-list-bid li")
                if not items:
                    print("本页未发现数据或抓取已结束。")
                    break
                    
                for item in items:
                    a = item.select_one("a")
                    title = a.text.strip() if a else ""
                    href = a.get("href") if a else ""
                    
                    span = item.select_one("span")
                    span_text = span.text if span else ""
                    
                    publish_time, purchaser, notice_type, region, project_type = "", "", "", "", ""
                    
                    raw_span = span_text.replace("\n", " ").replace("\r", " ")
                    time_match = re.search(r"(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})", raw_span)
                    publish_time = time_match.group(1) if time_match else ""
                    
                    purchaser_match = re.search(r"采购人：([^|]+)", raw_span)
                    purchaser = purchaser_match.group(1).strip() if purchaser_match else ""
                    
                    strongs = span.find_all("strong")
                    if len(strongs) >= 1:
                        notice_type = strongs[0].text.strip()
                    if len(strongs) >= 2:
                        project_type = strongs[1].text.strip()
                        
                    region_match = re.search(rf"{notice_type}\s*\|\s*([^|]+)\s*\|", raw_span)
                    if region_match:
                        region = region_match.group(1).strip()
                        
                    res_dict = {
                        "来源": "中国政府采购网",
                        "项目分类": "政府采购",
                        "项目阶段": notice_type,
                        "项目名称": title,
                        "发布时间": publish_time,
                        "招标人": purchaser,
                        "变更时间": "",
                        "计划招标时间": "",
                        "招标人联系人": "",
                        "招标人联系方式": "",
                        "招标代理机构": "",
                        "招标代理机构联系人": "",
                        "招标代理机构联系方式": "",
                        "中标人": "",
                        "中标人联系人": "",
                        "中标人联系方式": "",
                        "中标金额（元）": "",
                        "招标内容": project_type,
                        "项目地点": region,
                        "招标文件": href
                    }
                    results.append(res_dict)
                    
            except Exception as e:
                print(f"解析第 {page} 页时出错: {e}")
                
            time.sleep(2)
            
        print(f"共收集到基本信息 {len(results)} 条，开始进一步抓取详情页提取详细信息...")
        
        for idx, res in enumerate(results):
            try:
                det_headers = self.headers.copy()
                parsed_href = urllib.parse.urlparse(res["招标文件"])
                det_headers["Host"] = parsed_href.netloc
                
                det_r = self.session.get(res["招标文件"], headers=det_headers, timeout=10)
                det_r.encoding = 'utf-8'
                det_soup = BeautifulSoup(det_r.text, 'html.parser')
                text_content = det_soup.text.replace("\n", " ").replace("\r", " ").replace("\t", " ")
                
                detail_info = self._extract_detail(text_content)
                
                # Update base dict with detail info
                for k, v in detail_info.items():
                    if v and not res.get(k):
                        res[k] = v
                        
            except Exception as e:
                pass
            time.sleep(1)
                
        return results

    def save_to_csv(self, data, filename="bidding_data.csv"):
        if not data:
            print("没有可保存的数据。")
            return
            
        keys = [
            "来源", "项目分类", "项目阶段", "项目名称", "发布时间", 
            "招标人", "变更时间", "计划招标时间", "招标人联系人", "招标人联系方式", 
            "招标代理机构", "招标代理机构联系人", "招标代理机构联系方式", 
            "中标人", "中标人联系人", "中标人联系方式", "中标金额（元）", 
            "招标内容", "项目地点", "招标文件"
        ]
        with open(filename, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(data)
        print(f"成功将 {len(data)} 条数据保存至 {filename}")

def main():
    parser = argparse.ArgumentParser(description="招投标信息自动化采集工具")
    parser.add_argument("-k", "--keyword", default="", help="搜索关键词，不填则采集全部")
    parser.add_argument("-p", "--pages", type=int, default=1, help="采集页数，默认：1")
    parser.add_argument("-s", "--start_time", default="", help="开始时间，格式：YYYY-MM-DD")
    parser.add_argument("-e", "--end_time", default="", help="结束时间，格式：YYYY-MM-DD")
    parser.add_argument("-o", "--output", default="bidding_data.csv", help="导出CSV文件名")
    
    args = parser.parse_args()
    
    spider = BiddingSpider()
    data = spider.scrape_ccgp(args.keyword, args.start_time, args.end_time, args.pages)
    
    spider.save_to_csv(data, args.output)

if __name__ == "__main__":
    main()
