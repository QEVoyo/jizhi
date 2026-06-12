from utils.llm_client import call_llm


def generate_mistake_title(ai_response: str, user_question: str = "") -> str:
    """从AI回复中提取核心知识点作为错题标题"""
    try:
        prompt = f"""请从以下AI回复内容中提取核心知识点，作为错题本的标题。
要求：
- 标题长度不超过15字
- 提取最关键的知识点名称
- 如果内容涉及多个知识点，取最重要的一个
- 只输出标题，不要有其他内容

AI回复内容：
{ai_response[:500]}

标题："""

        title = call_llm([{"role": "user", "content": prompt}], temperature=0.3)
        title = title.strip().replace('"', '').replace('"', '')

        if len(title) > 20:
            title = title[:20]

        if not title or len(title) < 2:
            # 备用：用用户问题的前20字
            title = user_question[:20] if user_question else "错题"

        return title
    except Exception as e:
        print(f"生成标题失败: {e}")
        return user_question[:20] if user_question else "错题"