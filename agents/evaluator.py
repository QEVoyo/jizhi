from utils.llm_client import call_llm

EVALUATOR_SYSTEM = """你是严格的学习资源评估专家。输出JSON格式：
{"score": 1-10, "pass": true/false, "issues": ["问题1"], "suggestions": "修改建议"}
6分以下为不通过。"""


def evaluate(resource, user_profile, knowledge_point):
    prompt = f"""知识点：{knowledge_point}
用户水平：{user_profile['level']}
学习内容：{resource}

请评估这份内容是否适合该用户。"""

    response = call_llm([
        {"role": "system", "content": EVALUATOR_SYSTEM},
        {"role": "user", "content": prompt}
    ], temperature=0.3)
    return response