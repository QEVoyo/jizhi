from agents.planner import plan
from agents.generator import generate
from agents.evaluator import evaluate
from memory import UserMemory
from conversation import Conversation
from intent import detect_intent
from utils.llm_client import call_llm
import json

user_memory = UserMemory(user_id="student_001")
conversation = Conversation(user_id="student_001")

SYSTEM_PROMPT = """你是一个智能学习助手。保持友好、有耐心。"""

pref_prompt = user_memory.get_preference_prompt()

print("=" * 60)
print("🤖 智能学习助手（多智能体协作）")
print("=" * 60)
print("\n你可以问我任何学习问题")
print("输入 'quit' 退出，'feedback' 给评分")
print("=" * 60)

while True:
    user_input = input("\n你：").strip()

    if user_input.lower() == 'quit':
        print("👋 再见！")
        break

    if user_input.lower() == 'feedback':
        try:
            rating = int(input("请给本次学习打分（1-10分）：").strip())
            comment = input("有什么建议吗？：").strip()
            user_memory.add_feedback("general", rating, comment)
            print("✅ 感谢反馈！")
        except:
            print("输入无效")
        continue

    if user_input.lower() == 'clear':
        conversation.clear()
        print("✅ 对话历史已清空")
        continue

    # 1. 判断意图
    print("\n🔍 分析意图...")
    intent = detect_intent(user_input)
    print(f"   意图：{intent}")

    conversation.add_user_message(user_input)

    # 2. 根据意图调用不同Agent
    if intent == "plan":
        print("📋 调用规划Agent...")
        user = {"level": user_memory.data['preferences']['difficulty'], "style": "喜欢例子"}
        try:
            result = plan(user, user_input)
            print(f"\n📚 规划结果：\n{result}")
        except Exception as e:
            print(f"规划失败：{e}")
            result = "规划失败，请重试"

    elif intent == "generate":
        print("📖 调用生成Agent...")
        user = {"level": user_memory.data['preferences']['difficulty'], "style": "喜欢例子"}
        memory_context = user_memory.get_preference_prompt()
        try:
            result = generate(user_input, user, memory_context)
            print(f"\n✨ 生成结果：\n{result}")
        except Exception as e:
            print(f"生成失败：{e}")
            result = "生成失败，请重试"

    elif intent == "evaluate":
        print("🔍 调用评估Agent...")
        # 获取上一轮对话内容作为评估对象
        history = conversation.get_context(max_history=2)
        last_assistant = ""
        for msg in reversed(history):
            if msg["role"] == "assistant":
                last_assistant = msg["content"]
                break
        if not last_assistant:
            result = "没有可评估的内容，请先生成一些学习内容"
        else:
            user = {"level": user_memory.data['preferences']['difficulty']}
            try:
                eval_result = evaluate(last_assistant, user, user_input)
                print(f"\n✅ 评估结果：\n{eval_result}")
                result = eval_result
            except Exception as e:
                print(f"评估失败：{e}")
                result = "评估失败，请重试"

    else:  # chat
        print("💬 普通对话模式...")
        history = conversation.get_context(max_history=10)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT + pref_prompt},
            *history
        ]
        result = call_llm(messages, temperature=0.7)
        print(f"\n🤖 助手：{result}")

    conversation.add_assistant_message(result)