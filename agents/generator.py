from llm_client import call_llm

GENERATOR_SYSTEM = """你是基智，一个热情、博学的AI学习助手。

## 你的行为准则：
1. **先完整回答用户的问题**：无论用户问什么，都要先给出清晰、完整、有用的回答。
2. **再引导学习**：回答完后，自然地引导到学习方向，推荐相关知识点或思考题。
3. **根据用户水平调整**：如果用户是初学者，用简单语言；如果用户是进阶者，可以深入一些。

记住：永远先回答问题，再引导学习。"""


def generate(knowledge_point, user_profile, memory_hint=""):
    prompt = f"""知识点：{knowledge_point}
用户水平：{user_profile.get('level', '中等')}
风格偏好：{user_profile.get('style', '喜欢例子')}
{memory_hint}

请生成适合的学习内容（讲解+例子+练习）。"""

    response = call_llm([
        {"role": "system", "content": GENERATOR_SYSTEM},
        {"role": "user", "content": prompt}
    ])
    return response


def generate_with_history(user_input, user_profile, memory_context, history):
    from llm_client import call_llm
    messages = [
        {"role": "system", "content": """你是基智，一个热情、博学的AI学习助手。

## 你的行为准则：
1. **先完整回答用户的问题**：无论用户问什么，都要先给出清晰、完整、有用的回答。
2. **再引导学习**：回答完后，自然地引导到学习方向，推荐相关知识点或思考题。
3. **根据用户水平调整**：如果用户是初学者，用简单语言；如果用户是进阶者，可以深入一些。

记住：永远先回答问题，再引导学习。"""},
        *history,
        {"role": "user", "content": user_input}  # 改成 user_input
    ]
    return call_llm(messages)