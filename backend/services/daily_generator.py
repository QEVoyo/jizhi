"""
每日推荐 + 昨日学习总结 生成服务
由定时任务或手动 API 触发
"""
import httpx
from datetime import datetime, timedelta, timezone
from config import settings
from agents.llm_client import call_llm
from utils.notification import notify, NotifyError
from services.kp_questions import q_stem_text, score_by_kp
from logging_config import logger


async def get_active_users(days: int = 7) -> list[dict]:
    """最近 N 天有活动的用户（带资料，供推荐与总结用）。

    ⚠️ 2026-10-08 修正，原来有两处错：

    1. **查错了表**。原实现查 `questions`（AI 生成题）当"活跃"来源 —— 语义就不对：
       一个用户完全可能天天做题、从来没用过出题功能。而且**没有任何时间过滤**，
       `limit=500` 之后按插入顺序截断，"最近 7 天"这句话是假的。
       正确来源是 `user_actions`（全产品行为流水，带 `action_at`），
       与 `agents/tuning.py:_active_users` 同一个口径。

    2. **profiles 硬截断到 100 个**（`list(user_ids)[:100]`）。活跃用户一多，
       后面的会**静默收不到推荐**。改成按 100 一批查全 —— 分批是因为
       PostgREST 的 `in.(...)` 走 URL，几百个 uuid 会超长。
    """
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
    }
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    async with httpx.AsyncClient(timeout=30.0) as client:
        # ⚠️ **必须走 params 让 httpx 编码**，不能把 since 拼进 URL 字符串：
        #    `datetime.now(timezone.utc).isoformat()` 带 `+00:00`，
        #    裸拼进 query 时那个 `+` 会被当成空格 → PostgREST 报
        #    `invalid input syntax for type timestamp: "... 00:00"`，
        #    整个查询 400、活跃用户恒为 0 —— 而且看起来像「今天没人活跃」。
        #    （2026-10-08 实测踩到；`agents/tuning.py:_active_users` 走的就是 params。）
        res = await client.get(
            f"{settings.SUPABASE_URL}/rest/v1/user_actions",
            headers=headers,
            params={"select": "user_id", "action_at": f"gte.{since}", "limit": "5000"})
        if res.status_code != 200:
            # 不静默：查不到就说清楚，否则调用方只会看到"今天没有活跃用户"
            logger.warning(f"[daily] 取活跃用户失败 [{res.status_code}]: {res.text[:200]}")
            return []
        user_ids = sorted({r.get("user_id") for r in (res.json() or []) if r.get("user_id")})
        if not user_ids:
            return []

        # 分批查 profiles（每批 100，避免 URL 超长）
        profiles: list[dict] = []
        for i in range(0, len(user_ids), 100):
            ids = ",".join(f'"{uid}"' for uid in user_ids[i:i + 100])
            profile_url = (f"{settings.SUPABASE_URL}/rest/v1/profiles?id=in.({ids})"
                           f"&select=id,learning_stage,grade,major,learning_goal,nickname")
            profile_res = await client.get(profile_url, headers=headers)
            if profile_res.status_code == 200:
                profiles.extend(profile_res.json() or [])
            else:
                logger.warning(f"[daily] 取用户资料失败 [{profile_res.status_code}]: "
                               f"{profile_res.text[:200]}")
        return profiles


async def get_user_yesterday_activity(user_id: str) -> dict:
    """获取用户昨日学习数据"""
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
    }
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 查昨日掌握度变化（简化：取最近更新的题目）
        url = f"{settings.SUPABASE_URL}/rest/v1/questions?user_id=eq.{user_id}&select=topic,mastery_score&limit=50"
        res = await client.get(url, headers=headers)
        questions = res.json() if res.status_code == 200 else []

        # 查学程动作（activities 表从未建过 → 恒空；真实表是 user_actions）
        actions_url = (f"{settings.SUPABASE_URL}/rest/v1/user_actions?user_id=eq.{user_id}"
                       f"&select=action_type,action_at&order=action_at.desc&limit=20")
        actions_res = await client.get(actions_url, headers=headers)
        activities = actions_res.json() if actions_res.status_code == 200 else []

        # 统计
        topic_scores = {}
        for q in questions:
            t = q.get("topic") or "未分类"
            s = q.get("mastery_score", 0)
            if t not in topic_scores:
                topic_scores[t] = []
            topic_scores[t].append(s)

        avg_mastery = 0
        if topic_scores:
            # ⚠️ 2026-10-08 修：原来是 `sum((sum(s) for s in topic_scores.values()), [])`。
            #    `topic_scores` 的值是**分数列表**（{'foo': [80, 60]}），内层 `sum(s)`
            #    已经把列表压成一个 int，外层再拿 `[]` 去「拼」int →
            #    TypeError: can only concatenate list (not "int") to list。
            #    本意是拍平，直接 `sum(values, [])` 就是拍平。
            #    **这条路径从来没被跑过**（每日推荐只挂在手动调试端点上），
            #    所以这个崩溃一直没暴露 —— 一旦真推给用户就是 100% 失败。
            all_scores = sum(topic_scores.values(), [])
            avg_mastery = round(sum(all_scores) / len(all_scores)) if all_scores else 0

        weak = [t for t, scores in topic_scores.items() if sum(scores) / len(scores) < 50][:3]
        improved = [t for t, scores in topic_scores.items() if sum(scores) / len(scores) >= 80][:3]

        return {
            "question_count": len(questions),
            "avg_mastery": avg_mastery,
            "weak_topics": weak,
            "strong_topics": improved,
            "recent_activities": activities[:5],
        }


async def generate_daily_summary(user: dict) -> dict | None:
    """为单个用户生成昨日学习总结（**结构化**，2026-10-08 重做）。

    ⚠️ 改造前是把数字交给 LLM，让它复述成一段 150 字散文。结果：

        「昨天你完成了50道题，这份坚持很棒。整体掌握度9%，说明……别着急。
          Shell编程、文件操作和切片赋值的长度变化是你目前的薄弱点。建议……」

    **精确数据全埋在句子里**：题数、掌握度、薄弱点后端本来就**如实算出来了**
    （`get_user_yesterday_activity`），却让模型用自然语言再讲一遍 ——
    又丑（前端只能当一整块文本渲染）、又不可靠（模型可能说错数）。

    现在拆开：
      · **数字**由后端**原样带入** payload.stats，前端用卡片渲染
      · **薄弱/擅长知识点**是数组，前端渲染成标签
      · LLM **只写三段文字**：点评 / 建议 / 鼓励

    LLM 挂了也不丢整条：退回**确定性文案**（数字仍然是真数据）。
    """
    try:
        activity = await get_user_yesterday_activity(user["id"])
        if activity["question_count"] == 0:
            return None

        weak = [t for t in (activity.get("weak_topics") or []) if t]
        strong = [t for t in (activity.get("strong_topics") or []) if t]
        mastery = activity["avg_mastery"]
        count = activity["question_count"]

        profile_desc = f"{user.get('learning_stage', '未知')} {user.get('grade', '')}".strip()

        prompt = f"""你是一位温暖的学习助手"基智"，要给一位学生写**昨日学习总结的文字部分**。

学生背景：{profile_desc}
昨日真实数据（**不要复述这些数字**，前端会用卡片单独展示）：
- 完成题目：{count} 道
- 整体掌握度：{mastery}%
- 薄弱知识点：{'、'.join(weak) or '暂无'}
- 擅长知识点：{'、'.join(strong) or '暂无'}

请只写三段文字，返回严格 JSON：
{{
  "note": "一句点评（40字内）。针对掌握度与实际表现给客观判断，不要「你很棒」这种空话",
  "suggestion": "一条今天就能做的具体建议（60字内）。要具体到动作，不要「多加练习」这种空话",
  "encouragement": "一句鼓励（25字内）。真诚，不油腻"
}}

只返回 JSON，不要额外文字。"""

        prose = None
        try:
            raw = call_llm([
                {"role": "system", "content": "你是基智学习助手，说话温暖简洁。只返回 JSON。"},
                {"role": "user", "content": prompt},
            ], temperature=0.6)
            prose = _extract_json(raw)
        except Exception as e:                                  # noqa: BLE001
            logger.warning(f"[daily_summary] LLM 生成失败，用确定性文案: {e}")

        # 三段文字任一缺失就用兜底补上 —— **数字始终是真数据**，那才是重点
        note = (prose or {}).get("note") or _fallback_note(mastery)
        suggestion = (prose or {}).get("suggestion") or _fallback_suggestion(weak)
        encouragement = (prose or {}).get("encouragement") or "明天继续。"

        # 列表页显示的正文摘要（详情页渲染的是 payload，这里给没渲染能力的端兜底）
        digest = f"完成 {count} 道题，整体掌握度 {mastery}%。{note}"

        return {
            "user_id": user["id"],
            "type": "daily_summary",
            "title": "昨日学习总结",
            "content": digest,
            "summary": f"掌握度 {mastery}% | {count} 题",
            # ⚠️ 原来这里是 action_label / action_link。那两列表里有，但 `notify()`
            #    不写（全站统一走 `link`），所以写在这儿落不了库
            #    （同 daily_rec 那个静默 no-op 的坏链）。统一走 link。
            "link": "/career",
            "payload": {
                "kind": "summary",
                "stats": {"questions": count, "mastery": mastery},
                "weak": weak[:6],
                "strong": strong[:6],
                "note": note,
                "suggestion": suggestion,
                "encouragement": encouragement,
            },
            "is_read": False,
        }
    except Exception as e:
        logger.info(f"[WARNING] 生成总结失败 user={user['id']}: {e}")
        return None


def _extract_json(raw: str) -> dict | None:
    """从模型返回里抠出 JSON（括号计数法，容忍前后有说明文字）。"""
    if not raw:
        return None
    start = raw.find("{")
    if start < 0:
        return None
    depth, in_str, esc, end = 0, False, False, -1
    for i in range(start, len(raw)):
        ch = raw[i]
        if esc:
            esc = False
            continue
        if ch == "\\":
            esc = True
            continue
        if ch == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end <= 0:
        return None
    try:
        import json as _json
        got = _json.loads(raw[start:end])
        return got if isinstance(got, dict) else None
    except Exception as e:                                      # noqa: BLE001
        logger.warning(f"[daily_summary] LLM 返回的 JSON 解析失败: {e}")
        return None


def _fallback_note(mastery: int) -> str:
    if mastery >= 80:
        return "掌握得挺扎实，这个节奏可以保持。"
    if mastery >= 60:
        return "大体上跟上了，还有几处需要巩固。"
    if mastery >= 40:
        return "有些地方还没吃透，先别急着往前赶。"
    return "这些内容对你来说还比较新，别着急。"


def _fallback_suggestion(weak: list) -> str:
    if weak:
        return f"今天挑「{weak[0]}」单独做 5 道题，做完对着解析过一遍。"
    return "今天先做 5 道题，做完对着解析过一遍。"


def _focus_candidates(user: dict, activity: dict, source: str) -> tuple[list, str]:
    """按设置决定「先推什么、再推什么」→ ([(知识点, 依据说明), ...], 实际依据)。

    两种依据：
      profile —— 按个人信息：学习阶段 / 年级 / 专业 / 学习目标
      history —— 按以往做题记录：薄弱知识点（`get_user_yesterday_activity` 算出来的）

    ⚠️ 两条回落规则是必须的，否则会出现「选了一种依据但凑不出内容 → 永远不发」：
      选 history 但一条做题记录都没有 → 退回 profile
      选 profile 但资料没填全        → 退回 history
    两边都空 → 返回空列表，调用方不发（宁缺毋滥，不发空壳推荐）。

    ⚠️ **为什么返回一串而不是一个**（2026-10-08 实测）：依据挑出的知识点**未必在
    题库里有题** —— topic 来自 `questions` 表的 AI 生成题 topic，而
    `kp_questions.score_by_kp` 匹配的是题库的 `kp_name`，**是两套词汇**。
    实测 9 个真实 topic 里有 3 个一道题都搜不到（'Shell编程'、'切片赋值的长度变化影响'、
    '比较大小'）。只试第一个的话，约 **1/3 的用户会永远收不到推荐** ——
    正是上面那条回落规则想防的同一类病，只是换了个地方发作。
    """
    weak = [t for t in ((activity or {}).get("weak_topics") or []) if t]
    goal = (user.get("learning_goal") or "").strip()
    stage = (user.get("learning_stage") or "").strip()
    grade = (user.get("grade") or "").strip()
    major = (user.get("major") or "").strip()
    has_profile = bool(goal or stage or grade or major)

    if source == "history" and not weak:
        logger.info(f"[daily_rec] 选了 history 但无做题记录 → 回落 profile user={user['id']}")
        source = "profile"
    elif source == "profile" and not has_profile:
        logger.info(f"[daily_rec] 选了 profile 但资料为空 → 回落 history user={user['id']}")
        source = "history"
    elif source == "mix":
        source = "history" if weak else "profile"

    out: list = []
    if source == "history":
        out = [(t, f"依据你的做题记录：{t} 是最近最薄弱的知识点") for t in weak]
    else:
        # 资料取向：用学习目标/阶段当焦点，而不是错题。
        # 同一个词可能同时来自多个字段 → 去重保序。
        seen = set()
        basis = f"依据你的学习资料：{stage}{grade} · 目标 {goal or '未设置'}"
        for t in (goal, f"{stage}{grade}".strip(), major):
            if t and t not in seen:
                seen.add(t)
                out.append((t, basis))
    return out, source


# ---- 时间口径 ----
# ⚠️ 「今天」一律按**北京时间**算。服务器上 `datetime.now()` 大概率是 UTC，
#    直接拿它切日期，凌晨 0-8 点发出的推荐会被算成前一天
#    （`routers/xiaoji.py` 早就为这个踩过坑，那里也定义了 BEIJING）。
BEIJING = timezone(timedelta(hours=8))


def beijing_now() -> datetime:
    return datetime.now(BEIJING)


def today_key() -> str:
    """北京时间的今天，`YYYY-MM-DD`。用作「一天一条」的键。"""
    return beijing_now().strftime("%Y-%m-%d")


def now_hm() -> str:
    """北京时间的当前时刻 `HH:MM`，用来和用户设的发送时间比。"""
    return beijing_now().strftime("%H:%M")


async def has_today(user_id: str, notif_type: str) -> bool:
    """今天这条已经生成过了吗。

    **生成之前必须先问这一句**，两个理由：
      1. 省 LLM —— 推荐和总结都要调模型，重复生成是真金白银
      2. `learning.daily_rec` 不是聚合类型，同一天再发一次会撞未读聚合的
         部分唯一索引 → 409 → 非聚合类型**不走聚合回退、直接抛 NotifyError**
         （10-08 在 social.rank_pass 上踩过同一个坑）
    """
    since = beijing_now().strftime("%Y-%m-%dT00:00:00+08:00")
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/notifications",
                headers={"apikey": settings.SUPABASE_KEY,
                         "Authorization": f"Bearer {settings.SUPABASE_KEY}"},
                params={"user_id": f"eq.{user_id}", "type": f"eq.{notif_type}",
                        "created_at": f"gte.{since}", "select": "id", "limit": "1"})
        if res.status_code == 200:
            return bool(res.json())
        # 查不到就**当成没发过**：宁可多发一条（用户能删），不可因此漏发一整天
        logger.warning(f"[daily] 查今日是否已生成失败 [{res.status_code}]: {res.text[:200]}")
    except Exception as e:                                      # noqa: BLE001
        logger.warning(f"[daily] 查今日是否已生成异常: {e}")
    return False


def time_reached(user_time: str, now: str = None) -> bool:
    """用户的发送时间到了吗。格式 `HH:MM`；值不合法就当成「随时可发」。

    ⚠️ 用 `>=` 而不是 `==`：轮询是每 10 分钟一轮，`==` 会错过时间点；
    而且服务器重启/挂掉期间错过的那些，`>=` 能在下一轮补上。
    """
    t = (user_time or "").strip()
    if len(t) < 4 or ":" not in t:
        return True
    return (now or now_hm()) >= t[:5]


# ---- 三合一的档位（2026-10-08 定）----
# ⚠️ 这四个数**注册表和设计文档都没给**，是本轮拍的。按 10-08 的教训收在一处并点名，
#    不要散在判定式里假装它本来就该是 3。
DAILY_Q_COUNT = 3           # 每次推荐几道题（§六 说 3~5，取下限：宁少勿滥）
DONE_LOOKBACK_DAYS = 30     # 查多久内做过的题来排除
MINUTES_BASE = 5            # 时长粗估：内容块底 5 分钟
MINUTES_PER_Q = 2           # 每道题 2 分钟


async def _recent_done_ids(user_id: str) -> set:
    """该用户最近做过的题目 id —— 免得推荐刚做过的题。

    ⚠️ 无计划路径上**没有现成的排除集**：`subject_plan._get_done_ids` 依赖
    `plan_id`，而每日推荐不挂在任何计划上。所以这里直接查 `question_records` ——
    计划里的题和随机来的题都写这张表（`plan_id` 为空的链路 10-01 已打通）。
    """
    since = (datetime.now(timezone.utc) - timedelta(days=DONE_LOOKBACK_DAYS)).isoformat()
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # ⚠️ 走 params 编码，别把带 `+00:00` 的时间戳拼进 URL ——
            #    那个 `+` 会变成空格、整个查询 400（同 get_active_users 的坑）
            res = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/question_records",
                headers={"apikey": settings.SUPABASE_KEY,
                         "Authorization": f"Bearer {settings.SUPABASE_KEY}"},
                params={"user_id": f"eq.{user_id}", "created_at": f"gte.{since}",
                        "select": "question_id", "limit": "2000"})
        if res.status_code == 200:
            return {r.get("question_id") for r in (res.json() or []) if r.get("question_id")}
        logger.warning(f"[daily_rec] 取已做题失败 [{res.status_code}]: {res.text[:200]}")
    except Exception as e:                                      # noqa: BLE001
        logger.warning(f"[daily_rec] 取已做题异常: {e}")
    return set()


def _pack_questions(rows: list) -> list:
    """把检索结果压成 payload 的题目块。

    ⚠️ **必须带 `syllabus_id`**：题库 18,711 题里 **497 个 id 横跨多个库**
    （见 `local_question_bank.find_question_unique` 的说明）。做题端靠
    `syllabus_id` 定位题目，不带它就会跨库猜 —— **拿 A 科目的题判 B 科目的分**。
    §六 给的 schema 漏了这个字段，这里补上。

    `stem` 只存 120 字摘要（列表要显示），做题时再按 qid 拉完整题面。
    """
    out = []
    for q in rows or []:
        qid = str(q.get("id") or "")
        if not qid:
            continue
        out.append({
            "qid": qid,
            "stem": q_stem_text(q)[:120],
            "type": q.get("question_type") or "choice",
            "difficulty": q.get("difficulty_score") or q.get("difficulty"),
            "syllabus_id": q.get("syllabus_id") or "",
        })
    return out


async def _pick_video_block(topic: str, subject: str = "") -> dict | None:
    """视频块 —— **只命中复用，绝不排产**（§六 明确要求）。

    ⚠️ 用的是 `video_gen.find_ready_video`（纯只读），**不是** `ensure_videos`：
    后者查不到就插一行 `generating` 并丢进生成队列，一次给全体用户排产
    会把 worker 压垮。命中不到就返回 None，这一块空着。
    """
    from services import video_gen
    try:
        row = await video_gen.find_ready_video(knowledge_name=topic, subject=subject)
    except Exception as e:                                      # noqa: BLE001
        logger.warning(f"[daily_rec] 找视频失败 topic={topic}: {e}")
        return None
    if not row:
        return None
    # ⚠️ 时长列叫 `audio_duration`（秒，浮点），**不是 `duration`** ——
    #    实测拉一行才确认（查 `duration` 直接 400 column does not exist）。
    return {
        "video_id": row.get("id"),
        "title": row.get("title") or row.get("knowledge_name") or topic,
        "duration": _fmt_duration(row.get("audio_duration")),
        "duration_sec": row.get("audio_duration") or 0,
        "state": row.get("status") or "",
    }


def _fmt_duration(sec) -> str:
    """秒 → `M:SS`（卡片上显示「讲解视频 · 2:14」）。拿不到就返回空串。"""
    try:
        total = int(round(float(sec)))
    except (TypeError, ValueError):
        return ""
    if total <= 0:
        return ""
    return f"{total // 60}:{total % 60:02d}"


async def generate_daily_recommendation(user: dict) -> dict | None:
    """为单个用户生成每日推荐。

    ⚠️ 依据来源由 `notification_settings.daily_rec_source` 决定（profile / history / mix），
    用户在设置页里选 —— 见 message_center_design.md §六。
    """
    try:
        from utils.notification import get_settings
        cfg = await get_settings(user["id"])
        source = (cfg.get("daily_rec_source") or "mix").strip() or "mix"

        activity = await get_user_yesterday_activity(user["id"])
        candidates, source = _focus_candidates(user, activity, source)
        if not candidates:
            logger.info(f"[daily_rec] 依据凑不出内容，今天不发 user={user['id']} source={source}")
            return None

        # ---- 三件套（message_center_design.md §六）----
        # ② 题目：按知识点检索，排除近 30 天做过的
        # ③ 视频：只命中复用（find_ready_video 内部绝不排产）
        #
        # ⚠️ **候选要一个个试**：依据给出的知识点未必在题库里有题（两套词汇，
        #    见 `_focus_candidates` 的说明）。只试第一个的话约 1/3 的用户
        #    永远收不到推荐。试到能凑出至少一块为止。
        done = await _recent_done_ids(user["id"])
        topic, basis, questions, video, kp_id = "", "", [], None, ""
        for cand, cand_basis in candidates[:5]:
            q_rows = score_by_kp(cand, limit=DAILY_Q_COUNT, exclude_ids=done)
            qs = _pack_questions(q_rows)
            vid = await _pick_video_block(cand, qs[0].get("syllabus_id") if qs else "")
            if not qs and not vid:
                logger.info(f"[daily_rec] 「{cand}」题库与视频都没有，试下一个 user={user['id']}")
                continue
            topic, basis, questions, video = cand, cand_basis, qs, vid
            # kp_id 从命中的题里取 —— 依据只给得出知识点名，给不出 id
            kp_id = str((q_rows[0].get("kp_id") or q_rows[0].get("sub_category")) if q_rows else "")
            break

        # ⚠️ 空则不发：题目与视频**至少得有一块**。
        #    只有内容块 = 退化成改造前那段 120 字文字，那条路本来就没效果。
        if not topic:
            logger.info(f"[daily_rec] 候选知识点全都没内容，今天不发 "
                        f"user={user['id']} 候选={len(candidates)} 个")
            return None

        profile_desc = f"{user.get('learning_stage', '未知')} {user.get('grade', '')}"
        goal = user.get("learning_goal", "未设置")

        prompt = f"""你是学习助手"基智"。为用户推荐一个学习内容。

用户：{profile_desc}，{user.get('major', '')}专业，目标：{goal}
本次推荐的依据：{basis}
推荐的知识点：{topic}

要求：
1. 推荐一个具体的学习方向
2. 解释为什么这个知识点重要
3. 给出一个学习小技巧
4. 总字数 120 字以内
5. 纯文本，不用 Markdown"""

        ai_rec = call_llm([
            {"role": "system", "content": "你是基智学习助手，推荐简洁实用。"},
            {"role": "user", "content": prompt}
        ], temperature=0.7)

        minutes = MINUTES_BASE + MINUTES_PER_Q * len(questions)
        return {
            "user_id": user["id"],
            "type": "daily_rec",
            "title": f"今日推荐：{topic}",
            "content": ai_rec.strip(),
            "summary": basis,
            # ⚠️ 落点是 `/daily-learn`，**不带 id**：`notify()` 是「先 INSERT 再返回
            #    row id」，而 link 在插入那一刻就要定，拿不到自己的 id。
            #    所以路由写成可选 id（不带就取最新一条），卡片跳不带 id 的那个。
            "link": "/daily-learn",
            # ⚠️ 以前这里写的是 action_link / action_label。那两列**表里是有的**
            #    （建表时的老列），但 `notify()` 不写它们 —— 全站统一走 `link`。
            #    所以写在这里等于没写：xiaoji.py 读出来恒为空，卡片按钮点了没反应。
            #    统一走 link，别再改回去。
            "payload": {
                "content": {"title": topic, "kp_id": kp_id,
                            "minutes": minutes, "basis": basis},
                "questions": questions,
                "video": video,
                "progress": {"content": False, "questions": False, "video": False},
            },
            "is_read": False,
        }
    except Exception as e:
        logger.info(f"[WARNING] 生成推荐失败 user={user['id']}: {e}")
        return None


# ============================================================
# 两个生成逻辑的统一入口
#
# 「两个逻辑」= **每日学习推荐**（三合一）+ **每日总结**。两条各有自己的
# 开关与发送时间（`message_center_design.md` §十「加两个独立项」）：
#
#     daily_rec_enabled / daily_rec_time          默认 08:00
#     daily_summary_enabled / daily_summary_time  默认 07:00
#
# ⚠️ §十 原话：「**后端必须真的读这些开关**（现在没有任何代码读它们 ——
#    开关全是装饰，这是本轮要修的）」。本节的 deliver() 就是那个"真的读"。
#    此前 `daily_rec_time` 建了列、设置页收了也发了，但全仓零消费方。
# ============================================================

KINDS = {
    "rec": {
        "type": "learning.daily_rec",
        "switch": "daily_rec_enabled",
        "time_key": "daily_rec_time",
        "label": "每日学习推荐",
        "gen": generate_daily_recommendation,
        "link": "/daily-learn",
    },
    "summary": {
        "type": "learning.daily_summary",
        "switch": "daily_summary_enabled",
        "time_key": "daily_summary_time",
        "label": "每日总结",
        "gen": generate_daily_summary,
        "link": "/career",
    },
}


async def get_user_profile(user_id: str) -> dict | None:
    """取单个用户的资料（推荐/总结的 prompt 要阶段、年级、专业、目标）。

    手动生成那条路只有一个 user_id，拿不到 `get_active_users()` 里的资料 ——
    用它补齐，免得自己再造一份查询。
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/profiles",
                headers={"apikey": settings.SUPABASE_KEY,
                         "Authorization": f"Bearer {settings.SUPABASE_KEY}"},
                params={"id": f"eq.{user_id}",
                        "select": "id,learning_stage,grade,major,learning_goal,nickname",
                        "limit": "1"})
        rows = res.json() if res.status_code == 200 else []
        return rows[0] if rows else None
    except Exception as e:                                      # noqa: BLE001
        logger.warning(f"[daily] 取用户资料异常 {user_id}: {e}")
        return None


async def deliver(user: dict, kind: str, force: bool = False) -> str:
    """给一个用户发某一种每日消息，返回一句状态码：

        sent           发出去了
        skipped_off    用户把这个开关关了
        skipped_done   今天已经生成过了 ← 「检测到今日已生成就不再生成」就是这条
        skipped_time   还没到用户设定的时间（force=True 时不做这个判断）
        no_content     生成器凑不出内容（宁缺毋滥，按设计不发）
        error          写入通知失败（已记 ERROR）

    返回状态码而不是 bool，是为了让调度器打得出有信息量的日志 ——
    「今天一个都没发」和「发了 3 个」的区别，全在这些码里。
    """
    k = KINDS[kind]
    from utils.notification import get_settings
    cfg = await get_settings(user["id"])

    if not cfg.get(k["switch"], True):
        return "skipped_off"
    if await has_today(user["id"], k["type"]):
        return "skipped_done"
    if not force and not time_reached(cfg.get(k["time_key"])):
        return "skipped_time"

    notification = await k["gen"](user)
    if not notification:
        return "no_content"

    try:
        await notify(user["id"], k["type"],
                     source_id=f"{kind}_{today_key()}",
                     title=notification["title"], content=notification["content"],
                     link=notification.get("link") or k["link"],
                     payload=notification.get("payload"))
    except (NotifyError, KeyError) as e:
        logger.error(f"⚠️ {k['label']}未送达 user={user['id']}: {e}")
        return "error"
    return "sent"


async def run_daily(kind: str, user_id: str = None, force: bool = False) -> dict:
    """给「全部活跃用户」或指定的一个用户跑某一种每日消息。

    `force=True` 只忽略**发送时间**（手动端点用），**不去重** ——
    「今天已经生成过了」对谁都成立：用户要的是「点一次就有一条」，
    不是「点一次多一条」。去重那一层在 `deliver()` 里，绕不过去。
    """
    users = await get_active_users()
    if user_id:
        users = [u for u in users if u["id"] == user_id]
        # 手动指定的人可能不在「近 7 天活跃」里（比如刚注册、或沉寂了一阵），
        # 那就单独补一次资料 —— 否则「生成今日推荐」对自己点会毫无反应
        if not users:
            prof = await get_user_profile(user_id)
            if prof:
                users = [prof]
    if not users:
        return {"generated": 0, "total": 0, "message": "没有符合条件的用户"}

    k = KINDS[kind]
    logger.info(f"[daily] 开始生成{k['label']}，共 {len(users)} 个用户")
    tally: dict = {}
    for user in users:
        r = await deliver(user, kind, force=force)
        tally[r] = tally.get(r, 0) + 1
    logger.info(f"[daily] {k['label']}完成：{tally}")
    return {"generated": tally.get("sent", 0), "total": len(users), "detail": tally}


async def run_daily_summary(user_id: str = None, force: bool = False) -> dict:
    """执行昨日总结生成（支持指定用户或全部）"""
    return await run_daily("summary", user_id, force)


async def run_daily_recommendation(user_id: str = None, force: bool = False) -> dict:
    """执行每日推荐生成"""
    return await run_daily("rec", user_id, force)
