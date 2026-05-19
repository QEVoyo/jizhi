import json
import os
from datetime import datetime


class CountdownManager:
    def __init__(self, user_id="student_001"):
        self.user_id = user_id
        self.file_path = f"countdown_{user_id}.json"
        self.data = self._load()

    def _load(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"events": []}

    def _save(self):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def add_event(self, name, target_date):
        """添加倒计时事件"""
        self.data["events"].append({
            "id": f"cd_{int(datetime.now().timestamp())}",
            "name": name[:50],
            "target_date": target_date,  # 格式: YYYY-MM-DD
            "created_at": datetime.now().strftime("%Y-%m-%d")
        })
        self._save()
        return True

    def delete_event(self, event_id):
        self.data["events"] = [e for e in self.data["events"] if e["id"] != event_id]
        self._save()
        return True

    def get_events(self):
        """返回按日期排序的事件列表"""
        events = self.data["events"]
        # 按目标日期排序
        events.sort(key=lambda x: x["target_date"])
        return events

    def get_days_remaining(self, target_date):
        """计算剩余天数"""
        today = datetime.now().strftime("%Y-%m-%d")
        delta = datetime.strptime(target_date, "%Y-%m-%d") - datetime.strptime(today, "%Y-%m-%d")
        return delta.days