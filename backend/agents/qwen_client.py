"""千问 LLM 客户端（2026-08-25 新增）

小基全量收编到阿里云 DashScope（与语音通话同一个 key）：
  - 推理/聊天：qwen-plus（性价比均衡，env QWEN_CHAT_MODEL 可换 qwen-flash 等更便宜档位）
  - 识图：qwen3-vl-flash（最便宜的现行 VL，env QWEN_VISION_MODEL 可换）
走 DashScope OpenAI 兼容端点（compatible-mode/v1），复用 openai SDK。

价格参考（2026-08，元/百万 Token）：
  - 文本：qwen-plus 0.8 入 / 2.0 出；qwen-flash 0.15 入 / 1.5 出
  - 视觉：qwen3-vl-flash 0.367 入 / 2.94 出（≤32K）
"""
from openai import OpenAI

from config import settings
from logging_config import logger


def _client() -> OpenAI:
    return OpenAI(
        api_key=settings.DASHSCOPE_API_KEY,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        timeout=60.0,
    )


def call_qwen(messages, temperature=0.7, model=None):
    """非流式调用（默认 qwen-flash，model 可覆盖为 qwen-plus 等）"""
    client = _client()
    response = client.chat.completions.create(
        model=model or settings.QWEN_CHAT_MODEL,
        messages=messages,
        temperature=temperature,
        stream=False,
        timeout=55.0,
        max_tokens=8192,
    )
    return response.choices[0].message.content


def call_qwen_stream(messages, temperature=0.7, model=None):
    """流式调用：直接产出文本片段（与 call_llm_stream 接口一致）"""
    client = _client()
    response = client.chat.completions.create(
        model=model or settings.QWEN_CHAT_MODEL,
        messages=messages,
        temperature=temperature,
        stream=True,
        timeout=55.0,
        max_tokens=8192,
    )
    for chunk in response:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


def call_qwen_vision(image_url, prompt="请描述这张图片的内容", temperature=0.8):
    """识图（qwen-vl-plus，支持 URL / base64 data URL）"""
    client = _client()
    response = client.chat.completions.create(
        model=settings.QWEN_VISION_MODEL,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_url}},
            ]
        }],
        temperature=temperature,
        stream=False,
        timeout=55.0,
        max_tokens=2048,
    )
    return response.choices[0].message.content
