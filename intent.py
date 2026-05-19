from utils.llm_client import call_llm

INTENT_SYSTEM = """判断用户意图，只输出以下标签之一：
- plan: 用户想规划学习路径、问学什么、有哪些知识点、怎么安排学习顺序
- generate: 用户想学习知识、解释概念、举例、讲解、出题、测试、检测水平、总结、归纳、梳理、回顾、复习
- evaluate: 用户想评价已经生成的内容质量、问刚才的回答对不对、要求对已有内容打分
- chat: 普通问候、闲聊、与学习无关

注意：只要用户想学习新知识或总结内容，都是 generate。只有评价已经存在的内容才是 evaluate。

输出只能是一个单词，不要有其他内容。"""

def detect_intent(user_input: str) -> str:
    try:
        response = call_llm([
            {"role": "system", "content": INTENT_SYSTEM},
            {"role": "user", "content": user_input}
        ], temperature=0.1)
        intent = response.strip().lower()
        if intent not in ["plan", "generate", "evaluate", "chat"]:
            return "chat"
        return intent
    except Exception as e:
        print(f"意图识别失败: {e}")
        return "chat"