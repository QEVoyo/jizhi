import json
import base64
import hashlib
import hmac
import wave
import io
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import quote

from config import settings
from logging_config import logger


def _ws_module():
    """websocket-client 是可选依赖（只有讯飞 TTS / ASR 用它）。

    延迟导入：缺这个包时语音合成与语音听写不可用，但不该拖垮整个服务启动。
    返回 None 表示未安装。
    """
    try:
        import websocket
        return websocket
    except ImportError:
        return None


class XunfeiClient:
    """科大讯飞语音服务客户端（TTS + ASR，WebSocket v2 协议）

    2026-08-24 重写：老版 HTTP 接口（api.xfyun.cn/v1/service/v1/*）已被讯飞网关弃用
    （实测返回 10105/10106/10107 系列错误），改为官方现行 WebSocket v2：
      - 语音合成：wss://tts-api.xfyun.cn/v2/tts
      - 语音听写：wss://iat-api.xfyun.cn/v2/iat
    鉴权：hmac-sha256 签名（host + date + GET request-line）经 URL query 传递。
    """

    TTS_HOST = "tts-api.xfyun.cn"
    IAT_HOST = "iat-api.xfyun.cn"

    def __init__(self):
        self.appid = settings.XUNFEI_APPID
        self.api_key = settings.XUNFEI_API_KEY
        self.api_secret = settings.XUNFEI_API_SECRET

    # ============================================================
    # 鉴权
    # ============================================================

    @staticmethod
    def _gmt_date() -> str:
        return datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

    def _ws_url(self, host: str, path: str) -> str:
        """构建带鉴权参数的 WebSocket URL（v2 协议）"""
        date = self._gmt_date()
        signature_origin = f"host: {host}\ndate: {date}\nGET {path} HTTP/1.1"
        signature = base64.b64encode(
            hmac.new(self.api_secret.encode("utf-8"), signature_origin.encode("utf-8"), hashlib.sha256).digest()
        ).decode("utf-8")
        # authorization 必须是字符串形式（与 HTTP 头一致）再 base64，不是 JSON
        authorization_origin = (
            f'api_key="{self.api_key}", algorithm="hmac-sha256", '
            f'headers="host date request-line", signature="{signature}"'
        )
        authorization = base64.b64encode(authorization_origin.encode("utf-8")).decode("utf-8")
        return f"wss://{host}{path}?authorization={quote(authorization)}&date={quote(date)}&host={host}"

    # ============================================================
    # 语音合成（TTS）→ 返回 mp3 音频字节
    # ============================================================

    def get_tts_audio(self, text: str, speed: int = 5, volume: int = 5, pitch: int = 5, voice_name: str = "xiaoyan") -> Optional[bytes]:
        """
        语音合成（TTS）- 文字转语音
        :param text: 要合成的文本（自动分帧，单帧过长会拆开）
        :param speed: 语速 1-9（内部映射到讯飞 0-100）
        :param volume: 音量 1-9
        :param pitch: 音调 1-9
        :param voice_name: 音色名称（xiaoyan/xiaofeng/xiaoyu 等）
        :return: 音频二进制数据（mp3），失败返回 None
        """
        if not text:
            return None
        text = text.strip()[:1000]

        def scale(v: int) -> int:
            """1-9 → 0-100（讯飞取值区间）"""
            try:
                return max(0, min(100, round(int(v) / 9 * 100)))
            except (TypeError, ValueError):
                return 50

        business = {
            "aue": "lame",              # 输出 mp3
            "sfl": 1,
            "auf": "audio/L16;rate=16000",
            "vcn": voice_name or "xiaoyan",
            "speed": scale(speed),
            "volume": scale(volume),
            "pitch": scale(pitch),
            "tte": "UTF8",
        }

        websocket = _ws_module()
        if websocket is None:
            logger.info("[讯飞TTS] 未安装 websocket-client，该功能不可用（pip install websocket-client）")
            return None

        ws = None
        audio_parts = []
        try:
            # 握手偶发超时（网络抖动），重试一次
            try:
                ws = websocket.create_connection(self._ws_url(self.TTS_HOST, "/v2/tts"), timeout=10)
            except Exception:
                ws = websocket.create_connection(self._ws_url(self.TTS_HOST, "/v2/tts"), timeout=10)

            # 文本分帧：短文本单帧 status=2；长文本首帧 status=0、中间 1、末帧 2
            chunks = [text[i:i + 500] for i in range(0, len(text), 500)] or [text]
            for i, chunk in enumerate(chunks):
                status = 2 if len(chunks) == 1 else (0 if i == 0 else (2 if i == len(chunks) - 1 else 1))
                frame = {
                    "data": {
                        "status": status,
                        "text": base64.b64encode(chunk.encode("utf-8")).decode("utf-8"),
                    }
                }
                if i == 0:
                    frame["common"] = {"app_id": self.appid}
                    frame["business"] = business
                ws.send(json.dumps(frame))

            # 接收音频帧：TEXT 帧为控制信息（code/sid/audio base64/status），BINARY 帧为裸音频
            ws.settimeout(2)
            done = False
            while not done:
                try:
                    msg = ws.recv()
                except websocket.WebSocketTimeoutException:
                    break  # 静默 2s 视为合成结束
                if isinstance(msg, bytes):
                    # 二进制音频帧：可能带 "AU"+音频类型(1字节) 前缀
                    if msg[:2] == b"AU":
                        audio_parts.append(msg[3:])
                    else:
                        idx = msg.find(b"AU")
                        if idx != -1 and len(msg) > idx + 3:
                            audio_parts.append(msg[idx + 3:])
                        else:
                            audio_parts.append(msg)
                else:
                    try:
                        ctrl = json.loads(msg)
                    except (ValueError, TypeError):
                        continue
                    if ctrl.get("code") not in (0, None):
                        logger.info(f"TTS 错误: {ctrl.get('code')} {ctrl.get('message')}")
                        return None
                    data = ctrl.get("data") or {}
                    if data.get("audio"):
                        audio_parts.append(base64.b64decode(data["audio"]))
                    if data.get("status") == 2:
                        done = True
            ws.close()
            ws = None

            audio = b"".join(audio_parts)
            if not audio:
                logger.info("TTS 错误: 未收到音频数据")
                return None
            return audio
        except Exception as e:
            logger.info(f"TTS 异常: {e}")
            return None
        finally:
            if ws is not None:
                try:
                    ws.close()
                except Exception:
                    pass

    # ============================================================
    # 语音识别（ASR）→ 返回识别文本
    # ============================================================

    def speech_to_text(self, audio_data: bytes, format: str = "wav") -> Optional[str]:
        """
        语音转文字（ASR，讯飞语音听写 iat v2）
        :param audio_data: 音频字节。wav（RIFF 容器，任意采样率自动转 16k）或 raw（16k 16bit 单声道 PCM）
        :param format: "wav" 或 "raw"
        :return: 识别文本，失败返回 None
        """
        if not audio_data:
            return None

        pcm = self._to_pcm16k(audio_data, format)
        if not pcm:
            return None

        websocket = _ws_module()
        if websocket is None:
            logger.info("[讯飞ASR] 未安装 websocket-client，该功能不可用（pip install websocket-client）")
            return None

        business = {
            "domain": "iat",
            "language": "zh_cn",
            "accent": "mandarin",
            "dwa": "wpgs",      # 动态修正
            "ptt": 0,
            "aue": "raw",
            "vad_eos": 2000,
        }

        ws = None
        final_text = ""
        try:
            ws = websocket.create_connection(self._ws_url(self.IAT_HOST, "/v2/iat"), timeout=10)
            ws.send(json.dumps({
                "common": {"app_id": self.appid},
                "business": business,
                "data": {"status": 0, "format": "audio/L16;rate=16000", "encoding": "raw", "audio": ""},
            }))

            # 音频按 1280 字节（40ms）分帧发送，最后一帧 status=2
            FRAME = 1280
            total = len(pcm)
            sent = 0
            while sent < total:
                chunk = pcm[sent:sent + FRAME]
                sent += len(chunk)
                status = 2 if sent >= total else 0
                ws.send(json.dumps({
                    "data": {
                        "status": status,
                        "format": "audio/L16;rate=16000",
                        "encoding": "raw",
                        "audio": base64.b64encode(chunk).decode("utf-8"),
                    }
                }))
                # 按官方节奏 40ms 一帧，避免缓冲溢出/vad 提前断句
                import time
                time.sleep(0.04)

            # 接收识别结果：rpl 帧渐进更新（最后一个 rpl 是完整文本），data.status=2 收尾
            ws.settimeout(10)
            while True:
                try:
                    msg = ws.recv()
                except websocket.WebSocketTimeoutException:
                    break
                if isinstance(msg, bytes):
                    continue
                try:
                    ctrl = json.loads(msg)
                except (ValueError, TypeError):
                    continue
                if ctrl.get("code") not in (0, None):
                    logger.info(f"ASR 错误: {ctrl.get('code')} {ctrl.get('message')}")
                    return None
                data = ctrl.get("data") or {}
                result = data.get("result") or {}
                pgs = result.get("pgs", "")
                text = "".join(
                    c.get("w", "")
                    for item in (result.get("ws") or [])
                    for c in (item.get("cw") or [])
                )
                if pgs == "rpl":
                    final_text = text
                if data.get("status") == 2:
                    break
            ws.close()
            ws = None

            if not final_text:
                logger.info("ASR 错误: 未识别到文本")
                return None
            return final_text
        except Exception as e:
            logger.info(f"ASR 异常: {e}")
            return None
        finally:
            if ws is not None:
                try:
                    ws.close()
                except Exception:
                    pass

    @staticmethod
    def _to_pcm16k(audio_data: bytes, format: str) -> Optional[bytes]:
        """把 wav 容器（任意采样率）或 raw PCM 统一转成 16k 16bit 单声道 PCM"""
        if format == "raw":
            return audio_data
        if audio_data[:4] != b"RIFF":
            # 标了 wav 但实际是裸 PCM，按 16k 处理
            return audio_data
        try:
            w = wave.open(io.BytesIO(audio_data), "rb")
            src_rate = w.getframerate()
            n_channels = w.getnchannels()
            width = w.getsampwidth()
            raw = w.readframes(w.getnframes())
            w.close()
        except Exception:
            return None

        if width != 2:
            logger.info(f"ASR 不支持 {width} 字节采样")
            return None

        if src_rate == 16000 and n_channels == 1:
            return raw

        # 转单声道（取均值）+ 线性重采样到 16k
        samples = [int.from_bytes(raw[i:i + 2], "little", signed=True) for i in range(0, len(raw) - 1, 2 * n_channels)]
        if n_channels > 1:
            samples = [
                sum(samples[i * n_channels:(i + 1) * n_channels]) // n_channels
                for i in range(len(samples) // n_channels)
            ]
        if src_rate != 16000:
            ratio = src_rate / 16000
            resampled = []
            for i in range(int(len(samples) / ratio)):
                pos = i * ratio
                i0, i1 = int(pos), min(int(pos) + 1, len(samples) - 1)
                frac = pos - i0
                resampled.append(int(samples[i0] * (1 - frac) + samples[i1] * frac))
            samples = resampled
        return b"".join(int(s).to_bytes(2, "little", signed=True) for s in samples)

    # ============================================================
    # 音色列表
    # ============================================================

    def get_available_voices(self) -> list:
        """
        获取可用音色列表（2026-08-25 实测修正）
        - 移除：xiaorui（未授权 licc failed）；xiaoxuan/xiaoyu（与 xiaoyan/xiaofeng 音频字节完全相同，重复）
        - 正确标注方言：xiaokun=河南话、xiaomei=粤语
        """
        return [
            {"value": "xiaoyan", "label": "小燕 · 标准女声"},
            {"value": "xiaofeng", "label": "小峰 · 标准男声"},
            {"value": "xiaomeng", "label": "小萌 · 活力女声"},
            {"value": "xiaokun", "label": "小坤 · 河南话（男）"},
            {"value": "xiaomei", "label": "小梅 · 粤语（女）"},
        ]
