# -*- coding: utf-8 -*-
"""跨文件复用的**消息点快捷函数**（2026-10-07 接消息点时新增）

## 为什么单独一个文件

设计契约是「加一个消息点 = 注册表加一行 + 事件处调一次 `notify()`」，
大部分消息点确实就该在事件处直接写那 4 行（见 `community/posts.py` 的
`_notify_post_author`）。但有几个点是**同一个事件、多个入口**：

    learning.plan_generated —— 建计划有三条互不共用的路径：
        `learning_plan.create_plan`（自定义）
        `subject_plan.submit_diagnosis`（摸底诊断）
        `exam_papers.generate_plan_from_exam`（真题答卷）
    learning.mastery_jump / learning.weak_alert —— 掌握度有两个写入点：
        `subject_plan.submit_answer`（EWMA）与 `questions.evaluate_answer`（LLM 直接给分）

同一段 `notify()` 抄五遍，改一处就会漏四处 —— 所以抽到这里。
**只放「≥2 个文件要用」的**，单文件用的仍然留在本文件里就地写。

每个函数都遵守 `utils/notification.py` 的三条硬规矩：
失败不静默（记 ERROR）、类型必须注册、不绕过公共入口。
"""
from logging_config import logger


async def notify_plan_generated(user_id: str, plan_id: str, plan_name: str,
                                basis: str = "") -> None:
    """备考计划建好了 → `learning.plan_generated`。

    收件人就是计划的主人。三条建计划路径都调这里，`basis` 说明计划是怎么来的
    （摸底诊断 / 真题答卷 / 自己填的），用户从列表里分得清是哪一份。
    """
    if not user_id or not plan_id:
        return
    try:
        from utils.notification import notify, NotifyError
        await notify(
            user_id, "learning.plan_generated",
            source_id=plan_id,
            title=f"备考计划已生成：{plan_name or '未命名计划'}",
            content=(f"{basis}，去看看吧。" if basis else "去看看吧。"),
            # 不传 link：注册表的 /plan-detail/{source_id} 模板会自己拼好，
            # 跳转模板只留一份（见 notification_registry.resolve_link）
        )
    except (NotifyError, KeyError) as e:
        logger.error(f"⚠️ 计划生成通知未送达 user={user_id} plan={plan_id}: {e}")
    except Exception as e:                                      # noqa: BLE001
        logger.error(f"⚠️ 计划生成通知异常 user={user_id} plan={plan_id}: {e}")


# ---- 掌握度的两个阈值 ----
# ⚠️ 这两个数是**本轮定的**（注册表只写了「掌握度跃升」「薄弱知识点堆积」，
#    没说多少算跃升、几个算堆积）。要调只改这里，两个写入点同时生效。
JUMP_DELTA = 20.0        # 单次涨这么多才算「跃升」
JUMP_FLOOR = 60.0        # 且涨完得过及格线 —— 从 10 涨到 35 不算跃升
WEAK_LINE = 60.0         # 低于它算薄弱（与 questions.py 的判定口径一致）
WEAK_ALERT_AT = 5        # 薄弱知识点攒到几个提醒一次


async def notify_mastery_change(user_id: str, kp: str,
                                old_score: float, new_score: float) -> None:
    """掌握度变化后的两条消息：跃升 / 薄弱堆积。

    只在**该发的时候**发：
      · 跃升  —— 涨幅 ≥ JUMP_DELTA 且新分 ≥ JUMP_FLOOR
      · 堆积  —— 薄弱知识点**恰好**攒到 WEAK_ALERT_AT 个时报一次
        （用「恰好等于」而不是「大于等于」：否则第 6、7、8 个薄弱点会各报一遍）
    """
    if not user_id or not kp or old_score is None or new_score is None:
        return
    try:
        from utils.notification import notify, NotifyError

        if new_score - old_score >= JUMP_DELTA and new_score >= JUMP_FLOOR:
            await notify(
                user_id, "learning.mastery_jump",
                source_id=kp,
                title=f"「{kp}」掌握度跃升",
                content=f"从 {old_score:.0f} 提到了 {new_score:.0f}，这块可以过了。",
            )

        if new_score >= WEAK_LINE or old_score < WEAK_LINE:
            return          # 只有「本来薄弱、现在也还薄弱」才可能让薄弱数变多
        weak = await _count_weak(user_id)
        if weak != WEAK_ALERT_AT:      # 恰好攒到阈值才报，见上面说明
            return
        await notify(
            user_id, "learning.weak_alert",
            actor_name=kp,
            source_id="weak_count",
            title=f"薄弱知识点积到 {weak} 个了",
            content="挑一个先补吧，堆着会越来越难追。",
        )
    except (NotifyError, KeyError) as e:
        logger.error(f"⚠️ 掌握度通知未送达 user={user_id} kp={kp}: {e}")
    except Exception as e:                                      # noqa: BLE001
        logger.error(f"⚠️ 掌握度通知异常 user={user_id} kp={kp}: {e}")


async def _count_weak(user_id: str) -> int:
    """这个用户现在有几条薄弱知识点（掌握度低于 WEAK_LINE）。

    用 `Prefer: count=exact` 只取计数不拉行 —— 这里只关心个数。
    查不到时返回 -1（**故意不等于任何阈值**）：宁可这条提醒不发，
    也不要在读失败时误判成「正好攒到 5 个」。
    """
    import httpx
    from config import settings
    from services.supabase import get_supabase_service_headers

    url = (f"{settings.SUPABASE_URL}/rest/v1/user_kp_mastery"
           f"?user_id=eq.{user_id}&mastery_score=lt.{WEAK_LINE}&select=id")
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(url, headers={
                **get_supabase_service_headers(),
                "Prefer": "count=exact", "Range-Unit": "items", "Range": "0-0",
            })
        # PostgREST 超过一页返回 206，不是 200 —— 只认 200 会把「有数据」读成失败
        if res.status_code not in (200, 206):
            return -1
        cr = res.headers.get("content-range") or ""
        return int(cr.split("/")[-1]) if "/" in cr else -1
    except Exception as e:                                      # noqa: BLE001
        logger.warning(f"[notify] 统计薄弱知识点失败 user={user_id}: {e}")
        return -1
