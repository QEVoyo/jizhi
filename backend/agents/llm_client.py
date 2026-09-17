import os
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
from logging_config import logger

# 加载环境变量
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"
load_dotenv(env_path)

def get_api_key():
    return os.getenv("DEEPSEEK_API_KEY")

def get_base_url():
    return os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

def get_model():
    """文本模型 —— deepseek-flash（V4.1 Flash，2026-09-10 上线）"""
    return os.getenv("DEEPSEEK_MODEL", "deepseek-flash")

def _thinking_kwargs():
    """思考模式开关：默认关（置 env DEEPSEEK_THINKING=1 开启）。

    V4.1 Flash 默认开思考——回答前先在 reasoning_content 里推理一段（不显示给用户）。
    实测（2026-09-10）：首字 0.6s → 1~13s、输出 token 翻数倍，且思考计入 max_tokens
    （额度给小时会只思考不出正文）。迁移前的 deepseek-chat 本就是非思考档，
    故此处默认关闭以保持一致；若要开启，前端还需支持展示 reasoning_content 折叠块。
    """
    if os.getenv("DEEPSEEK_THINKING", "0") == "1":
        return {}
    return {"extra_body": {"thinking": {"type": "disabled"}}}

def call_llm(messages, temperature=0.7, use_cache=True):
    """非流式调用"""
    client = OpenAI(api_key=get_api_key(), base_url=get_base_url(), timeout=60.0)
    response = client.chat.completions.create(
        model=get_model(),
        messages=messages,
        temperature=temperature,
        stream=False,
        timeout=55.0,
        max_tokens=8192,
        **_thinking_kwargs(),
    )
    logger.info("=== llm_stream 返回了 ===")  # 加这行
    return response.choices[0].message.content

def call_llm_stream(messages, temperature=0.7):
    """流式调用"""
    logger.info("🔥 call_llm_stream 被调用了")
    client = OpenAI(api_key=get_api_key(), base_url=get_base_url(), timeout=60.0)
    response = client.chat.completions.create(
        model=get_model(),
        messages=messages,
        temperature=temperature,
        stream=True,
        timeout=55.0,
        **_thinking_kwargs(),
    )
    for chunk in response:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

def get_vision_model():
    """识图模型 —— V4.1 Flash 原生多模态，与文本同一个模型

    2026-09-10 由 deepseek-v4-flash-vision-exp（已下线）切换而来；env 可覆盖。
    """
    return os.getenv("DEEPSEEK_VISION_MODEL", get_model())

def call_llm_vision(image_url, prompt="请描述这张图片的内容", temperature=0.8):
    """DeepSeek 视觉模型 - 非流式图片理解（支持 URL / base64）"""
    client = OpenAI(api_key=get_api_key(), base_url=get_base_url(), timeout=60.0)
    response = client.chat.completions.create(
        model=get_vision_model(),
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
        }],
        temperature=temperature,
        stream=False,
        timeout=55.0,
        max_tokens=2048,
        **_thinking_kwargs(),
    )
    return response.choices[0].message.content

def call_llm_vision_stream(image_url, prompt="请描述这张图片的内容", temperature=0.8):
    """DeepSeek 视觉模型 - 流式图片理解"""
    client = OpenAI(api_key=get_api_key(), base_url=get_base_url(), timeout=60.0)
    response = client.chat.completions.create(
        model=get_vision_model(),
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
        }],
        temperature=temperature,
        stream=True,
        timeout=55.0,
        max_tokens=2048,
        **_thinking_kwargs(),
    )
    for chunk in response:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content