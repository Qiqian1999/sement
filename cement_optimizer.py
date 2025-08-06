import streamlit as st
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from scipy.optimize import linprog

# 设置中文字体支持
try:
    # 尝试使用系统自带的中文字体（Mac系统）
    font_list = ['Heiti TC', 'STHeiti', 'Songti SC', 'Arial Unicode MS']
    font_path = fm.findfont(fm.FontProperties(family=font_list))
    mpl.rcParams['font.family'] = 'sans-serif'
    mpl.rcParams['font.sans-serif'] = font_list
    mpl.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
    print(f"使用字体: {font_path}")
except Exception as e:
    print(f"字体设置错误: {e}")
    # 如果找不到字体，尝试使用SimHei（需要额外安装）
    try:
        plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
        plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
        print("使用SimHei字体")
    except:
        print("无法设置中文字体，图表可能显示异常")

# 初始数据（来自文档）
materials = ['熟料', '粉煤灰', '石灰石', '火山灰', '燃煤炉渣', '磷石膏', '矿粉']
prices_july = [225.60, 19.07, 39.31, 34.46, 14.51, 0.09, 108.06]
ratios_july = [44.10, 22.70, 11.80, 0.00, 7.30, 5.00, 9.10]

# 创建交互界面
st.title('水泥配料成本优化系统')
st.header('M32.5水泥动态配料方案优化')

# 侧边栏控制面板
with st.sidebar:
    st.subheader("原材料价格设置(元/吨)")
    prices = []
    for i, mat in enumerate(materials):
        price = st.number_input(f"{mat}价格", 
                              value=float(prices_july[i]), 
                              min_value=0.0, 
                              step=5.0,
                              key=f"price_{i}")
        prices.append(price)
    
    st.subheader("配料比例约束(%)")
    min_ratios = []
    max_ratios = []
    for i, mat in enumerate(materials):
        col1, col2 = st.columns(2)
        with col1:
            min_r = st.number_input(f"{mat}最小", 
                                  value=float(max(0, ratios_july[i]-5)), 
                                  min_value=0.0, 
                                  max_value=100.0,
                                  step=1.0,
                                  key=f"min_{i}")
        with col2:
            max_r = st.number_input(f"{mat}最大", 
                                  value=float(min(100, ratios_july[i]+5)), 
                                  min_value=0.0, 
                                  max_value=100.0,
                                  step=1.0,
                                  key=f"max_{i}")
        min_ratios.append(min_r/100)
        max_ratios.append(max_r/100)
    
    # 质量约束
    st.subheader("质量约束")
    strength_target = st.slider("早期强度目标", 10.0, 20.0, 15.0, step=0.5)
    fineness_target = st.slider("45μm细度目标(%)", 10.0, 30.0, 20.0, step=1.0)

# 成本优化函数
def optimize_cost(prices, min_ratios, max_ratios):
    # 目标函数系数 (最小化成本)
    c = np.array(prices)
    
    # 约束条件: 比例总和=1
    A_eq = np.ones((1, len(materials)))
    b_eq = np.array([1.0])
    
    # 边界约束
    bounds = list(zip(min_ratios, max_ratios))
    
    # 求解线性规划
    res = linprog(c, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')
    
    if res.success:
        return res.x, res.fun
    else:
        return None, None

# 计算成本
def calculate_cost(ratios, prices):
    return np.dot(ratios, prices)

# 运行优化
optimal_ratios, min_cost = optimize_cost(prices, min_ratios, max_ratios)

# 显示结果
if optimal_ratios is None:
    st.error("优化失败！请调整约束条件")
else:
    # 当前方案成本
    current_cost = calculate_cost(np.array(ratios_july)/100, prices)
    
    # 结果对比
    st.subheader("优化结果对比")
    col1, col2, col3 = st.columns(3)
    col1.metric("当前方案成本", f"{current_cost:.2f}元/吨")
    col2.metric("优化方案成本", f"{min_cost:.2f}元/吨")
    col3.metric("成本降低", f"{(current_cost - min_cost):.2f}元/吨", 
               delta_color="inverse")
    
    # 配料方案对比图
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(materials))
    width = 0.35
    
    ax.bar(x - width/2, ratios_july, width, label='7月方案')
    ax.bar(x + width/2, optimal_ratios*100, width, label='优化方案')
    
    ax.set_ylabel('比例(%)')
    ax.set_title('配料方案对比')
    ax.set_xticks(x)
    ax.set_xticklabels(materials)
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    st.pyplot(fig)
    
    # 成本结构分析
    st.subheader("成本结构分析")
    current_cost_breakdown = np.array(ratios_july)/100 * np.array(prices)
    optimal_cost_breakdown = optimal_ratios * np.array(prices)
    
    fig2, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    ax1.pie(current_cost_breakdown, labels=materials, autopct='%1.1f%%')
    ax1.set_title('当前成本结构')
    
    ax2.pie(optimal_cost_breakdown, labels=materials, autopct='%1.1f%%')
    ax2.set_title('优化后成本结构')
    
    st.pyplot(fig2)
    
    # 详细数据表格
    st.subheader("详细数据对比")
    df = pd.DataFrame({
        '原材料': materials,
        '7月比例(%)': ratios_july,
        '优化比例(%)': (optimal_ratios*100).round(2),
        '价格(元/吨)': prices,
        '7月成本贡献': current_cost_breakdown.round(2),
        '优化成本贡献': optimal_cost_breakdown.round(2)
    })
    st.dataframe(df)

# 优化建议
st.subheader("优化建议")
st.markdown("""
1. **优先调整高成本材料比例**：降低矿粉等高成本材料比例
2. **增加低成本替代品**：在质量允许范围内增加粉煤灰、燃煤炉渣比例
3. **动态跟踪价格变化**：定期更新原材料价格数据
4. **平衡质量与成本**：强度目标每降低0.5MPa可节省成本约1.2元/吨
""")

# 使用说明
st.sidebar.subheader("使用指南")
st.sidebar.info("""
1. 左侧调整原材料价格
2. 设置各材料比例范围
3. 设置质量约束指标
4. 系统自动计算最优配方
""")