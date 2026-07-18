import os
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

# 加载环境变量
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"
load_dotenv(env_path)

def get_api_key():
    return os.getenv("DEEPSEEK_API_KEY")

def get_base_url():
    return os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

def call_llm(messages, temperature=0.7, use_cache=True):
    """非流式调用"""
    client = OpenAI(api_key=get_api_key(), base_url=get_base_url())
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        temperature=temperature,
        stream=False
    )
    print("=== llm_stream 返回了 ===")  # 加这行
    return response.choices[0].message.content

def call_llm_stream(messages, temperature=0.7):
    """流式调用"""
    print("🔥 call_llm_stream 被调用了")
    client = OpenAI(api_key=get_api_key(), base_url=get_base_url())
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        temperature=temperature,
        stream=True
    )
    for chunk in response:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content