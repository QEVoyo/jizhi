import redis
import json
import hashlib
from openai import OpenAI
from config import settings

# 连接 Redis
try:
    print("尝试连接 Redis...")
    redis_client = redis.Redis(
        host="127.0.0.1",
        port=6379,
        db=0,
        decode_responses=True,
        socket_connect_timeout=3
    )
    redis_client.ping()
    print("Redis 连接成功")
except Exception as e:
    print(f"Redis 连接失败，错误信息: {e}")
    redis_client = None


def get_cache_key(messages, temperature):
    """生成缓存 key"""
    content = str(messages) + str(temperature)
    return hashlib.md5(content.encode()).hexdigest()


def call_llm(messages, temperature=0.7, use_cache=True):
    """调用大模型，带 Redis 缓存"""

    # 检查缓存
    if use_cache and redis_client:
        cache_key = get_cache_key(messages, temperature)
        cached = redis_client.get(cache_key)
        if cached:
            print("命中缓存")
            # 检查缓存内容是否有效
            if cached and len(cached) > 10:
                return cached
            else:
                # 缓存内容无效，删除
                redis_client.delete(cache_key)
                print("缓存内容无效，已删除")

    # 调用 API
    client = OpenAI(
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL
    )
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        temperature=temperature,
        stream=False
    )
    result = response.choices[0].message.content

    # 检查结果是否有效
    if not result or len(result) < 10:
        print(f"AI 返回内容为空或太短: {result}")
        return "{}"

    # 存入缓存（1小时过期）
    if use_cache and redis_client:
        cache_key = get_cache_key(messages, temperature)
        redis_client.setex(cache_key, 3600, result)

    return result


def call_llm_stream(messages, temperature=0.7):
    """流式调用"""
    client = OpenAI(
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL
    )
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        temperature=temperature,
        stream=True
    )
    return response