import streamlit as st
import random
import json
import time
from typing import List, Dict, Any

# ================= 1. 配置与样式 (Configuration) =================
st.set_page_config(
    page_title="英语选词填空 Pro",
    page_icon="📝",
    layout="centered",
    initial_sidebar_state="expanded"
)

def inject_custom_css():
    """注入自定义CSS，适配深色模式并优化视觉体验"""
    st.markdown("""
    <style>
        /* 填空下划线动态样式 */
        .blank {
            border-bottom: 2px solid #2563eb;
            color: #2563eb;
            font-weight: bold;
            padding: 0 5px;
            margin: 0 2px;
            display: inline-block;
            min-width: 60px;
            text-align: center;
            transition: all 0.3s ease;
        }
        .blank:hover {
            background-color: rgba(37, 99, 235, 0.1);
            cursor: default;
        }
        /* 题目卡片：使用 CSS 变量适配深色/浅色模式 */
        .question-card {
            background-color: var(--secondary-background-color);
            padding: 24px;
            border-radius: 12px;
            border-left: 6px solid #2563eb;
            font-size: 18px;
            margin-bottom: 24px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            line-height: 1.6;
        }
        /* 按钮容器微调 */
        div.stButton > button {
            width: 100%;
            border-radius: 8px;
            padding: 12px 20px;
            text-align: left;
            transition: transform 0.1s;
        }
        div.stButton > button:active {
            transform: scale(0.98);
        }
        /* 统计指标优化 */
        [data-testid="stMetricValue"] {
            font-size: 26px;
            color: #2563eb;
        }
    </style>
    """, unsafe_allow_html=True)

# ================= 2. 数据层 (Model) =================
@st.cache_data
def load_question_bank() -> List[Dict[str, str]]:
    """
    加载题库。使用缓存装饰器，避免每次重运行都重新创建列表。
    在实际生产中，这里可以改为读取 JSON 或 CSV 文件。
    """
    return [
        {"question": "In schools, teachers and pupils alike often _____ that if a concept has been easy to learn, then the lesson has been successful.", "answer": "assume", "translation": "在学校里，教师和学生往往认为，如果某个概念容易掌握，那么这节课就算成功了。"},
        {"question": "Lu Xun produced many long-lasting short stories, the themes of which cover an extensive _____ and reflect a multitude of aspects of social life.", "answer": "range", "translation": "鲁迅创作了大量流传久远的短篇小说，题材广泛，反映了社会生活的方方面面。"},
        {"question": "These arguments were _____ a hundred years ago and they still hold true today.", "answer": "valid", "translation": "这些论点在一百年前成立，至今依然适用。"},
        {"question": "The president said curbing the addiction of alcohol would save money and _____ lives.", "answer": "prolong", "translation": "总统表示，遏制酒精成瘾将节省资金并延长寿命。"},
        {"question": "The total amount raised so far is _____ $1,000.", "answer": "approaching", "translation": "到目前为止，总共筹集的资金已接近 1000 美元。"},
        {"question": "There is still no general _____ on whether global warming is real or not.", "answer": "consensus", "translation": "关于全球变暖是否真实存在，目前仍未达成普遍共识。"},
        {"question": "For decades, the U.S. led the world in the proportion of citizens with college degrees, but in recent years it has been _____ by other countries.", "answer": "surpassed", "translation": "数十年来，美国在公民大学学历比例方面长期位居全球首位，但近年来已被其他国家超越。"},
        {"question": "It is the company's _____ decision to sell part of its business to focus on its core products.", "answer": "strategic", "translation": "这是公司的一项战略决策，即出售部分业务以专注于其核心产品。"},
        {"question": "Although she once _____ freedom and independence, she now gives up her career and becomes a devoted housewife.", "answer": "preached", "translation": "她虽曾高呼自由独立，如今却放弃事业，甘当贤妻良母。"},
        {"question": "We have some statistics, but we really need something more _____ before we can make any firm decisions.", "answer": "definite", "translation": "我们掌握了一些统计数据，但在做出任何明确决策前，确实需要更确切的依据。"},
        {"question": "All doctoral students are expected to hand in their thesis abstracts before Friday, so don't _____ details for the time being.", "answer": "sweat over", "translation": "所有博士生都应在周五前提交论文摘要，所以目前先别在细节上纠结。"},
        {"question": "In the past decade, the global mean sea levels have doubled _____ the 20th century trend of 1.6 mm per year.", "answer": "compared to", "translation": "在过去十年里，全球平均海平面的上升速度是 20 世纪每年 1.6 毫米这一趋势的两倍。"},
        {"question": "If you have _____ all the exercises in this book, you are ready for the advanced course.", "answer": "followed through", "translation": "若您已完成本书所有练习，即可进入进阶课程。"},
        {"question": "The company's stock has declined by more than 50 percent since the start of this year, _____ last year when it gained 30 percent.", "answer": "in contrast with", "translation": "该公司股价自今年年初以来已下跌超过 50%，与去年上涨 30% 形成鲜明对比。"},
        {"question": "Studies show that _____ people who consciously control their diet are healthier than those overeating.", "answer": "on average", "translation": "研究表明，与暴饮暴食者相比，自觉控制饮食的人群平均健康状况更佳。"},
        {"question": "A large quantity of real cases suggest that the average speed of the vehicles _____ closely with the severity of the accident caused.", "answer": "correlates", "translation": "大量真实案例表明，车辆的平均速度与所造成的事故严重程度紧密相关。"},
        {"question": "Agricultural technologies have _____ farm production, resulting in a dramatic increase in grain output.", "answer": "revolutionized", "translation": "农业技术彻底改变了农业生产，导致了粮食产量的大幅度增长。"},
        {"question": "Officials claim that the chemical leak accident _____ no real danger for surrounding residents.", "answer": "poses", "translation": "官员们声称，此次化学品泄漏事故对周边居民不构成真正的危险。"},
        {"question": "We still have no _____ proof that climate change is caused solely by human activity.", "answer": "conclusive", "translation": "我们仍然没有确凿的证据证明气候变化完全是由人类活动造成的。"},
        {"question": "You will have to _____ your comments to our Head Office.", "answer": "address", "translation": "您需要将您的意见提交给我们总部。"},
        {"question": "He was sentenced to ten years' imprisonment for _____ the stock market and making huge profits illegally.", "answer": "rigging", "translation": "他因操纵股市和非法获得巨额利益被判处 10 年监禁。"},
        {"question": "The company, which started out by handling big data, has now _____ into a high-prestige enterprise that covers many domains of internet services.", "answer": "evolved", "translation": "这家以处理大数据起家的公司，现在已发展成为一家涵盖多个互联网服务领域的高声望企业。"},
        {"question": "If the air pressure in aircraft cabin becomes lower, oxygen masks will _____ drop down.", "answer": "automatically", "translation": "如果飞机舱内气压降低，氧气面罩会自动脱落。"},
        {"question": "Farming technology enables the crops to be _____ by liquid fertilizer, which is more effective and sustainable than the conventional method.", "answer": "nourished", "translation": "农业技术使得作物可以通过液体肥料得到滋养，这比传统方法更有效，更可持续。"},
        {"question": "A study of hundreds of elderly people shows that some have similar lifestyles, but _____ in health conditions.", "answer": "variable", "translation": "一项对数百名老年人的研究表明，有些人生活方式相似，但健康状况不相同。"},
        {"question": "The doctor cautions that this drug may have the effect of _____ the Patients' heart rate.", "answer": "speeding up", "translation": "医生提醒说，这种药物可能会有加快患者心跳的效果。"},
        {"question": "He built up a successful business within short years but it was all done _____ his health.", "answer": "at the expense of", "translation": "他在短短几年内建立起了一家成功的企业，但这一切都是以他健康为代价。"},
        {"question": "It is an army man's duty to _____ orders strictly during a military operation.", "answer": "act on", "translation": "在军事行动中，严格遵守命令是军人的职责。"},
        {"question": "_____ public belief, the results of all scientific studies aren't conclusive.", "answer": "Contrary to", "translation": "与公众的普遍看法相反，并非所有的科学研究的结果都是结论性的。"},
        {"question": "If someone tries to persuade you to invest in a project that is least likely to pay off, you might as well _____ it.", "answer": "close your ears to", "translation": "如果有人试图说服你去投资一个最不可能有回报的项目，你大可对其不闻不问。"},
        {"question": "Every year, 1.25 million people die in traffic accidents around the world, which is _____ to the entire population of China's Lijiang City.", "answer": "equivalent", "translation": "全世界每年有 125 万人死于交通事故，相当于中国丽江市的总人口。"},
        {"question": "Huawei, a Chinese technology company that provides telecommunication equipment and sells consumer electronics, enjoys high _____ both locally and internationally.", "answer": "prestige", "translation": "华为是一家提供通信设备和销售消费电子产品的中国科技公司，在国内外都享有很高的声望。"},
        {"question": "His _____ of the theory was not accurate or objective.", "answer": "interpretation", "translation": "他对该理论的诠释既不准确也不客观。"},
        {"question": "We hope that our research will have an _____ on the environment, especially the air quality in cities.", "answer": "impact", "translation": "我们希望我们的研究能对环境产生影响，尤其是城市的空气质量。"},
        {"question": "You shouldn't _____ the possibility of losing the match.", "answer": "discount", "translation": "你不应低估输掉比赛的可能性。"},
        {"question": "It's common _____ in western culture to tip the hairdresser.", "answer": "practice", "translation": "在西方文化中，给理发师小费是常见的惯例。"},
        {"question": "The lawyer's arguments are well grounded because he has collected enough _____ concerning the case.", "answer": "proof", "translation": "律师的论点很有根据，因为他收集了关于此案的足够证据。"},
        {"question": "There has been so much media _____ of the facts that nobody knows the truth of the issue.", "answer": "manipulation", "translation": "媒体对事实进行了大量操控，以至于没人知道事情的真相。"},
        {"question": "These workshops, usually of a couple of days' _____, bring scholars and administrators together to address some problems.", "answer": "duration", "translation": "这些研讨会通常持续数天，汇集学者和管理者共同解决一些问题。"},
        {"question": "The sales of healthcare products have been increasing drastically, which _____ the public's pursuit of health and longevity.", "answer": "mirrors", "translation": "保健品的销量急剧增长，反映了公众对健康和长寿的追求。"},
        {"question": "People in rural or underserved urban areas tend to be much _____ when it comes to the latest computing technology.", "answer": "behind the times", "translation": "在农村或城市服务不足地区，人们对最新的计算技术往往非常落伍。"},
        {"question": "The glaciers on several mountain ranges are decreasing in size _____ reduction in gases that help to maintain temperatures, and changes in the region's climate.", "answer": "due to", "translation": "几条山脉的冰川正在缩小，这是由于有助于维持温度的气体减少以及该地区气候发生变化所致。"},
        {"question": "Talk to someone or a professional about your problems. Don't let your depression _____.", "answer": "build up", "translation": "向他人或专业人士倾诉你的问题，别让你的抑郁情绪累积。"},
        {"question": "The increasing number of solitary persons, in a sense, is _____ the lack of communication in the modern world.", "answer": "a metaphor for", "translation": "从某种意义上说，独居者人数的增加是现代世界缺乏沟通的写照。"},
        {"question": "He is studying like crazy to _____ the lessons he missed during his stay in the hospital.", "answer": "make up", "translation": "他正在疯狂学习，以弥补住院期间落下的课程。"},
        {"question": "The company's new president will have to _____ some complicated legal problems from his predecessor.", "answer": "inherit", "translation": "公司的新总裁将不得不接手前任留下的一些复杂的法律问题。"},
        {"question": "The railway company claimed that they would _____ 20 percent of a fare if their train is more than an hour late.", "answer": "refund", "translation": "铁路公司声称，如果列车晚点超过一小时，他们将退还 20% 的车费。"},
        {"question": "There are rules to prohibit emission of poisonous waste, yet some factories _____ them for the sake of costs.", "answer": "disregard", "translation": "虽然有规定禁止排放有毒废物，但一些工厂为了成本考虑对此置之不理。"},
        {"question": "The system is so sensitive that it can _____ changes in temperature as small as 0.003 degrees.", "answer": "detect", "translation": "该系统非常灵敏，能够检测到小至 0.003 度的温度变化。"},
        {"question": "The composer _____ that he copied the tune from an old Beatles song.", "answer": "denies", "translation": "这位作曲家否认他从一首披头士的老歌中抄袭了曲调。"},
        {"question": "After 30 years' living in Guangzhou, Elizabeth has been _____ into the local culture, and now she speaks fluent Cantonese.", "answer": "assimilated", "translation": "在广州生活了 30 年后，伊丽莎白已融入了当地文化，现在能说一口流利的粤语。"},
        {"question": "The executives believed that combining the two work teams would _____ their strength by several times.", "answer": "multiply", "translation": "高管们相信，将这两个工作团队合并会使他们的力量成倍增加。"},
        {"question": "Some manual labor is bound to be _____ by artificial intelligence, so workers need retraining for more technical jobs.", "answer": "displaced", "translation": "一些体力劳动必然会被人工智能取代，因此工人需要接受再培训以从事技术性更强的工作。"},
        {"question": "The common nutrition advice usually includes the general statement 'eat less _____ food and choose fresh food instead.", "answer": "processed", "translation": "常见的营养建议通常包括这样一句通用的话：“少吃加工食品，选择新鲜食品。”"},
        {"question": "Some people are anxious to try various health _____, but never stick to any of them.", "answer": "regimes", "translation": "有些人急于尝试各种养生方法，但从未坚持过任何一种。"},
        {"question": "It will take some time for the applicants to _____ the forms for overseas study programs.", "answer": "fill out", "translation": "申请者需要一些时间来填写海外留学项目的申请表。"},
        {"question": "The case was handed over to independent investigators so that there could be no inference of bias _____ any party.", "answer": "in favor of", "translation": "该案被移交给独立调查员，以确保不会产生偏袒任何一方的嫌疑。"},
        {"question": "The government programs are intended to _____ poverty throughout the country within ten years.", "answer": "be rid of", "translation": "这些政府计划旨在十年内在全国范围内消除贫困。"},
        {"question": "When you have to cope with so many issues at the same time, mistakes _____ happen.", "answer": "are bound to", "translation": "当你不得不同时处理这么多问题时，错误必然会发生。"},
        {"question": "As a result, the method of _____ means convenience for the policy makers, but not practical to the local governments with their specific needs and situations.", "answer": "one size fits all", "translation": "因此，“一刀切”的方法对政策制定者来说意味着便利，但对于有特定需求和情况的当地政府来说并不切实际。"},
        {"question": "What is fundamental to a company's survival is to _____ and always go a few steps ahead in the industry.", "answer": "innovate", "translation": "一家公司生存的根本在于创新，并始终保持行业领先几步。"},
        {"question": "All the member countries at the conference have signed a treaty to _____ their loyalty to the alliance.", "answer": "proclaim", "translation": "与会各国签署了一项条约，以表明他们对联盟的忠诚。"},
        {"question": "It is well _____ that women generally have a longer life span than men.", "answer": "documented", "translation": "女性通常比男性寿命更长，这一点已有充分记载。"},
        {"question": "The attorney's arguments are valid since he has collected enough _____ concerning the case.", "answer": "proof", "translation": "律师的论点是有力的，因为他已收集了关于此案的充分证据。"},
        {"question": "Their _____ views have been opposed by the public.", "answer": "extreme", "translation": "他们的极端观点遭到了公众的反对。"},
        {"question": "Studies suggest that regular intake of vitamins significantly improves brain _____.", "answer": "function", "translation": "研究表明，定期摄入维生素能显著改善大脑功能。"},
        {"question": "It is proved that playing sports can _____ the social development of young people, teaching them how to interact with peers outside the classroom.", "answer": "foster", "translation": "事实证明，进行体育运动能促进青少年的社会发展，教会他们如何在课堂外与同龄人互动。"},
        {"question": "Big-name employers, from central enterprises to tech giants, have a(n) _____ in favor of recruiting graduates from prestigious universities.", "answer": "bias", "translation": "从央企到科技巨头，知名雇主普遍存在一种偏爱招聘名校毕业生的偏见。"},
        {"question": "His account of the situation was very _____ and you should check facts before making a judgment.", "answer": "biased", "translation": "他对情况的描述带有很大偏见，你在做判断前应该核实事实。"},
        {"question": "Despite low interest rates, the concept of depositing money in the bank still _____ among the vast majority of people.", "answer": "prevails", "translation": "尽管利率很低，在银行存款的观念仍在绝大多数人中流行。"},
        {"question": "He couldn't find the application form; probably he had not even been given one _____.", "answer": "in the first place", "translation": "他找不到申请表；可能一开始就没有人给他一份。"},
        {"question": "They often look towards the same evidence as those _____ proving its existence, but draw different conclusions.", "answer": "in favor of", "translation": "他们常常和那些支持其存在的人看同样的证据，却得出不同的结论。"},
        {"question": "An alarming number of physicians are unable to _____ the pressure of practicing everyday medicine.", "answer": "cope with", "translation": "数量惊人的医生无法应对日常行医的压力。"},
        {"question": "In preparation for the spelling competition, students are busy reviewing the words in the dictionary and trying to _____ them to memory.", "answer": "commit", "translation": "为准备拼写比赛，学生们正忙于复习词典里的单词，并努力把它们记下来。"},
        {"question": "When you are in a leadership position, many people will _____ whether intentionally or not.", "answer": "take a leaf from your book", "translation": "当你身处领导职位时，很多人都会有意识或无意识地效仿你。"}
    ]

# ================= 3. 逻辑控制 (Controller) =================

def initialize_session_state(total_questions: int):
    """初始化所有 Session State 变量"""
    default_states = {
        'status_map': [0] * total_questions,  # 0:未做, 1:正确, 2:错误
        'queue': [],
        'current_q_index': 0,
        'quiz_active': False,
        'current_options': [],
        'answer_state': 'unanswered',
        'current_mode_name': '随机',
        'has_shown_welcome': False
    }
    
    for key, value in default_states.items():
        if key not in st.session_state:
            st.session_state[key] = value

def handle_welcome_toast():
    """首次访问时的欢迎弹窗"""
    if not st.session_state.has_shown_welcome:
        msg = """
        📢 **声明**
        该网页仅供交流，非盈利。
        若你付费获取，请联系QQ：1490473838
        
        👨‍💻 **作者**：霡霂
        """
        st.toast(msg, icon="👋")
        st.session_state.has_shown_welcome = True

def prepare_new_question(questions: List[Dict]):
    """准备下一题的数据"""
    if st.session_state.current_q_index >= len(st.session_state.queue):
        st.session_state.quiz_active = False
        st.balloons()
        return

    real_index = st.session_state.queue[st.session_state.current_q_index]
    question_data = questions[real_index]
    correct_answer = question_data['answer']
    
    # 混淆项生成逻辑
    all_answers = [q['answer'] for q in questions]
    # 过滤掉正确答案和重复项
    wrong_pool = list(set([a for a in all_answers if a != correct_answer]))
    distractors = random.sample(wrong_pool, min(3, len(wrong_pool)))
    
    options = [correct_answer] + distractors
    random.shuffle(options)
    
    st.session_state.current_options = options
    st.session_state.answer_state = 'unanswered'

def start_practice(mode: str, questions: List[Dict]):
    """启动练习模式"""
    total_len = len(questions)
    indices = []
    
    if mode == 'random':
        indices = list(range(total_len))
        random.shuffle(indices)
        st.session_state.current_mode_name = "随机刷题"
    elif mode == 'sequential':
        indices = [i for i, s in enumerate(st.session_state.status_map) if s != 1]
        st.session_state.current_mode_name = "顺序刷题"
    elif mode == 'review':
        indices = [i for i, s in enumerate(st.session_state.status_map) if s == 2]
        random.shuffle(indices)
        st.session_state.current_mode_name = "错题重练"

    if not indices:
        msg = "🎉 太棒了！目前没有错题！" if mode == 'review' else "✅ 所有题目已完成！建议重置进度。"
        st.toast(msg)
        return

    st.session_state.queue = indices
    st.session_state.current_q_index = 0
    st.session_state.quiz_active = True
    prepare_new_question(questions)
    st.rerun()

def process_answer(selected_option: str, questions: List[Dict]):
    """处理用户答案提交"""
    real_index = st.session_state.queue[st.session_state.current_q_index]
    correct_answer = questions[real_index]['answer']
    
    if selected_option == correct_answer:
        st.session_state.answer_state = 'correct'
        st.session_state.status_map[real_index] = 1
    else:
        st.session_state.answer_state = 'wrong'
        st.session_state.status_map[real_index] = 2

def next_question_action(questions: List[Dict]):
    """进入下一题的动作"""
    st.session_state.current_q_index += 1
    prepare_new_question(questions)

# ================= 4. 界面渲染 (View) =================

def render_sidebar(questions: List[Dict]):
    with st.sidebar:
        st.header("⚙️ 设置")
        auto_next = st.toggle("⚡ 答对自动切题", value=True, help="回答正确后，自动等待1.5秒并进入下一题")
        
        st.subheader("选择模式")
        c1, c2, c3 = st.columns(3)
        if c1.button("🎲 随机", use_container_width=True):
            start_practice('random', questions)
        if c2.button("📝 顺序", use_container_width=True):
            start_practice('sequential', questions)
        if c3.button("💊 错题", use_container_width=True):
            start_practice('review', questions)
            
        st.markdown("---")
        render_stats(questions)
        render_backup_tools(questions)
        return auto_next

def render_stats(questions: List[Dict]):
    """渲染统计面板"""
    st.subheader("📊 统计看板")
    total_q = len(questions)
    # 使用 NumPy 或简单的列表推导式计算
    status = st.session_state.status_map
    done_q = sum(1 for s in status if s != 0)
    correct_q = sum(1 for s in status if s == 1)
    wrong_q = sum(1 for s in status if s == 2)
    acc = int((correct_q / done_q * 100)) if done_q > 0 else 0
    
    m1, m2 = st.columns(2)
    m1.metric("已刷题数", done_q, f"总库 {total_q}")
    m2.metric("正确率", f"{acc}%")
    st.metric("错题本", wrong_q)
    
    if st.button("🗑️ 重置进度", type="primary"):
        st.session_state.status_map = [0] * total_q
        st.session_state.quiz_active = False
        st.rerun()

def render_backup_tools(questions: List[Dict]):
    """渲染备份恢复工具"""
    with st.expander("💾 数据备份/恢复"):
        export_data = json.dumps(st.session_state.status_map)
        st.download_button("下载进度备份 (.json)", export_data, "eng_quiz_backup.json", "application/json")
        
        uploaded_file = st.file_uploader("上传进度文件", type="json")
        if uploaded_file is not None:
            try:
                loaded_status = json.load(uploaded_file)
                if len(loaded_status) == len(questions):
                    st.session_state.status_map = loaded_status
                    st.success("恢复成功！")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"题目数量不匹配 (文件:{len(loaded_status)} vs 题库:{len(questions)})")
            except Exception as e:
                st.error(f"解析失败: {e}")

def render_quiz_area(questions: List[Dict], auto_next: bool):
    """渲染核心答题区域"""
    if st.session_state.current_q_index >= len(st.session_state.queue):
        st.success("🎉 本轮练习结束！")
        if st.button("返回主页"):
            st.session_state.quiz_active = False
            st.rerun()
        return

    real_idx = st.session_state.queue[st.session_state.current_q_index]
    q_data = questions[real_idx]
    
    # 进度条
    progress = (st.session_state.current_q_index + 1) / len(st.session_state.queue)
    st.progress(progress)
    st.caption(f"当前模式: {st.session_state.current_mode_name} | 进度: {st.session_state.current_q_index + 1} / {len(st.session_state.queue)}")
    
    # 题目展示
    display_question = q_data['question'].replace("_____", '<span class="blank">_____</span>')
    st.markdown(f'<div class="question-card">{display_question}</div>', unsafe_allow_html=True)
    
    # 选项交互区
    if st.session_state.answer_state == 'unanswered':
        render_options(questions, real_idx)
    else:
        render_result(q_data, auto_next, questions)

def render_options(questions: List[Dict], real_idx: int):
    """渲染选项按钮"""
    # 使用 Container 使得布局更紧凑
    with st.container():
        for opt in st.session_state.current_options:
            if st.button(f"🔘 {opt}", key=f"btn_{real_idx}_{opt}"):
                process_answer(opt, questions)
                st.rerun()
        
        # 查看答案按钮
        if st.button("👁️ 实在不会，看答案"):
            st.session_state.status_map[real_idx] = 2
            st.session_state.answer_state = 'show_answer'
            st.rerun()

def render_result(q_data: Dict, auto_next: bool, questions: List[Dict]):
    """渲染结果反馈"""
    is_correct = (st.session_state.answer_state == 'correct')
    
    if is_correct:
        st.success(f"✅ 回答正确！ 答案：{q_data['answer']}")
    else:
        st.error(f"❌ 回答错误。 正确答案是：{q_data['answer']}")
    
    st.info(f"📚 **翻译**：{q_data['translation']}")
    
    # 下一题按钮
    if st.button("下一题 ➜", type="primary"):
        next_question_action(questions)
        st.rerun()

    # 自动跳转逻辑
    if is_correct and auto_next:
        time.sleep(1.0) # 缩短等待时间，提升流畅度
        next_question_action(questions)
        st.rerun()

# ================= 5. 主程序入口 =================

def main():
    inject_custom_css()
    questions = load_question_bank()
    initialize_session_state(len(questions))
    handle_welcome_toast()
    
    st.title("选词填空刷题 Pro")
    auto_next = render_sidebar(questions)
    
    if not st.session_state.quiz_active:
        st.info("👈 请在左侧侧边栏选择一种模式开始刷题")
        st.markdown("""
        ### 使用说明
        1. **随机模式**：从题库中随机抽取题目。
        2. **顺序模式**：按顺序练习未掌握的题目。
        3. **错题模式**：专门攻克历史错题。
        """)
    else:
        render_quiz_area(questions, auto_next)

if __name__ == "__main__":
    main()
