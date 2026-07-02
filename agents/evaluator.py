from llm_client import call_llm

EVALUATOR_SYSTEM = EVALUATOR_SYSTEM = """你是基智，一个热情、博学的AI学习评估专家。

## 你的行为准则：
1. **先完整回答用户的问题**：无论用户问什么，都要先给出清晰、完整、有用的回答。
2. **再引导评估**：回答完后，评估用户的学习内容，给出具体建议。
3. **温和鼓励**：用温暖、积极的语气给出反馈。

记住：永远先回答问题，再引导评估。"""


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
    from llm_client import call_llm
    messages = [
        {"role": "system", "content": EVALUATOR_SYSTEM},
        *history,
        {"role": "user", "content": f"学习内容：{resource}\n用户水平：{user_profile.get('level')}\n用户问题：{user_input}"}
    ]
    return call_llm(messages)