from .llm_client import call_llm_stream

EVALUATOR_SYSTEM = """你是基智，一个热情、博学的AI学习评估专家。

## 你的行为准则：
1. **先完整回答用户的问题**：无论用户问什么，都要先给出清晰、完整、有用的回答。
2. **再引导评估**：回答完后，评估用户的学习内容，给出具体建议。
3. **温和鼓励**：用温暖、积极的语气给出反馈。

记住：永远先回答问题，再引导评估。"""


def evaluate_with_history_stream(resource, user_profile, user_input, history):
    """流式评估"""
    messages = [
        {"role": "system", "content": EVALUATOR_SYSTEM},
        *history,
        {"role": "user", "content": f"学习内容：{resource}\n用户水平：{user_profile.get('level', '中等')}\n用户问题：{user_input}"}
    ]
    return call_llm_stream(messages, temperature=0.5)