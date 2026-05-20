import json
import os


class Conversation:
    """管理对话历史，保持上下文"""

    def __init__(self, user_id="default"):
        self.user_id = user_id
        self.history_file = f"conversation_{user_id}.json"
        self.messages = self._load()

    def _load(self):
        if os.path.exists(self.history_file):
            with open(self.history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _save(self):
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(self.messages, f, ensure_ascii=False, indent=2)

    def add_user_message(self, content):
        self.messages.append({"role": "user", "content": content})
        self._save()

    def add_assistant_message(self, content):
        self.messages.append({"role": "assistant", "content": content})
        self._save()

    def get_context(self, max_history=10):
        """获取最近N条对话作为上下文"""
        return self.messages[-max_history:]

    def get_last_assistant_message(self):
        """获取最后一轮助手的回复"""
        for msg in reversed(self.messages):
            if msg["role"] == "assistant":
                return msg["content"]
        return None

    def clear(self):
        self.messages = []
        self._save()