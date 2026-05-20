import json
import os
from typing import Dict, List


class UserMemory:
    """用户偏好记忆（长期）"""

    def __init__(self, user_id="default"):
        self.user_id = user_id
        self.memory_file = f"memory_{user_id}.json"
        self.data = self._load()

    def _load(self) -> Dict:
        if os.path.exists(self.memory_file):
            with open(self.memory_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "user_id": self.user_id,
            "session_count": 0,
            "preferences": {
                "difficulty": "intermediate",
                "style": "balanced",
                "length": "medium"
            },
            "feedback_history": [],
            "learned_topics": []
        }

    def _save(self):
        with open(self.memory_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def update_preference(self, key: str, value: str):
        if key in self.data["preferences"]:
            self.data["preferences"][key] = value
            self._save()

    def add_feedback(self, topic: str, rating: int, comment: str = ""):
        self.data["feedback_history"].insert(0, {
            "topic": topic,
            "rating": rating,
            "comment": comment
        })
        self.data["feedback_history"] = self.data["feedback_history"][:10]

        if rating < 5:
            if self.data["preferences"]["difficulty"] == "advanced":
                self.data["preferences"]["difficulty"] = "intermediate"
            elif self.data["preferences"]["difficulty"] == "intermediate":
                self.data["preferences"]["difficulty"] = "beginner"

        self.data["session_count"] += 1
        self._save()

    def add_learned_topic(self, topic: str):
        if topic not in self.data["learned_topics"]:
            self.data["learned_topics"].append(topic)
            self._save()

    def get_preference_prompt(self) -> str:
        diff_map = {"beginner": "初学者水平", "intermediate": "中等水平", "advanced": "高级水平"}
        style_map = {"example_heavy": "多举例", "theory_heavy": "多理论", "balanced": "均衡"}

        difficulty = self.data['preferences'].get('difficulty', 'intermediate')
        style = self.data['preferences'].get('style', 'balanced')

        return f"""
【用户偏好】
- 难度：{diff_map.get(difficulty, '中等水平')}
- 风格：{style_map.get(style, '均衡')}
"""

    def clear(self):
        if os.path.exists(self.memory_file):
            os.remove(self.memory_file)
        self.data = self._load()