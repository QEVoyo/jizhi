import requests
import json

BASE_URL = "http://localhost:8000"

# 替换成你的真实 user_id
USER_ID = "dd35a8f3-c94d-41ec-8d2c-61fb4e442044"


def test_record(action_type):
    """测试单个埋点"""
    try:
        resp = requests.post(
            f"{BASE_URL}/career/actions/record",
            json={"user_id": USER_ID, "action_type": action_type, "metadata": {}},
            timeout=5
        )
        if resp.status_code == 200 and resp.json().get("success"):
            return "✅"
        else:
            return f"❌ {resp.status_code}"
    except Exception as e:
        return f"❌ {str(e)[:30]}"


def test_stats():
    """获取行为统计"""
    try:
        resp = requests.get(f"{BASE_URL}/career/actions/stats/{USER_ID}", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            print("\n📊 行为统计:")
            print(f"  总记录数: {data.get('total', 0)}")
            print("  各类型数量:")
            for k, v in data.get('stats', {}).items():
                if not k.endswith("_today"):
                    print(f"    {k}: {v}")
            return data
        else:
            print(f"❌ 获取统计失败: {resp.status_code}")
            return None
    except Exception as e:
        print(f"❌ 异常: {e}")
        return None


def test_task_progress():
    """获取任务进度"""
    try:
        resp = requests.get(f"{BASE_URL}/career/task-progress/{USER_ID}", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            print("\n📋 任务进度:")
            seed_count = len(data.get("seed", []))
            daily_count = len(data.get("daily", []))
            long_count = len(data.get("long", []))
            ach_count = len(data.get("achievements", []))
            print(f"  播种任务: {seed_count} 个")
            print(f"  每日任务: {daily_count} 个")
            print(f"  发芽任务: {long_count} 个")
            print(f"  成就: {ach_count} 个")

            # 显示已完成数量
            done_seed = len([t for t in data.get("seed", []) if t.get("done")])
            done_ach = len([a for a in data.get("achievements", []) if a.get("done")])
            print(f"  已完成的播种: {done_seed}/{seed_count}")
            print(f"  已解锁的成就: {done_ach}/{ach_count}")
            return data
        else:
            print(f"❌ 获取任务进度失败: {resp.status_code}")
            return None
    except Exception as e:
        print(f"❌ 异常: {e}")
        return None


if __name__ == "__main__":
    print("=" * 50)
    print("📊 综合测试")
    print("=" * 50)

    # 1. 测试所有埋点
    print("\n📝 测试埋点:")
    action_types = [
        "login", "chat", "use_plan_agent", "use_generate_agent", "use_evaluate_agent",
        "view_career", "view_report", "update_nickname", "update_avatar", "update_bio",
        "generate_question", "create_set", "add_to_set", "complete_question",
        "conquer_mistake", "checkin", "use_timer"
    ]

    for action_type in action_types:
        result = test_record(action_type)
        print(f"  {result} {action_type}")

    # 2. 获取统计
    test_stats()

    # 3. 获取任务进度
    test_task_progress()

    print("\n" + "=" * 50)
    print("✅ 测试完成")