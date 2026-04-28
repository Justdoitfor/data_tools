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

    def _clean_spaces(self, text):
        return re.sub(r"\s+", " ", text or "").strip()

    def _extract_section(self, text, start_marker, end_markers):
        if not text or not start_marker:
            return ""
        start_idx = text.find(start_marker)
        if start_idx < 0:
            return ""
        end_idx = len(text)
        for m in end_markers or []:
            i = text.find(m, start_idx + len(start_marker))
            if i >= 0 and i < end_idx:
                end_idx = i
        return text[start_idx:end_idx]

    def _extract_phones(self, text):
        if not text:
            return []
        matches = re.findall(r"(?:\d{3,4}-\d{7,8}|\d{11}|\d{7,8})", text)
        seen = set()
        out = []
        for m in matches:
            if m not in seen:
                seen.add(m)
                out.append(m)
        return out

    def _extract_contact_name(self, text):
        if not text:
            return ""
        m = re.search(r"项目联系人[：:\s]*([\u4e00-\u9fa5A-Za-z·•]{2,20})", text)
        return m.group(1).strip() if m else ""
        
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
            "计划招标时间": "",
            "招标内容": "" # 新增完整内容
        }

        text_content = self._clean_spaces(text_content)
        detail_info["招标内容"] = text_content
        
        # 中标金额
        am = re.search(r"(?:中标|成交)(?:总)?金额[：:\s]*([0-9.,]+(?:\s*万元|元|万|%))", text_content)
        if am: detail_info["中标金额（元）"] = am.group(1).strip()
            
        # 中标人
        wm = re.search(r"(?:中标|成交)(?:人|供应商)(?:名称)?[：:\s]*([\u4e00-\u9fa5A-Za-z0-9_()（）]+(?:公司|中心|厂|院))", text_content)
        if wm: detail_info["中标人"] = wm.group(1).strip()
            
        # 招标代理机构
        agent_m = re.search(r"(?:代理机构|采购代理机构)(?:名称)?[：:\s]*([\u4e00-\u9fa5A-Za-z0-9_()（）]+(?:公司|中心|厂|院|局))", text_content)
        if agent_m: detail_info["招标代理机构"] = agent_m.group(1).strip()

        buyer_sec = self._extract_section(
            text_content,
            "采购人信息",
            ["采购代理机构信息", "采购代理机构", "项目联系方式", "3.项目联系方式", "3. 项目联系方式"],
        )
        if buyer_sec:
            buyer_phones = self._extract_phones(buyer_sec)
            if buyer_phones:
                detail_info["招标人联系方式"] = buyer_phones[0]
            detail_info["招标人联系人"] = self._extract_contact_name(buyer_sec)

        agent_sec = self._extract_section(
            text_content,
            "采购代理机构信息",
            ["项目联系方式", "3.项目联系方式", "3. 项目联系方式"],
        )
        if agent_sec:
            agent_phones = self._extract_phones(agent_sec)
            if agent_phones:
                detail_info["招标代理机构联系方式"] = agent_phones[0]
            detail_info["招标代理机构联系人"] = self._extract_contact_name(agent_sec)

        project_sec = self._extract_section(
            text_content,
            "项目联系方式",
            ["十、", "十.", "附件", "附件：", "招标文件", "公告期限"],
        )
        if project_sec:
            project_name = self._extract_contact_name(project_sec)
            project_phones = self._extract_phones(project_sec)
            if project_name and not detail_info["招标代理机构联系人"] and not detail_info["招标人联系人"]:
                detail_info["招标代理机构联系人"] = project_name
            if project_phones and not detail_info["招标代理机构联系方式"] and not detail_info["招标人联系方式"]:
                detail_info["招标代理机构联系方式"] = project_phones[0]

        if detail_info["招标代理机构联系方式"]:
            detail_info["招标代理机构联系方式"] = re.sub(r"[^\d\-]", "", detail_info["招标代理机构联系方式"])
        if detail_info["招标人联系方式"]:
            detail_info["招标人联系方式"] = re.sub(r"[^\d\-]", "", detail_info["招标人联系方式"])
        if detail_info["中标人联系方式"]:
            detail_info["中标人联系方式"] = re.sub(r"[^\d\-]", "", detail_info["中标人联系方式"])

        # 粗略提取地址
        addr_m = re.search(r"项目地点[：:\s]*([\u4e00-\u9fa5A-Za-z0-9_()（）]+)", text_content)
        if addr_m: detail_info["项目地点"] = addr_m.group(1).strip()
            
        # 变更时间/计划招标时间
        change_time_m = re.search(r"更正日期[：:\s]*(\d{4}年\d{1,2}月\d{1,2}日|\d{4}-\d{1,2}-\d{1,2})", text_content)
        if change_time_m: detail_info["变更时间"] = change_time_m.group(1).strip()
            
        plan_time_m = re.search(r"预计采购时间[：:\s]*(\d{4}年\d{1,2}月|\d{4}-\d{1,2})", text_content)
        if plan_time_m: detail_info["计划招标时间"] = plan_time_m.group(1).strip()
            
        return detail_info
        
    def scrape_ccgp(self, keyword, start_time, end_time, max_pages=1):
        results = []
        try:
            self.session.get("https://search.ccgp.gov.cn/", headers=self.headers, timeout=10)
        except:
            pass

        encoded_kw = urllib.parse.quote(keyword) if keyword else "%20"
        st = start_time.replace("-", "%3A") if start_time else ""
        et = end_time.replace("-", "%3A") if end_time else ""
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
                    if len(strongs) >= 1: notice_type = strongs[0].text.strip()
                    if len(strongs) >= 2: project_type = strongs[1].text.strip()
                        
                    region_match = re.search(rf"{notice_type}\s*\|\s*([^|]+)\s*\|", raw_span)
                    if region_match: region = region_match.group(1).strip()
                        
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
                        "招标内容": "",
                        "项目地点": region,
                        "招标文件": href
                    }
                    results.append(res_dict)
                    
            except Exception as e:
                print(f"解析第 {page} 页时出错: {e}")
                
            time.sleep(2)
            
        print(f"共收集到基本信息 {len(results)} 条，开始进一步抓取详情页提取详细信息与完整正文...")
        
        for idx, res in enumerate(results):
            print(f"  -> 正在抓取详情页 [{idx+1}/{len(results)}]: {res['项目名称'][:20]}...")
            try:
                det_headers = self.headers.copy()
                parsed_href = urllib.parse.urlparse(res["招标文件"])
                det_headers["Host"] = parsed_href.netloc
                
                det_r = self.session.get(res["招标文件"], headers=det_headers, timeout=5)
                det_r.encoding = det_r.apparent_encoding or "utf-8"
                det_soup = BeautifulSoup(det_r.text, 'html.parser')
                
                # 寻找核心正文区域
                content_div = det_soup.select_one(".vF_detail_content")
                if not content_div:
                    content_div = det_soup.select_one(".vT_detail_content")
                if not content_div:
                    content_div = det_soup.select_one(".main") or det_soup.find("body")
                    
                # 替换各种不可见字符为空格
                text_content = content_div.get_text("\n").replace("\r", "\n").replace("\t", "\n")
                
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
