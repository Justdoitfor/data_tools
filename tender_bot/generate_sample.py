import csv
import random
from datetime import datetime, timedelta

def generate_sample_data(filename):
    regions = ["北京", "上海", "广东", "江苏", "浙江", "四川", "山东", "湖北", "河南", "陕西"]
    project_types = ["工程", "服务", "货物"]
    notice_types = ["招标公告", "中标结果", "变更公告"]
    
    companies = [f"科技有限责任公司{i}部" for i in range(1, 20)]
    tenderers = [f"{r}市公安局" for r in regions] + [f"{r}省教育厅" for r in regions] + [f"中国XX集团{r}分公司" for r in regions]
    keywords = ["大数据平台", "智慧城市系统", "服务器采购", "安防监控工程", "办公电脑采购", "云服务租赁", "信息化改造", "网络安全设备", "数据中心机房建设", "政务云迁移"]

    headers = ["project_name", "tenderer", "winner", "amount", "publish_date", "region", "project_type", "notice_type", "source_url"]
    
    start_date = datetime.strptime("2023-01-01", "%Y-%m-%d")
    
    with open(filename, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        
        for i in range(1, 201):
            region = random.choice(regions)
            project_type = random.choice(project_types)
            notice_type = random.choice(notice_types)
            keyword = random.choice(keywords)
            
            project_name = f"{region}2023年度{keyword}项目"
            tenderer = random.choice([t for t in tenderers if region in t] or tenderers)
            
            # 招标公告往往没有中标单位
            if notice_type == "招标公告":
                winner = ""
            else:
                winner = random.choice(companies)
                
            # 金额在10万到5000万之间
            amount = round(random.uniform(10_0000, 5000_0000), 2)
            
            # 日期
            days_offset = random.randint(0, 360)
            publish_date = (start_date + timedelta(days=days_offset)).strftime("%Y-%m-%d")
            
            source_url = f"http://example-gov-bidding.com/article/{i}"
            
            writer.writerow([
                project_name, tenderer, winner, amount, publish_date, region, project_type, notice_type, source_url
            ])
            
            # 模拟脏数据（用于演示清洗逻辑）：偶尔制造重复项或缺失字段
            if random.random() < 0.05:
                writer.writerow([
                    project_name, tenderer, winner, amount, publish_date, region, project_type, notice_type, source_url
                ])

if __name__ == "__main__":
    generate_sample_data("sample_data.csv")
    print("Sample data generated successfully: sample_data.csv")
