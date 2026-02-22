"""学校层次数据模块。

简化的学校层次分类：
- 985_211: 985 和 211 院校
- overseas: 海外知名院校
- ordinary: 普通国内院校
"""

SCHOOLS_985: dict[str, list[str]] = {
    "清华大学": ["清华", "清华大学"],
    "北京大学": ["北大", "北京大学"],
    "复旦大学": ["复旦", "复旦大学"],
    "上海交通大学": ["上交", "上海交通大学", "上海交大"],
    "浙江大学": ["浙大", "浙江大学"],
    "中国科学技术大学": ["中科大", "中国科学技术大学", "中国科大"],
    "南京大学": ["南大", "南京大学"],
    "西安交通大学": ["西交", "西安交通大学", "西安交大"],
    "哈尔滨工业大学": ["哈工大", "哈尔滨工业大学", "哈工"],
    "中国人民大学": ["人大", "中国人民大学"],
    "北京航空航天大学": ["北航", "北京航空航天大学"],
    "北京理工大学": ["北理", "北京理工大学"],
    "中国农业大学": ["中国农大", "中国农业大学"],
    "北京师范大学": ["北师大", "北京师范大学"],
    "中央民族大学": ["中央民大", "中央民族大学"],
    "南开大学": ["南开", "南开大学"],
    "天津大学": ["天大", "天津大学"],
    "大连理工大学": ["大工", "大连理工大学"],
    "东北大学": ["东大", "东北大学"],
    "吉林大学": ["吉大", "吉林大学"],
    "同济大学": ["同济", "同济大学"],
    "华东师范大学": ["华东师大", "华东师范大学"],
    "东南大学": ["东南", "东南大学"],
    "厦门大学": ["厦大", "厦门大学"],
    "山东大学": ["山大", "山东大学"],
    "中国海洋大学": ["中国海大", "中国海洋大学"],
    "武汉大学": ["武大", "武汉大学"],
    "华中科技大学": ["华科", "华中科技大学"],
    "湖南大学": ["湖大", "湖南大学"],
    "中南大学": ["中南", "中南大学"],
    "中山大学": ["中大", "中山大学"],
    "华南理工大学": ["华工", "华南理工大学"],
    "四川大学": ["川大", "四川大学"],
    "重庆大学": ["重大", "重庆大学"],
    "电子科技大学": ["电子科大", "电子科技大学"],
    "西北工业大学": ["西工大", "西北工业大学"],
    "西北农林科技大学": ["西北农林", "西北农林科技大学"],
    "兰州大学": ["兰大", "兰州大学"],
    "国防科技大学": ["国防科大", "国防科技大学"],
}

SCHOOLS_211_NON_985: dict[str, list[str]] = {
    "北京交通大学": ["北交", "北京交通大学"],
    "北京工业大学": ["北工大", "北京工业大学"],
    "北京科技大学": ["北科", "北京科技大学"],
    "北京化工大学": ["北化", "北京化工大学"],
    "北京邮电大学": ["北邮", "北京邮电大学"],
    "北京林业大学": ["北林", "北京林业大学"],
    "北京中医药大学": ["北中医", "北京中医药大学"],
    "北京外国语大学": ["北外", "北京外国语大学"],
    "中国传媒大学": ["中传", "中国传媒大学"],
    "对外经济贸易大学": ["对外经贸", "对外经济贸易大学"],
    "中央财经大学": ["央财", "中央财经大学"],
    "中国政法大学": ["法大", "中国政法大学"],
    "华北电力大学": ["华电", "华北电力大学"],
    "中国矿业大学": ["矿大", "中国矿业大学"],
    "中国石油大学": ["石大", "中国石油大学"],
    "中国地质大学": ["地大", "中国地质大学"],
    "苏州大学": ["苏大", "苏州大学"],
    "南京航空航天大学": ["南航", "南京航空航天大学"],
    "南京理工大学": ["南理", "南京理工大学"],
    "河海大学": ["河海", "河海大学"],
    "南京师范大学": ["南师大", "南京师范大学"],
    "中国药科大学": ["药大", "中国药科大学"],
    "南京农业大学": ["南农", "南京农业大学"],
    "江南大学": ["江南", "江南大学"],
    "东华大学": ["东华", "东华大学"],
    "上海外国语大学": ["上外", "上海外国语大学"],
    "上海财经大学": ["上财", "上海财经大学"],
    "华东理工大学": ["华理", "华东理工大学"],
    "上海大学": ["上大", "上海大学"],
    "暨南大学": ["暨大", "暨南大学"],
    "华南师范大学": ["华师", "华南师范大学"],
    "西南交通大学": ["西南交大", "西南交通大学"],
    "西南财经大学": ["西财", "西南财经大学"],
    "四川农业大学": ["川农", "四川农业大学"],
    "贵州大学": ["贵大", "贵州大学"],
    "云南大学": ["云大", "云南大学"],
    "西藏大学": ["藏大", "西藏大学"],
    "西北大学": ["西大", "西北大学"],
    "西安电子科技大学": ["西电", "西安电子科技大学"],
    "长安大学": ["长安", "长安大学"],
    "陕西师范大学": ["陕师大", "陕西师范大学"],
    "青海大学": ["青大", "青海大学"],
    "宁夏大学": ["宁大", "宁夏大学"],
    "新疆大学": ["新大", "新疆大学"],
    "石河子大学": ["石大", "石河子大学"],
    "湖南师范大学": ["湖师大", "湖南师范大学"],
    "东北师范大学": ["东师", "东北师范大学"],
    "延边大学": ["延大", "延边大学"],
    "大连海事大学": ["海大", "大连海事大学"],
    "辽宁大学": ["辽大", "辽宁大学"],
    "哈尔滨工程大学": ["哈工程", "哈尔滨工程大学"],
    "东北林业大学": ["东林", "东北林业大学"],
    "东北农业大学": ["东农", "东北农业大学"],
    "安徽大学": ["安大", "安徽大学"],
    "合肥工业大学": ["合工大", "合肥工业大学"],
    "南昌大学": ["昌大", "南昌大学"],
    "郑州大学": ["郑大", "郑州大学"],
    "武汉理工大学": ["武理", "武汉理工大学"],
    "华中农业大学": ["华农", "华中农业大学"],
    "华中师范大学": ["华师", "华中师范大学"],
    "中南财经政法大学": ["中南财", "中南财经政法大学"],
    "广西大学": ["西大", "广西大学"],
    "海南大学": ["海大", "海南大学"],
    "内蒙古大学": ["内大", "内蒙古大学"],
    "太原理工大学": ["太理", "太原理工大学"],
    "福州大学": ["福大", "福州大学"],
}

OVERSEAS_TOP_SCHOOLS: dict[str, list[str]] = {
    "MIT": ["MIT", "麻省理工", "Massachusetts Institute of Technology"],
    "Stanford University": ["Stanford", "斯坦福", "斯坦福大学"],
    "Harvard University": ["Harvard", "哈佛", "哈佛大学"],
    "California Institute of Technology": [
        "Caltech",
        "加州理工",
        "加州理工学院",
    ],
    "University of Chicago": ["UChicago", "芝加哥大学"],
    "Princeton University": ["Princeton", "普林斯顿", "普林斯顿大学"],
    "Yale University": ["Yale", "耶鲁", "耶鲁大学"],
    "Columbia University": ["Columbia", "哥伦比亚大学"],
    "University of Pennsylvania": ["UPenn", "宾夕法尼亚大学", "宾大"],
    "Cornell University": ["Cornell", "康奈尔大学"],
    "University of California, Berkeley": [
        "UC Berkeley",
        "伯克利",
        "加州大学伯克利分校",
    ],
    "University of California, Los Angeles": ["UCLA", "加州大学洛杉矶分校"],
    "University of Cambridge": ["Cambridge", "剑桥", "剑桥大学"],
    "University of Oxford": ["Oxford", "牛津", "牛津大学"],
    "Imperial College London": ["IC", "帝国理工", "帝国理工学院"],
    "University College London": ["UCL", "伦敦大学学院"],
    "London School of Economics": ["LSE", "伦敦政经", "伦敦政治经济学院"],
    "ETH Zurich": ["ETH", "苏黎世联邦理工", "苏黎世联邦理工学院"],
    "National University of Singapore": ["NUS", "新加坡国立大学"],
    "Nanyang Technological University": ["NTU", "南洋理工大学"],
    "University of Toronto": ["U of T", "多伦多大学"],
    "University of Melbourne": ["墨尔本大学"],
    "University of Sydney": ["悉尼大学"],
    "University of Hong Kong": ["HKU", "香港大学"],
    "Chinese University of Hong Kong": ["CUHK", "香港中文大学"],
    "Hong Kong University of Science and Technology": ["HKUST", "香港科技大学"],
}


def get_school_tier(school_name: str) -> str:
    """获取学校的层次。

    Args:
        school_name: 学校名称（全称或简称）

    Returns:
        str: 学校层次，可能值：
            - "985_211": 985 或 211 院校
            - "overseas": 海外知名院校
            - "ordinary": 普通国内院校
    """
    if not school_name:
        return "ordinary"

    school_lower = school_name.lower().strip()

    for full_name, aliases in SCHOOLS_985.items():
        if any(
            alias.lower() in school_lower or school_lower in alias.lower()
            for alias in aliases + [full_name]
        ):
            return "985_211"

    for full_name, aliases in SCHOOLS_211_NON_985.items():
        if any(
            alias.lower() in school_lower or school_lower in alias.lower()
            for alias in aliases + [full_name]
        ):
            return "985_211"

    for full_name, aliases in OVERSEAS_TOP_SCHOOLS.items():
        if any(
            alias.lower() in school_lower or school_lower in alias.lower()
            for alias in aliases + [full_name]
        ):
            return "overseas"

    return "ordinary"


def check_school_tier_match(school_name: str, required_tiers: list[str]) -> bool:
    """检查学校是否符合指定的层次要求（支持多选）。

    Args:
        school_name: 学校名称
        required_tiers: 要求的学校层次列表（如 ["985_211", "overseas"]）

    Returns:
        bool: 是否符合任一要求
    """
    if not required_tiers:
        return True

    school_tier = get_school_tier(school_name)
    return school_tier in required_tiers
