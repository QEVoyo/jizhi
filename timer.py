import json
import os
from datetime import datetime


class TimerManager:
    def __init__(self, user_id="student_001"):
        self.user_id = user_id
        self.file_path = f"timer_{user_id}.json"
        self.data = self._load()

    def _load(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"timers": []}

    def _save(self):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def add_timer(self, name, timer_type, duration_minutes=0):
        timer = {
            "id": f"timer_{int(datetime.now().timestamp())}",
            "name": name[:50],
            "type": timer_type,  # 'countdown' 或 'stopwatch'
            "duration_minutes": duration_minutes,
            "created_at": datetime.now().strftime("%Y-%m-%d")
        }
        self.data["timers"].append(timer)
        self._save()
        return True

    def delete_timer(self, timer_id):
        self.data["timers"] = [t for t in self.data["timers"] if t["id"] != timer_id]
        self._save()
        return True

    def get_timers(self):
        timers = self.data.get("timers", [])
        for t in timers:
            # 兼容旧数据
            if "type" not in t:
                t["type"] = "countdown"
            if "duration_minutes" not in t:
                t["duration_minutes"] = 0
        return timers