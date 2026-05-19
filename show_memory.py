from memory import UserMemory

user_memory = UserMemory("student_001")
summary = user_memory.get_summary()

print("\n📊 用户学习档案")
print("="*40)
for key, value in summary.items():
    print(f"{key}: {value}")
print("="*40)

# 显示最近3条反馈
print("\n📝 最近反馈记录：")
for f in user_memory.memory["feedback_history"][:3]:
    print(f"  - {f['topic']} / {f['subtopic']}：{f['score']}分 " + (f"（{f['comment']}）" if f['comment'] else ""))