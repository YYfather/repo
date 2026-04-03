"""
机器学习教学工具 - 基于Streamlit的交互式机器学习演示（增强版）
支持算法：线性回归、决策树、随机森林、SVM、逻辑回归、KNN、朴素贝叶斯、梯度提升树、XGBoost、LightGBM
新增功能：交叉验证、超参数调优、模型比较、SHAP解释、学习曲线、模型保存
"""

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import pickle
import json
from datetime import datetime
from io import BytesIO
import os
import matplotlib.font_manager as fm

# 机器学习相关
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV, learning_curve, validation_curve
from sklearn.preprocessing import StandardScaler, LabelEncoder, MinMaxScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_curve, auc,
    mean_squared_error, mean_absolute_error, r2_score,
    make_scorer
)
from sklearn.datasets import load_iris, load_wine, load_breast_cancer, make_classification, make_regression
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge, Lasso
from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier, plot_tree
from sklearn.ensemble import (
    RandomForestRegressor, RandomForestClassifier,
    GradientBoostingRegressor, GradientBoostingClassifier,
    AdaBoostRegressor, AdaBoostClassifier,
    ExtraTreesRegressor, ExtraTreesClassifier
)
from sklearn.svm import SVR, SVC
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.naive_bayes import GaussianNB
from sklearn.neural_network import MLPClassifier, MLPRegressor

# 尝试导入可选库
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

import warnings
warnings.filterwarnings('ignore')

# # 全局配置中文字体
# plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'PingFang SC', 'Heiti TC', 'sans-serif']
# plt.rcParams['axes.unicode_minus'] = False

# 全局配置中文字体（适配云端部署）
# 假设你的字体文件名为 SimHei.ttf，并且放在了与此脚本同级的目录下
font_path = "SimHei.ttf" 

if os.path.exists(font_path):
    # 如果找到了本地/云端的字体文件，就动态加载它
    fm.fontManager.addfont(font_path)
    font_prop = fm.FontProperties(fname=font_path)
    # 将 matplotlib 的全局字体设置为我们刚刚加载的字体
    plt.rcParams['font.sans-serif'] = [font_prop.get_name()]
else:
    # 如果找不到文件（作为备用方案），再尝试使用系统默认可能存在的中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'PingFang SC', 'sans-serif']

# 解决坐标轴负号'-'显示为方块的问题
plt.rcParams['axes.unicode_minus'] = False

# 设置页面配置
st.set_page_config(
    page_title="机器学习教学工具",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #ff7f0e;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    .feature-importance {
        background-color: #e8f4f8;
        padding: 1rem;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# 初始化session state
if 'models_trained' not in st.session_state:
    st.session_state['models_trained'] = {}
if 'comparison_results' not in st.session_state:
    st.session_state['comparison_results'] = []
if 'training_history' not in st.session_state:
    st.session_state['training_history'] = []

# 主标题
st.markdown('<h1 class="main-header">🎓 机器学习教学工具</h1>', unsafe_allow_html=True)
st.markdown("### 交互式机器学习算法演示与学习平台 | 支持算法比较、交叉验证、模型解释")

# 侧边栏配置
with st.sidebar:
    st.header("📚 算法与数据设置")
    
    # 功能模式选择
    app_mode = st.selectbox(
        "选择功能模式",
        ["单模型训练", "多模型比较", "超参数调优", "交叉验证", "模型解释"],
        help="选择要使用的功能模式"
    )
    
    # 任务类型选择
    task_type = st.selectbox(
        "选择任务类型",
        ["分类任务", "回归任务"],
        help="分类任务：预测离散类别；回归任务：预测连续数值"
    )
    
    # 根据任务类型显示算法选项
    if task_type == "分类任务":
        algorithm_options = ["逻辑回归", "决策树分类", "随机森林分类", "支持向量机(SVM)", 
                           "K近邻(KNN)", "朴素贝叶斯", "梯度提升分类", "AdaBoost分类", 
                           "ExtraTrees分类", "神经网络(MLP)"]
        if XGBOOST_AVAILABLE:
            algorithm_options.append("XGBoost分类")
        if LIGHTGBM_AVAILABLE:
            algorithm_options.append("LightGBM分类")
            
        if app_mode == "多模型比较":
            selected_algorithms = st.multiselect(
                "选择要比较的算法",
                algorithm_options,
                default=algorithm_options[:4],
                help="选择多个算法进行比较"
            )
        else:
            algorithm = st.selectbox(
                "选择算法",
                algorithm_options,
                help="选择要演示的分类算法"
            )
    else:
        algorithm_options = ["线性回归", "Ridge回归", "Lasso回归", "决策树回归", 
                           "随机森林回归", "支持向量回归(SVR)", "K近邻回归", 
                           "梯度提升回归", "AdaBoost回归", "ExtraTrees回归", "神经网络(MLP)"]
        if XGBOOST_AVAILABLE:
            algorithm_options.append("XGBoost回归")
        if LIGHTGBM_AVAILABLE:
            algorithm_options.append("LightGBM回归")
            
        if app_mode == "多模型比较":
            selected_algorithms = st.multiselect(
                "选择要比较的算法",
                algorithm_options,
                default=algorithm_options[:4],
                help="选择多个算法进行比较"
            )
        else:
            algorithm = st.selectbox(
                "选择算法",
                algorithm_options,
                help="选择要演示的回归算法"
            )
    
    st.divider()
    
    # 数据集选择
    st.subheader("📊 数据集设置")
    
    if task_type == "分类任务":
        dataset_option = st.selectbox(
            "选择数据集",
            ["鸢尾花数据集", "葡萄酒数据集", "乳腺癌数据集", "自定义二分类数据集", 
             "自定义多分类数据集", "上传CSV文件"],
            help="选择用于演示的数据集"
        )
    else:
        dataset_option = st.selectbox(
            "选择数据集",
            ["波士顿房价(模拟)", "自定义回归数据集", "复杂非线性回归", "上传CSV文件"],
            help="选择用于演示的数据集"
        )
    
    # 数据预处理选项
    st.divider()
    st.subheader("🔧 数据预处理")
    
    preprocessing_options = st.expander("预处理选项", expanded=False)
    with preprocessing_options:
        scaling_method = st.selectbox(
            "特征缩放方法",
            ["StandardScaler", "MinMaxScaler", "无缩放"],
            help="选择特征缩放方法"
        )
        handle_imbalance = st.checkbox("处理类别不平衡（仅分类）", value=False)
        if handle_imbalance and task_type == "分类任务":
            imbalance_method = st.selectbox(
                "不平衡处理方法",
                ["class_weight", "SMOTE（需安装）"],
                help="选择处理类别不平衡的方法"
            )
    
    # 超参数设置
    st.divider()
    st.subheader("⚙️ 超参数调整")
    
    # 通用参数
    test_size = st.slider("测试集比例", 0.1, 0.5, 0.2, 0.05, help="用于模型评估的数据比例")
    random_state = st.number_input("随机种子", value=42, help="确保结果可重复")
    
    # 根据算法显示特定参数
    model_params = {}
    
    if app_mode != "多模型比较":
        if algorithm == "逻辑回归":
            C = st.slider("正则化强度 C (越小正则化越强)", 0.01, 10.0, 1.0, 0.01)
            max_iter = st.number_input("最大迭代次数", value=100, min_value=50, max_value=1000)
            model_params = {"C": C, "max_iter": max_iter, "random_state": random_state}
            
        elif algorithm in ["决策树分类", "决策树回归"]:
            max_depth = st.slider("最大深度", 1, 20, 5, help="控制树的深度，防止过拟合")
            min_samples_split = st.slider("最小分割样本数", 2, 20, 2)
            min_samples_leaf = st.slider("最小叶节点样本数", 1, 20, 1)
            model_params = {
                "max_depth": max_depth,
                "min_samples_split": min_samples_split,
                "min_samples_leaf": min_samples_leaf,
                "random_state": random_state
            }
            
        elif algorithm in ["随机森林分类", "随机森林回归"]:
            n_estimators = st.slider("树的数量", 10, 200, 100, 10)
            max_depth = st.slider("每棵树的最大深度", 1, 20, 10)
            model_params = {
                "n_estimators": n_estimators,
                "max_depth": max_depth,
                "random_state": random_state,
                "n_jobs": -1
            }
            
        elif algorithm in ["支持向量机(SVM)", "支持向量回归(SVR)"]:
            kernel = st.selectbox("核函数", ["rbf", "linear", "poly", "sigmoid"])
            C = st.slider("正则化参数 C", 0.1, 10.0, 1.0, 0.1)
            if kernel in ["rbf", "poly", "sigmoid"]:
                gamma = st.selectbox("Gamma", ["scale", "auto"])
                model_params = {"kernel": kernel, "C": C, "gamma": gamma}
            else:
                model_params = {"kernel": kernel, "C": C}
                
        elif algorithm in ["K近邻(KNN)", "K近邻回归"]:
            n_neighbors = st.slider("邻居数量 K", 1, 20, 5)
            weights = st.selectbox("权重方式", ["uniform", "distance"])
            model_params = {"n_neighbors": n_neighbors, "weights": weights}
            
        elif algorithm == "朴素贝叶斯":
            model_params = {}
            
        elif algorithm in ["线性回归", "Ridge回归", "Lasso回归"]:
            if algorithm == "Ridge回归":
                alpha = st.slider("正则化强度 alpha", 0.01, 10.0, 1.0, 0.01)
                model_params = {"alpha": alpha}
            elif algorithm == "Lasso回归":
                alpha = st.slider("正则化强度 alpha", 0.01, 10.0, 1.0, 0.01)
                model_params = {"alpha": alpha, "random_state": random_state}
            else:
                model_params = {}
                
        elif algorithm in ["梯度提升分类", "梯度提升回归"]:
            n_estimators = st.slider("提升轮数", 10, 200, 100, 10)
            learning_rate = st.slider("学习率", 0.01, 1.0, 0.1, 0.01)
            max_depth = st.slider("最大深度", 1, 10, 3)
            model_params = {
                "n_estimators": n_estimators,
                "learning_rate": learning_rate,
                "max_depth": max_depth,
                "random_state": random_state
            }
            
        elif algorithm in ["AdaBoost分类", "AdaBoost回归"]:
            n_estimators = st.slider("提升轮数", 10, 200, 50, 10)
            learning_rate = st.slider("学习率", 0.01, 2.0, 1.0, 0.01)
            model_params = {
                "n_estimators": n_estimators,
                "learning_rate": learning_rate,
                "random_state": random_state
            }
            
        elif algorithm in ["ExtraTrees分类", "ExtraTrees回归"]:
            n_estimators = st.slider("树的数量", 10, 200, 100, 10)
            max_depth = st.slider("每棵树的最大深度", 1, 20, 10)
            model_params = {
                "n_estimators": n_estimators,
                "max_depth": max_depth,
                "random_state": random_state,
                "n_jobs": -1
            }
            
        elif algorithm in ["神经网络(MLP)"]:
            hidden_layer_sizes = st.text_input("隐藏层结构（用逗号分隔）", "100,50")
            activation = st.selectbox("激活函数", ["relu", "tanh", "logistic"])
            max_iter = st.number_input("最大迭代次数", value=200, min_value=100, max_value=1000)
            hidden_layers = tuple(map(int, hidden_layer_sizes.split(',')))
            model_params = {
                "hidden_layer_sizes": hidden_layers,
                "activation": activation,
                "max_iter": max_iter,
                "random_state": random_state
            }
            
        elif algorithm == "XGBoost分类" and XGBOOST_AVAILABLE:
            n_estimators = st.slider("提升轮数", 10, 200, 100, 10)
            learning_rate = st.slider("学习率", 0.01, 1.0, 0.1, 0.01)
            max_depth = st.slider("最大深度", 1, 10, 6)
            model_params = {
                "n_estimators": n_estimators,
                "learning_rate": learning_rate,
                "max_depth": max_depth,
                "random_state": random_state,
                "eval_metric": "logloss"
            }
            
        elif algorithm == "XGBoost回归" and XGBOOST_AVAILABLE:
            n_estimators = st.slider("提升轮数", 10, 200, 100, 10)
            learning_rate = st.slider("学习率", 0.01, 1.0, 0.1, 0.01)
            max_depth = st.slider("最大深度", 1, 10, 6)
            model_params = {
                "n_estimators": n_estimators,
                "learning_rate": learning_rate,
                "max_depth": max_depth,
                "random_state": random_state
            }
            
        elif algorithm in ["LightGBM分类", "LightGBM回归"] and LIGHTGBM_AVAILABLE:
            n_estimators = st.slider("提升轮数", 10, 200, 100, 10)
            learning_rate = st.slider("学习率", 0.01, 1.0, 0.1, 0.01)
            max_depth = st.slider("最大深度", -1, 20, -1)
            num_leaves = st.slider("叶子节点数", 10, 100, 31)
            model_params = {
                "n_estimators": n_estimators,
                "learning_rate": learning_rate,
                "max_depth": max_depth,
                "num_leaves": num_leaves,
                "random_state": random_state
            }

# 加载数据集
@st.cache_data
def load_dataset(dataset_option, task_type):
    """加载数据集"""
    if dataset_option == "鸢尾花数据集":
        data = load_iris()
        X, y = data.data, data.target
        feature_names = data.feature_names
        target_names = data.target_names
        return X, y, feature_names, target_names, "classification"
    
    elif dataset_option == "葡萄酒数据集":
        data = load_wine()
        X, y = data.data, data.target
        feature_names = data.feature_names
        target_names = data.target_names
        return X, y, feature_names, target_names, "classification"
    
    elif dataset_option == "乳腺癌数据集":
        data = load_breast_cancer()
        X, y = data.data, data.target
        feature_names = data.feature_names
        target_names = data.target_names
        return X, y, feature_names, target_names, "classification"
    
    elif dataset_option == "自定义二分类数据集":
        X, y = make_classification(
            n_samples=500, n_features=2, n_informative=2,
            n_redundant=0, n_clusters_per_class=1, random_state=42
        )
        feature_names = ["特征1", "特征2"]
        target_names = ["类别0", "类别1"]
        return X, y, feature_names, target_names, "classification"
    
    elif dataset_option == "自定义多分类数据集":
        X, y = make_classification(
            n_samples=500, n_features=4, n_informative=4,
            n_redundant=0, n_classes=3, n_clusters_per_class=1, random_state=42
        )
        feature_names = [f"特征{i+1}" for i in range(4)]
        target_names = ["类别0", "类别1", "类别2"]
        return X, y, feature_names, target_names, "classification"
    
    elif dataset_option == "波士顿房价(模拟)":
        np.random.seed(42)
        n_samples = 500
        X = np.random.randn(n_samples, 5)
        y = (3 * X[:, 0] + 2 * X[:, 1] - 1.5 * X[:, 2] + 
             0.5 * X[:, 3] + np.random.randn(n_samples) * 0.5 + 25)
        feature_names = ["房间数", "距离市中心", "犯罪率", "税率", "师生比"]
        target_names = None
        return X, y, feature_names, target_names, "regression"
    
    elif dataset_option == "自定义回归数据集":
        X, y = make_regression(
            n_samples=500, n_features=2, n_informative=2,
            noise=10, random_state=42
        )
        feature_names = ["特征1", "特征2"]
        target_names = None
        return X, y, feature_names, target_names, "regression"
    
    elif dataset_option == "复杂非线性回归":
        np.random.seed(42)
        n_samples = 500
        X = np.random.randn(n_samples, 3)
        y = (np.sin(X[:, 0] * 3) + 0.5 * X[:, 1]**2 + 
             np.exp(-X[:, 2]**2) + np.random.randn(n_samples) * 0.3)
        feature_names = ["特征1", "特征2", "特征3"]
        target_names = None
        return X, y, feature_names, target_names, "regression"
    
    return None, None, None, None, None

# 创建模型
def create_model(algorithm, model_params, task_type):
    """根据算法名称创建模型"""
    if task_type == "分类任务":
        if algorithm == "逻辑回归":
            return LogisticRegression(**model_params)
        elif algorithm == "决策树分类":
            return DecisionTreeClassifier(**model_params)
        elif algorithm == "随机森林分类":
            return RandomForestClassifier(**model_params)
        elif algorithm == "支持向量机(SVM)":
            return SVC(**model_params, probability=True)
        elif algorithm == "K近邻(KNN)":
            return KNeighborsClassifier(**model_params)
        elif algorithm == "朴素贝叶斯":
            return GaussianNB(**model_params)
        elif algorithm == "梯度提升分类":
            return GradientBoostingClassifier(**model_params)
        elif algorithm == "AdaBoost分类":
            return AdaBoostClassifier(**model_params)
        elif algorithm == "ExtraTrees分类":
            return ExtraTreesClassifier(**model_params)
        elif algorithm == "神经网络(MLP)":
            return MLPClassifier(**model_params)
        elif algorithm == "XGBoost分类" and XGBOOST_AVAILABLE:
            return xgb.XGBClassifier(**model_params)
        elif algorithm == "LightGBM分类" and LIGHTGBM_AVAILABLE:
            return lgb.LGBMClassifier(**model_params)
    else:
        if algorithm == "线性回归":
            return LinearRegression(**model_params)
        elif algorithm == "Ridge回归":
            return Ridge(**model_params)
        elif algorithm == "Lasso回归":
            return Lasso(**model_params)
        elif algorithm == "决策树回归":
            return DecisionTreeRegressor(**model_params)
        elif algorithm == "随机森林回归":
            return RandomForestRegressor(**model_params)
        elif algorithm == "支持向量回归(SVR)":
            return SVR(**model_params)
        elif algorithm == "K近邻回归":
            return KNeighborsRegressor(**model_params)
        elif algorithm == "梯度提升回归":
            return GradientBoostingRegressor(**model_params)
        elif algorithm == "AdaBoost回归":
            return AdaBoostRegressor(**model_params)
        elif algorithm == "ExtraTrees回归":
            return ExtraTreesRegressor(**model_params)
        elif algorithm == "神经网络(MLP)":
            return MLPRegressor(**model_params)
        elif algorithm == "XGBoost回归" and XGBOOST_AVAILABLE:
            return xgb.XGBRegressor(**model_params)
        elif algorithm == "LightGBM回归" and LIGHTGBM_AVAILABLE:
            return lgb.LGBMRegressor(**model_params)
    
    return None

# 数据预处理
def preprocess_data(X, y, scaling_method, test_size, random_state, handle_imbalance=False):
    """数据预处理"""
    # 分割数据
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )
    
    # 特征缩放
    if scaling_method == "StandardScaler":
        scaler = StandardScaler()
    elif scaling_method == "MinMaxScaler":
        scaler = MinMaxScaler()
    else:
        scaler = None
    
    if scaler:
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
    else:
        X_train_scaled = X_train
        X_test_scaled = X_test
    
    return X_train_scaled, X_test_scaled, y_train, y_test, scaler

# 主界面
col1, col2 = st.columns([2, 1])

with col1:
    # 步骤 1：获取数据 (不论是内置数据还是 CSV 上传)
    X, y, feature_names, target_names, data_type = None, None, None, None, None
    
    if dataset_option != "上传CSV文件":
        X, y, feature_names, target_names, data_type = load_dataset(dataset_option, task_type)
    else:
        st.markdown('<h2 class="sub-header">📤 上传CSV数据集</h2>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("选择CSV文件", type=['csv'])
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                
                # 自动处理缺失值
                if df.isnull().values.any():
                    df = df.dropna()
                    st.warning(f"检测到缺失值，已自动清除包含缺失值的行。当前剩余 {df.shape[0]} 行。")

                st.success(f"✅ 成功加载数据，共 {df.shape[0]} 行，{df.shape[1]} 列")
                
                target_column = st.selectbox("选择目标列（要预测的列）", df.columns.tolist())
                feature_columns = st.multiselect("选择特征列", 
                                                [col for col in df.columns if col != target_column],
                                                default=[col for col in df.columns if col != target_column][:5])
                
                if feature_columns and target_column:
                    X_raw = df[feature_columns]
                    y_raw = df[target_column].values
                    
                    # 自动处理类别特征进行独热编码
                    X_processed = pd.get_dummies(X_raw, drop_first=True)
                    X_temp = X_processed.values
                    feature_names_temp = X_processed.columns.tolist()

                    if len(feature_names_temp) > len(feature_columns):
                        st.info("检测到非数值特征，已自动执行独热编码 (One-Hot Encoding)。")
                    
                    if task_type == "分类任务":
                        le = LabelEncoder()
                        y_temp = le.fit_transform(y_raw)
                        target_names_temp = [str(cls) for cls in le.classes_]
                        data_type_temp = "classification"
                        
                        # 赋值给全局流水线变量
                        X = X_temp
                        y = y_temp
                        feature_names = feature_names_temp
                        target_names = target_names_temp
                        data_type = data_type_temp
                    else:
                        try:
                            # 🚨 修复点：强制将目标列转换为 float Numpy 数组
                            y_temp = pd.to_numeric(y_raw).astype(float)
                            if isinstance(y_temp, pd.Series):
                                y_temp = y_temp.values
                                
                            target_names_temp = None
                            data_type_temp = "regression"
                            
                            # 赋值给全局流水线变量
                            X = X_temp
                            y = y_temp
                            feature_names = feature_names_temp
                            target_names = target_names_temp
                            data_type = data_type_temp
                        except ValueError:
                            # 如果转换失败，抛出友好错误并终止数据流水线渲染
                            st.error("⚠️ 数据类型错误：您目前选择了 **'回归任务'**，但选中的目标列包含了非数值（文本）数据！请重新选择全数值的目标列，或者将左侧的【任务类型】切换为 **'分类任务'**。")
                    
            except Exception as e:
                st.error(f"处理文件出错: {str(e)}")

    # 步骤 2：核心流水线 (当数据成功准备好时执行)
    if X is not None and y is not None:
        st.markdown('<h2 class="sub-header">📈 数据集概览</h2>', unsafe_allow_html=True)
        
        # 显示数据集基本信息
        info_col1, info_col2, info_col3, info_col4 = st.columns(4)
        with info_col1:
            st.metric("样本数量", X.shape[0])
        with info_col2:
            st.metric("特征数量", X.shape[1])
        with info_col3:
            if data_type == "classification":
                st.metric("类别数量", len(np.unique(y)))
            else:
                st.metric("目标范围", f"{y.min():.2f} - {y.max():.2f}")
        with info_col4:
            st.metric("任务类型", "分类" if data_type == "classification" else "回归")
        
        # 显示数据预览
        with st.expander("📋 查看数据预览", expanded=False):
            df_preview = pd.DataFrame(X, columns=feature_names)
            df_preview['目标'] = y
            st.dataframe(df_preview.head(10))
            
            # 显示数据统计
            st.subheader("数据统计")
            st.dataframe(df_preview.describe())
        
        # 数据可视化
        st.markdown('<h2 class="sub-header">📊 数据可视化</h2>', unsafe_allow_html=True)
        
        viz_tab1, viz_tab2, viz_tab3, viz_tab4 = st.tabs(["特征分布", "相关性热力图", "特征与目标关系", "目标分布"])
        
        with viz_tab1:
            if X.shape[1] <= 6:
                fig, axes = plt.subplots(2, (X.shape[1] + 1) // 2, figsize=(12, 8))
                if X.shape[1] > 1:
                    axes = axes.flatten()
                else:
                    axes = [axes]
                for i, (feature, ax) in enumerate(zip(feature_names, axes)):
                    ax.hist(X[:, i], bins=30, edgecolor='black', alpha=0.7)
                    ax.set_xlabel(feature)
                    ax.set_ylabel('频数')
                    ax.set_title(f'{feature} 分布')
                # 隐藏多余的子图
                if isinstance(axes, np.ndarray):
                    for j in range(i + 1, len(axes)):
                        axes[j].set_visible(False)
                plt.tight_layout()
                st.pyplot(fig)
            else:
                st.info("特征数量较多，显示前6个特征的分布")
                fig, axes = plt.subplots(2, 3, figsize=(12, 8))
                axes = axes.flatten()
                for i in range(min(6, X.shape[1])):
                    axes[i].hist(X[:, i], bins=30, edgecolor='black', alpha=0.7)
                    axes[i].set_xlabel(feature_names[i])
                    axes[i].set_ylabel('频数')
                    axes[i].set_title(f'{feature_names[i]} 分布')
                plt.tight_layout()
                st.pyplot(fig)
        
        with viz_tab2:
            if X.shape[1] <= 10:
                df_corr = pd.DataFrame(X, columns=feature_names)
                corr_matrix = df_corr.corr()
                fig, ax = plt.subplots(figsize=(10, 8))
                sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0,
                           square=True, linewidths=1, ax=ax)
                ax.set_title('特征相关性热力图')
                st.pyplot(fig)
            else:
                st.warning("特征数量过多，不建议显示完整相关性热力图")
        
        with viz_tab3:
            if data_type == "classification" and X.shape[1] == 2:
                fig, ax = plt.subplots(figsize=(10, 8))
                scatter = ax.scatter(X[:, 0], X[:, 1], c=y, cmap='viridis', 
                                   alpha=0.6, edgecolors='k', linewidth=0.5)
                ax.set_xlabel(feature_names[0])
                ax.set_ylabel(feature_names[1])
                ax.set_title('特征空间分布（按类别着色）')
                plt.colorbar(scatter, ax=ax, label='类别')
                st.pyplot(fig)
            elif data_type == "regression" and X.shape[1] == 2:
                fig, ax = plt.subplots(figsize=(10, 8))
                scatter = ax.scatter(X[:, 0], X[:, 1], c=y, cmap='viridis', 
                                   alpha=0.6, edgecolors='k', linewidth=0.5)
                ax.set_xlabel(feature_names[0])
                ax.set_ylabel(feature_names[1])
                ax.set_title('特征空间分布（按目标值着色）')
                plt.colorbar(scatter, ax=ax, label='目标值')
                st.pyplot(fig)
            else:
                n_features = min(X.shape[1], 4)
                fig, axes = plt.subplots(1, n_features, figsize=(15, 4))
                if n_features == 1:
                    axes = [axes]
                for i in range(n_features):
                    axes[i].scatter(X[:, i], y, alpha=0.5, edgecolors='k', linewidth=0.5)
                    axes[i].set_xlabel(feature_names[i])
                    axes[i].set_ylabel('目标')
                    axes[i].set_title(f'{feature_names[i]} vs 目标')
                plt.tight_layout()
                st.pyplot(fig)
        
        with viz_tab4:
            if data_type == "classification":
                unique, counts = np.unique(y, return_counts=True)
                fig, ax = plt.subplots(figsize=(8, 6))
                if target_names is not None and len(target_names) > 0:
                    bars = ax.bar(target_names, counts, color='skyblue', edgecolor='black')
                else:
                    bars = ax.bar([f'类别{i}' for i in unique], counts, color='skyblue', edgecolor='black')
                ax.set_xlabel('类别')
                ax.set_ylabel('样本数量')
                ax.set_title('类别分布')
                
                # 在柱子上显示数量
                for bar, count in zip(bars, counts):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                            f'{count}', ha='center', va='bottom')
                
                st.pyplot(fig)
            else:
                fig, ax = plt.subplots(figsize=(8, 6))
                ax.hist(y, bins=30, edgecolor='black', alpha=0.7)
                ax.set_xlabel('目标值')
                ax.set_ylabel('频数')
                ax.set_title('目标值分布')
                st.pyplot(fig)
        
        # 根据不同模式显示不同内容
        if app_mode == "单模型训练":
            st.markdown('<h2 class="sub-header">🤖 单模型训练与评估</h2>', unsafe_allow_html=True)
            
            if st.button("🚀 开始训练模型", type="primary", use_container_width=True):
                with st.spinner('正在训练模型...'):
                    # 数据预处理
                    X_train_scaled, X_test_scaled, y_train, y_test, scaler = preprocess_data(
                        X, y, scaling_method, test_size, random_state
                    )
                    
                    # 创建模型
                    model = create_model(algorithm, model_params, task_type)
                    
                    if model is not None:
                        # 训练模型
                        model.fit(X_train_scaled, y_train)
                        y_pred = model.predict(X_test_scaled)
                        
                        # 保存到session state
                        st.session_state['current_model'] = {
                            'model': model,
                            'scaler': scaler,
                            'X_train': X_train_scaled,
                            'X_test': X_test_scaled,
                            'y_train': y_train,
                            'y_test': y_test,
                            'y_pred': y_pred,
                            'feature_names': feature_names,
                            'target_names': target_names,
                            'algorithm': algorithm,
                            'data_type': data_type
                        }
                        
                        # 记录训练历史
                        st.session_state['training_history'].append({
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            'algorithm': algorithm,
                            'dataset': dataset_option,
                            'task_type': task_type,
                            'params': model_params
                        })
                        
                    st.success("✅ 模型训练完成！")
            
            # 显示模型结果
            if 'current_model' in st.session_state:
                model_info = st.session_state['current_model']
                model = model_info['model']
                
                # 每次从session state中拉取之前保存的数据
                X_train_scaled = model_info['X_train'] 
                y_train = model_info['y_train']  
                
                y_test = model_info['y_test']
                y_pred = model_info['y_pred']
                data_type = model_info['data_type']
                
                st.markdown("### 📊 模型评估结果")
                
                if data_type == "classification":
                    accuracy = accuracy_score(y_test, y_pred)
                    
                    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
                    with metric_col1:
                        st.metric("准确率", f"{accuracy:.4f}")
                    with metric_col2:
                        precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
                        st.metric("精确率", f"{precision:.4f}")
                    with metric_col3:
                        recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
                        st.metric("召回率", f"{recall:.4f}")
                    with metric_col4:
                        f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
                        st.metric("F1分数", f"{f1:.4f}")
                    
                    result_tab1, result_tab2, result_tab3, result_tab4 = st.tabs(
                        ["混淆矩阵", "决策边界(2D)", "特征重要性", "学习曲线"]
                    )
                    
                    with result_tab1:
                        # 强制对齐类别维度以防止 heatmap 报错
                        if target_names is not None:
                            cm = confusion_matrix(y_test, y_pred, labels=range(len(target_names)))
                        else:
                            cm = confusion_matrix(y_test, y_pred)
                            
                        fig, ax = plt.subplots(figsize=(8, 6))
                        if target_names is not None:
                            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                                       xticklabels=target_names, yticklabels=target_names, ax=ax)
                        else:
                            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax)
                        ax.set_xlabel('预测标签')
                        ax.set_ylabel('真实标签')
                        ax.set_title('混淆矩阵')
                        st.pyplot(fig)
                        
                        with st.expander("📋 查看详细分类报告"):
                            # 强制指定 labels 以防止类别数与 target_names 长度不匹配引发 ValueError
                            if target_names is not None:
                                report = classification_report(y_test, y_pred, labels=range(len(target_names)), target_names=target_names, zero_division=0)
                            else:
                                report = classification_report(y_test, y_pred, zero_division=0)
                            st.text(report)
                    
                    with result_tab2:
                        if X.shape[1] == 2:
                            h = 0.02
                            x_min, x_max = X[:, 0].min() - 1, X[:, 0].max() + 1
                            y_min, y_max = X[:, 1].min() - 1, X[:, 1].max() + 1
                            xx, yy = np.meshgrid(np.arange(x_min, x_max, h),
                                                np.arange(y_min, y_max, h))
                            
                            scaler = model_info['scaler']
                            Z = model.predict(scaler.transform(np.c_[xx.ravel(), yy.ravel()]))
                            Z = Z.reshape(xx.shape)
                            
                            fig, ax = plt.subplots(figsize=(10, 8))
                            ax.contourf(xx, yy, Z, alpha=0.4, cmap='viridis')
                            scatter = ax.scatter(X[:, 0], X[:, 1], c=y, cmap='viridis',
                                               edgecolors='k', linewidth=0.5)
                            ax.set_xlabel(feature_names[0])
                            ax.set_ylabel(feature_names[1])
                            ax.set_title('决策边界可视化')
                            plt.colorbar(scatter, ax=ax)
                            st.pyplot(fig)
                        else:
                            st.info("决策边界可视化仅支持2D特征空间")
                    
                    with result_tab3:
                        if hasattr(model, 'feature_importances_'):
                            importances = model.feature_importances_
                            indices = np.argsort(importances)[::-1]
                            
                            fig, ax = plt.subplots(figsize=(10, 6))
                            bars = ax.bar(range(len(importances)), importances[indices])
                            ax.set_xticks(range(len(importances)))
                            ax.set_xticklabels([feature_names[i] for i in indices], rotation=45, ha='right')
                            ax.set_xlabel('特征')
                            ax.set_ylabel('重要性')
                            ax.set_title('特征重要性排序')
                            
                            # 在柱子上显示数值
                            for bar, importance in zip(bars, importances[indices]):
                                height = bar.get_height()
                                ax.text(bar.get_x() + bar.get_width()/2., height,
                                        f'{importance:.3f}', ha='center', va='bottom')
                            
                            plt.tight_layout()
                            st.pyplot(fig)
                        elif hasattr(model, 'coef_'):
                            coefs = np.abs(model.coef_[0]) if len(model.coef_.shape) > 1 else np.abs(model.coef_)
                            indices = np.argsort(coefs)[::-1]
                            
                            fig, ax = plt.subplots(figsize=(10, 6))
                            bars = ax.bar(range(len(coefs)), coefs[indices])
                            ax.set_xticks(range(len(coefs)))
                            ax.set_xticklabels([feature_names[i] for i in indices], rotation=45, ha='right')
                            ax.set_xlabel('特征')
                            ax.set_ylabel('系数绝对值')
                            ax.set_title('特征权重（系数绝对值）')
                            
                            # 在柱子上显示数值
                            for bar, coef in zip(bars, coefs[indices]):
                                height = bar.get_height()
                                ax.text(bar.get_x() + bar.get_width()/2., height,
                                        f'{coef:.3f}', ha='center', va='bottom')
                            
                            plt.tight_layout()
                            st.pyplot(fig)
                        else:
                            st.info("该算法不支持特征重要性可视化")
                    
                    with result_tab4:
                        # 绘制学习曲线
                        train_sizes, train_scores, test_scores = learning_curve(
                            model, X_train_scaled, y_train, cv=5,
                            train_sizes=np.linspace(0.1, 1.0, 10),
                            scoring='accuracy'
                        )
                        
                        train_mean = np.mean(train_scores, axis=1)
                        train_std = np.std(train_scores, axis=1)
                        test_mean = np.mean(test_scores, axis=1)
                        test_std = np.std(test_scores, axis=1)
                        
                        fig, ax = plt.subplots(figsize=(10, 6))
                        ax.plot(train_sizes, train_mean, 'o-', color='blue', label='训练得分')
                        ax.plot(train_sizes, test_mean, 'o-', color='green', label='验证得分')
                        ax.fill_between(train_sizes, train_mean - train_std,
                                       train_mean + train_std, alpha=0.1, color='blue')
                        ax.fill_between(train_sizes, test_mean - test_std,
                                       test_mean + test_std, alpha=0.1, color='green')
                        ax.set_xlabel('训练样本数')
                        ax.set_ylabel('准确率')
                        ax.set_title('学习曲线')
                        ax.legend(loc='best')
                        ax.grid(True, alpha=0.3)
                        st.pyplot(fig)
                
                else:  # 回归任务
                    mse = mean_squared_error(y_test, y_pred)
                    rmse = np.sqrt(mse)
                    mae = mean_absolute_error(y_test, y_pred)
                    r2 = r2_score(y_test, y_pred)
                    
                    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
                    with metric_col1:
                        st.metric("MSE", f"{mse:.4f}")
                    with metric_col2:
                        st.metric("RMSE", f"{rmse:.4f}")
                    with metric_col3:
                        st.metric("MAE", f"{mae:.4f}")
                    with metric_col4:
                        st.metric("R²分数", f"{r2:.4f}")
                    
                    result_tab1, result_tab2, result_tab3, result_tab4 = st.tabs(
                        ["预测 vs 真实", "残差图", "特征重要性", "学习曲线"]
                    )
                    
                    with result_tab1:
                        fig, ax = plt.subplots(figsize=(8, 8))
                        ax.scatter(y_test, y_pred, alpha=0.6, edgecolors='k', linewidth=0.5)
                        ax.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 
                               'r--', lw=2, label='完美预测线')
                        ax.set_xlabel('真实值')
                        ax.set_ylabel('预测值')
                        ax.set_title('预测值 vs 真实值')
                        ax.legend()
                        ax.grid(True, alpha=0.3)
                        st.pyplot(fig)
                    
                    with result_tab2:
                        residuals = y_test - y_pred
                        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
                        
                        axes[0].hist(residuals, bins=30, edgecolor='black', alpha=0.7)
                        axes[0].set_xlabel('残差')
                        axes[0].set_ylabel('频数')
                        axes[0].set_title('残差分布')
                        axes[0].axvline(x=0, color='r', linestyle='--', label='零线')
                        axes[0].legend()
                        
                        axes[1].scatter(y_pred, residuals, alpha=0.6, edgecolors='k', linewidth=0.5)
                        axes[1].axhline(y=0, color='r', linestyle='--', label='零线')
                        axes[1].set_xlabel('预测值')
                        axes[1].set_ylabel('残差')
                        axes[1].set_title('残差 vs 预测值')
                        axes[1].legend()
                        axes[1].grid(True, alpha=0.3)
                        
                        plt.tight_layout()
                        st.pyplot(fig)
                    
                    with result_tab3:
                        if hasattr(model, 'feature_importances_'):
                            importances = model.feature_importances_
                            indices = np.argsort(importances)[::-1]
                            
                            fig, ax = plt.subplots(figsize=(10, 6))
                            bars = ax.bar(range(len(importances)), importances[indices])
                            ax.set_xticks(range(len(importances)))
                            ax.set_xticklabels([feature_names[i] for i in indices], rotation=45, ha='right')
                            ax.set_xlabel('特征')
                            ax.set_ylabel('重要性')
                            ax.set_title('特征重要性排序')
                            
                            # 在柱子上显示数值
                            for bar, importance in zip(bars, importances[indices]):
                                height = bar.get_height()
                                ax.text(bar.get_x() + bar.get_width()/2., height,
                                        f'{importance:.3f}', ha='center', va='bottom')
                            
                            plt.tight_layout()
                            st.pyplot(fig)
                        elif hasattr(model, 'coef_'):
                            coefs = np.abs(model.coef_)
                            indices = np.argsort(coefs)[::-1]
                            
                            fig, ax = plt.subplots(figsize=(10, 6))
                            bars = ax.bar(range(len(coefs)), coefs[indices])
                            ax.set_xticks(range(len(coefs)))
                            ax.set_xticklabels([feature_names[i] for i in indices], rotation=45, ha='right')
                            ax.set_xlabel('特征')
                            ax.set_ylabel('系数绝对值')
                            ax.set_title('特征权重（系数绝对值）')
                            
                            # 在柱子上显示数值
                            for bar, coef in zip(bars, coefs[indices]):
                                height = bar.get_height()
                                ax.text(bar.get_x() + bar.get_width()/2., height,
                                        f'{coef:.3f}', ha='center', va='bottom')
                            
                            plt.tight_layout()
                            st.pyplot(fig)
                        else:
                            st.info("该算法不支持特征重要性可视化")
                    
                    with result_tab4:
                        # 绘制学习曲线
                        train_sizes, train_scores, test_scores = learning_curve(
                            model, X_train_scaled, y_train, cv=5,
                            train_sizes=np.linspace(0.1, 1.0, 10),
                            scoring='r2'
                        )
                        
                        train_mean = np.mean(train_scores, axis=1)
                        train_std = np.std(train_scores, axis=1)
                        test_mean = np.mean(test_scores, axis=1)
                        test_std = np.std(test_scores, axis=1)
                        
                        fig, ax = plt.subplots(figsize=(10, 6))
                        ax.plot(train_sizes, train_mean, 'o-', color='blue', label='训练得分')
                        ax.plot(train_sizes, test_mean, 'o-', color='green', label='验证得分')
                        ax.fill_between(train_sizes, train_mean - train_std,
                                       train_mean + train_std, alpha=0.1, color='blue')
                        ax.fill_between(train_sizes, test_mean - test_std,
                                       test_mean + test_std, alpha=0.1, color='green')
                        ax.set_xlabel('训练样本数')
                        ax.set_ylabel('R²分数')
                        ax.set_title('学习曲线')
                        ax.legend(loc='best')
                        ax.grid(True, alpha=0.3)
                        st.pyplot(fig)
                
                # 模型保存功能
                st.markdown("### 💾 保存模型与结果")
                save_col1, save_col2 = st.columns(2)
                
                with save_col1:
                    # 创建模型保存包
                    model_package = {
                        'model': model,
                        'scaler': model_info['scaler'],
                        'feature_names': feature_names,
                        'target_names': target_names,
                        'algorithm': algorithm,
                        'task_type': task_type,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    # 使用 BytesIO 避免在本地生成临时文件
                    model_buffer = BytesIO()
                    pickle.dump(model_package, model_buffer)
                    model_buffer.seek(0)
                    
                    model_filename = f"ml_model_{algorithm}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
                    
                    st.download_button(
                        label="📥 下载模型文件 (.pkl)",
                        data=model_buffer,
                        file_name=model_filename,
                        mime="application/octet-stream",
                        use_container_width=True
                    )
                
                with save_col2:
                    # 准备评估结果数据
                    results = {
                        'algorithm': algorithm,
                        'dataset': dataset_option,
                        'task_type': task_type,
                        'metrics': {},
                        'parameters': model_params,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    if data_type == "classification":
                        results['metrics'] = {
                            'accuracy': float(accuracy_score(y_test, y_pred)),
                            'precision': float(precision_score(y_test, y_pred, average='weighted', zero_division=0)),
                            'recall': float(recall_score(y_test, y_pred, average='weighted', zero_division=0)),
                            'f1': float(f1_score(y_test, y_pred, average='weighted', zero_division=0))
                        }
                    else:
                        results['metrics'] = {
                            'mse': float(mean_squared_error(y_test, y_pred)),
                            'rmse': float(np.sqrt(mean_squared_error(y_test, y_pred))),
                            'mae': float(mean_absolute_error(y_test, y_pred)),
                            'r2': float(r2_score(y_test, y_pred))
                        }
                    
                    results_json = json.dumps(results, ensure_ascii=False, indent=2)
                    results_filename = f"ml_results_{algorithm}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    
                    st.download_button(
                        label="📥 下载评估结果 (.json)",
                        data=results_json,
                        file_name=results_filename,
                        mime="application/json",
                        use_container_width=True
                    )
        
        elif app_mode == "多模型比较":
            st.markdown('<h2 class="sub-header">📊 多模型比较</h2>', unsafe_allow_html=True)
            
            if 'selected_algorithms' in locals() and selected_algorithms:
                if st.button("🚀 开始比较所有选中模型", type="primary", use_container_width=True):
                    with st.spinner('正在训练多个模型并进行比较...'):
                        # 数据预处理
                        X_train_scaled, X_test_scaled, y_train, y_test, scaler = preprocess_data(
                            X, y, scaling_method, test_size, random_state
                        )
                        
                        comparison_results = []
                        
                        for algo in selected_algorithms:
                            # 创建模型（使用默认参数）
                            default_params = {"random_state": random_state}
                            if "随机森林" in algo:
                                default_params.update({"n_estimators": 100, "n_jobs": -1})
                            elif "梯度提升" in algo:
                                default_params.update({"n_estimators": 100, "learning_rate": 0.1})
                            
                            model = create_model(algo, default_params, task_type)
                            
                            if model is not None:
                                # 训练模型
                                model.fit(X_train_scaled, y_train)
                                y_pred = model.predict(X_test_scaled)
                                
                                # 计算指标
                                if data_type == "classification":
                                    accuracy = accuracy_score(y_test, y_pred)
                                    precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
                                    recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
                                    f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
                                    
                                    comparison_results.append({
                                        'Algorithm': algo,
                                        'Accuracy': accuracy,
                                        'Precision': precision,
                                        'Recall': recall,
                                        'F1': f1
                                    })
                                else:
                                    mse = mean_squared_error(y_test, y_pred)
                                    rmse = np.sqrt(mse)
                                    mae = mean_absolute_error(y_test, y_pred)
                                    r2 = r2_score(y_test, y_pred)
                                    
                                    comparison_results.append({
                                        'Algorithm': algo,
                                        'MSE': mse,
                                        'RMSE': rmse,
                                        'MAE': mae,
                                        'R2': r2
                                    })
                        
                        st.session_state['comparison_results'] = comparison_results
                        st.success(f"✅ 成功比较了 {len(comparison_results)} 个模型！")
            
            # 显示比较结果
            if st.session_state['comparison_results']:
                st.markdown("### 📈 比较结果")
                
                # 转换为DataFrame
                df_comparison = pd.DataFrame(st.session_state['comparison_results'])
                st.dataframe(df_comparison.style.highlight_max(axis=0, color='lightgreen'))
                
                # 可视化比较
                if data_type == "classification":
                    metrics_to_plot = ['Accuracy', 'Precision', 'Recall', 'F1']
                else:
                    metrics_to_plot = ['MSE', 'RMSE', 'MAE', 'R2']
                
                fig, axes = plt.subplots(2, 2, figsize=(14, 10))
                axes = axes.flatten()
                
                for i, metric in enumerate(metrics_to_plot):
                    if i < len(axes):
                        ax = axes[i]
                        bars = ax.bar(df_comparison['Algorithm'], df_comparison[metric])
                        ax.set_xlabel('算法')
                        ax.set_ylabel(metric)
                        ax.set_title(f'{metric} 比较')
                        ax.tick_params(axis='x', rotation=45)
                        
                        # 在柱子上显示数值
                        for bar, value in zip(bars, df_comparison[metric]):
                            height = bar.get_height()
                            ax.text(bar.get_x() + bar.get_width()/2., height,
                                    f'{value:.3f}', ha='center', va='bottom')
                
                plt.tight_layout()
                st.pyplot(fig)
                
                # 最佳模型
                if data_type == "classification":
                    best_idx = df_comparison['Accuracy'].idxmax()
                    best_algo = df_comparison.loc[best_idx, 'Algorithm']
                    best_score = df_comparison.loc[best_idx, 'Accuracy']
                    st.success(f"🏆 最佳模型: {best_algo} (准确率: {best_score:.4f})")
                else:
                    best_idx = df_comparison['R2'].idxmax()
                    best_algo = df_comparison.loc[best_idx, 'Algorithm']
                    best_score = df_comparison.loc[best_idx, 'R2']
                    st.success(f"🏆 最佳模型: {best_algo} (R²分数: {best_score:.4f})")
        
        elif app_mode == "超参数调优":
            st.markdown('<h2 class="sub-header">🔧 超参数调优</h2>', unsafe_allow_html=True)
            
            # 超参数网格
            param_grids = {
                "逻辑回归": {
                    'C': [0.001, 0.01, 0.1, 1, 10, 100],
                    'penalty': ['l2']
                },
                "决策树分类": {
                    'max_depth': [3, 5, 7, 10, None],
                    'min_samples_split': [2, 5, 10],
                    'min_samples_leaf': [1, 2, 4]
                },
                "随机森林分类": {
                    'n_estimators': [50, 100, 200],
                    'max_depth': [5, 10, 15, None],
                    'min_samples_split': [2, 5, 10]
                },
                "支持向量机(SVM)": {
                    'C': [0.1, 1, 10],
                    'kernel': ['linear', 'rbf'],
                    'gamma': ['scale', 'auto']
                },
                "线性回归": {},
                "随机森林回归": {
                    'n_estimators': [50, 100, 200],
                    'max_depth': [5, 10, 15, None],
                    'min_samples_split': [2, 5, 10]
                }
            }
            
            if algorithm in param_grids:
                st.write(f"### 对 {algorithm} 进行超参数调优")
                
                # 显示参数网格
                with st.expander("查看参数网格"):
                    st.json(param_grids[algorithm])
                
                if st.button("🚀 开始超参数调优", type="primary"):
                    with st.spinner('正在进行超参数调优（这可能需要几分钟）...'):
                        # 数据预处理
                        X_train_scaled, X_test_scaled, y_train, y_test, scaler = preprocess_data(
                            X, y, scaling_method, test_size, random_state
                        )
                        
                        # 创建基础模型
                        base_model = create_model(algorithm, {}, task_type)
                        
                        # 网格搜索
                        if data_type == "classification":
                            scoring = 'accuracy'
                        else:
                            scoring = 'r2'
                        
                        grid_search = GridSearchCV(
                            base_model, 
                            param_grids[algorithm],
                            cv=5,
                            scoring=scoring,
                            n_jobs=-1,
                            verbose=1
                        )
                        
                        grid_search.fit(X_train_scaled, y_train)
                        
                        # 显示结果
                        st.success("✅ 超参数调优完成！")
                        
                        st.markdown("### 📊 调优结果")
                        
                        # 最佳参数
                        st.write("**最佳参数:**")
                        st.json(grid_search.best_params_)
                        
                        # 最佳分数
                        st.metric("最佳交叉验证分数", f"{grid_search.best_score_:.4f}")
                        
                        # 使用最佳参数重新训练
                        best_model = grid_search.best_estimator_
                        y_pred = best_model.predict(X_test_scaled)
                        
                        if data_type == "classification":
                            test_accuracy = accuracy_score(y_test, y_pred)
                            st.metric("测试集准确率", f"{test_accuracy:.4f}")
                        else:
                            test_r2 = r2_score(y_test, y_pred)
                            st.metric("测试集R²分数", f"{test_r2:.4f}")
                        
                        # 保存最佳模型
                        st.session_state['current_model'] = {
                            'model': best_model,
                            'scaler': scaler,
                            'X_train': X_train_scaled,
                            'X_test': X_test_scaled,
                            'y_train': y_train,
                            'y_test': y_test,
                            'y_pred': y_pred,
                            'feature_names': feature_names,
                            'target_names': target_names,
                            'algorithm': algorithm,
                            'data_type': data_type
                        }
            else:
                st.warning(f"暂不支持对 {algorithm} 进行超参数调优")
        
        elif app_mode == "交叉验证":
            st.markdown('<h2 class="sub-header">🔄 交叉验证</h2>', unsafe_allow_html=True)
            
            cv_folds = st.slider("交叉验证折数", 3, 10, 5)
            
            if st.button("🚀 开始交叉验证", type="primary"):
                with st.spinner('正在进行交叉验证...'):
                    # 数据预处理
                    X_scaled = StandardScaler().fit_transform(X) if scaling_method == "StandardScaler" else X
                    
                    # 创建模型
                    model = create_model(algorithm, model_params, task_type)
                    
                    if model is not None:
                        # 交叉验证
                        if data_type == "classification":
                            scoring = 'accuracy'
                        else:
                            scoring = 'r2'
                        
                        cv_scores = cross_val_score(
                            model, X_scaled, y, 
                            cv=cv_folds, 
                            scoring=scoring,
                            n_jobs=-1
                        )
                        
                        # 显示结果
                        st.markdown("### 📊 交叉验证结果")
                        
                        metric_col1, metric_col2, metric_col3 = st.columns(3)
                        with metric_col1:
                            st.metric("平均分数", f"{cv_scores.mean():.4f}")
                        with metric_col2:
                            st.metric("标准差", f"{cv_scores.std():.4f}")
                        with metric_col3:
                            st.metric("分数范围", f"{cv_scores.min():.4f} - {cv_scores.max():.4f}")
                        
                        # 可视化
                        fig, ax = plt.subplots(figsize=(10, 6))
                        bars = ax.bar(range(1, cv_folds + 1), cv_scores)
                        ax.axhline(y=cv_scores.mean(), color='r', linestyle='--', label=f'平均: {cv_scores.mean():.4f}')
                        ax.set_xlabel('折数')
                        ax.set_ylabel('分数')
                        ax.set_title(f'{cv_folds}折交叉验证结果')
                        ax.legend()
                        
                        # 在柱子上显示数值
                        for bar, score in zip(bars, cv_scores):
                            height = bar.get_height()
                            ax.text(bar.get_x() + bar.get_width()/2., height,
                                    f'{score:.4f}', ha='center', va='bottom')
                        
                        st.pyplot(fig)
                        
                        # 统计信息
                        st.markdown("### 📈 统计信息")
                        stats_df = pd.DataFrame({
                            '统计量': ['平均值', '标准差', '最小值', '最大值', '中位数'],
                            '值': [
                                cv_scores.mean(),
                                cv_scores.std(),
                                cv_scores.min(),
                                cv_scores.max(),
                                np.median(cv_scores)
                            ]
                        })
                        st.dataframe(stats_df)
        
        elif app_mode == "模型解释":
            st.markdown('<h2 class="sub-header">🔍 模型解释</h2>', unsafe_allow_html=True)
            
            if not SHAP_AVAILABLE:
                st.warning("请安装SHAP库以使用模型解释功能: `pip install shap`")
                st.info("SHAP (SHapley Additive exPlanations) 是一种博弈论方法，用于解释机器学习模型的输出。")
            else:
                st.info("SHAP解释功能需要先训练一个模型。请在单模型训练模式下训练模型，然后返回此模式。")
                
                if 'current_model' in st.session_state:
                    model_info = st.session_state['current_model']
                    model = model_info['model']
                    X_train = model_info['X_train']
                    feature_names = model_info['feature_names']
                    
                    if st.button("🚀 生成SHAP解释", type="primary"):
                        with st.spinner('正在生成SHAP解释（这可能需要一些时间）...'):
                            try:
                                # 创建SHAP解释器
                                tree_models = ["随机森林分类", "决策树分类", "梯度提升分类", "XGBoost分类", "LightGBM分类", 
                                               "随机森林回归", "决策树回归", "梯度提升回归", "XGBoost回归", "LightGBM回归"]
                                if algorithm in tree_models:
                                    explainer = shap.TreeExplainer(model)
                                else:
                                    explainer = shap.Explainer(model, X_train)
                                
                                # 计算SHAP值
                                shap_values = explainer(X_train[:100])  # 使用前100个样本
                                
                                st.markdown("### 📊 SHAP特征重要性")
                                
                                # 特征重要性图
                                fig, ax = plt.subplots(figsize=(10, 6))
                                shap.plots.bar(shap_values, show=False)
                                st.pyplot(fig)
                                
                                # SHAP摘要图
                                st.markdown("### 📊 SHAP摘要图")
                                fig, ax = plt.subplots(figsize=(10, 6))
                                shap.plots.beeswarm(shap_values, show=False)
                                st.pyplot(fig)
                                
                                # 单样本解释
                                st.markdown("### 🔍 单样本解释")
                                sample_idx = st.slider("选择样本索引", 0, min(99, len(X_train)-1), 0)
                                
                                fig, ax = plt.subplots(figsize=(10, 6))
                                shap.plots.waterfall(shap_values[sample_idx], show=False)
                                st.pyplot(fig)
                                
                            except Exception as e:
                                st.error(f"生成SHAP解释时出错: {str(e)}")

with col2:
    st.markdown('<h2 class="sub-header">📖 算法说明</h2>', unsafe_allow_html=True)
    
    algorithm_info = {
        "逻辑回归": {
            "简介": "逻辑回归是一种用于二分类或多分类的线性模型，实际上用于分类任务。",
            "优点": ["简单高效，训练速度快", "输出具有概率意义", "可解释性强"],
            "缺点": ["假设特征与目标之间存在线性关系", "容易欠拟合", "对异常值敏感"],
            "适用场景": ["二分类问题", "需要概率输出的场景", "基准模型建立"]
        },
        "决策树分类": {
            "简介": "通过一系列if-then-else规则对数据进行分类，形成树状结构。",
            "优点": ["易于理解和解释", "无需数据标准化", "可以处理混合特征"],
            "缺点": ["容易过拟合", "对数据变化不稳定", "可能生成复杂树"],
            "适用场景": ["需要强解释性", "特征间存在复杂交互", "无需预处理"]
        },
        "随机森林分类": {
            "简介": "多棵决策树的集成，通过投票机制做出预测。",
            "优点": ["准确率高", "抗过拟合", "可评估特征重要性"],
            "缺点": ["训练时间长", "内存消耗大", "解释性低于单树"],
            "适用场景": ["高准确率需求", "高维特征", "算力冗余充足"]
        },
        "支持向量机(SVM)": {
            "简介": "寻找最优超平面分隔数据，最大化分类间隔。",
            "优点": ["高维空间有效", "抵抗过拟合", "核技巧处理非线性"],
            "缺点": ["大规模数据训练极慢", "对缩放敏感", "核与参数选择困难"],
            "适用场景": ["特征维度>样本数", "明确边界", "中小规模数据"]
        },
        "K近邻(KNN)": {
            "简介": "根据最近的K个邻居类别进行投票。",
            "优点": ["直观", "无显式训练", "对异常值一定抵抗"],
            "缺点": ["推理计算成本高", "特征缩放极度敏感", "遭遇维度灾难"],
            "适用场景": ["小规模数据", "不规则边界", "快速原型"]
        },
        "朴素贝叶斯": {
            "简介": "基于贝叶斯定理，假设特征相互独立。",
            "优点": ["速度极快", "小数据有效", "高维处理优良"],
            "缺点": ["独立假设现实罕见", "数据分布敏感", "概率平滑问题"],
            "适用场景": ["文本分类", "实时预测", "高频流数据"]
        },
        "线性回归": {
            "简介": "建立特征与连续目标的线性关系。",
            "优点": ["极快", "最高解释性", "基座模型"],
            "缺点": ["线性假设强", "异常值极敏感", "易欠拟合"],
            "适用场景": ["强线性关联", "归因分析", "性能极度敏感"]
        },
        "决策树回归": {
            "简介": "递归划分特征空间预测连续值。",
            "优点": ["捕捉非线性", "无需标准化", "鲁棒性较好"],
            "缺点": ["严重过拟合", "丧失外推能力", "阶梯状输出"],
            "适用场景": ["复杂非线性", "不可外推的内插区间", "混合特征类型"]
        },
        "随机森林回归": {
            "简介": "决策树集成取均值预测。",
            "优点": ["平滑阶梯", "高准度", "自带特征重要性"],
            "缺点": ["大体积模型", "训练耗时", "黑盒化"],
            "适用场景": ["精度优先", "算力宽裕", "无需强解释"]
        },
        "支持向量回归(SVR)": {
            "简介": "寻找使所有样本点距离小于ε的函数。",
            "优点": ["高维有效", "非线性映射", "强泛化边界"],
            "缺点": ["推理训练皆慢", "缩放强依赖", "调参困难"],
            "适用场景": ["中小规模连续预测", "高维回归", "需抑制噪点影响"]
        },
        "梯度提升分类": {
            "简介": "通过迭代训练多个弱学习器来纠正前一轮的错误。",
            "优点": ["预测精度高", "处理缺失值", "特征重要性评估"],
            "缺点": ["训练时间长", "参数调优复杂", "容易过拟合"],
            "适用场景": ["竞赛常用", "结构化数据", "需要高精度"]
        },
        "XGBoost分类": {
            "简介": "极端梯度提升，梯度提升的高效实现。",
            "优点": ["速度更快", "内置正则化", "支持并行计算"],
            "缺点": ["参数复杂", "内存消耗大", "需要仔细调参"],
            "适用场景": ["大数据集", "竞赛首选", "需要高性能"]
        },
        "LightGBM分类": {
            "简介": "微软开发的梯度提升框架，基于直方图算法。",
            "优点": ["训练速度极快", "内存消耗低", "支持类别特征"],
            "缺点": ["对小数据集可能过拟合", "参数敏感", "需要更多树"],
            "适用场景": ["超大数据集", "需要快速训练", "工业级应用"]
        }
    }
    
    # 显示当前选择的算法信息
    if app_mode != "多模型比较":
        current_algo = algorithm
    else:
        current_algo = "随机森林分类"  # 默认显示
    
    if current_algo in algorithm_info:
        info = algorithm_info[current_algo]
        
        st.markdown(f"**{current_algo}**")
        st.markdown(f"_{info['简介']}_")
        
        with st.expander("✅ 优点", expanded=True):
            for advantage in info['优点']:
                st.markdown(f"- {advantage}")
        
        with st.expander("❌ 缺点"):
            for disadvantage in info['缺点']:
                st.markdown(f"- {disadvantage}")
        
        with st.expander("🎯 适用场景"):
            for scenario in info['适用场景']:
                st.markdown(f"- {scenario}")
    
    st.divider()
    
    # 显示训练历史
    if st.session_state['training_history']:
        st.markdown('<h2 class="sub-header">📜 训练历史</h2>', unsafe_allow_html=True)
        
        with st.expander("查看最近训练记录", expanded=False):
            for i, record in enumerate(reversed(st.session_state['training_history'][-5:])):
                st.markdown(f"**{i+1}. {record['algorithm']}**")
                st.markdown(f"时间: {record['timestamp']}")
                st.markdown(f"数据集: {record['dataset']}")
                st.markdown(f"任务类型: {record['task_type']}")
                st.markdown("---")
    
    st.divider()
    st.markdown('<h2 class="sub-header">📚 学习资源</h2>', unsafe_allow_html=True)
    
    with st.expander("📖 推荐阅读"):
        st.markdown("""
        **机器学习基础:**
        - 《统计学习方法》- 李航
        - 《机器学习》- 周志华
        - 《Pattern Recognition and Machine Learning》- Bishop
        
        **实践指南:**
        - Scikit-learn官方文档
        - 《Hands-On Machine Learning with Scikit-Learn》
        - Kaggle竞赛和教程
        
        **高级主题:**
        - 《Deep Learning》- Goodfellow
        - 《XGBoost: A Scalable Tree Boosting System》
        - 《LightGBM: A Highly Efficient Gradient Boosting Decision Tree》
        """)
    
    with st.expander("🔗 在线资源"):
        st.markdown("""
        - [Scikit-learn算法选择图](https://scikit-learn.org/stable/tutorial/machine_learning_map/)
        - [Kaggle Learn](https://www.kaggle.com/learn)
        - [Google Machine Learning Crash Course](https://developers.google.com/machine-learning/crash-course)
        - [XGBoost文档](https://xgboost.readthedocs.io/)
        - [LightGBM文档](https://lightgbm.readthedocs.io/)
        - [SHAP文档](https://shap.readthedocs.io/)
        """)
    
    st.divider()
    st.markdown('<h2 class="sub-header">💡 使用提示</h2>', unsafe_allow_html=True)
    st.markdown("""
    1. **从简单开始**: 先尝试逻辑回归或线性回归作为基准
    2. **观察数据**: 理解数据分布和特征关系
    3. **调整参数**: 观察超参数如何影响模型性能
    4. **比较算法**: 同一数据集尝试不同算法
    5. **关注过拟合**: 注意训练集和测试集性能差异
    6. **使用交叉验证**: 获得更可靠的性能评估
    7. **解释模型**: 使用SHAP等工具理解模型决策
    8. **保存结果**: 记录最佳模型和参数配置
    """)

st.divider()
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>🎓 机器学习教学工具 | 基于Streamlit构建</p>
    <p>适用于课堂教学、自学和实验演示 | 支持算法比较、交叉验证、模型解释</p>
</div>
""", unsafe_allow_html=True)
