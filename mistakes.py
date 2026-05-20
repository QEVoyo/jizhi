import json
import os
from datetime import datetime


class MistakeManager:
    def __init__(self, user_id="student_001"):
        self.user_id = user_id
        self.file_path = f"mistakes_{user_id}.json"
        self.data = self._load()

    def _load(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"mistakes": []}

    def _save(self):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def add_mistake(self, question, user_answer="", correct_answer="", conversation_snapshot=None, title=""):
        mistake = {
            "id": f"mistake_{int(datetime.now().timestamp())}",
            "title": title[:50] if title else question[:50],
            "question": question[:500],
            "user_answer": user_answer[:200],
            "correct_answer": correct_answer[:500],
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "learning",
            "conversation_snapshot": conversation_snapshot
        }
        self.data["mistakes"].insert(0, mistake)
        self._save()
        return True

    def mark_conquered(self, mistake_id):
        for m in self.data["mistakes"]:
            if m["id"] == mistake_id:
                m["status"] = "conquered"
                self._save()
                return True
        return False

    def delete_mistake(self, mistake_id):
        self.data["mistakes"] = [m for m in self.data["mistakes"] if m["id"] != mistake_id]
        self._save()
        return True

    def get_learning_mistakes(self):
        return [m for m in self.data["mistakes"] if m["status"] == "learning"]

    def get_conquered_mistakes(self):
        return [m for m in self.data["mistakes"] if m["status"] == "conquered"]

    def get_all_mistakes(self):
        return self.data["mistakes"]

    def count_by_status(self):
        learning = len(self.get_learning_mistakes())
        conquered = len(self.get_conquered_mistakes())
        return learning, conquered