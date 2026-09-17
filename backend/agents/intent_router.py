"""小基对话意图路由 —— 自动判别（2026-09-10）

替代原「呼叫对象」下拉框：不再让用户手动选角色，改为按用户说的话自动分流。

三级阶梯，逐级升昂贵，绝大多数消息在第一级就结束：

  ① 规则层   —— 明确指令词命中即分流。零成本、零延迟。
  ② 关键词门 —— 不含任何「像是在派活」的词 → 直接判闲聊，一次模型调用都不做。
                 闲聊、知识问答、情感倾诉全部止步于此（绝大多数消息）。
                 含关键词但带疑问词（怎么/为什么/吗？）同样判闲聊——那是在**问**，
                 不是在**派活**（「这道题怎么做」不该被当成出题指令）。
  ③ 模型层   —— 仅当「像是在派活、但规则没抓住」时，调一次 qwen-flash 兜底
                 （约 0.004 分/次、~0.4s）。换个说法的指令在这一层被接住。

设计原则：**默认闲聊**。判成闲聊的代价是用户再说一句；误判成派活会打断用户。
所以规则只在高度明确时才分流，模型层也提示「拿不准就答 chat」。

钱不是瓶颈（分类一次约 0.004 分），**延迟才是**——所以关键是让聊天路径
一次模型调用都不多花。allow_llm=False 时只跑 ①②（输入框实时预判用）。
"""
from __future__ import annotations

from typing import Optional

from logging_config import logger

INTENTS = ("chat", "generate", "plan", "evaluate")

# ============================================================
# ① 规则层（命中即分流，所以只放几乎不可能有歧义的说法）
#   strong：任何长度都认（说法本身足够明确）
#   soft  ：只有短句才认（避免长句里提到「计划」二字就被误分流）
# ============================================================
_STRONG: list[tuple[str, tuple[str, ...]]] = [
    ("generate", (
        "出题", "出道题", "出个题", "出一道", "出几道", "出个卷", "出份卷", "出套卷",
        "来一道", "来几道", "来道题", "生成题", "生成一道", "生成几道",
        "给我出", "帮我出", "做几道题", "练几道", "练习题", "刷题", "考考我", "测测我",
    )),
    ("plan", (
        "学习计划", "备考计划", "复习计划", "做个计划", "制定计划", "生成计划",
        "学习规划", "学习路线", "学习方案", "备考方案", "帮我安排", "安排一下",
    )),
    ("evaluate", (
        "学情", "学习报告", "评估我", "分析我的", "分析一下我的",
        "我学得怎么样", "我学得咋样", "我的水平", "诊断一下",
    )),
]

_SOFT_MAX_LEN = 24
_SOFT: list[tuple[str, tuple[str, ...]]] = [
    ("plan", ("计划", "规划", "怎么学", "怎么安排", "怎么规划")),
    ("evaluate", ("评估", "诊断")),
    ("generate", ("题目", "试卷")),
]

# ============================================================
# ② 关键词门：判断「这句话值不值得花一次模型调用」
#   不是判定意图，只是决定要不要进第 ③ 层
# ============================================================
_GATE_WORDS = (
    "题", "卷", "练习", "训练", "多练", "刷", "考", "测", "计划", "规划", "安排", "方案", "路线",
    "学情", "评估", "诊断", "报告", "分析", "水平", "掌握", "薄弱", "错题", "复习", "备考",
)

# 带这些词说明用户在「问」而不是在「派活」→ 直接判闲聊，不花钱
_QUESTION_WORDS = (
    "怎么", "为什么", "什么", "如何", "吗", "?", "？", "哪", "谁", "多少", "是不是", "能不能",
)

_GATE_MAX_LEN = 40

# ============================================================
# ③ 模型层（仅歧义时）
# ============================================================
_PROMPT = """判断用户这句话想让你做什么，只输出一个词：

- generate：让出题、要练习题或试卷
- plan：让做学习计划、规划学习路线
- evaluate：让评估学习情况、分析学情
- chat：其他一切（闲聊、提问、答疑、倾诉）

拿不准一律答 chat。

用户输入：{text}

只输出一个词："""


def _match_rules(text: str) -> Optional[tuple[str, str]]:
    """返回 (intent, 命中的词) 或 None"""
    for intent, words in _STRONG:
        for w in words:
            if w in text:
                return intent, w
    if len(text) <= _SOFT_MAX_LEN:
        for intent, words in _SOFT:
            for w in words:
                if w in text:
                    return intent, w
    return None


def route_intent(text: str, allow_llm: bool = True) -> dict:
    """判别用户这句话该走哪条链路。

    allow_llm=False 时只跑规则层与关键词门（零成本、零延迟），供输入框实时预判；
    发送时用默认的 allow_llm=True 得到权威结果。

    返回 {"intent", "matched", "hit"}：
      matched ∈ rule | soft-rule | gate-no-llm | llm | short | llm-error
    """
    t = (text or "").strip()
    if len(t) < 2:
        return {"intent": "chat", "matched": "short", "hit": ""}

    # ① 规则层
    hit = _match_rules(t)
    if hit:
        intent, word = hit
        return {"intent": intent, "matched": "rule", "hit": word}

    # ② 关键词门：不像派活 / 是在问 / 太长 → 闲聊，不调模型
    if not any(w in t for w in _GATE_WORDS):
        return {"intent": "chat", "matched": "gate-no-llm", "hit": ""}
    if any(w in t for w in _QUESTION_WORDS):
        return {"intent": "chat", "matched": "gate-no-llm", "hit": ""}
    if len(t) > _GATE_MAX_LEN:
        return {"intent": "chat", "matched": "gate-no-llm", "hit": ""}

    # ③ 模型层
    if not allow_llm:
        return {"intent": "chat", "matched": "gate-no-llm", "hit": ""}

    try:
        from agents.qwen_client import call_qwen
        out = call_qwen(
            [{"role": "user", "content": _PROMPT.format(text=t[:300])}],
            temperature=0.1,
        )
        intent = (out or "").strip().lower()
        # 模型偶尔会带标点/多余字，取第一个命中的意图词
        for k in INTENTS:
            if k in intent:
                logger.info(f"[intent] llm 判别 {k} ← {t[:30]!r}")
                return {"intent": k, "matched": "llm", "hit": ""}
        return {"intent": "chat", "matched": "llm", "hit": ""}
    except Exception as e:
        logger.info(f"[intent] 模型层失败，回落闲聊: {e}")
        return {"intent": "chat", "matched": "llm-error", "hit": ""}
