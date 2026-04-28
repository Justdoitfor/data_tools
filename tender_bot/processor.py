import pandas as pd
import numpy as np

class DataProcessor:
    def __init__(self, data_path: str = None, df: pd.DataFrame = None):
        if df is not None:
            self.df = df
        elif data_path:
            self.df = pd.read_csv(data_path)
        else:
            raise ValueError("Must provide either data_path or df.")
            
    def clean_data(self):
        """数据清洗与去重"""
        # 1. 删除关键字段为空的行
        self.df = self.df.dropna(subset=['project_name', 'amount'])
        
        # 2. 去重（同一项目，同一地区，同一公告类型）
        before_count = len(self.df)
        self.df = self.df.drop_duplicates(subset=['project_name', 'region', 'notice_type'], keep='last')
        after_count = len(self.df)
        print(f"[*] 去重完成：清理了 {before_count - after_count} 条重复数据。当前有效数据: {after_count} 条。")
        
        # 3. 数据类型转换
        self.df['amount'] = pd.to_numeric(self.df['amount'], errors='coerce')
        self.df['publish_date'] = pd.to_datetime(self.df['publish_date'], errors='coerce')
        
        # 4. 填充缺失值
        self.df['winner'] = self.df['winner'].fillna('未知')
        self.df['tenderer'] = self.df['tenderer'].fillna('未知')
        
        return self.df

    def sort_data(self, by='publish_date', ascending=False):
        """多维排序"""
        if by in self.df.columns:
            return self.df.sort_values(by=by, ascending=ascending)
        return self.df

    def top_winners(self, top_n=10):
        """招投标主体关联分析：高频中标单位"""
        # 排除“未知”或空字符串
        df_winners = self.df[(self.df['winner'] != '未知') & (self.df['winner'] != '')]
        
        if df_winners.empty:
            return pd.DataFrame()
            
        top = df_winners.groupby('winner').agg(
            中标次数=('project_name', 'count'),
            累计金额=('amount', 'sum')
        ).sort_values(by='中标次数', ascending=False).head(top_n).reset_index()
        return top

    def top_tenderers(self, top_n=10):
        """高频发布招标的单位（商机推荐）"""
        top = self.df.groupby('tenderer').agg(
            发布次数=('project_name', 'count'),
            总预算金额=('amount', 'sum')
        ).sort_values(by='发布次数', ascending=False).head(top_n).reset_index()
        return top

    def amount_distribution(self):
        """项目金额区间统计"""
        bins = [0, 500000, 2000000, 10000000, float('inf')]
        labels = ['50万以下', '50-200万', '200-1000万', '1000万以上']
        self.df['金额区间'] = pd.cut(self.df['amount'], bins=bins, labels=labels, right=False)
        dist = self.df['金额区间'].value_counts().reset_index()
        dist.columns = ['金额区间', '项目数量']
        return dist
        
    def trend_analysis(self):
        """趋势分析：按月统计金额"""
        df_trend = self.df.copy()
        df_trend['month'] = df_trend['publish_date'].dt.to_period('M').astype(str)
        trend = df_trend.groupby('month').agg(
            项目数=('project_name', 'count'),
            总金额=('amount', 'sum')
        ).reset_index()
        return trend.sort_values(by='month')

if __name__ == "__main__":
    # 简单测试逻辑
    processor = DataProcessor(data_path="sample_data.csv")
    processor.clean_data()
    print("高频中标单位 Top 3:")
    print(processor.top_winners(3))
    print("金额分布:")
    print(processor.amount_distribution())
