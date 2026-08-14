import requests
import json
from typing import List, Dict
from config import settings
from logging_config import logger


class VolcClient:
    """火山引擎豆包API客户端（支持流式）"""

    def __init__(self):
        self.api_key = settings.ARK_API_KEY
        self.endpoint_id = settings.VOLC_ROLE_ENDPOINT_ID
        self.host = "ark.cn-beijing.volces.com"
        self.base_url = f"https://{self.host}/api/v3"

        logger.info(f"=== API Key 前20位: {self.api_key[:20] if self.api_key else 'None'} ===")
        logger.info(f"=== 接入点ID: {self.endpoint_id} ===")

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.8) -> str:
        """调用角色模型对话（非流式）"""
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
            resp = requests.post(url, headers=headers, json=body, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
                return "小基今天有点累了，明天再聊吧~"
            return "小基今天有点累了，明天再聊吧~"
        except Exception as e:
            logger.info(f"=== 调用火山API异常: {e} ===")
            return "嗯嗯，我在听！你继续说~"

    def vision_stream(self, image_url: str, prompt: str = "请描述这张图片的内容"):
        """
        豆包多模态图片理解 - 真流式输出
        """
        vision_endpoint = settings.VOLC_VISION_ENDPOINT_ID

        url = f"{self.base_url}/chat/completions"
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ]
        body = {
            "model": vision_endpoint,
            "messages": messages,
            "temperature": 0.8,
            "max_tokens": 2048,
            "stream": True  # 👈 开启真流式
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        try:
            response = requests.post(url, headers=headers, json=body, stream=True, timeout=30)
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith("data:") and line != "data: [DONE]":
                        try:
                            data = json.loads(line[5:])
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except:
                            continue
        except Exception as e:
            yield f"图片理解出错: {str(e)}"