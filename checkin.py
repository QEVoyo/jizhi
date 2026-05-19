import json
import os
from datetime import datetime


class CheckInManager:
    def __init__(self, user_id="student_001"):
        self.user_id = user_id
        self.file_path = f"checkin_{user_id}.json"
        self.data = self._load()

    def _load(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"projects": []}

    def _save(self):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def add_project(self, name, target_days):
        """添加打卡项目"""
        if len(self.data["projects"]) >= 10:
            return False, "打卡项目已达上限（10个）"
        for p in self.data["projects"]:
            if p["name"] == name:
                return False, "项目名称已存在"
        self.data["projects"].append({
            "name": name,
            "target_days": target_days,
            "completed_days": 0,
            "last_checkin": None
        })
        self._save()
        return True, "添加成功"

    def checkin(self, project_name):
        """每日打卡"""
        for p in self.data["projects"]:
            if p["name"] == project_name:
                today = datetime.now().strftime("%Y-%m-%d")
                if p["last_checkin"] == today:
                    return False, "今天已经打卡过了"
                p["completed_days"] += 1
                p["last_checkin"] = today
                self._save()
                return True, f"打卡成功！已完成 {p['completed_days']}/{p['target_days']} 天"
        return False, "项目不存在"

    def delete_project(self, project_name):
        """删除打卡项目"""
        for i, p in enumerate(self.data["projects"]):
            if p["name"] == project_name:
                self.data["projects"].pop(i)
                self._save()
                return True, "删除成功"
        return False, "项目不存在"

    def get_projects(self):
        return self.data["projects"]