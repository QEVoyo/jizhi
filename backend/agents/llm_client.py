import os
import time
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
from logging_config import logger
from utils import gen_audit

# 加载环境变量
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"
load_dotenv(env_path)

# 埋点用的 provider 名，与 utils/gen_audit.py 里记的取值一致
_PROVIDER = "deepseek"

# ============================================================================
# ⚠️ 这个文件是**全站 DeepSeek 调用的咽喉**（2026-10-16 起的埋点位置）
#
#   打模型的代码只有这几个函数，40 处业务调用点全都落到这里。所以埋点打在
#   这一层而不是逐个改调用点：**改 7 个函数就覆盖全站，而且以后新写的调用点
#   自动被计入** —— 逐个改的那种做法，漏一个就是一个统计黑洞，且没人会发现。
#
#   记账约定（与 utils/gen_audit.py 一致）：
#     · 成功 → note_ok（含耗时、输出长度）
#     · 抛异常 → note_fail 之后**照常上抛**，埋点绝不改变调用方看到的行为
#     · 流式 → 在流跑完时记；消费方中途断开也记（detail.aborted），
#              因为模型那边已经烧过 token 了，不记会让统计系统性偏低
#
#   purpose 参数：进后台「按用途」分组。默认 "unknown"，调用方顺手传一个
#   （如 purpose="question_gen"）就能分得清是哪类生成。**不传不影响计数**。
#
#   不走这个 SDK 的那几条（websocket / 私有协议）埋点在它们各自的客户端里，
#   本层够不着 —— 语音 ASR / TTS / 实时通话都在其中。全部入口登记在
#   utils/gen_audit.py 的 AI_ENTRY_POINTS，后台面板据此显示覆盖率。
# ============================================================================


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

def call_llm(messages, temperature=0.7, use_cache=True, purpose="unknown"):
    """非流式调用"""
    started = time.perf_counter()
    try:
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
    except Exception as e:
        gen_audit.note_fail(provider=_PROVIDER, model=get_model(), purpose=purpose,
                            started=started, error=e)
        raise
    logger.info("=== llm_stream 返回了 ===")  # 加这行
    content = response.choices[0].message.content
    gen_audit.note_ok(provider=_PROVIDER, model=get_model(), purpose=purpose,
                      started=started, output=content)
    return content

def call_llm_stream(messages, temperature=0.7, purpose="unknown"):
    """流式调用"""
    logger.info("🔥 call_llm_stream 被调用了")
    started = time.perf_counter()
    buf: list = []
    try:
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
            # ⚠️ 不能直接 chunk.choices[0] —— 部分模型会在流末尾补一个 choices 为空的
            # usage 块（千问侧实测 qwen3.8-flash 如此），取 [0] 会抛 IndexError
            # 把整条流打断：用户看到「说到一半突然没了」，日志只有一行 list index out of range。
            # DeepSeek 目前不发这种块，属预防性守卫。
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta and delta.content:
                buf.append(delta.content)
                yield delta.content
    except GeneratorExit:
        # 消费方提前断开（用户切页面 / 关掉对话框）。
        # 模型那边**已经烧过一次**了 —— 不记的话统计会系统性偏低。
        gen_audit.note_ok(provider=_PROVIDER, model=get_model(), purpose=purpose,
                          started=started, output="".join(buf),
                          detail={"aborted": True})
        raise
    except Exception as e:
        gen_audit.note_fail(provider=_PROVIDER, model=get_model(), purpose=purpose,
                            started=started, error=e)
        raise
    gen_audit.note_ok(provider=_PROVIDER, model=get_model(), purpose=purpose,
                      started=started, output="".join(buf))

def get_vision_model():
    """识图模型 —— V4.1 Flash 原生多模态，与文本同一个模型

    2026-09-10 由 deepseek-v4-flash-vision-exp（已下线）切换而来；env 可覆盖。
    """
    return os.getenv("DEEPSEEK_VISION_MODEL", get_model())

def call_llm_vision(image_url, prompt="请描述这张图片的内容", temperature=0.8,
                    purpose="unknown"):
    """DeepSeek 视觉模型 - 非流式图片理解（支持 URL / base64）"""
    started = time.perf_counter()
    try:
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
    except Exception as e:
        gen_audit.note_fail(provider=_PROVIDER, model=get_vision_model(),
                            purpose=purpose, started=started, error=e)
        raise
    content = response.choices[0].message.content
    gen_audit.note_ok(provider=_PROVIDER, model=get_vision_model(), purpose=purpose,
                      started=started, output=content)
    return content

def call_llm_vision_stream(image_url, prompt="请描述这张图片的内容", temperature=0.8,
                           purpose="unknown"):
    """DeepSeek 视觉模型 - 流式图片理解"""
    started = time.perf_counter()
    buf: list = []
    try:
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
            # ⚠️ 不能直接 chunk.choices[0] —— 部分模型会在流末尾补一个 choices 为空的
            # usage 块（千问侧实测 qwen3.8-flash 如此），取 [0] 会抛 IndexError
            # 把整条流打断：用户看到「说到一半突然没了」，日志只有一行 list index out of range。
            # DeepSeek 目前不发这种块，属预防性守卫。
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta and delta.content:
                buf.append(delta.content)
                yield delta.content
    except GeneratorExit:
        gen_audit.note_ok(provider=_PROVIDER, model=get_vision_model(), purpose=purpose,
                          started=started, output="".join(buf),
                          detail={"aborted": True})
        raise
    except Exception as e:
        gen_audit.note_fail(provider=_PROVIDER, model=get_vision_model(),
                            purpose=purpose, started=started, error=e)
        raise
    gen_audit.note_ok(provider=_PROVIDER, model=get_vision_model(), purpose=purpose,
                      started=started, output="".join(buf))
