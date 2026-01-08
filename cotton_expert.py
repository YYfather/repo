import streamlit as st
import bisect
import pandas as pd
from datetime import datetime

# ================= 1. 肥料知识库 =================
FERTILIZER_KNOWLEDGE = {
    "硼 B (mg/kg)": {
        "缺乏": {
            "肥料类型": "硼砂、水溶性硼肥",
            "施用方法": ["基施：缺硼田块基施硼砂 1.0-1.5 kg/亩", 
                      "叶面喷施：现蕾-开花期喷施 0.1%-0.2% 硼砂溶液，亩用100-150g水溶性硼肥"],
            "注意事项": "硼砂需用温水溶解，避免与碱性农药混用",
            "来源": "新疆农业农村厅《2024年春季主要农作物科学施肥指导意见》"
        },
        "丰富": "硼元素充足，无需额外补充，避免硼中毒影响棉花生长"
    },
    
    "钼 Mo (mg/kg)": {
        "缺乏": {
            "肥料类型": "钼酸铵",
            "施用方法": ["叶面喷施：苗期或蕾期喷施0.05%-0.1%钼酸铵溶液，1-2次"],
            "注意事项": "钼肥用量极少，需精确称量，避免过量",
            "来源": "《棉花科学施肥指导意见》微量元素部分"
        },
        "丰富": "钼元素充足，无需补充"
    },
    
    "锰 Mn (mg/kg)": {
        "缺乏": {
            "肥料类型": "硫酸锰",
            "施用方法": ["基施：缺锰田块基施硫酸锰 1-2 kg/亩",
                      "叶面喷施：蕾期-花期喷施0.2%-0.3%硫酸锰溶液"],
            "注意事项": "锰肥可与多数农药混用，避免与碱性物质混用",
            "来源": "新疆2024年微量元素施肥指导意见"
        },
        "丰富": "锰元素充足"
    },
    
    "锌 Zn (mg/kg)": {
        "缺乏": {
            "肥料类型": "硫酸锌",
            "施用方法": ["基施：缺锌田块基施硫酸锌 1-2 kg/亩",
                      "叶面喷施：蕾期、初花期、盛花期喷施0.2%-0.3%硫酸锌溶液"],
            "注意事项": "锌肥可与磷肥配合施用，提高利用率",
            "来源": "新疆2024年微量元素施肥指导意见"
        },
        "丰富": "锌元素充足"
    },
    
    "铜 Cu (mg/kg)": {
        "缺乏": {
            "肥料类型": "硫酸铜",
            "施用方法": ["基施：缺铜田块基施硫酸铜 1-2 kg/亩",
                      "叶面喷施：蕾期-花期喷施0.1%-0.2%硫酸铜溶液"],
            "注意事项": "铜肥有毒性，严格按推荐用量施用",
            "来源": "新疆2024年微量元素施肥指导意见"
        },
        "丰富": "铜元素充足"
    },
    
    "铁 Fe (mg/kg)": {
        "缺乏": {
            "肥料类型": "硫酸亚铁、螯合铁",
            "施用方法": ["基施：缺铁田块基施硫酸亚铁 2-3 kg/亩",
                      "叶面喷施：现蕾后喷施0.2%-0.3%硫酸亚铁溶液"],
            "注意事项": "铁肥易氧化失效，建议与有机肥配合施用或使用螯合铁",
            "来源": "新疆2024年微量元素施肥指导意见"
        },
        "丰富": "铁元素充足"
    },
    
    "有机质 g/kg": {
        "缺乏": {
            "肥料类型": "棉籽饼、牛羊粪堆肥、商品有机肥",
            "施用方法": ["北疆：亩施棉籽饼50-100kg或牛羊粪堆肥600-1000kg",
                      "南疆：亩施优质堆肥类有机肥2吨以上",
                      "秸秆还田：棉花秸秆全部还田"],
            "注意事项": "有机肥需充分腐熟，避免烧苗",
            "来源": "《2025年棉花科学施肥指导意见》西北棉区与黄淮海棉区部分"
        },
        "丰富": "有机质含量适宜，保持现有施肥措施"
    },
    
    "碱解氮 ppm": {
        "缺乏": {
            "肥料类型": "尿素、炭基肥、复合肥",
            "施用方法": ["基施：常规氮肥按需施用",
                      "追施：减氮15%配施炭基肥可提高氮素利用率至55.1%",
                      "分期施用：增加蕾期-花铃期施用比例"],
            "注意事项": "氮肥深施覆土，减少挥发损失",
            "来源": "《减氮配施炭基肥对棉田土壤养分、氮素利用率及产量的影响》"
        },
        "丰富": "氮素充足，注意平衡施肥，避免旺长"
    },
    
    "有效磷 ppm": {
        "缺乏": {
            "肥料类型": "磷酸二氢钾、磷酸一铵、过磷酸钙",
            "施用方法": ["基施：磷肥全层深施",
                      "叶面喷施：盛花期后喷施0.3%-0.5%磷酸二氢钾，7-10天一次，连续2-3次",
                      "滴灌：水溶性磷肥随水滴施"],
            "注意事项": "磷肥移动性差，需靠近根系施用",
            "来源": "《2025年棉花科学施肥指导意见》"
        },
        "丰富": "磷素充足，可适当减少磷肥用量"
    },
    
    "速效钾 ppm": {
        "缺乏": {
            "肥料类型": "氯化钾、硫酸钾",
            "施用方法": ["基施：黄淮海棉区适宜氯化钾用量约150kg/ha（约10kg/亩）",
                      "追施：新疆棉区钾肥基追各半，亩用量5-10kg K₂O",
                      "滴灌：水溶性钾肥随水滴施"],
            "注意事项": "氯化钾适合多数土壤，盐碱地建议用硫酸钾",
            "来源": "《黄淮海地区钾肥对棉花产量的影响及最佳钾肥施用量研究》"
        },
        "丰富": "钾素充足，注意氮钾平衡"
    }
}

# 综合施肥原则
GENERAL_PRINCIPLES = [
    "📊 **测土配方施肥**：依据土壤检测结果和棉花目标产量确定肥料配比",
    "🌱 **有机无机配合**：推行秸秆还田，有机肥替代氮肥比例10%-20%",
    "⚡ **微量元素针对性补充**：缺啥补啥，消除高产障碍因素",
    "💧 **水肥一体化**：滴灌棉区推荐水溶肥与水肥一体化技术",
    "📅 **分期施肥**：氮肥分期施用，增加生育中期（蕾期-花铃期）比例"
]

# ================= 2. 核心评估逻辑 =================
RULES_DB = {
    "硼 B (mg/kg)": ([0.2, 0.5, 1.0, 2.0], ["1 (很缺)", "2 (缺)", "3 (适中)", "4 (丰)", "5 (很丰)"]),
    "钼 Mo (mg/kg)": ([0.1, 0.15, 0.2, 0.3], ["1 (很缺)", "2 (缺)", "3 (适中)", "4 (丰)", "5 (很丰)"]),
    "锰 Mn (mg/kg)": ([1.0, 5.0, 15.0, 30.0], ["1 (很缺)", "2 (缺)", "3 (适中)", "4 (丰)", "5 (很丰)"]),
    "锌 Zn (mg/kg)": ([0.3, 0.5, 1.0, 3.0], ["1 (很缺)", "2 (缺)", "3 (适中)", "4 (丰)", "5 (很丰)"]),
    "铜 Cu (mg/kg)": ([0.1, 0.2, 1.0, 1.8], ["1 (很缺)", "2 (缺)", "3 (适中)", "4 (丰)", "5 (很丰)"]),
    "铁 Fe (mg/kg)": ([2.5, 4.5, 10.0, 20.0], ["1 (很缺)", "2 (缺)", "3 (适中)", "4 (丰)", "5 (很丰)"]),
    "有机质 g/kg": ([12.0, 15.0, 18.0], ["极低", "低", "中", "高"]),  # 默认北疆标准，运行时根据区域调整
    "碱解氮 ppm": ([40.0, 60.0, 90.0], ["极低", "低", "中", "高"]),
    "有效磷 ppm": ([7.0, 13.0, 30.0], ["极低", "低", "中", "高"]),
    "速效钾 ppm": ([80.0, 160.0, 210.0], ["极低", "低", "中", "高"])
}

def evaluate_soil(measurements):
    """评估土壤养分状况"""
    results = []
    for item_name, value in measurements.items():
        if item_name not in RULES_DB or value is None:
            continue
        thresholds, grades = RULES_DB[item_name]
        index = bisect.bisect_right(thresholds, value)
        grade = grades[index] if 0 <= index < len(grades) else "异常"
        
        # 状态分类
        status = "正常"
        if "缺" in grade or "低" in grade: 
            status = "缺乏"
        elif "丰" in grade or "高" in grade: 
            status = "丰富"
        
        results.append({
            "检测项目": item_name,
            "检测数值": value,
            "评估等级": grade,
            "状态": status
        })
    return results

def generate_fertilizer_recommendations(results):
    """根据评估结果生成详细的肥料建议"""
    recommendations = []
    
    for item in results:
        item_name = item["检测项目"]
        status = item["状态"]
        grade = item["评估等级"]
        
        if item_name in FERTILIZER_KNOWLEDGE:
            knowledge = FERTILIZER_KNOWLEDGE[item_name]
            nutrient_name = item_name.split()[0]  # 提取养分名称
            
            if status == "缺乏" and "缺乏" in knowledge:
                advice = knowledge["缺乏"]
                rec = {
                    "养分": nutrient_name,
                    "状态": f"{status} ({grade})",
                    "推荐肥料": advice["肥料类型"],
                    "施用方法": "；".join(advice["施用方法"]),
                    "注意事项": advice.get("注意事项", ""),
                    "数据来源": advice.get("来源", "")
                }
                recommendations.append(rec)
            elif status == "丰富" and "丰富" in knowledge:
                rec = {
                    "养分": nutrient_name,
                    "状态": f"{status} ({grade})",
                    "建议": knowledge["丰富"],
                    "数据来源": knowledge.get("缺乏", {}).get("来源", "通用施肥指南")
                }
                recommendations.append(rec)
            elif status == "正常":
                rec = {
                    "养分": nutrient_name,
                    "状态": f"{status} ({grade})",
                    "建议": "保持现有施肥管理",
                    "数据来源": "系统评估"
                }
                recommendations.append(rec)
    
    return recommendations

def export_advice_text(region, fertilizer_recs):
    """生成可导出的施肥建议文本"""
    advice_text = "=" * 60 + "\n"
    advice_text += "新疆棉田土壤养分施肥建议方案\n"
    advice_text += "=" * 60 + "\n"
    advice_text += f"评估时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    advice_text += f"种植区域: {region}\n"
    advice_text += "-" * 60 + "\n\n"
    
    # 缺乏养分建议
    lacking_items = [r for r in fertilizer_recs if "缺乏" in r["状态"]]
    if lacking_items:
        advice_text += "【需重点补充的养分】\n\n"
        for rec in lacking_items:
            advice_text += f"■ {rec['养分']} ({rec['状态']})\n"
            advice_text += f"  推荐肥料: {rec['推荐肥料']}\n"
            advice_text += f"  施用方法: {rec['施用方法']}\n"
            if rec['注意事项']:
                advice_text += f"  注意事项: {rec['注意事项']}\n"
            advice_text += f"  依据来源: {rec['数据来源']}\n\n"
    
    # 丰富养分提醒
    abundant_items = [r for r in fertilizer_recs if "丰富" in r["状态"]]
    if abundant_items:
        advice_text += "【养分充足项目】\n\n"
        for rec in abundant_items:
            advice_text += f"✓ {rec['养分']}: {rec['建议']}\n"
        advice_text += "\n"
    
    # 综合原则
    advice_text += "【综合施肥原则】\n"
    for principle in GENERAL_PRINCIPLES:
        advice_text += f"• {principle.replace('**', '')}\n"
    
    advice_text += "\n" + "=" * 60 + "\n"
    advice_text += "注：本建议基于土壤检测结果，实际施肥请结合当地农技指导\n"
    advice_text += "=" * 60
    
    return advice_text

# ================= 3. Streamlit 界面构建 =================
st.set_page_config(
    page_title="新疆棉田土壤养分专家系统", 
    page_icon="🌱",
    layout="wide"
)

# 标题区域
st.title("🌱 新疆棉田土壤养分智能评估与施肥指导系统")
st.markdown("""
<div style='background-color:#f0f8ff; padding:15px; border-radius:10px; border-left:5px solid #4CAF50;'>
<strong>系统说明：</strong> 输入土壤检测数据，系统自动评估养分状况并给出科学施肥建议。
所有建议均基于新疆棉区最新研究成果和官方指导文件。
</div>
""", unsafe_allow_html=True)

# 创建两列布局
col1, col2 = st.columns([1, 2])

# ================= 侧边栏输入区 =================
with col1:
    st.sidebar.header("📝 输入检测数据")
    st.sidebar.info("提示：未检测的项目请留空或保持为0")
    
    # 区域选择
    region = st.sidebar.radio("选择种植区域", ("北疆", "南疆"), index=0)
    
    # 定义有机质阈值标准
    if region == "北疆":
        om_thresholds = [12.0, 15.0, 18.0]
    else:  # 南疆
        om_thresholds = [8.0, 12.0, 16.0]
    
    # 输入表单
    inputs = {}
    
    with st.sidebar.expander("📊 基础养分 (必填)", expanded=True):
        inputs["有机质 g/kg"] = st.number_input("有机质 (g/kg)", min_value=0.0, step=0.1, format="%.2f")
        inputs["碱解氮 ppm"] = st.number_input("碱解氮 (ppm)", min_value=0.0, step=1.0)
        inputs["有效磷 ppm"] = st.number_input("有效磷 (ppm)", min_value=0.0, step=0.1)
        inputs["速效钾 ppm"] = st.number_input("速效钾 (ppm)", min_value=0.0, step=1.0)
    
    with st.sidebar.expander("🔬 微量元素 (选填)", expanded=False):
        inputs["铁 Fe (mg/kg)"] = st.number_input("铁 Fe (mg/kg)", min_value=0.0, step=0.1)
        inputs["锰 Mn (mg/kg)"] = st.number_input("锰 Mn (mg/kg)", min_value=0.0, step=0.1)
        inputs["铜 Cu (mg/kg)"] = st.number_input("铜 Cu (mg/kg)", min_value=0.0, step=0.01)
        inputs["锌 Zn (mg/kg)"] = st.number_input("锌 Zn (mg/kg)", min_value=0.0, step=0.01)
        inputs["硼 B (mg/kg)"]  = st.number_input("硼 B (mg/kg)", min_value=0.0, step=0.01)
        inputs["钼 Mo (mg/kg)"] = st.number_input("钼 Mo (mg/kg)", min_value=0.0, step=0.001, format="%.3f")
    
    # 过滤有效输入
    valid_inputs = {k: v for k, v in inputs.items() if v > 0}
    
    # 评估按钮
    assess_button = st.sidebar.button("🚀 开始评估", type="primary", use_container_width=True)
    
    # 添加肥料计算器
    st.sidebar.markdown("---")
    st.sidebar.subheader("🧮 肥料用量计算器")
    
    with st.sidebar.expander("点击使用计算器", expanded=False):
        calc_fertilizer = st.selectbox(
            "选择肥料",
            ["尿素 (N 46%)", "磷酸二铵 (N 18% P₂O₅ 46%)", "氯化钾 (K₂O 60%)", 
             "硫酸钾 (K₂O 50%)", "硼砂 (B 11%)", "硫酸锌 (Zn 35%)"]
        )
        
        calc_amount = st.number_input("需要补充的养分量 (kg/亩)", min_value=0.0, step=0.5, value=5.0)
        
        if st.button("计算用量"):
            if "尿素" in calc_fertilizer:
                result = calc_amount / 0.46
                st.success(f"需要 **{result:.1f} kg/亩** {calc_fertilizer}")
            elif "硼砂" in calc_fertilizer:
                result = calc_amount / 0.11
                st.success(f"需要 **{result:.2f} kg/亩** {calc_fertilizer}")
            elif "硫酸锌" in calc_fertilizer:
                result = calc_amount / 0.35
                st.success(f"需要 **{result:.2f} kg/亩** {calc_fertilizer}")
            elif "氯化钾" in calc_fertilizer:
                result = calc_amount / 0.60
                st.success(f"需要 **{result:.1f} kg/亩** {calc_fertilizer}")
            elif "硫酸钾" in calc_fertilizer:
                result = calc_amount / 0.50
                st.success(f"需要 **{result:.1f} kg/亩** {calc_fertilizer}")
            else:
                st.info("请输入具体需要补充的养分量")

# ================= 主展示区 =================
with col2:
    if not assess_button:
        # 初始状态显示
        st.subheader("欢迎使用土壤养分评估系统")
        st.markdown("""
        ### 📋 使用流程：
        1. 在左侧选择种植区域（北疆/南疆）
        2. 输入土壤检测数据
        3. 点击"开始评估"按钮
        4. 查看详细的评估报告和施肥建议
        
        ### 🌟 系统特点：
        - ✅ 基于最新科研成果和官方指南
        - ✅ 涵盖大量元素和微量元素
        - ✅ 提供详细的施肥方法和注意事项
        - ✅ 支持施肥方案导出
        - ✅ 包含肥料用量计算器
        
        ### 📚 数据来源：
        所有建议均参考：
        - 新疆农业农村厅《2024年春季主要农作物科学施肥指导意见》
        - 《2025年棉花科学施肥指导意见》
        - 新疆棉区最新研究成果
        """)
        
        # 显示当前有机质标准
        st.info(f"当前选择的**{region}**有机质标准：{om_thresholds[0]}/{om_thresholds[1]}/{om_thresholds[2]} (g/kg) 分级阈值")
    
    else:
        if not valid_inputs:
            st.warning("⚠️ 请在左侧输入至少一项有效数据！")
            st.stop()
        
        # ================= 执行评估 =================
        with st.spinner("正在评估土壤养分状况..."):
            # 临时修改RULES_DB中有机质的标准
            original_om_rule = RULES_DB["有机质 g/kg"]
            RULES_DB["有机质 g/kg"] = (om_thresholds, ["极低", "低", "中", "高"])
            
            # 计算结果
            report_data = evaluate_soil(valid_inputs)
            df = pd.DataFrame(report_data)
            
            # 恢复原始有机质标准
            RULES_DB["有机质 g/kg"] = original_om_rule
            
            # 生成肥料建议
            fertilizer_recs = generate_fertilizer_recommendations(report_data)
            
            # 生成导出文本
            export_text = export_advice_text(region, fertilizer_recs)
        
        # ================= 显示结果 =================
        st.success(f"✅ 评估完成！共分析 {len(report_data)} 项指标")
        
        # 1. 快速概览
        st.subheader("📈 快速诊断")
        col_a, col_b, col_c = st.columns(3)
        
        lacking_count = len([item for item in report_data if item["状态"] == "缺乏"])
        abundant_count = len([item for item in report_data if item["状态"] == "丰富"])
        normal_count = len([item for item in report_data if item["状态"] == "正常"])
        
        with col_a:
            st.metric("缺乏养分", f"{lacking_count}项", delta=None)
        with col_b:
            st.metric("丰富养分", f"{abundant_count}项", delta=None)
        with col_c:
            st.metric("正常养分", f"{normal_count}项", delta=None)
        
        # 2. 详细评估表
        st.subheader("📊 详细评估报告")
        
        def color_status(val):
            if '缺' in val or '低' in val or '极低' in val: 
                return 'background-color: #ffcccc; color: #b30000; font-weight: bold'
            elif '丰' in val or '高' in val: 
                return 'background-color: #ccffcc; color: #006600; font-weight: bold'
            elif '适中' in val or '中' in val: 
                return 'background-color: #e6f3ff; color: #0066cc; font-weight: bold'
            return ''
        
        styled_df = df.style.applymap(color_status, subset=['评估等级'])
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        # 3. 肥料建议
        if fertilizer_recs:
            st.subheader("💡 科学施肥指导")
            
            # 缺乏养分详细建议
            lacking_items = [r for r in fertilizer_recs if "缺乏" in r["状态"]]
            if lacking_items:
                st.error(f"⚠️ 发现 {len(lacking_items)} 项需要补充的养分")
                
                for i, rec in enumerate(lacking_items):
                    with st.expander(f"🔴 {rec['养分']} - {rec['状态']}", expanded=(i == 0)):
                        st.markdown(f"**📦 推荐肥料**: `{rec['推荐肥料']}`")
                        st.markdown(f"**🛠️ 施用方法**:")
                        methods = rec['施用方法'].split('；')
                        for method in methods:
                            st.markdown(f"- {method}")
                        
                        if rec['注意事项']:
                            st.markdown(f"**⚠️ 注意事项**: {rec['注意事项']}")
                        
                        st.caption(f"📚 依据: {rec['数据来源']}")
            
            # 丰富养分提醒
            abundant_items = [r for r in fertilizer_recs if "丰富" in r["状态"]]
            if abundant_items:
                st.warning(f"📈 有 {len(abundant_items)} 项养分充足，请注意平衡施肥")
                abundant_cols = st.columns(3)
                for idx, rec in enumerate(abundant_items):
                    with abundant_cols[idx % 3]:
                        st.info(f"**{rec['养分']}**: {rec['建议']}")
            
            # 正常养分
            normal_items = [r for r in fertilizer_recs if "正常" in r.get("建议", "") or r.get("状态", "").startswith("正常")]
            if normal_items:
                st.success(f"✅ 有 {len(normal_items)} 项养分处于适宜水平")
        
        # 4. 综合施肥原则
        st.subheader("📚 综合施肥原则")
        principle_cols = st.columns(2)
        for idx, principle in enumerate(GENERAL_PRINCIPLES):
            with principle_cols[idx % 2]:
                st.markdown(f"<div style='padding:10px; background-color:#f5f5f5; border-radius:5px; margin:5px;'>{principle}</div>", 
                           unsafe_allow_html=True)
        
        # 5. 导出功能
        st.subheader("📥 方案导出")
        
        col_export1, col_export2 = st.columns(2)
        with col_export1:
            # 下载按钮
            st.download_button(
                label="📄 下载施肥方案",
                data=export_text,
                file_name=f"棉田施肥方案_{region}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with col_export2:
            # 预览按钮
            if st.button("👁️ 预览方案内容", use_container_width=True):
                with st.expander("📋 施肥方案预览", expanded=True):
                    st.text(export_text)
        
        # 6. 数据统计
        st.subheader("📈 数据统计")
        
        if len(report_data) > 0:
            # 创建简单的统计图表
            status_counts = df["状态"].value_counts()
            
            chart_data = pd.DataFrame({
                "状态": status_counts.index,
                "数量": status_counts.values
            })
            
            # 显示统计图
            st.bar_chart(chart_data.set_index("状态"))
            
            # 总结
            lacking_names = [item['检测项目'].split(' ')[0] for item in report_data 
                            if item['状态'] == "缺乏"]
            if lacking_names:
                st.error(f"**重点提示**: 土壤中 **{'、'.join(lacking_names)}** 含量不足，是当前施肥管理的重点！")
            else:
                st.success("**整体评价**: 土壤养分状况良好，继续保持科学施肥管理。")

# ================= 页脚信息 =================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9em;'>
<p>🌱 新疆棉田土壤养分专家系统 v2.0 | 基于最新科研成果与官方指南</p>
<p>⚠️ 注意：本系统提供科学参考，实际施肥请结合当地农技人员指导</p>
</div>
""", unsafe_allow_html=True)
