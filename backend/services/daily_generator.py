"""
每日推荐 + 昨日学习总结 生成服务
由定时任务或手动 API 触发
"""
import asyncio
import re
import httpx
from datetime import datetime, timedelta, timezone
from config import settings
from agents.llm_client import call_llm
from services.supabase import get_supabase_service_headers
from services import summary_copy
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


# ============================================================
# 学习总结的时间窗口
#
# ⚠️ 2026-10-16 之前这个函数叫「昨日」，但**根本没有日期过滤** ——
#    取的是 questions 表里该用户的**全历史**，还是 `limit=50` 截断的前 50 条：
#      · 完成题数 = min(真实行数, 50) → 真实做了 231 题的用户也显示「完成 50 道题」
#      · 没写 order= → 每次取到的是哪 50 条不确定 → 掌握度在 0 / 9 / 56 之间跳
#      · mastery_score 对绝大多数行是**从没写过的默认 0**，不是"答了 0 分"
#    真库实测：19 条总结里 16 条写着「完成 50 道题」，而全站最新一条作答是 9 天前。
#
#    改按 N 天窗口 + 真实计数。窗口取 7 天是因为按「昨日」严格算的话，
#    现在这个活跃度下**全站没人收得到总结**（真库实测某日 0 条作答）。
# ============================================================
SUMMARY_WINDOW_DAYS = 7

# 「学习行为」白名单 —— 只数**真的产生或消费了学习内容**的动作。
#
# ⚠️ **必须是白名单，不能是黑名单。** user_actions 里 login / view_career /
#    update_nickname 这类纯导航与账号动作占了很大比例（真库实测 login 229 次、
#    view_career 230 次，各占两成以上）。全算进去的话，一个这周一次题都没做、
#    只是天天登录的用户会收到「最近 7 天学习 14 次」—— 那正是这次要修的那类假数字。
#
#    新出现的动作类型默认**不算**学习；要算就显式加到这里，顺便回答一次
#    「它到底是不是学习」。
#
# ⚠️ 这份白名单是照着 user_actions 里**实际出现过的 30 种类型**逐个判的
#    （2026-10-16 真库枚举），不是拍脑袋列的。加漏一种的后果是那个动作
#    在总结里彻底消失 —— 比如 `complete_question`（完成题目）漏掉的话，
#    认真做题的人反而显示"零学习行为"。
LEARNING_ACTIONS = {
    # 出题 / 做题 / 错题
    "generate_question", "complete_question", "conquer_mistake",
    # 对话与四类智能体
    "chat", "use_plan_agent", "use_generate_agent",
    "use_evaluate_agent", "xiaoji_tool",
    # 视频与词条
    "generate_video", "watch_video", "wordbook_lookup",
    # 题集 / 计时 / 摸底诊断
    "create_set", "add_to_set", "use_timer", "timer_complete", "diagnosis_done",
    # 看自己的学习数据（掌握度看板 / 报告）
    "view_mastery", "view_report",
}
# 判过的、**故意不算**的（写在这儿免得下次有人再纠结一遍）：
#   login / change_password / update_nickname / update_bio / update_avatar
#     / change_status —— 账号与个人资料操作
#   view_career —— 学程页（排行/成就），是激励页不是学习内容；而且它是
#     全站最高频动作（230/925），放进来会把"学习行为"整个稀释掉
#   checkin / claim_achievement —— 签到与领成就，是激励不是学习
#   test_direct / __probe_write__ —— 测试与探针写进去的脏数据

# 只用于给模型读的中文名（数字仍然是后端算的，这里只影响措辞）
LEARNING_ACTION_LABEL = {
    "generate_question": "出题",
    "complete_question": "完成题目",
    "conquer_mistake": "攻克错题",
    "chat": "和小基对话",
    "use_plan_agent": "用计划智能体",
    "use_generate_agent": "用生成智能体",
    "use_evaluate_agent": "用评估智能体",
    "xiaoji_tool": "用小基工具",
    "generate_video": "生成讲解视频",
    "watch_video": "看讲解视频",
    "wordbook_lookup": "查词条",
    "create_set": "建题集",
    "add_to_set": "加题集",
    "use_timer": "用专注计时",
    "timer_complete": "完成一次专注",
    "diagnosis_done": "做完摸底诊断",
    "view_mastery": "看掌握度看板",
    "view_report": "看学习报告",
}


async def get_user_recent_activity(user_id: str, days: int = SUMMARY_WINDOW_DAYS) -> dict:
    """最近 N 天的真实学习数据。三张表，**全部如实计数，不做任何推算**。

    对应技术报告里的两条闭环链，分开取数：
      · 资源库链   → `questions`（AI 逐题评分，`source=generated`）
      · 学科计划链 → `user_kp_mastery`（EWMA 累计）
      另加 `user_actions` 的行为流水。

    ⚠️ **掌握度只统计 mastery_score > 0 的行。**
       那个字段对大多数行从没被写过，默认值就是 0（真库实测：470 行里 345 行
       mastery_score=0 且 `is_mistake` 也不是 true —— 按技术报告写的规则，
       真的答错会被标 is_mistake，所以那些 0 是**缺失**，不是"零分"）。
       把缺失值当零分平均，结论必然错，而且是**往"你很差"的方向错**：
       用户会收到「掌握度为零说明基础概念还没打通，先别急着刷题」这种话。
       一行有效评分都没有时返回 None，前端显示「—」而不是 0%。

    ⚠️ 三个查询都走 **service_role**：原实现用的是 anon key，RLS 一旦收紧就会
       静默返回空列表，总结会变成"你这周什么都没做"——那种错比报错更难查。
    """
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    headers = get_supabase_service_headers()
    base = f"{settings.SUPABASE_URL}/rest/v1"

    async def fetch(path: str, params: dict, label: str):
        """取一张表。失败返回 None（与"真的是空"区分开）。"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as c:
                r = await c.get(f"{base}/{path}", params=params, headers=headers)
            if r.status_code != 200:
                logger.warning("[summary] %s 查询失败 status=%s body=%s",
                               label, r.status_code, r.text[:200])
                return None
            return r.json()
        except Exception as e:                                    # noqa: BLE001
            logger.warning("[summary] %s 查询异常 %s: %s", label, type(e).__name__, e)
            return None

    questions, kp_rows, actions = await asyncio.gather(
        fetch("questions",
              {"user_id": f"eq.{user_id}", "created_at": f"gte.{since}",
               "select": "topic,normalized_topic,mastery_score,is_mistake,source"},
              "资源库链·作答"),
        fetch("user_kp_mastery",
              {"user_id": f"eq.{user_id}", "last_practiced_at": f"gte.{since}",
               "select": "kp_name,mastery_score,correct_count,total_count"},
              "学科计划链·知识点"),
        # ⚠️ 取 action_at 不是为了显示，是为了**算出真实的天数分布**。
        #    不取的话模型只能看到"7 次"，然后自己脑补成"连着走了七天"
        #    —— 实测真的这么写过。与其禁止它推断，不如把真相给它。
        fetch("user_actions",
              {"user_id": f"eq.{user_id}", "action_at": f"gte.{since}",
               "select": "action_type,action_at"},
              "行为流水"),
    )

    sources_ok = {
        "questions": questions is not None,
        "kp": kp_rows is not None,
        "actions": actions is not None,
    }
    questions = questions or []
    kp_rows = kp_rows or []
    actions = actions or []

    # ── 资源库链：按知识点聚合**有效评分** ──
    topic_scores: dict[str, list] = {}
    scored = 0
    for q in questions:
        s = q.get("mastery_score") or 0
        if s <= 0:
            continue                     # 缺失值，跳过（理由见上面的大段说明）
        scored += 1
        t = q.get("normalized_topic") or q.get("topic") or "未分类"
        topic_scores.setdefault(t, []).append(s)

    avg_mastery = None
    if topic_scores:
        all_scores = sum(topic_scores.values(), [])
        avg_mastery = round(sum(all_scores) / len(all_scores))

    def topic_avg(scores):
        return sum(scores) / len(scores)

    ranked = sorted(topic_scores.items(), key=lambda kv: topic_avg(kv[1]))
    weak = [t for t, s in ranked if topic_avg(s) < 60][:6]
    strong = [t for t, s in ranked if topic_avg(s) >= 80][:6]

    # ── 学科计划链：EWMA 掌握度（这一列是逐次递推出来的真值，不是缺失）──
    kp_topics = [{"name": k.get("kp_name") or k.get("kp_id") or "未命名知识点",
                  "mastery": round(k.get("mastery_score") or 0),
                  "correct": k.get("correct_count") or 0,
                  "total": k.get("total_count") or 0}
                 for k in kp_rows]
    kp_topics.sort(key=lambda k: k["mastery"])

    # ── 行为：区分「全部动作」与「学习动作」──
    learning = [a for a in actions if a.get("action_type") in LEARNING_ACTIONS]
    breakdown: dict[str, int] = {}
    for a in learning:
        breakdown[a["action_type"]] = breakdown.get(a["action_type"], 0) + 1

    # 学习行为分布在几天里（**按北京时间切天**，与全站口径一致）。
    #
    # ⚠️ 这个数必须真算出来给模型 —— 不给的话它会拿"7 次"编成"连着走了七天"，
    #    而那可能完全是假的（一天做完 7 次和连着 7 天各做 1 次是两回事）。
    #    「与其禁止推断，不如把真相给它」比写十条禁令都管用。
    active_days = 0
    if learning:
        days_seen = set()
        for a in learning:
            ts = a.get("action_at")
            if not ts:
                continue
            try:
                dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
                days_seen.add(dt.astimezone(timezone(timedelta(hours=8))).strftime("%Y-%m-%d"))
            except (ValueError, AttributeError):
                continue
        active_days = len(days_seen)

    return {
        "days": days,
        "question_count": len(questions),
        "mistake_count": sum(1 for q in questions if q.get("is_mistake") is True),
        "scored_count": scored,
        "avg_mastery": avg_mastery,
        "weak_topics": weak,
        "strong_topics": strong,
        "kp_topics": kp_topics[:6],
        "action_count": len(actions),           # 全部动作（含登录等）
        "learning_count": len(learning),        # 只算学习动作
        "action_breakdown": breakdown,
        "active_days": active_days,             # 学习行为铺在几天里（真实切天）
        "sources_ok": sources_ok,
    }


async def generate_daily_summary(user: dict) -> dict | None:
    """为单个用户生成昨日学习总结（**结构化**，2026-10-08 重做）。

    ⚠️ 改造前是把数字交给 LLM，让它复述成一段 150 字散文。结果：

        「昨天你完成了50道题，这份坚持很棒。整体掌握度9%，说明……别着急。
          Shell编程、文件操作和切片赋值的长度变化是你目前的薄弱点。建议……」

    **精确数据全埋在句子里**：题数、掌握度、薄弱点后端本来就**如实算出来了**
    （`get_user_recent_activity`），却让模型用自然语言再讲一遍 ——
    又丑（前端只能当一整块文本渲染）、又不可靠（模型可能说错数）。

    现在拆开：
      · **数字**由后端**原样带入** payload.stats，前端用卡片渲染
      · **薄弱/擅长知识点**是数组，前端渲染成标签
      · LLM **只写三段文字**：点评 / 建议 / 鼓励

    LLM 挂了也不丢整条：退回**确定性文案**（数字仍然是真数据）。
    """
    try:
        activity = await get_user_recent_activity(user["id"])
        # 窗口内真的一件**学习**的事都没做 → 不发。
        # ⚠️ 用的是 learning_count 而不是 action_count：光登录了 10 次不算学习，
        #    给这种人发"学习总结"就是噪音（而且会逼着总结去编内容）。
        #    三个来源任一有货就发 —— 计划链练了知识点、或查了词条，都算。
        if (activity["question_count"] == 0 and activity["learning_count"] == 0
                and not activity["kp_topics"]):
            return None
        # 三个来源一个都没取到时**不发**：那说明是查询挂了，不是"这人没学习"。
        # 发出去就是一份"你这周什么都没做"的假总结 —— 比不发伤人得多。
        if not any(activity["sources_ok"].values()):
            logger.warning("[summary] 三个数据源全部取数失败，跳过 user=%s", user["id"])
            return None

        weak = [t for t in (activity.get("weak_topics") or []) if t]
        strong = [t for t in (activity.get("strong_topics") or []) if t]
        mastery = activity["avg_mastery"]      # None = 没有有效评分（不是 0 分）
        count = activity["question_count"]
        scored = activity["scored_count"]
        mistakes = activity["mistake_count"]
        kp_topics = activity["kp_topics"]
        days = activity["days"]
        active_days = activity["active_days"]

        profile_desc = f"{user.get('learning_stage', '未知')} {user.get('grade', '')}".strip()

        # ── 数字卡片：**只放真的算得出来的**，取不到的宁可不显示 ──
        # 技术报告那条原则在这里同样适用：只用真实数据，不推算不放大。
        learning_count = activity["learning_count"]
        breakdown = activity["action_breakdown"]
        breakdown_line = "、".join(
            f"{LEARNING_ACTION_LABEL.get(k, k)} {v} 次"
            for k, v in sorted(breakdown.items(), key=lambda kv: -kv[1])) or "无"

        stats = []
        if count:
            stats.append({"label": "练习题目", "value": count, "unit": "道"})
        if scored:
            stats.append({"label": "掌握度", "value": mastery, "unit": "%",
                          "hint": f"仅统计已批改的 {scored} 道"})
        if mistakes:
            stats.append({"label": "其中错题", "value": mistakes, "unit": "道"})
        if kp_topics:
            stats.append({"label": "计划知识点", "value": len(kp_topics), "unit": "个"})
        if learning_count:
            stats.append({"label": "学习行为", "value": learning_count, "unit": "次",
                          "hint": breakdown_line})
        if not stats:
            # 理论上到不了这里（上面已经拦掉"什么都没做"），兜一下别给前端空数组
            stats.append({"label": "学习行为", "value": learning_count, "unit": "次"})

        # 模型只写文字，数字一律由后端原样带入（同 daily_rec 的分工）
        mastery_line = (f"- 整体掌握度：{mastery}%（只统计已批改的 {scored} 道）"
                        if scored else
                        "- 整体掌握度：**本期没有已批改的作答，这项没有数据**")
        kp_line = ('、'.join(f"{k['name']}({k['mastery']}%)" for k in kp_topics) or '无')

        # ── 三段文字的两种来源：**模型优先，模板兜底** ──
        #
        # 模板库见 services/summary_copy.py。这里的随机是刻意的：
        # 分组每次随机挑一条，范本也每次随机取几条 —— 同一个人连着几天
        # 收到一模一样的句子会立刻出戏，然后再也不点开。
        bucket = summary_copy.bucket_for(
            count=count, scored=scored, mastery=mastery,
            kp_topics=kp_topics, learning_count=learning_count)
        slots = {
            "days": days,
            "count": count,
            "scored": scored,
            # ⚠️ mastery 可能是 None（没有已批改的作答）。填成"—"而不是 0 ——
            #    模板只做字符串插值、不做比较，所以 None 不会让它算错。
            "mastery": mastery if mastery is not None else "—",
            "weak": weak[0] if weak else "薄弱环节",
            "kp": len(kp_topics),
            "behaviors": breakdown_line,
            # ⚠️ {actions} 是**学习行为数**，和 {count}（答题数）是两个东西。
            #    behaviors_only 那几条模板要的是这个 —— 写成 {count} 会得到
            #    「有 0 次学习动作（查词条 3 次、对话 1 次）」这种自相矛盾的句子。
            "actions": learning_count,
        }
        fallback = summary_copy.render(bucket, **slots)

        # ⚠️ 给模型的是**结构**（这段怎么组织），不是成品句子。
        #    成品句子摆在面前模型会照抄 —— 那正是"模板味"的来源。
        #    两种模板的分工见 services/summary_copy.py 的文件头。
        note_struct = summary_copy.structure_for(bucket, "note")
        sug_struct = summary_copy.structure_for(bucket, "suggestion")
        enc_struct = summary_copy.structure_for(bucket, "encouragement")

        prompt = f"""你是一位温暖的学习助手"基智"，要给一位学生写**最近 {days} 天学习总结的文字部分**。

学生背景：{profile_desc}
真实数据（**不要复述这些数字**，前端会用卡片单独展示）：
- 练习题目：{count} 道，其中错题 {mistakes} 道
{mastery_line}
- 薄弱知识点：{'、'.join(weak) or '无'}
- 擅长知识点：{'、'.join(strong) or '无'}
- 计划里的知识点掌握度：{kp_line}
- 学习行为：{learning_count} 次（{breakdown_line}），分布在 {active_days} 天里（共 {days} 天）

**这三段分别要怎么写**（这是结构，不是例子 —— 照着它组织语言，别找现成的句子套）：
· 点评：{note_struct}
· 建议：{sug_struct}
· 鼓励：{enc_struct}

⚠️ 几条硬约束：
1. **不要提到上面没有的数字**，也不要自己换算或估计。
2. 掌握度那项如果写着"没有数据"，就**不要评价掌握度**，改成点评练习量或学习节奏。
3. **不要复述**：具体数值、以及**知识点名**（"需要加强 / 掌握不错 / 计划知识点"
   那几组标签已经把知识点列全了）。你要给的是**判断**，不是把它们再念一遍。
   反例：「错题集中在三角恒等变换和导数定义，说明卡点正是下一步要补的地方」
   —— 前半句是念标签，后半句是同义反复（等于什么都没说）。
   正例：「数列这块已经稳了，导数定义还差一轮巩固」—— 同样是那两个知识点，
   但给的是**程度上的判断**。
4. **不要拔高**。学习行为那行给的是明细（如"完成题目 6 次、和小基对话 3 次"），
   概括时别把聊天、查词条说成"坐下来学"、"刷了一天题"、"一周九次苦读"。
   宁可说得平一点，也别把 3 次聊天算成学习时长。
5. **时间分布以"分布在 N 天里（共 M 天）"那个数为准**，别自己推。
   **「坚持 / 没断 / 一直在」这类话，只在 N 接近 M 时才能说。**
   反例（实测写过）：N=2、M=7 时说「你这周没断线」—— 那明明断了五天。
   N 明显小于 M 的，就老实说次数，别夸他坚持，也别指责他断
   （"这周有两次学习"就是一句准确且不伤人的话）。
6. 鼓励要**落到这个人身上**（他这周具体做了什么），不要「你真棒」这种放之四海皆准的空话。
7. **这是一个人自己用的备考工具**，没有同学、没有课堂。别建议「讲给同学听」
   「小组讨论」这类做不到的事。
8. 一句话里**别重复同一个数字**（"挑 5 道题做完，题量固定在 5 道" —— 说一遍就够）。
   写完读一遍，读不通的句子重写。

请只写三段文字，返回严格 JSON：
{{
  "note": "一句点评（40字内）。针对实际表现给客观判断",
  "suggestion": "一条今天就能做的具体建议（60字内）。要具体到动作",
  "encouragement": "一句鼓励（25字内）。真诚，不油腻"
}}

只返回 JSON，不要额外文字。"""

        prose = None
        try:
            raw = call_llm([
                {"role": "system", "content": "你是基智学习助手，说话温暖简洁。只返回 JSON。"},
                {"role": "user", "content": prompt},
            ], temperature=0.85)     # 调高：鼓励类文字需要一点变化，0.6 太容易写成套话
            prose = _extract_json(raw)
        except Exception as e:                                  # noqa: BLE001
            logger.warning(f"[daily_summary] LLM 生成失败，整条走模板: {e}")

        # 逐段决定：模型给了就用模型的，没给（或返回残缺）就用模板补这一段。
        # **数字始终是真数据**，那才是重点。
        note = _cjk_spacing((prose or {}).get("note") or fallback["note"])
        suggestion = _cjk_spacing((prose or {}).get("suggestion") or fallback["suggestion"])
        encouragement = _cjk_spacing((prose or {}).get("encouragement") or fallback["encouragement"])

        # 这段文字是谁写的 —— 记进 payload，排查时能一眼看出
        # （"AI 总结还是模板总结"这个问题，在数据里要有答案）
        from_ai = [k for k in ("note", "suggestion", "encouragement")
                   if (prose or {}).get(k)]
        prose_source = ("ai" if len(from_ai) == 3
                        else "template" if not from_ai
                        else "mixed")

        # 列表页显示的正文摘要（详情页渲染的是 payload，这里给没渲染能力的端兜底）
        # ⚠️ 分三种情况写，别硬套「练习 N 道题」——一道题没做的时候那句话是错的。
        if count:
            digest = f"最近 {days} 天练习 {count} 道题"
            if scored:
                digest += f"，已批改的 {scored} 道平均掌握度 {mastery}%"
        elif kp_topics:
            digest = (f"最近 {days} 天在计划里练了 {len(kp_topics)} 个知识点，"
                      f"没走资源库出题")
        else:
            digest = f"最近 {days} 天没练题，但有 {learning_count} 次学习行为（{breakdown_line}）"
        digest += f"。{note}"

        summary_line = (f"{count} 题" + (f" | 掌握度 {mastery}%" if scored else "")
                        if count else f"{learning_count} 次学习行为")

        return {
            "user_id": user["id"],
            "type": "daily_summary",
            "title": f"近期学习总结",
            "content": digest,
            "summary": summary_line,
            # ⚠️ 原来这里是 action_label / action_link。那两列表里有，但 `notify()`
            #    不写（全站统一走 `link`），所以写在这儿落不了库
            #    （同 daily_rec 那个静默 no-op 的坏链）。统一走 link。
            "link": "/career",
            "payload": {
                "kind": "summary",
                "days": days,
                # ⚠️ stats 从**对象改成了列表**（老的是 {"questions":n,"mastery":m}）。
                #    前端两种都要认 —— 历史上那 19 条通知还是老形状。
                "stats": stats,
                "weak": weak[:6],
                "strong": strong[:6],
                "kp": kp_topics[:6],
                "note": note,
                "suggestion": suggestion,
                "encouragement": encouragement,
                # 三段文字是模型写的、模板填的、还是混合的。
                # 排查「今天怎么都是套话」时，第一个要看的就是这个字段。
                "prose_source": prose_source,
                "bucket": bucket,
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


# 注：早先这里有两个兜底函数（_fallback_note / _fallback_suggestion），
# 每个只返回一句写死的话。2026-10-16 被 services/summary_copy.py 的模板库取代 ——
# 那边的分组更细（练了题但没批改、只在计划里练、只有行为没练题……）、
# 每种情况都有多条随机挑，而且同时给模型当语气范本。
# 一句话的兜底在这两件事上都做不到。


_CJK = r"一-鿿"


def _cjk_spacing(text: str) -> str:
    """阿拉伯数字和中文之间补一个空格：「今天挑5道」→「今天挑 5 道」。

    ⚠️ 用后处理而不是写进提示词：模型对**排版类**指令的执行率很低
       （说了也时灵时不灵，同一批输出里一半带空格一半不带），
       而这纯粹是个确定性字符串变换 —— 代码做才可靠。
       （内容是模型的，排版是代码的，两件事分开。）

    `%` 两边不动：「86%」本来就该贴着数字。
    """
    if not text:
        return text
    text = re.sub(rf"(\d)([{_CJK}])", r"\1 \2", text)
    text = re.sub(rf"([{_CJK}])(\d)", r"\1 \2", text)
    return text


def _focus_candidates(user: dict, activity: dict, source: str) -> tuple[list, str]:
    """按设置决定「先推什么、再推什么」→ ([(知识点, 依据说明), ...], 实际依据)。

    两种依据：
      profile —— 按个人信息：学习阶段 / 年级 / 专业 / 学习目标
      history —— 按以往做题记录：薄弱知识点（`get_user_recent_activity` 算出来的，
                只统计**真被批改过**的题 —— 见那个函数的说明）

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

        # ⚠️ 推荐用 **30 天**窗口，比总结的 7 天宽。
        #    两个窗口的用途不同：总结是"最近学得怎么样"，推荐是"该补哪个老短板"
        #    —— 短板不该因为这两周没练就消失。
        #    （改之前这里拿的是全历史里**任意** 50 条，连"最近"都算不上。）
        activity = await get_user_recent_activity(user["id"], days=30)
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
