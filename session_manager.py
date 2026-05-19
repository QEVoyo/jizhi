import json
import os
import time
from datetime import datetime


class SessionManager:
    def __init__(self, user_id="student_001"):
        self.user_id = user_id
        self.file_path = f"sessions_{user_id}.json"
        self.data = self._load()

    def _load(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "current_session_id": None,
            "sessions": []
        }

    def _save(self):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def create_session(self, title="新对话"):
        session_id = f"session_{int(time.time())}"
        new_session = {
            "id": session_id,
            "title": title,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "messages": []
        }
        # 确保 sessions 是列表
        if not isinstance(self.data.get("sessions"), list):
            self.data["sessions"] = []
        self.data["sessions"].insert(0, new_session)
        self.data["current_session_id"] = session_id
        self._save()
        return session_id

    def get_current_session(self):
        current_id = self.data.get("current_session_id")
        if not current_id:
            return None
        sessions = self.data.get("sessions", [])
        for s in sessions:
            if s.get("id") == current_id:
                return s
        return None

    def switch_session(self, session_id):
        sessions = self.data.get("sessions", [])
        for s in sessions:
            if s.get("id") == session_id:
                self.data["current_session_id"] = session_id
                self._save()
                return True
        return False

    def add_message(self, role, content):
        session = self.get_current_session()
        if session:
            if "messages" not in session:
                session["messages"] = []
            session["messages"].append({
                "role": role,
                "content": content,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            self._save()

    def get_messages(self):
        session = self.get_current_session()
        if session:
            return session.get("messages", [])
        return []

    def update_title(self, session_id, new_title):
        sessions = self.data.get("sessions", [])
        for s in sessions:
            if s.get("id") == session_id:
                s["title"] = new_title[:30]
                self._save()
                return True
        return False

    def get_all_sessions(self):
        return self.data.get("sessions", [])

    def clear_current_messages(self):
        session = self.get_current_session()
        if session:
            session["messages"] = []
            self._save()