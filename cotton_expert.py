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

# ================= 3. 通用施肥量计算模块 =================
class FertilizerCalculator:
    """通用肥料施用量计算器"""
    
    # 养分丰缺标准（基于等级判断）
    NUTRIENT_STANDARDS = {
        "硼 B (mg/kg)": {
            "thresholds": [0.2, 0.5, 1.0, 2.0],
            "grades": ["极缺", "缺", "适中", "丰", "很丰"],
            "target_range": (0.8, 1.5)  # 适宜范围
        },
        "钼 Mo (mg/kg)": {
            "thresholds": [0.1, 0.15, 0.2, 0.3],
            "grades": ["极缺", "缺", "适中", "丰", "很丰"],
            "target_range": (0.15, 0.25)
        },
        "锰 Mn (mg/kg)": {
            "thresholds": [1.0, 5.0, 15.0, 30.0],
            "grades": ["极缺", "缺", "适中", "丰", "很丰"],
            "target_range": (10, 25)
        },
        "锌 Zn (mg/kg)": {
            "thresholds": [0.3, 0.5, 1.0, 3.0],
            "grades": ["极缺", "缺", "适中", "丰", "很丰"],
            "target_range": (1.0, 2.5)
        },
        "铜 Cu (mg/kg)": {
            "thresholds": [0.1, 0.2, 1.0, 1.8],
            "grades": ["极缺", "缺", "适中", "丰", "很丰"],
            "target_range": (0.5, 1.5)
        },
        "铁 Fe (mg/kg)": {
            "thresholds": [2.5, 4.5, 10.0, 20.0],
            "grades": ["极缺", "缺", "适中", "丰", "很丰"],
            "target_range": (8, 15)
        },
        "有机质 g/kg": {
            "thresholds": [12.0, 15.0, 18.0],
            "grades": ["极低", "低", "中", "高"],
            "target_range": (16, 25)
        },
        "碱解氮 ppm": {
            "thresholds": [40.0, 60.0, 90.0],
            "grades": ["极低", "低", "中", "高"],
            "target_range": (80, 120)
        },
        "有效磷 ppm": {
            "thresholds": [7.0, 13.0, 30.0],
            "grades": ["极低", "低", "中", "高"],
            "target_range": (15, 40)
        },
        "速效钾 ppm": {
            "thresholds": [80.0, 160.0, 210.0],
            "grades": ["极低", "低", "中", "高"],
            "target_range": (150, 250)
        }
    }
    
    # 肥料养分含量（%）
    FERTILIZER_CONTENT = {
        "尿素": {"N": 46.0},
        "碳酸氢铵": {"N": 17.0},
        "磷酸二铵": {"N": 18.0, "P2O5": 46.0},
        "过磷酸钙": {"P2O5": 12.0},
        "钙镁磷肥": {"P2O5": 12.0},
        "氯化钾": {"K2O": 60.0},
        "硫酸钾": {"K2O": 50.0},
        "硫酸锌": {"Zn": 35.0},
        "硼砂": {"B": 11.0},
        "硫酸锰": {"Mn": 31.0},
        "硫酸亚铁": {"Fe": 19.0},
        "硫酸铜": {"Cu": 25.0},
        "钼酸铵": {"Mo": 54.0},
        "有机肥": {"有机质": 45.0}  # 假设有机肥含有机质45%
    }
    
    # 土壤养分单位转换系数（mg/kg/ppm 到 kg/亩）
    # 假设耕层深度20cm，土壤容重1.2g/cm³，则1亩地耕层土壤重量约为150,000kg
    # 1 mg/kg = 1 ppm = 1 g/吨 = 0.15 kg/亩（150,000kg × 1mg/kg = 150g = 0.15kg）
    SOIL_CONVERSION = 0.15  # 将mg/kg转换为kg/亩的系数
    
    # 肥料利用率（%）
    UTILIZATION_RATE = {
        "N": 0.35,   # 氮肥利用率
        "P": 0.20,   # 磷肥利用率
        "K": 0.45,   # 钾肥利用率
        "微量元素": 0.10,  # 微量元素利用率
        "有机质": 0.30   # 有机肥利用率
    }
    
    @staticmethod
    def calculate_deficiency(nutrient_name, current_value):
        """
        计算养分缺乏量（每亩）
        nutrient_name: 养分名称
        current_value: 当前测定值
        """
        if nutrient_name not in FertilizerCalculator.NUTRIENT_STANDARDS:
            return {"error": "未知养分"}
        
        std = FertilizerCalculator.NUTRIENT_STANDARDS[nutrient_name]
        target_min, target_max = std["target_range"]
        
        # 判断是否需要补充
        if current_value >= target_min:
            deficiency_ppm = 0
            deficiency_kg_per_mu = 0
            status = "充足"
        else:
            # 计算达到目标下限的缺乏量（每kg/亩）
            deficiency_ppm = target_min - current_value
            deficiency_kg_per_mu = deficiency_ppm * FertilizerCalculator.SOIL_CONVERSION
            status = "缺乏"
        
        # 确定缺乏程度
        thresholds = std["thresholds"]
        index = bisect.bisect_right(thresholds, current_value)
        grade = std["grades"][index] if 0 <= index < len(std["grades"]) else "异常"
        
        return {
            "nutrient": nutrient_name,
            "current_value": current_value,
            "target_min": target_min,
            "target_max": target_max,
            "deficiency_ppm": round(deficiency_ppm, 3),
            "deficiency_kg_per_mu": round(deficiency_kg_per_mu, 3),
            "status": status,
            "grade": grade
        }
    
    @staticmethod
    def calculate_fertilizer_amount(deficiency_info, fertilizer_type, area_mu=1.0):
        """
        计算所需肥料用量
        deficiency_info: 缺乏信息字典
        fertilizer_type: 肥料类型
        area_mu: 面积（亩）
        """
        if deficiency_info["deficiency_kg_per_mu"] <= 0:
            return {
                "fertilizer": fertilizer_type,
                "amount_per_mu": 0,
                "total_amount": 0,
                "unit": "kg",
                "status": "无需补充"
            }
        
        # 获取养分类型
        nutrient_name = deficiency_info["nutrient"]
        if "氮" in nutrient_name:
            nutrient_symbol = "N"
            utilization = FertilizerCalculator.UTILIZATION_RATE["N"]
        elif "磷" in nutrient_name:
            nutrient_symbol = "P2O5"
            utilization = FertilizerCalculator.UTILIZATION_RATE["P"]
        elif "钾" in nutrient_name:
            nutrient_symbol = "K2O"
            utilization = FertilizerCalculator.UTILIZATION_RATE["K"]
        elif "有机质" in nutrient_name:
            # 有机质特殊处理
            nutrient_symbol = "有机质"
            utilization = FertilizerCalculator.UTILIZATION_RATE["有机质"]
        else:
            # 微量元素
            nutrient_symbol = nutrient_name.split()[0]  # 如 "Zn", "B"
            utilization = FertilizerCalculator.UTILIZATION_RATE["微量元素"]
        
        # 计算肥料用量
        if fertilizer_type in FertilizerCalculator.FERTILIZER_CONTENT:
            fertilizer = FertilizerCalculator.FERTILIZER_CONTENT[fertilizer_type]
            
            # 找到对应的养分含量
            content = None
            for key in fertilizer:
                if key == nutrient_symbol or (nutrient_symbol in key):
                    content = fertilizer[key] / 100  # 转换为小数
                    break
            
            if content is None:
                # 如果找不到精确匹配，尝试模糊匹配
                if "有机" in fertilizer_type and "有机质" in nutrient_name:
                    content = fertilizer.get("有机质", 0.45) / 100
                else:
                    return {"error": f"肥料{fertilizer_type}不含所需养分{nutrient_symbol}"}
            
            # 计算理论用量（每亩）
            deficiency_kg_per_mu = deficiency_info["deficiency_kg_per_mu"]
            theoretical_amount_per_mu = deficiency_kg_per_mu / content
            
            # 考虑肥料利用率
            actual_amount_per_mu = theoretical_amount_per_mu / utilization
            
            # 根据缺乏程度调整
            if deficiency_info["grade"] in ["极缺", "极低"]:
                actual_amount_per_mu *= 1.2  # 增加20%
            elif deficiency_info["grade"] in ["缺", "低"]:
                actual_amount_per_mu *= 1.0
            else:
                actual_amount_per_mu *= 0.8  # 减少20%
            
            # 计算总面积用量
            total_amount = actual_amount_per_mu * area_mu
            
            result = {
                "fertilizer": fertilizer_type,
                "content": f"{fertilizer_type}含{nutrient_symbol} {fertilizer.get(nutrient_symbol, fertilizer.get('有机质', 0))}%",
                "deficiency_per_mu": round(deficiency_kg_per_mu, 3),
                "theoretical_per_mu": round(theoretical_amount_per_mu, 2),
                "actual_per_mu": round(actual_amount_per_mu, 2),
                "total_amount": round(total_amount, 2),
                "unit": "kg",
                "area": area_mu,
                "utilization_rate": f"{utilization*100}%"
            }
            
            return result
        else:
            return {"error": "未知肥料类型"}

# ================= 4. 集成通用计算功能的施肥建议生成 =================
def generate_comprehensive_recommendations(results, region="北疆", area_mu=1.0):
    """
    生成综合施肥建议（结合知识库和通用计算）
    """
    recommendations = []
    calculator = FertilizerCalculator()
    
    # 调整有机质标准
    if region == "南疆":
        calculator.NUTRIENT_STANDARDS["有机质 g/kg"]["thresholds"] = [8.0, 12.0, 16.0]
        calculator.NUTRIENT_STANDARDS["有机质 g/kg"]["target_range"] = (12, 20)
    
    for item in results:
        item_name = item["检测项目"]
        current_value = item["检测数值"]
        status = item["状态"]
        grade = item["评估等级"]
        nutrient_name = item_name.split()[0]
        
        # 通用缺乏量计算（不传入面积参数）
        deficiency_info = calculator.calculate_deficiency(item_name, current_value)
        
        # 基础信息
        rec = {
            "养分": nutrient_name,
            "状态": f"{status} ({grade})",
            "当前值": current_value,
            "目标范围": f"{deficiency_info['target_min']}-{deficiency_info['target_max']}",
            "缺乏量(kg/亩)": deficiency_info["deficiency_kg_per_mu"],
            "缺乏量(ppm)": deficiency_info["deficiency_ppm"]
        }
        
        # 根据不同状态生成建议
        if status == "缺乏":
            # 获取知识库建议
            if item_name in FERTILIZER_KNOWLEDGE and "缺乏" in FERTILIZER_KNOWLEDGE[item_name]:
                kb_advice = FERTILIZER_KNOWLEDGE[item_name]["缺乏"]
                rec["知识库建议"] = {
                    "推荐肥料": kb_advice["肥料类型"],
                    "施用方法": "；".join(kb_advice["施用方法"]),
                    "注意事项": kb_advice.get("注意事项", ""),
                    "来源": kb_advice.get("来源", "")
                }
            
            # 通用计算建议
            if deficiency_info["deficiency_kg_per_mu"] > 0:
                # 根据养分类型选择合适的肥料
                if "氮" in item_name:
                    fertilizer_options = ["尿素", "磷酸二铵"]
                elif "磷" in item_name:
                    fertilizer_options = ["磷酸二铵", "过磷酸钙"]
                elif "钾" in item_name:
                    fertilizer_options = ["氯化钾", "硫酸钾"]
                elif "锌" in item_name:
                    fertilizer_options = ["硫酸锌"]
                elif "硼" in item_name:
                    fertilizer_options = ["硼砂"]
                elif "锰" in item_name:
                    fertilizer_options = ["硫酸锰"]
                elif "铁" in item_name:
                    fertilizer_options = ["硫酸亚铁"]
                elif "铜" in item_name:
                    fertilizer_options = ["硫酸铜"]
                elif "钼" in item_name:
                    fertilizer_options = ["钼酸铵"]
                elif "有机质" in item_name:
                    fertilizer_options = ["有机肥"]
                else:
                    fertilizer_options = []
                
                if fertilizer_options:
                    # 计算各种肥料的用量（传入面积参数）
                    fert_calcs = []
                    for fert in fertilizer_options:
                        calc = calculator.calculate_fertilizer_amount(
                            deficiency_info, fert, area_mu  # 传入面积
                        )
                        if "error" not in calc and calc.get("total_amount", 0) > 0:
                            fert_calcs.append(calc)
                    
                    if fert_calcs:
                        rec["通用计算建议"] = {
                            "需要补充": f"{deficiency_info['deficiency_kg_per_mu']} kg/亩（以纯养分计）",
                            "肥料用量": fert_calcs
                        }
        
        elif status == "丰富":
            if item_name in FERTILIZER_KNOWLEDGE and "丰富" in FERTILIZER_KNOWLEDGE[item_name]:
                rec["建议"] = FERTILIZER_KNOWLEDGE[item_name]["丰富"]
            else:
                rec["建议"] = "养分充足，无需补充"
        
        else:  # 正常
            rec["建议"] = "保持现有施肥管理"
        
        recommendations.append(rec)
    
    return recommendations

# ================= 5. 导出功能增强 =================
def export_comprehensive_advice(region, fertilizer_recs, area_mu=1.0):
    """生成可导出的综合施肥建议文本"""
    advice_text = "=" * 70 + "\n"
    advice_text += "新疆棉田土壤养分施肥建议方案（综合版）\n"
    advice_text += "=" * 70 + "\n"
    advice_text += f"评估时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    advice_text += f"种植区域: {region}\n"
    advice_text += f"面积: {area_mu} 亩\n"
    advice_text += "-" * 70 + "\n\n"
    
    # 缺乏养分详细建议
    lacking_items = [r for r in fertilizer_recs if "缺乏" in r["状态"]]
    if lacking_items:
        advice_text += "【需重点补充的养分及施用量计算】\n\n"
        for rec in lacking_items:
            advice_text += f"■ {rec['养分']} ({rec['状态']})\n"
            advice_text += f"  当前含量: {rec['当前值']} | 目标范围: {rec['目标范围']}\n"
            advice_text += f"  养分缺乏量: {rec['缺乏量(kg/亩)']} kg/亩（纯养分）\n\n"
            
            # 知识库建议
            if "知识库建议" in rec:
                kb = rec["知识库建议"]
                advice_text += f"  📚 知识库建议：\n"
                advice_text += f"     推荐肥料: {kb['推荐肥料']}\n"
                advice_text += f"     施用方法: {kb['施用方法']}\n"
                if kb['注意事项']:
                    advice_text += f"     注意事项: {kb['注意事项']}\n"
                advice_text += f"     依据来源: {kb['来源']}\n\n"
            
            # 通用计算建议
            if "通用计算建议" in rec:
                calc = rec["通用计算建议"]
                advice_text += f"  🧮 通用计算建议：\n"
                advice_text += f"     需要补充: {calc['需要补充']}\n"
                
                for fert in calc["肥料用量"]:
                    if isinstance(fert, dict) and "fertilizer" in fert:
                        # 显示每亩用量和总用量
                        advice_text += f"     • {fert['fertilizer']}: {fert.get('actual_per_mu', 0):.2f} kg/亩"
                        if area_mu > 1:
                            advice_text += f" (总面积{area_mu}亩，共需{fert.get('total_amount', 0):.2f} kg)"
                        if "content" in fert:
                            advice_text += f" ({fert['content']})"
                        advice_text += "\n"
                
                # 获取肥料利用率
                if calc["肥料用量"] and len(calc["肥料用量"]) > 0:
                    first_fert = calc["肥料用量"][0]
                    util_rate = first_fert.get('utilization_rate', '30-50%')
                    advice_text += f"     注：考虑肥料利用率{util_rate}的推荐用量\n\n"
    
    # 丰富养分提醒
    abundant_items = [r for r in fertilizer_recs if "丰富" in r["状态"]]
    if abundant_items:
        advice_text += "【养分充足项目】\n\n"
        for rec in abundant_items:
            advice_text += f"✓ {rec['养分']}: {rec.get('建议', '养分充足，无需补充')}\n"
        advice_text += "\n"
    
    # 综合原则
    advice_text += "【综合施肥原则】\n"
    for principle in GENERAL_PRINCIPLES:
        advice_text += f"• {principle.replace('**', '')}\n"
    
    # 计算说明
    advice_text += "\n" + "-" * 70 + "\n"
    advice_text += "📊 计算说明：\n"
    advice_text += "1. 通用计算基于：耕层深度20cm，土壤容重1.2g/cm³，1亩耕层土壤约150,000kg\n"
    advice_text += "2. 养分换算：1 mg/kg = 0.15 kg/亩（纯养分）\n"
    advice_text += "3. 肥料利用率参考：氮肥35%、磷肥20%、钾肥45%、微量元素10%\n"
    advice_text += "4. 实际施肥请结合土壤质地、灌溉条件、产量目标等调整\n"
    advice_text += "=" * 70 + "\n"
    advice_text += "注：本建议结合知识库经验与通用计算，实际施肥请结合当地农技指导\n"
    advice_text += "=" * 70
    
    return advice_text

# ================= 6. Streamlit 界面构建 =================
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
包含知识库经验建议和通用定量计算两种方案。
</div>
""", unsafe_allow_html=True)

# 初始化session state
if 'assessment_results' not in st.session_state:
    st.session_state.assessment_results = None
if 'fertilizer_recs' not in st.session_state:
    st.session_state.fertilizer_recs = None
if 'export_text' not in st.session_state:
    st.session_state.export_text = None
if 'valid_inputs' not in st.session_state:
    st.session_state.valid_inputs = {}
if 'region' not in st.session_state:
    st.session_state.region = "北疆"
if 'show_calculator' not in st.session_state:
    st.session_state.show_calculator = False
if 'area_mu' not in st.session_state:
    st.session_state.area_mu = 1.0

# ================= 侧边栏输入区 =================
st.sidebar.header("📝 输入检测数据")
st.sidebar.info("提示：未检测的项目请留空或保持为0")

# 区域选择
region = st.sidebar.radio("选择种植区域", ("北疆", "南疆"), index=0)
st.session_state.region = region

# 面积输入
area_mu = st.sidebar.number_input("棉田面积（亩）", min_value=0.1, value=1.0, step=0.5, key="area_input")
st.session_state.area_mu = area_mu

# 定义有机质阈值标准
if region == "北疆":
    om_thresholds = [12.0, 15.0, 18.0]
else:  # 南疆
    om_thresholds = [8.0, 12.0, 16.0]

# 输入表单
inputs = {}

with st.sidebar.expander("📊 基础养分 (必填)", expanded=True):
    inputs["有机质 g/kg"] = st.number_input("有机质 (g/kg)", min_value=0.0, step=0.1, format="%.2f", key="om_input")
    inputs["碱解氮 ppm"] = st.number_input("碱解氮 (ppm)", min_value=0.0, step=1.0, key="n_input")
    inputs["有效磷 ppm"] = st.number_input("有效磷 (ppm)", min_value=0.0, step=0.1, key="p_input")
    inputs["速效钾 ppm"] = st.number_input("速效钾 (ppm)", min_value=0.0, step=1.0, key="k_input")

with st.sidebar.expander("🔬 微量元素 (选填)", expanded=False):
    inputs["铁 Fe (mg/kg)"] = st.number_input("铁 Fe (mg/kg)", min_value=0.0, step=0.1, key="fe_input")
    inputs["锰 Mn (mg/kg)"] = st.number_input("锰 Mn (mg/kg)", min_value=0.0, step=0.1, key="mn_input")
    inputs["铜 Cu (mg/kg)"] = st.number_input("铜 Cu (mg/kg)", min_value=0.0, step=0.01, key="cu_input")
    inputs["锌 Zn (mg/kg)"] = st.number_input("锌 Zn (mg/kg)", min_value=0.0, step=0.01, key="zn_input")
    inputs["硼 B (mg/kg)"]  = st.number_input("硼 B (mg/kg)", min_value=0.0, step=0.01, key="b_input")
    inputs["钼 Mo (mg/kg)"] = st.number_input("钼 Mo (mg/kg)", min_value=0.0, step=0.001, format="%.3f", key="mo_input")

# 过滤有效输入
valid_inputs = {k: v for k, v in inputs.items() if v > 0}

# 评估按钮
assess_button = st.sidebar.button("🚀 开始评估", type="primary", use_container_width=True)

# 添加肥料计算器
st.sidebar.markdown("---")
st.sidebar.subheader("🧮 肥料用量计算器")

# 使用session state来控制计算器显示
if st.sidebar.button("点击使用计算器", use_container_width=True):
    st.session_state.show_calculator = not st.session_state.show_calculator

if st.session_state.show_calculator:
    with st.sidebar.expander("肥料计算器", expanded=True):
        calc_fertilizer = st.selectbox(
            "选择肥料",
            ["尿素 (N 46%)", "磷酸二铵 (N 18% P₂O₅ 46%)", "氯化钾 (K₂O 60%)", 
             "硫酸钾 (K₂O 50%)", "硼砂 (B 11%)", "硫酸锌 (Zn 35%)"],
            key="fert_calc_select"
        )
        
        calc_amount = st.number_input("需要补充的养分量 (kg/亩)", min_value=0.0, step=0.5, value=5.0, key="calc_amount")
        
        if st.button("计算用量", key="calc_btn"):
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
if not assess_button:
    # 初始状态显示
    st.subheader("欢迎使用土壤养分评估系统")
    col_welcome_1, col_welcome_2 = st.columns([1.2, 1])
    with col_welcome_1:
        st.markdown("""
        ### 📋 使用流程：
        1. 在左侧选择种植区域（北疆/南疆）
        2. 输入土壤检测数据
        3. 输入棉田面积
        4. 点击"开始评估"按钮
        5. 查看详细的评估报告和施肥建议
        
        ### 🌟 系统特点：
        - ✅ 基于最新科研成果和官方指南
        - ✅ 包含知识库经验和通用计算两种方案
        - ✅ 定量计算养分缺乏量和肥料用量
        - ✅ 提供详细的施肥方法和注意事项
        - ✅ 支持施肥方案导出
        """)
    with col_welcome_2:
        st.markdown("""
        ### 📚 数据来源：
        所有建议均参考：
        - 新疆农业农村厅《2024年春季主要农作物科学施肥指导意见》
        - 《2025年棉花科学施肥指导意见》
        - 新疆棉区最新研究成果
        
        ### 📌 区域标准提示
        """)
        st.info(f"当前选择的**{st.session_state.region}**有机质标准：\n{om_thresholds[0]}/{om_thresholds[1]}/{om_thresholds[2]} (g/kg) 分级阈值")

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
        
        # 恢复原始有机质标准
        RULES_DB["有机质 g/kg"] = original_om_rule
        
        # 保存评估结果到session state
        st.session_state.assessment_results = report_data
        st.session_state.valid_inputs = valid_inputs

# 显示评估结果（如果session state中有数据）
if st.session_state.assessment_results is not None:
    report_data = st.session_state.assessment_results
    valid_inputs = st.session_state.valid_inputs
    
    # 生成综合建议（包括通用计算）
    fertilizer_recs = generate_comprehensive_recommendations(
        report_data, 
        st.session_state.region, 
        st.session_state.area_mu
    )
    
    # 生成导出文本
    export_text = export_comprehensive_advice(
        st.session_state.region, 
        fertilizer_recs,
        st.session_state.area_mu
    )
    
    # 保存到session state
    st.session_state.fertilizer_recs = fertilizer_recs
    st.session_state.export_text = export_text
    
    df = pd.DataFrame(report_data)
    
    # ================= 显示结果 =================
    st.success(f"✅ 评估完成！共分析 {len(report_data)} 项指标")
    
    # 1. 快速概览
    st.subheader("📈 快速诊断")
    col_a, col_b, col_c, col_d = st.columns(4)
    
    lacking_count = len([item for item in report_data if item["状态"] == "缺乏"])
    abundant_count = len([item for item in report_data if item["状态"] == "丰富"])
    normal_count = len([item for item in report_data if item["状态"] == "正常"])
    total_count = len(report_data)
    
    with col_a:
        st.metric("总检测项", f"{total_count}项", delta=None)
    with col_b:
        st.metric("缺乏养分", f"{lacking_count}项", delta=None)
    with col_c:
        st.metric("丰富养分", f"{abundant_count}项", delta=None)
    with col_d:
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
    st.dataframe(styled_df, use_container_width=True, hide_index=True, height=min(400, len(df)*40 + 50))
    
    # 3. 科学施肥指导
    if fertilizer_recs:
        st.subheader("💡 科学施肥指导")
        
        # 分栏展示缺乏/丰富/正常养分
        col_fer_1, col_fer_2 = st.columns([1.5, 1])
        
        # 缺乏养分详细建议
        lacking_items = [r for r in fertilizer_recs if "缺乏" in r["状态"]]
        with col_fer_1:
            if lacking_items:
                st.error(f"⚠️ 发现 {len(lacking_items)} 项需要补充的养分")
                
                for i, rec in enumerate(lacking_items):
                    with st.expander(f"🔴 {rec['养分']} - {rec['状态']}", expanded=(i == 0)):
                        st.markdown(f"**📊 现状分析**:")
                        st.markdown(f"- 当前含量: `{rec['当前值']}`")
                        st.markdown(f"- 目标范围: `{rec['目标范围']}`")
                        st.markdown(f"- 缺乏量: `{rec['缺乏量(kg/亩)']} kg/亩` (纯养分)")
                        
                        if "知识库建议" in rec:
                            kb = rec["知识库建议"]
                            st.markdown(f"**📚 知识库经验建议**:")
                            st.markdown(f"- 推荐肥料: `{kb['推荐肥料']}`")
                            st.markdown(f"- 施用方法:")
                            methods = kb['施用方法'].split('；')
                            for method in methods:
                                st.markdown(f"  • {method}")
                            
                            if kb['注意事项']:
                                st.markdown(f"- 注意事项: {kb['注意事项']}")
                            st.caption(f"📖 依据: {kb['来源']}")
                        
                        if "通用计算建议" in rec:
                            calc = rec["通用计算建议"]
                            st.markdown(f"**🧮 通用计算建议**:")
                            st.markdown(f"- 需要补充: `{calc['需要补充']}`")
                            
                            for fert in calc["肥料用量"]:
                                if isinstance(fert, dict) and "fertilizer" in fert:
                                    per_mu = fert.get('actual_per_mu', 0)
                                    total = fert.get('total_amount', 0)
                                    if per_mu > 0:
                                        if st.session_state.area_mu > 1:
                                            st.markdown(f"  • {fert['fertilizer']}: `{per_mu} kg/亩` (总面积需 {total} kg)")
                                        else:
                                            st.markdown(f"  • {fert['fertilizer']}: `{per_mu} kg/亩`")
        
        # 丰富/正常养分
        with col_fer_2:
            # 丰富养分提醒
            abundant_items = [r for r in fertilizer_recs if "丰富" in r["状态"]]
            if abundant_items:
                st.warning(f"📈 有 {len(abundant_items)} 项养分充足")
                for rec in abundant_items:
                    st.info(f"**{rec['养分']}**: {rec.get('建议', '养分充足，无需补充')}")
            
            # 正常养分
            normal_items = [r for r in fertilizer_recs if "正常" in r.get("建议", "") or r.get("状态", "").startswith("正常")]
            if normal_items:
                st.success(f"✅ 有 {len(normal_items)} 项养分处于适宜水平")
                for rec in normal_items[:3]:
                    st.markdown(f"• **{rec['养分']}**: {rec['建议']}")
                if len(normal_items) > 3:
                    st.markdown(f"• ... 还有 {len(normal_items)-3} 项养分正常")
    
    # 4. 通用施用量计算
    st.subheader("🧮 通用施用量计算")
    
    # 创建两列布局
    calc_col1, calc_col2 = st.columns([1, 1])
    
    with calc_col1:
        st.markdown("##### 养分缺乏量计算")
        calc_data = []
        for rec in fertilizer_recs:
            if "缺乏" in rec["状态"] and "缺乏量(kg/亩)" in rec:
                calc_data.append({
                    "养分": rec["养分"],
                    "当前值": rec["当前值"],
                    "目标范围": rec["目标范围"],
                    "缺乏量(kg/亩)": rec["缺乏量(kg/亩)"]
                })
        
        if calc_data:
            calc_df = pd.DataFrame(calc_data)
            st.dataframe(calc_df, use_container_width=True)
        else:
            st.info("没有检测到缺乏的养分")
    
    with calc_col2:
        st.markdown("##### 肥料用量参考")
        for rec in fertilizer_recs:
            if "缺乏" in rec["状态"] and "通用计算建议" in rec:
                with st.expander(f"{rec['养分']}肥料用量", expanded=False):
                    calc = rec["通用计算建议"]
                    st.markdown(f"**需要补充**: {calc['需要补充']}")
                    
                    for fert in calc["肥料用量"]:
                        if isinstance(fert, dict) and "fertilizer" in fert:
                            per_mu = fert.get('actual_per_mu', 0)
                            total = fert.get('total_amount', 0)
                            if per_mu > 0:
                                st.markdown(f"**{fert['fertilizer']}**:")
                                st.markdown(f"- 用量: **{per_mu} kg/亩**")
                                if st.session_state.area_mu > 1:
                                    st.markdown(f"- 总面积用量: **{total} kg** (共{st.session_state.area_mu}亩)")
                                if "content" in fert:
                                    st.markdown(f"- 养分含量: {fert['content']}")
                                st.markdown(f"- 肥料利用率: {fert.get('utilization_rate', '30-50%')}")
                                st.markdown("---")
    
    # 5. 添加计算原理说明
    with st.expander("📊 查看计算原理"):
        st.markdown("""
        ### 通用计算原理
        
        **1. 养分缺乏量计算：**
        ```
        缺乏量(kg/亩) = (目标值 - 当前值) × 转换系数
        转换系数 = 0.15 (基于1亩耕层土壤约150,000kg)
        ```
        
        **2. 肥料用量计算：**
        ```
        每亩理论用量 = 缺乏量 ÷ 肥料养分含量
        每亩实际用量 = 每亩理论用量 ÷ 肥料利用率
        总用量 = 每亩实际用量 × 面积(亩)
        ```
        
        **3. 肥料利用率参考：**
        - 氮肥：30-40%
        - 磷肥：15-25%
        - 钾肥：40-50%
        - 微量元素：5-15%
        
        **4. 注意事项：**
        - 计算结果为理论值，需根据土壤质地、灌溉条件调整
        - 砂质土壤养分流失快，建议增加10-20%用量
        - 粘质土壤保肥性好，可适当减少用量
        - 计算结果需结合农技人员经验调整
        """)
    
    # 6. 综合施肥原则
    st.subheader("📚 综合施肥原则")
    principle_container = st.container()
    with principle_container:
        st.markdown("<div style='display: flex; gap: 10px; overflow-x: auto; padding: 10px 0;'>", unsafe_allow_html=True)
        for idx, principle in enumerate(GENERAL_PRINCIPLES):
            st.markdown(f"""
            <div style='flex: 1; min-width: 250px; padding: 15px; background-color:#f5f5f5; border-radius:8px;'>
                {principle}
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # 7. 导出功能
    st.subheader("📥 方案导出")
    col_export1, col_export2, col_export3 = st.columns([1, 1, 2])
    with col_export1:
        # 下载按钮
        st.download_button(
            label="📄 下载施肥方案",
            data=export_text,
            file_name=f"棉田施肥方案_{st.session_state.region}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    with col_export2:
        # 预览按钮
        if st.button("👁️ 预览方案内容", use_container_width=True):
            with st.expander("📋 施肥方案预览", expanded=True):
                st.text(export_text)
    
    # 8. 数据统计
    st.subheader("📈 数据统计")
    if len(report_data) > 0:
        # 创建简单的统计图表
        status_counts = df["状态"].value_counts()
        
        chart_data = pd.DataFrame({
            "状态": status_counts.index,
            "数量": status_counts.values
        })
        
        st.bar_chart(chart_data.set_index("状态"), height=300)
        
        # 总结提示
        lacking_names = [item['检测项目'].split(' ')[0] for item in report_data 
                        if item['状态'] == "缺乏"]
        if lacking_names:
            st.markdown(f"""
            <div style='padding: 15px; background-color: #fff0f0; border-left: 5px solid #ff4444; border-radius: 5px; margin: 10px 0;'>
                <strong>重点提示</strong>：土壤中 <strong>{'、'.join(lacking_names)}</strong> 含量不足，是当前施肥管理的重点！
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style='padding: 15px; background-color: #f0fff0; border-left: 5px solid #00C851; border-radius: 5px; margin: 10px 0;'>
                <strong>整体评价</strong>：土壤养分状况良好，继续保持科学施肥管理。
            </div>
            """, unsafe_allow_html=True)

# ================= 页脚信息 =================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9em;'>
<p>🌱 新疆棉田土壤养分专家系统 v3.0 | 知识库+通用计算双轨制</p>
<p>⚠️ 注意：本系统提供科学参考，实际施肥请结合当地农技人员指导</p>
</div>
""", unsafe_allow_html=True)
