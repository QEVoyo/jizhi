from utils.llm_client import call_llm
import json

PLANNER_SYSTEM = """你是学习规划专家。根据用户的学习目标，给出学习建议和知识点规划。
输出纯文字，不要输出JSON格式。用友好的语气，按顺序列出知识点。
示例：
好的，根据你的情况，我建议按以下顺序学习：
1. 变量和数据类型
2. 条件判断
3. 循环"""


def plan(user_profile, topic):
    prompt = f"用户水平：{user_profile.get('level', '中等')}，学习目标：{topic}"
    response = call_llm([
        {"role": "system", "content": PLANNER_SYSTEM},
        {"role": "user", "content": prompt}
    ], temperature=0.7)

    return response