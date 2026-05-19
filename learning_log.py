import json
import os
from datetime import datetime


class LearningLogManager:
    def __init__(self, user_id="student_001"):
        self.user_id = user_id
        self.file_path = f"learning_log_{user_id}.json"
        self.data = self._load()

    def _load(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"logs": []}

    def _save(self):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def add_log(self, keyword: str, date: str = None):
        """添加一条学习日志"""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        # 检查同一天是否已有相同关键词（可选：去重）
        # 这里不去重，保留多条记录
        self.data["logs"].append({
            "id": f"log_{int(datetime.now().timestamp())}",
            "keyword": keyword[:50],
            "date": date,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        self._save()
        return True

    def get_logs_grouped_by_date(self):
        """按日期分组获取学习日志"""
        grouped = {}
        for log in self.data["logs"]:
            date = log["date"]
            if date not in grouped:
                grouped[date] = []
            grouped[date].append(log)

        # 按日期倒序排序
        sorted_dates = sorted(grouped.keys(), reverse=True)
        return {date: grouped[date] for date in sorted_dates}

    def delete_log(self, log_id):
        """删除单条日志"""
        self.data["logs"] = [l for l in self.data["logs"] if l["id"] != log_id]
        self._save()
        return True

    def clear_all(self):
        """清空所有日志"""
        self.data["logs"] = []
        self._save()

    def get_recent_logs(self, limit=30):
        """获取最近N条日志"""
        return self.data["logs"][-limit:][::-1]

    def count_by_date(self, date):
        """统计某天的学习条目数"""
        return len([l for l in self.data["logs"] if l["date"] == date])