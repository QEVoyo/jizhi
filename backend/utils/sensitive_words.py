# backend/utils/sensitive_words.py

import httpx
from config import settings
from logging_config import logger

# 「审核服务不可用」时返回的固定理由。
#
# ⚠️ 这个常量有实际作用，不是文案：check_content_safety 是 **fail-closed** 的
#    （审核服务挂了就拒绝内容），所以「被判定违规」和「服务不可用」在当前接口上
#    长得一模一样 —— 都是 (False, 某个理由)。
#
#    而这两件事的**后果必须不同**：判定违规要扣用户信誉，
#    服务不可用绝不能扣 —— 否则模型 API 抖一下，全站用户一起掉分。
#
#    所以下面用恒等比较把它区分出来（不是比字符串内容，是比这个对象）。
SERVICE_UNAVAILABLE = "内容安全审核服务暂时不可用，请稍后重试"


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
        #
        # ⚠️ 注意这个返回值与「判定违规」的区别靠 SERVICE_UNAVAILABLE 常量，
        #    调用方要扣信誉的话必须先把这种情况排除掉（见 check_and_penalize）。
        return False, SERVICE_UNAVAILABLE


def is_service_failure(reason: str) -> bool:
    """这个 False 是"审核服务挂了"造成的，不是"内容真的违规"。"""
    return reason == SERVICE_UNAVAILABLE


def contains_sensitive(text: str) -> bool:
    """检查文本是否包含敏感内容（兼容旧接口）"""
    safe, _ = check_content_safety(text)
    return not safe


async def check_and_penalize(
    text: str,
    user_id: str | None,
    *,
    field: str = "",
    endpoint: str = "",
) -> tuple:
    """
    check_content_safety 的**异步**包装：判定违规时顺手扣信誉 + 记安全事件。

    为什么单独一个函数而不是把惩罚塞进 check_content_safety：
        后者是**同步**函数（还阻塞在 LLM 调用上），而扣分要写 Supabase，
        混进去会让它变成一个又阻塞又发网络请求的东西。
        这里保持 check_content_safety 原样，只在外面加一层。

    为什么调用方该用这个而不是自己判：
        扣分 + 记事件 + 「服务不可用不算违规」这三件事每次都写一遍，
        迟早有一处漏掉或者写反。收在一处。

    返回与 check_content_safety 相同：(is_safe, reason)。
    """
    safe, reason = check_content_safety(text)
    if safe:
        return safe, reason

    # ★ 关键分支：服务不可用不是用户的错，绝不能扣分。
    #   这是本函数存在的第一个理由（见 SERVICE_UNAVAILABLE 的说明）。
    if is_service_failure(reason):
        return safe, reason

    if not user_id:
        return safe, reason

    # 记安全事件（谁、在哪个字段、命中什么）
    #
    # ⚠️ 这里**不传 request**，只传显式的末端点名。理由：
    #    这几个调用点都在已登录接口里，user_id 才是关联主键（不像限流命中
    #    那种"可能是匿名扫描"的场景必须靠 IP）。
    #    而为了拿 IP 要给 4 个文件、6 个 handler 加 Request 参数并调整签名顺序，
    #    收益不匹配。传 endpoint 字符串同样能让后台按端点聚合出"哪个入口最常被撞"。
    try:
        from utils.security_log import EVENT_BANNED_WORD, SEVERITY_WARN, record_event
        await record_event(
            EVENT_BANNED_WORD,
            severity=SEVERITY_WARN,
            user_id=user_id,
            endpoint=endpoint or None,
            status_code=400,
            detail={"field": field, "reason": (reason or "")[:200],
                    "text_len": len(text or "")},
        )
    except Exception as e:
        logger.warning("违禁词安全事件记录失败: %s", e)

    # 扣信誉分
    try:
        from utils.reputation import apply_delta
        await apply_delta(
            user_id, "content.banned_word",
            source_type="content", reason_text=(reason or "")[:200],
            detail={"field": field},
        )
    except Exception as e:
        logger.warning("违禁词信誉扣分失败: %s", e)

    return safe, reason