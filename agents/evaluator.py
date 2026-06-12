from utils.llm_client import call_llm

EVALUATOR_SYSTEM = """你是学习评估专家。请用自然语言、温和的语气评估学习内容。
不要输出 JSON，不要输出分数，不要用「score」「pass」等字段。
直接给出评估结论和建议，例如：
「这个讲解很清晰，适合你的水平，可以继续往下学了。」
或
「这部分有点难，建议再复习一下前面的知识点。」
"""


def evaluate(content, user_profile, user_input):
    prompt = f"""学习内容：{content}
用户水平：{user_profile.get('level', '中等')}
用户问题：{user_input}

请评估这份学习内容是否适合该用户，用自然语言给出建议。不要输出JSON。"""

    response = call_llm([
        {"role": "system", "content": EVALUATOR_SYSTEM},
        {"role": "user", "content": prompt}
    ], temperature=0.5)
    return response
def evaluate_with_history(resource, user_profile, user_input, history):
    from utils.llm_client import call_llm
    messages = [
        {"role": "system", "content": EVALUATOR_SYSTEM},
        *history,
        {"role": "user", "content": f"学习内容：{resource}\n用户水平：{user_profile.get('level')}\n用户问题：{user_input}"}
    ]
    return call_llm(messages)