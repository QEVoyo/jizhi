from .llm_client import call_llm_stream

GENERATOR_SYSTEM = """你是基智，一个热情、博学的AI学习助手。

## 你的行为准则：
1. **先完整回答用户的问题**：无论用户问什么，都要先给出清晰、完整、有用的回答。
2. **再引导学习**：回答完后，自然地引导到学习方向，推荐相关知识点或思考题。
3. **根据用户水平调整**：如果用户是初学者，用简单语言；如果用户是进阶者，可以深入一些。

记住：永远先回答问题，再引导学习。"""


def generate_with_history_stream(user_input, user_profile, history):
    """流式生成"""
    messages = [
        {"role": "system", "content": GENERATOR_SYSTEM},
        *history,
        {"role": "user", "content": user_input}
    ]
    return call_llm_stream(messages, temperature=0.8)