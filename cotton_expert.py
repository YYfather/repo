import streamlit as st
import bisect
import pandas as pd

# ================= 1. 核心逻辑 (复用之前的优化代码) =================
RULES_DB = {
    "硼 B (mg/kg)": ([0.2, 0.5, 1.0, 2.0], ["1 (很缺)", "2 (缺)", "3 (适中)", "4 (丰)", "5 (很丰)"]),
    "钼 Mo (mg/kg)": ([0.1, 0.15, 0.2, 0.3], ["1 (很缺)", "2 (缺)", "3 (适中)", "4 (丰)", "5 (很丰)"]),
    "锰 Mn (mg/kg)": ([1.0, 5.0, 15.0, 30.0], ["1 (很缺)", "2 (缺)", "3 (适中)", "4 (丰)", "5 (很丰)"]),
    "锌 Zn (mg/kg)": ([0.3, 0.5, 1.0, 3.0], ["1 (很缺)", "2 (缺)", "3 (适中)", "4 (丰)", "5 (很丰)"]),
    "铜 Cu (mg/kg)": ([0.1, 0.2, 1.0, 1.8], ["1 (很缺)", "2 (缺)", "3 (适中)", "4 (丰)", "5 (很丰)"]),
    "铁 Fe (mg/kg)": ([2.5, 4.5, 10.0, 20.0], ["1 (很缺)", "2 (缺)", "3 (适中)", "4 (丰)", "5 (很丰)"]),
    "有机质(北疆) g/kg": ([12.0, 15.0, 18.0], ["极低", "低", "中", "高"]),
    "有机质(南疆) g/kg": ([8.0, 12.0, 16.0], ["极低", "低", "中", "高"]),
    "碱解氮 ppm": ([40.0, 60.0, 90.0], ["极低", "低", "中", "高"]),
    "有效磷 ppm": ([7.0, 13.0, 30.0], ["极低", "低", "中", "高"]),
    "速效钾 ppm": ([80.0, 160.0, 210.0], ["极低", "低", "中", "高"])
}

def evaluate_soil(measurements):
    results = []
    for item_name, value in measurements.items():
        if item_name not in RULES_DB or value is None:
            continue
        thresholds, grades = RULES_DB[item_name]
        index = bisect.bisect_right(thresholds, value)
        grade = grades[index] if 0 <= index < len(grades) else "异常"
        
        # 简单的颜色标记逻辑
        status = "正常"
        if "缺" in grade or "低" in grade: status = "缺乏"
        elif "丰" in grade or "高" in grade: status = "丰富"
        
        results.append({
            "检测项目": item_name,
            "检测数值": value,
            "评估等级": grade,
            "状态": status
        })
    return results

# ================= 2. Streamlit 界面构建 =================

# 页面配置
st.set_page_config(page_title="土壤养分专家系统", page_icon="🌱")

st.title("🌱 土壤养分智能评估系统")
st.markdown("请输入土壤检测报告中的数值，系统将自动生成评价等级。")

# 创建侧边栏输入区
st.sidebar.header("📝 输入检测数据")
st.sidebar.info("提示：不需要填写的项目请留空或保持为 0")

# --- 区域选择 (处理有机质) ---
region = st.sidebar.radio("选择种植区域 (影响有机质标准)", ("北疆", "南疆"))

# --- 输入表单 ---
inputs = {}

with st.sidebar.expander("基础养分 (必填)", expanded=True):
    # 有机质特殊处理
    om_val = st.number_input("有机质 (g/kg)", min_value=0.0, step=0.1, format="%.2f")
    if om_val > 0:
        inputs[f"有机质({region}) g/kg"] = om_val
        
    inputs["碱解氮 ppm"] = st.number_input("碱解氮 (ppm)", min_value=0.0, step=1.0)
    inputs["有效磷 ppm"] = st.number_input("有效磷 (ppm)", min_value=0.0, step=0.1)
    inputs["速效钾 ppm"] = st.number_input("速效钾 (ppm)", min_value=0.0, step=1.0)

with st.sidebar.expander("微量元素 (选填)", expanded=False):
    inputs["铁 Fe (mg/kg)"] = st.number_input("铁 Fe", min_value=0.0, step=0.1)
    inputs["锰 Mn (mg/kg)"] = st.number_input("锰 Mn", min_value=0.0, step=0.1)
    inputs["铜 Cu (mg/kg)"] = st.number_input("铜 Cu", min_value=0.0, step=0.01)
    inputs["锌 Zn (mg/kg)"] = st.number_input("锌 Zn", min_value=0.0, step=0.01)
    inputs["硼 B (mg/kg)"]  = st.number_input("硼 B", min_value=0.0, step=0.01)
    inputs["钼 Mo (mg/kg)"] = st.number_input("钼 Mo", min_value=0.0, step=0.001, format="%.3f")

# 过滤掉为0的输入 (假设0为未检测，如果0是有效值需调整逻辑)
valid_inputs = {k: v for k, v in inputs.items() if v > 0}

# ================= 3. 结果展示区 =================

if st.button("开始评估", type="primary"):
    if not valid_inputs:
        st.warning("请在侧边栏至少输入一项有效数据！")
    else:
        # 计算结果
        report_data = evaluate_soil(valid_inputs)
        df = pd.DataFrame(report_data)

        # 1. 总体概览
        st.subheader("📊 评估报告")
        
        # 2. 表格展示 (使用 dataframe 高亮功能)
        def color_status(val):
            color = 'black'
            if '缺' in val or '低' in val: color = 'red'
            elif '丰' in val or '高' in val: color = 'green'
            elif '适中' in val or '中' in val: color = 'blue'
            return f'color: {color}; font-weight: bold'

        st.dataframe(
            df.style.map(color_status, subset=['评估等级']),
            use_container_width=True,
            hide_index=True
        )

        # 3. 专家建议 (动态生成)
        st.subheader("💡 施肥建议")
        lacking = [item['检测项目'].split(' ')[0] for item in report_data if '缺' in item['评估等级'] or '低' in item['评估等级']]
        
        if lacking:
            st.error(f"⚠️ 注意：土壤缺乏 **{'、'.join(lacking)}**，建议重点补充相应肥料。")
        else:
            st.success("✅ 土壤养分状况良好，请继续保持平衡施肥。")

else:
    st.info("👈 请在左侧输入数据后点击“开始评估”")
