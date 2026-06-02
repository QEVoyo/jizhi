from utils.llm_client import call_llm

GENERATOR_SYSTEM = """你是个性化学习资源生成专家。根据知识点和用户水平，生成讲解+例子+练习。
输出纯文字，自然流畅，不要输出JSON格式。"""


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
    from utils.llm_client import call_llm
    messages = [
        {"role": "system", "content": GENERATOR_SYSTEM + memory_context},
        *history,
        {"role": "user", "content": user_input}
    ]
    return call_llm(messages)