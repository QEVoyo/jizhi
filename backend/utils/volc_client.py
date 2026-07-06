import requests
import json
from typing import List, Dict
from config import settings


class VolcClient:
    """火山引擎豆包API客户端"""

    def __init__(self):
        self.api_key = settings.ARK_API_KEY
        self.endpoint_id = settings.VOLC_ROLE_ENDPOINT_ID
        self.host = "ark.cn-beijing.volces.com"
        self.base_url = f"https://{self.host}/api/v3"

        print(f"=== API Key 前20位: {self.api_key[:20] if self.api_key else 'None'} ===")
        print(f"=== 接入点ID: {self.endpoint_id} ===")

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.8) -> str:
        """调用角色模型对话"""
        print("=== volc_client.chat 被调用 ===")
        print(f"=== 消息数量: {len(messages)} ===")

        url = f"{self.base_url}/chat/completions"

        body = {
            "model": self.endpoint_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 2048,
            "stream": False
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        try:
            print("=== 准备发送请求到火山API ===")
            resp = requests.post(url, headers=headers, json=body, timeout=30)
            print(f"=== 火山API状态: {resp.status_code} ===")
            print(f"=== 火山API返回: {resp.text[:500]} ===")

            if resp.status_code == 200:
                data = resp.json()
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
                else:
                    print(f"=== 返回格式异常: {data} ===")
                    return "小基今天有点累了，明天再聊吧~"
            elif resp.status_code == 401:
                print("=== 认证失败 ===")
                return "小基说：主人，API Key 好像不对哦，检查一下吧~"
            else:
                print(f"=== 请求失败: {resp.status_code} ===")
                return "小基今天有点累了，明天再聊吧~"
        except Exception as e:
            print(f"=== 调用火山API异常: {e} ===")
            return "嗯嗯，我在听！你继续说~"

    def chat_with_image(self, messages: List[Dict], temperature: float = 0.8) -> str:
        """图片理解对话"""
        print("=== volc_client.chat_with_image 被调用 ===")
        print(f"=== 消息数量: {len(messages)} ===")

        url = f"{self.base_url}/chat/completions"

        body = {
            "model": settings.VOLC_VISION_ENDPOINT_ID,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 2048,
            "stream": False
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        try:
            print("=== 准备发送图片理解请求 ===")
            resp = requests.post(url, headers=headers, json=body, timeout=30)
            print(f"=== 火山API状态: {resp.status_code} ===")
            print(f"=== 火山API返回: {resp.text[:500]} ===")

            if resp.status_code == 200:
                data = resp.json()
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
            return "图片理解失败了，再试一次吧~"
        except Exception as e:
            print(f"=== 图片理解异常: {e} ===")
            return "看不太清楚这张图呢~"