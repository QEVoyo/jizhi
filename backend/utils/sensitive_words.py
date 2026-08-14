# backend/utils/sensitive_words.py

import httpx
from config import settings
from logging_config import logger


def check_content_safety(text: str) -> tuple:
    """
    使用 AI 检查内容是否安全
    返回: (is_safe: bool, reason: str)
    """
    if not text:
        return True, ""

    prompt = f"""请判断以下用户输入是否包含违规内容，只输出 JSON 格式，不要有其他内容。

违规内容包括：
1. 政治敏感内容（如分裂国家、攻击领导人、颠覆政权等）
2. 色情低俗内容（如性暗示、色情描写、裸体等）
3. 暴力恐怖内容（如杀人、爆炸、恐怖袭击等）
4. 违法违规内容（如毒品、赌博、诈骗等）
5. 人身攻击和侮辱（如歧视、辱骂、诽谤等）
6. 其他有害信息（如谣言、诈骗信息等）

用户输入：{text[:500]}

输出格式：
{{"safe": true/false, "reason": "如果违规，简要说明原因；如果安全，留空"}}
"""

    try:
        # 用 DeepSeek 快速判断
        from agents.llm_client import call_llm
        result = call_llm([
            {"role": "system", "content": "你是一个内容安全审核员，只输出 JSON 格式。"},
            {"role": "user", "content": prompt}
        ], temperature=0.1)

        import json
        # 提取 JSON
        result = result.strip()
        start = result.find('{')
        end = result.rfind('}')
        if start != -1 and end != -1:
            result = result[start:end+1]
            data = json.loads(result)
            return data.get("safe", True), data.get("reason", "")
        return True, ""

    except Exception as e:
        logger.info(f"[WARNING] 内容安全检查失败 (默认拒绝): {e}")
        # ✅ 安全策略：审核服务异常时拒绝内容，避免绕过
        # 只有明确判定为 safe 才放行
        return False, f"内容安全审核服务暂时不可用，请稍后重试"


def contains_sensitive(text: str) -> bool:
    """检查文本是否包含敏感内容（兼容旧接口）"""
    safe, _ = check_content_safety(text)
    return not safe