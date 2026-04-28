import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scraper import TenderScraper
from processor import DataProcessor
import time
import os

# 页面配置
st.set_page_config(page_title="招投标数据监控与分析系统", layout="wide", page_icon="📈")
st.title("📈 招投标信息自动化采集与分析平台")
st.markdown("该工具支持从招投标信息平台批量抓取相关公告信息，并自动进行清洗、去重与多维关联分析，辅助挖掘潜在商机。")

# --- 侧边栏：任务控制与参数设置 ---
st.sidebar.header("🎯 采集任务设置")
with st.sidebar.form("scrape_form"):
    keyword = st.text_input("关键字", value="大数据")
    region = st.selectbox("地区选择", ["全国", "北京", "上海", "广东", "江苏", "浙江", "四川"])
    limit = st.slider("采集条数(仅演示)", 10, 100, 20)
    submitted = st.form_submit_button("运行采集任务")

# --- 初始化加载已有数据 ---
data_file = "sample_data.csv"
if not os.path.exists(data_file):
    st.error(f"未找到初始示例数据文件 {data_file}，请先运行 generate_sample.py")
    st.stop()

# 定义状态来保存当前查看的数据
if 'current_data' not in st.session_state:
    st.session_state['current_data'] = pd.read_csv(data_file)
    st.session_state['data_source'] = "初始示例数据"

# --- 如果用户点击了采集，执行抓取并合并数据 ---
if submitted:
    with st.spinner(f"正在全网实时检索关键字: '{keyword}', 地区: '{region}'..."):
        scraper = TenderScraper()
        # 执行爬虫逻辑
        new_df = scraper.fetch_mock_data(keyword, region, limit)
        
        # 将新数据与老数据合并 (模拟数据库入库)
        old_df = st.session_state['current_data']
        combined_df = pd.concat([old_df, new_df], ignore_index=True)
        st.session_state['current_data'] = combined_df
        st.session_state['data_source'] = f"更新于 {time.strftime('%Y-%m-%d %H:%M:%S')} (包含新采集数据)"
        st.success(f"采集完成！新增 {len(new_df)} 条数据。")

# --- 数据清洗与分析 ---
df = st.session_state['current_data']
processor = DataProcessor(df=df)
clean_df = processor.clean_data()

st.markdown(f"**数据源状态**: `{st.session_state['data_source']}` | **当前有效数据总量**: `{len(clean_df)}` 条")

# --- 第一部分：指标卡片 ---
st.subheader("📊 宏观分析与商机概览")
col1, col2, col3, col4 = st.columns(4)
total_amount = clean_df['amount'].sum()
avg_amount = clean_df['amount'].mean()
total_projects = len(clean_df)
unique_tenderers = clean_df['tenderer'].nunique()

col1.metric("招投标项目总数", f"{total_projects} 个")
col2.metric("涉及总金额", f"{total_amount / 10000:,.2f} 万元")
col3.metric("平均预算/中标额", f"{avg_amount / 10000:,.2f} 万元")
col4.metric("潜在甲方单位数量", f"{unique_tenderers} 家")

st.markdown("---")

# --- 第二部分：数据分析与可视化图表 ---
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.write("### 📈 月度招投标金额趋势")
    trend_df = processor.trend_analysis()
    fig_trend = px.line(trend_df, x='month', y='总金额', text='项目数', 
                        title="各月度项目金额与数量趋势", markers=True)
    fig_trend.update_traces(textposition="top center")
    st.plotly_chart(fig_trend, use_container_width=True)

with row1_col2:
    st.write("### 💰 项目金额区间分布")
    dist_df = processor.amount_distribution()
    fig_pie = px.pie(dist_df, values='项目数量', names='金额区间', 
                     title="项目金额预算范围占比", hole=0.4)
    st.plotly_chart(fig_pie, use_container_width=True)

row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.write("### 🏆 高频中标单位 (竞品分析)")
    top_winners = processor.top_winners(10)
    fig_winners = px.bar(top_winners, x='中标次数', y='winner', orientation='h', 
                         title="中标频次 TOP 10 单位", color='累计金额')
    fig_winners.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_winners, use_container_width=True)

with row2_col2:
    st.write("### 💼 热门招标单位 (大客户推荐)")
    top_tenderers = processor.top_tenderers(10)
    fig_tenderers = px.bar(top_tenderers, x='发布次数', y='tenderer', orientation='h', 
                           title="高频招标单位 TOP 10", color='总预算金额')
    fig_tenderers.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_tenderers, use_container_width=True)

# --- 第三部分：数据明细表 ---
st.markdown("---")
st.subheader("📋 招投标明细数据池")

# 排序筛选过滤功能
sort_col = st.selectbox("排序维度", ["发布时间倒序", "金额从大到小", "金额从小到大"])
if sort_col == "发布时间倒序":
    display_df = processor.sort_data(by='publish_date', ascending=False)
elif sort_col == "金额从大到小":
    display_df = processor.sort_data(by='amount', ascending=False)
else:
    display_df = processor.sort_data(by='amount', ascending=True)

# 转换为展示用格式
display_df['publish_date'] = display_df['publish_date'].dt.strftime('%Y-%m-%d')
st.dataframe(display_df, use_container_width=True, height=400)
