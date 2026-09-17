"""小基人格风格 —— 唯一事实源（2026-09-11）

文字聊天（routers/community/xiaoji.py）与实时语音通话（routers/xiaoji.py
_build_call_instructions）此前各维护一份 personality_styles，风格文案易漂移。
取值与文案统一放这里，两处只引用；人设主体文本（聊天/语音约束不同）仍各自维护。
"""
from __future__ import annotations

PERSONALITY_STYLES = {
    "warm": "温暖友善，像朋友一样聊天，偶尔幽默，会用一些轻松的语气词",
    "humorous": "幽默风趣，喜欢开玩笑和玩梗，偶尔自嘲，让聊天轻松有趣",
    "formal": "正式得体，条理清晰，用词准确，回答有结构不啰嗦",
    "encouraging": "鼓励为主，多多肯定用户的努力，善于打气和给信心",
}


def style_of(personality: str) -> str:
    """取风格文案；未知/空值回落 warm（与原两处 .get 行为一致）"""
    return PERSONALITY_STYLES.get(personality, PERSONALITY_STYLES["warm"])
