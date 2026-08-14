import requests
import json
import base64
import hashlib
import hmac
import time
from datetime import datetime
from typing import Optional
from config import settings
from logging_config import logger


class XunfeiClient:
    """科大讯飞语音服务客户端（TTS + ASR）"""

    def __init__(self):
        self.appid = settings.XUNFEI_APPID
        self.api_key = settings.XUNFEI_API_KEY
        self.api_secret = settings.XUNFEI_API_SECRET

        # 语音合成（TTS）
        self.tts_url = "https://api.xfyun.cn/v1/service/v1/tts"

        # 语音识别（ASR）- 使用流式听写
        self.asr_url = "https://api.xfyun.cn/v1/service/v1/ise"

        # 通用：语音听写（实时）
        self.iat_url = "https://api.xfyun.cn/v1/service/v1/iat"

    def get_tts_audio(self, text: str, speed: int = 5, volume: int = 5, pitch: int = 5, voice_name: str = "xiaoyan") -> bytes:
        """
        语音合成（TTS）- 文字转语音
        :param text: 要合成的文本（最多 1000 字符）
        :param speed: 语速 1-9，默认 5
        :param volume: 音量 1-9，默认 5
        :param pitch: 音调 1-9，默认 5
        :param voice_name: 音色名称（xiaoyan, xiaofeng, xiaokun, xiaorui, xiaomei 等）
        :return: 音频二进制数据（MP3 格式）
        """
        if not text:
            return None

        if len(text) > 1000:
            text = text[:1000]

        body = {
            "common": {
                "app_id": self.appid
            },
            "business": {
                "aue": "wav",           # 音频编码格式：raw 为 PCM
                "sfl": 1,               # 采样率：1=16k
                "auf": "audio/L16;rate=16000",  # 音频格式
                "speed": speed,
                "volume": volume,
                "pitch": pitch,
                "vcn": voice_name       # 发音人
            },
            "data": {
                "text": base64.b64encode(text.encode("utf-8")).decode("utf-8")
            }
        }

        headers = self._build_headers(self.tts_url, body)

        try:
            resp = requests.post(self.tts_url, headers=headers, json=body, timeout=10)
            if resp.status_code == 200:
                return resp.content
            else:
                logger.info(f"TTS 错误: {resp.status_code} {resp.text}")
                return None
        except Exception as e:
            logger.info(f"TTS 异常: {e}")
            return None

    def speech_to_text(self, audio_data: bytes, format: str = "wav") -> Optional[str]:
        """语音识别（ASR）- 语音转文字"""
        import base64
        import requests
        import json

        try:
            # 如果是 webm 格式，先尝试用 wav 方式处理
            # 讯飞 web API 支持 wav 格式
            body = {
                "common": {"app_id": self.appid},
                "business": {
                    "domain": "iat",
                    "language": "zh_cn",
                    "accent": "mandarin",
                    "ptt": 0,
                    "dwa": "wpgs"
                },
                "data": {
                    "audio": base64.b64encode(audio_data).decode("utf-8"),
                    "encoding": "raw",
                    "status": 2
                }
            }

            # 如果是 webm 格式，尝试改用 wav 编码
            if format == "webm":
                body["data"]["encoding"] = "wav"

            headers = self._build_headers(self.iat_url, body)
            resp = requests.post(self.iat_url, headers=headers, json=body, timeout=15)

            if resp.status_code == 200:
                result = resp.json()
                if result.get("code") == 0 and "data" in result:
                    data = json.loads(result["data"])
                    return data.get("result", {}).get("text", "").strip()
                else:
                    logger.info(f"ASR 错误: {result.get('message', '未知错误')}")
                    return None
            else:
                logger.info(f"ASR HTTP 错误: {resp.status_code} {resp.text}")
                return None

        except Exception as e:
            logger.info(f"ASR 异常: {e}")
            return None

    def _build_headers(self, url: str, body: dict) -> dict:
        """构建讯飞 API 请求头（含签名）"""
        import datetime as dt

        now = dt.datetime.utcnow()
        date = now.strftime("%a, %d %b %Y %H:%M:%S GMT")

        # 构建签名字符串
        signature_origin = f"host: api.xfyun.cn\ndate: {date}\nPOST /v1/service/v1/tts HTTP/1.1"
        signature_sha = hmac.new(
            self.api_secret.encode("utf-8"),
            signature_origin.encode("utf-8"),
            hashlib.sha256
        ).digest()
        signature = base64.b64encode(signature_sha).decode("utf-8")
        authorization = f'api_key="{self.api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature}"'

        return {
            "Content-Type": "application/json",
            "Accept": "audio/*",
            "Host": "api.xfyun.cn",
            "Date": date,
            "Authorization": authorization
        }

    def get_available_voices(self) -> list:
        """
        获取可用音色列表
        讯飞官方音色：
        - xiaoyan: 标准女声
        - xiaofeng: 标准男声
        - xiaokun: 童声
        - xiaorui: 温柔女声
        - xiaomei: 甜美女声
        - xiaoxuan: 知性女声
        - xiaoyu: 年轻男声
        - xiaomeng: 活力女声
        """
        return [
            {"value": "xiaoyan", "label": "标准女声"},
            {"value": "xiaofeng", "label": "标准男声"},
            {"value": "xiaokun", "label": "童声"},
            {"value": "xiaorui", "label": "温柔女声"},
            {"value": "xiaomei", "label": "甜美女声"},
            {"value": "xiaoxuan", "label": "知性女声"},
            {"value": "xiaoyu", "label": "年轻男声"},
            {"value": "xiaomeng", "label": "活力女声"},
        ]