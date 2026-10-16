"""千问 LLM 客户端（2026-08-25 新增）

小基全量收编到阿里云 DashScope（与语音通话同一个 key）：
  - 推理/聊天：qwen-plus（性价比均衡，env QWEN_CHAT_MODEL 可换 qwen-flash 等更便宜档位）
  - 识图：qwen3-vl-flash（最便宜的现行 VL，env QWEN_VISION_MODEL 可换）
走 DashScope OpenAI 兼容端点（compatible-mode/v1），复用 openai SDK。

价格参考（2026-08，元/百万 Token）：
  - 文本：qwen-plus 0.8 入 / 2.0 出；qwen-flash 0.15 入 / 1.5 出
  - 视觉：qwen3-vl-flash 0.367 入 / 2.94 出（≤32K）

⚠️ 埋点位置与约定同 agents/llm_client.py 的文件头 —— 这里是千问侧的咽喉，
   三个函数覆盖全部 qwen 文本/视觉生成。改这里就能保证不漏计。
"""
import time

from openai import OpenAI

from config import settings
from logging_config import logger
from utils import gen_audit

_PROVIDER = "qwen"


def _client() -> OpenAI:
    return OpenAI(
        api_key=settings.DASHSCOPE_API_KEY,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        timeout=60.0,
    )


def call_qwen(messages, temperature=0.7, model=None, purpose="unknown"):
    """非流式调用（默认 qwen-flash，model 可覆盖为 qwen-plus 等）"""
    used = model or settings.QWEN_CHAT_MODEL
    started = time.perf_counter()
    try:
        client = _client()
        response = client.chat.completions.create(
            model=used,
            messages=messages,
            temperature=temperature,
            stream=False,
            timeout=55.0,
            max_tokens=8192,
        )
    except Exception as e:
        gen_audit.note_fail(provider=_PROVIDER, model=used, purpose=purpose,
                            started=started, error=e)
        raise
    content = response.choices[0].message.content
    gen_audit.note_ok(provider=_PROVIDER, model=used, purpose=purpose,
                      started=started, output=content)
    return content


def call_qwen_stream(messages, temperature=0.7, model=None, purpose="unknown"):
    """流式调用：直接产出文本片段（与 call_llm_stream 接口一致）"""
    used = model or settings.QWEN_CHAT_MODEL
    started = time.perf_counter()
    buf: list = []
    try:
        client = _client()
        response = client.chat.completions.create(
            model=used,
            messages=messages,
            temperature=temperature,
            stream=True,
            timeout=55.0,
            max_tokens=8192,
        )
        for chunk in response:
            # ⚠️ 不能直接 chunk.choices[0] —— 部分模型（实测 qwen3.8-flash）会在流末尾
            # 补一个 choices 为空的 usage 块，取 [0] 会抛 IndexError 把整条流打断：
            # 用户看到的是「说到一半突然没了」，日志里只有一个 list index out of range。
            # qwen-flash 不发这种块，所以这个坑一直没暴露。
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta and delta.content:
                buf.append(delta.content)
                yield delta.content
    except GeneratorExit:
        # 消费方提前断开（用户切页面 / 关掉对话框）—— 模型那边已经烧过一次，要记。
        gen_audit.note_ok(provider=_PROVIDER, model=used, purpose=purpose,
                          started=started, output="".join(buf),
                          detail={"aborted": True})
        raise
    except Exception as e:
        gen_audit.note_fail(provider=_PROVIDER, model=used, purpose=purpose,
                            started=started, error=e)
        raise
    gen_audit.note_ok(provider=_PROVIDER, model=used, purpose=purpose,
                      started=started, output="".join(buf))


def call_qwen_vision(image_url, prompt="请描述这张图片的内容", temperature=0.8,
                     purpose="unknown"):
    """识图（qwen-vl-plus，支持 URL / base64 data URL）"""
    used = settings.QWEN_VISION_MODEL
    started = time.perf_counter()
    try:
        client = _client()
        response = client.chat.completions.create(
            model=used,
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
    except Exception as e:
        gen_audit.note_fail(provider=_PROVIDER, model=used, purpose=purpose,
                            started=started, error=e)
        raise
    content = response.choices[0].message.content
    gen_audit.note_ok(provider=_PROVIDER, model=used, purpose=purpose,
                      started=started, output=content)
    return content
