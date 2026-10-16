"""
从模型输出里抠 JSON —— 全仓唯一实现（2026-10-15）

## 为什么要有这个文件

在这之前，全仓有 **10 个**各写各的解析函数：

    routers/questions.py:50   extract_json_from_response   find/rfind + loads
    routers/daily_learn.py:209         _extract_json      括号计数
    routers/vocab.py:40                _extract_entry_json
    services/daily_generator.py:214    _extract_json      括号计数
    services/video_gen.py:243          _extract_json      去围栏 + find/rfind
    services/xiaoji_memory.py:141      _extract_json      正则
    scripts/seed_*.py (4 个)           parse_json / extract_json_array

它们**各自只处理了自己当初遇到的那一种脏输出**，于是同一个模型换一种写法就炸：
有的不认 markdown 围栏，有的被字符串里的 `}` 骗过，有的不修尾逗号。

## 这里统一处理的五种脏输出（每一种都有真实来源）

  1. **markdown 围栏**  ```json ... ```    —— 提示词说了"只输出 JSON"它照样加
  2. **前后有废话**     "好的，这是结果：{...}  希望对你有帮助"
  3. **字符串里的括号** `{"code": "}"}`     —— 朴素计数器的经典翻车点（见下）
  4. **尾逗号**         `{"a":1,"b":2,}`    —— JSON 不允许，模型很爱写
  5. **被截断**         `{"a":1,"b":[1,2`  —— 撞 max_tokens，括号没闭合

## 那个"字符串里的括号"为什么必须单独处理

最直觉的写法是数括号：遇到 `{` 加一、`}` 减一、归零就截断。它会被这一行骗死：

    {"sql": "SELECT * FROM t WHERE x = '}'", "ok": true}

计数器在字符串里的那个 `}` 上归零，于是只抠出 `{"sql": "SELECT * FROM t WHERE x = '"`，
json.loads 报错，调用方以为模型没按要求输出，重试一次 —— 又错。

所以下面是个**状态机**：要知道自己此刻在不在字符串里、有没有被反斜杠转义。
"""

from __future__ import annotations

import json
import re
from typing import Any

# ```json ... ``` / ``` ... ```（大小写不敏感，允许后面的空行）
_FENCE_RE = re.compile(r"```(?:json|JSON)?\s*\n?(.*?)```", re.DOTALL)

# 尾逗号：} 或 ] 前面多余的那个逗号
_TRAILING_COMMA_RE = re.compile(r",\s*([}\]])")


class JSONExtractError(ValueError):
    """抠不出合法 JSON。调用方**应当**把它当成"模型这次没按格式来"处理，
    通常重试一次就好 —— 不要让它变成 500。"""


def _scan_candidates(text: str) -> list[tuple[int, int]]:
    """
    找出所有「平衡的」JSON 片段，返回 (起点, 终点) 列表（终点是开区间）。

    状态机要点：只有**不在字符串里**的括号才计数。
    """
    spans: list[tuple[int, int]] = []
    stack: list[str] = []
    start = -1
    in_str = False
    escaped = False
    quote = ""

    for i, ch in enumerate(text):
        if in_str:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                in_str = False
            continue

        if ch in ('"', "'"):
            # 单引号不是合法 JSON，但模型偶尔会用；当作字符串起点处理更稳
            in_str, quote = True, ch
            continue

        if ch in "{[":
            if not stack:
                start = i
            stack.append(ch)
        elif ch in "}]":
            if not stack:
                continue                       # 孤立的右括号，忽略
            open_ch = stack.pop()
            # 类型要对上才算数：{ 配 }、[ 配 ]
            if (open_ch, ch) not in (("{", "}"), ("[", "]")):
                stack.clear()
                start = -1
                continue
            if not stack and start >= 0:
                spans.append((start, i + 1))
                start = -1

    return spans


def _repair_truncated(text: str) -> str:
    """
    给被 max_tokens 截断的 JSON 补上缺失的闭合符号，并丢掉结尾那个不完整的键值对。

    为什么值得修：撞 max_tokens 是**常态**（尤其是出题这种长输出），
    而截断的输出里前面的内容往往完全可用。丢掉整条重来一次 LLM 调用，
    成本远高于在这里补两行。
    """
    in_str = False
    escaped = False
    quote = ""
    stack: list[str] = []

    for ch in text:
        if in_str:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                in_str = False
            continue
        if ch in ('"', "'"):
            in_str, quote = True, ch
        elif ch in "{[":
            stack.append(ch)
        elif ch in "}]" and stack:
            stack.pop()

    repaired = text
    if in_str:
        # 停在字符串中间：先把这个字符串闭上
        repaired += quote
    # 结尾可能是个半截的 `,"key":` —— 从最后一个逗号处砍掉更安全
    repaired = re.sub(r",\s*$", "", repaired.rstrip())
    repaired = re.sub(r',\s*"[^"]*"\s*:\s*$', "", repaired.rstrip())

    for open_ch in reversed(stack):
        repaired += "}" if open_ch == "{" else "]"
    return repaired


def _try_loads(candidate: str) -> Any:
    """三种由松到紧的尝试。都不行就抛 JSONExtractError。"""
    attempts = [
        candidate,
        _TRAILING_COMMA_RE.sub(r"\1", candidate),      # 去尾逗号
    ]
    for attempt in attempts:
        try:
            return json.loads(attempt)
        except (json.JSONDecodeError, TypeError):
            continue
    # 最后一招：补闭合
    try:
        return json.loads(_repair_truncated(_TRAILING_COMMA_RE.sub(r"\1", candidate)))
    except (json.JSONDecodeError, TypeError) as e:
        raise JSONExtractError(str(e)) from e


def extract_json(text: str, *, prefer: str = "object") -> Any:
    """
    从模型输出里抠出 JSON。

    prefer: 'object' 优先返回 dict（找不到再退而求其次）
            'array'  优先返回 list
            'any'    谁先出现要谁

    ⚠️ 返回的可能是 dict **或** list —— 调用方要按自己的 prefer 判类型。
       不在这里强制转换，是因为"我要 dict 却拿到 list"是调用方该明确处理的
       语义问题（多半意味着提示词没写清楚），不该被这里静默吞掉。

    失败抛 JSONExtractError（不是返回 None）：
       返回 None 的写法会让调用方写出 `if result is None` 然后忘记判，
       而异常至少会在日志里留个栈。
    """
    if not text or not text.strip():
        raise JSONExtractError("模型返回为空")

    raw = text.strip()

    # ① 先看有没有 markdown 围栏。有的话**只在围栏内容里找** ——
    #    否则围栏外的解释文字里如果带个 {} 会被优先抠出来。
    fences = _FENCE_RE.findall(raw)
    search_space = fences if fences else [raw]

    candidates: list[tuple[int, int, str]] = []   # (优先级, 位置, 片段)
    for block in search_space:
        for s, e in _scan_candidates(block):
            frag = block[s:e]
            kind = "object" if frag.lstrip().startswith("{") else "array"
            if prefer == "any":
                prio = 0
            else:
                prio = 0 if kind == prefer else 1
            candidates.append((prio, s, frag))

    if not candidates:
        # 一个平衡片段都没有 → 多半是被截断了。整段拿去修。
        body = search_space[0]
        return _try_loads(body)

    # 优先级高的排前面；同优先级里**取最长的那段**
    # （嵌套时短的片段是长的前缀，取长的才不会半路截断）
    candidates.sort(key=lambda c: (c[0], -len(c[2])))

    last_err: Exception | None = None
    for _prio, _pos, frag in candidates[:5]:        # 最多试 5 个，别在垃圾上磨
        try:
            return _try_loads(frag)
        except JSONExtractError as e:
            last_err = e
            continue

    # 所有平衡片段都解不开：退回"整段修复"
    try:
        return _try_loads(search_space[0])
    except JSONExtractError as e:
        raise JSONExtractError(f"抠不出 JSON（试了 {len(candidates)} 个片段）：{e}") from e


def extract_object(text: str) -> dict:
    """要 dict。拿不到就抛 —— 不返回 {}，空字典会让"失败"看起来像"成功但内容为空"。"""
    data = extract_json(text, prefer="object")
    if not isinstance(data, dict):
        raise JSONExtractError(f"期望 JSON 对象，实际拿到 {type(data).__name__}")
    return data


def extract_array(text: str) -> list:
    """
    要 list。

    ⚠️ 模型有时返回 `{"questions": [...]}` 而不是裸数组 —— 这种情况**自动拆包**，
       因为提示词写的是"输出 JSON 数组"而它包了一层，是它没听话、
       不是调用方要处理的分支。
    """
    data = extract_json(text, prefer="array")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("questions", "items", "data", "results", "list", "array"):
            if isinstance(data.get(key), list):
                return data[key]
        # 只有一个值且它是数组 —— 大概率就是它
        lists = [v for v in data.values() if isinstance(v, list)]
        if len(lists) == 1:
            return lists[0]
    raise JSONExtractError(f"期望 JSON 数组，实际拿到 {type(data).__name__}")
