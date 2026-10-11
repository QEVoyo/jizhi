# -*- coding: utf-8 -*-
"""消息点注册表 —— 全系统唯一的消息类型定义（2026-10-07）

加一个消息点 = **本文件加一行** + 事件处调一次 `notify()`。前端零改动。

字段说明：
    group        大类，决定 Tab / 角标归属 / 主题色（见前端 messageTypes.js）
    label        前端显示名（Tab、列表标题兜底）
    aggregate    是否按 (user_id, type, source_id) 聚合成一行，用 msg_count 计条数
    todo         待办型：已读必须由「处理动作」驱动，看见不算，也不参与「走到页面即已读」
    default_on   新用户默认开关
    priority     high → 除了站内，还要发邮件/桌面通知（见 §通道）
    link         缺省跳转模板，支持 {source_id} {actor_id}；消息自带 link 时优先用它
    payload_schema  有值表示这条消息带结构化内容（目前只有三合一推荐）

⚠️ 未注册的 type 会被 `notify()` 直接拒绝 —— 这是刻意的。
   改造前线上出现过 `task_done` / `task_failed` 这种「后端在写、前端没定义」的类型，
   在列表里显示成英文原文。**类型必须先注册再发。**
"""

# ---------------------------------------------------------------- 配色
# 九个大类各一个主题色（**固定语义色，不随品牌色变** —— 理由同「危险/成功/警告」：
# 这是分类标识，不是品牌表达）。组内每个消息点再由它派生出一个渐变色，
# 所以「看色相认大类，看深浅认具体消息点」。
#
# ⚠️ 配色只有这一份实现（`derive_color`）—— 前端与预览页都从这里取，
#    见 `GET /messages/registry` 返回的 c1/c2。不要在别处再写一遍公式。
import colorsys

GROUPS = {
    "chat":       {"label": "好友消息", "color": "#3B82F6", "order": 1,
                   "switch": "chat_enabled",
                   "note": "跟品牌色同一色系（--brand）"},
    "social":     {"label": "社区互动", "color": "#E6A23C", "order": 2,
                   "switch": "social_enabled", "note": "沿用线上已有配色"},
    "learning":   {"label": "学习",     "color": "#67C23A", "order": 3,
                   "switch": "learning_enabled", "note": "沿用线上已有配色"},
    "plan":       {"label": "计划提醒", "color": "#F56C6C", "order": 4,
                   "switch": "plan_reminder_enabled", "note": "沿用线上已有配色"},
    "evaluation": {"label": "评估",     "color": "#8B5CF6", "order": 5,
                   "switch": "evaluation_enabled", "note": "沿用线上已有配色"},
    "career":     {"label": "学程",     "color": "#F59E0B", "order": 6,
                   "switch": "career_enabled", "note": "沿用线上已有配色"},
    "todo":       {"label": "待办",     "color": "#06B6D4", "order": 7,
                   "switch": "todo_enabled", "note": "新增：需要你动手"},
    "system":     {"label": "系统消息", "color": "#64748B", "order": 8,
                   "switch": "system_enabled", "note": "新增：中性、留底"},
    "admin":      {"label": "管理",     "color": "#6366F1", "order": 9,
                   "switch": "admin_enabled", "note": "新增：管理员专属"},
}


def _hex_to_hsl(hex_color: str) -> tuple:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    hh, ll, ss = colorsys.rgb_to_hls(r, g, b)
    return hh * 360, ss * 100, ll * 100


# 组内总跨度**固定**，与组里有几个消息点无关。
# 早先按「每步 6°」写，13 个点的 learning 组直接跨到 ±36°，
# 第一个点变成 hsl(58) 的**黄色** —— 色相跑出绿色系，"看色相认大类"就不成立了。
HUE_SPAN = 8.0      # 色相 ±8°：同一色系，肉眼仍是"同一个颜色"
LIGHT_SPAN = 14.0   # 明度 ±14%：相邻两点分得开


def derive_color(group: str, k: int, n: int) -> dict:
    """组内第 k 个（从 1 起）、该组共 n 个消息点 → 它的渐变色。

    t = -1 … +1 的归一化位置：色相、明度、饱和度都围绕大类色对称铺开。
    看色相认大类，看深浅认具体消息点。
    """
    base_h, base_s, base_l = _hex_to_hsl(GROUPS[group]["color"])
    t = 0.0 if n <= 1 else (k - (n + 1) / 2) / ((n - 1) / 2)

    def _clamp(v, lo=0.0, hi=100.0):
        return max(lo, min(hi, v))

    h = (base_h + t * HUE_SPAN) % 360
    l = _clamp(base_l + t * LIGHT_SPAN, 26, 78)
    s = _clamp(base_s - t * 8, 35, 95)

    c1 = f"hsl({h - 4:.0f}, {s:.0f}%, {_clamp(l + 6, 20, 86):.0f}%)"
    c2 = f"hsl({h + 4:.0f}, {_clamp(s + 5):.0f}%, {_clamp(l - 6, 16, 80):.0f}%)"
    return {"c1": c1, "c2": c2, "hue": round(h), "t": round(t, 3)}


def _t(group, label, **kw):
    d = {"group": group, "label": label, "aggregate": False, "todo": False,
         "once": False, "default_on": True, "priority": "normal",
         "link": "", "payload_schema": None, "shape": None}
    d.update(kw)
    return d


# ---------------------------------------------------------------- 详情形态
# 66 个消息点如果各写一套详情模板，加一个点就要动前端 —— 那正是
# 「加消息点 = 注册表加一行、前端零改动」要避免的。
# 所以只定义**几种内容形态**，由**已有的标志**推导出来。
#
# ⚠️ 顺序有意义：先看 payload（结构化的两种），再看 aggregate / todo，
#    最后按大类兜底。例如 `todo.set_share` 既是 todo 又在 todo 组，
#    应该走 todo 分支而不是兜底。
SHAPES = ("rec", "summary", "actors", "todo", "notice", "celebrate", "plain")


def _shape_of(v: dict) -> str:
    schema = v.get("payload_schema")
    if schema == "daily_rec":
        return "rec"                 # 学习推荐三合一：三块预览 + 去学习
    if schema == "daily_summary":
        return "summary"             # 昨日总结：数字卡片 + 知识点标签 + 三段文字
    if v.get("aggregate"):
        return "actors"              # 聚合：N 人做了某事 → 人物标签 + 聚合明细
    if v.get("todo"):
        return "todo"                # 待办：要动手处理
    g = v.get("group")
    if g == "system":
        return "notice"              # 账号/处置类正式通知，语气偏重
    if g == "career":
        return "celebrate"           # 学程成就/晋升，语气偏轻快
    return "plain"                   # 其余：分段正文


# ---------------------------------------------------------------- 消息点
TYPES = {
    # ============ chat 好友消息（3）============
    "chat.message":         _t("chat", "新消息", aggregate=True,
                               link="/community/chat/{actor_id}"),
    "chat.friend_request":  _t("chat", "好友请求", todo=True,
                               link="/community/friends"),
    "chat.friend_accepted": _t("chat", "好友请求已通过",
                               link="/community/friends"),
    # 被移出好友：事实通知，但社交上偏敏感 → 默认关，想开自己开
    "chat.friend_removed":  _t("chat", "被移出好友", default_on=False,
                               link="/community/friends"),

    # ============ social 社区互动（7）============
    # 落点是新建的 /post/:id 详情页（收藏页与我的帖子也一直在往这儿跳，
    # 而那个路由原本不存在）。评论/回复由调用方补 ?comment={cid} 精确到那一条。
    "social.post_like":     _t("social", "帖子被赞", aggregate=True,
                               link="/post/{source_id}"),
    "social.post_collect":  _t("social", "帖子被收藏", aggregate=True,
                               link="/post/{source_id}"),
    "social.post_comment":  _t("social", "帖子被评论",
                               link="/post/{source_id}"),
    "social.comment_reply": _t("social", "评论被回复", priority="high",
                               link="/post/{source_id}"),
    "social.video_like":    _t("social", "视频被赞", aggregate=True,
                               link="/video/{source_id}"),
    "social.video_comment": _t("social", "视频被评论", link="/video/{source_id}"),
    # ⚠️ aggregate=True：一次涨分可能同时超过好几位好友，紧接着的几次涨分还会再超过人。
    #    不聚合的话「你超过了 1 位好友」会连着刷屏。按天聚合成一条。
    "social.rank_pass":     _t("social", "好友榜被超越", aggregate=True, default_on=False,
                               link="/community/rank"),

    # ============ learning 学习闭环（11）============
    "learning.video_ready":     _t("learning", "讲解视频已就绪", link="/video/{source_id}"),
    "learning.video_failed":    _t("learning", "讲解视频生成失败", priority="high"),
    "learning.plan_generated":  _t("learning", "备考计划已生成", link="/plan-detail/{source_id}"),
    "learning.diagnosis_done":  _t("learning", "摸底诊断已完成", link="/evaluation-report"),
    "learning.exam_graded":     _t("learning", "交卷批改完成", link="/evaluation-report"),
    "learning.task_done":       _t("learning", "后台任务完成"),
    "learning.task_failed":     _t("learning", "后台任务失败", priority="high"),
    "learning.mastery_jump":    _t("learning", "掌握度提升", link="/mastery-board"),
    "learning.weak_alert":      _t("learning", "薄弱知识点提醒", link="/mastery-board"),
    # ⚠️ aggregate=True（2026-10-08 定的）：一次错题复习常常连着攻克好几道，
    #    逐条发就是刷屏 —— 按天聚合成一条，与 career.task_done 同一套处理。
    "learning.mistake_conquered": _t("learning", "错题被征服", aggregate=True,
                                     link="/mastery-board"),
    "learning.mistake_threshold": _t("learning", "错题本已达阈值", link="/mastery-board"),
    "learning.daily_rec":       _t("learning", "每日学习推荐",
                                   payload_schema="daily_rec"),
    # 2026-10-08 起也带结构化 payload（stats 数组 + 三段文字），见 daily_generator
    "learning.daily_summary":   _t("learning", "昨日学习总结", default_on=False,
                                   payload_schema="daily_summary"),
    # 词条本：按遗忘曲线到期待复习（`wordbook_lookup` 是既有埋点）
    "learning.wordbook_review": _t("learning", "词条该复习了", link="/wordbook"),

    # ============ plan 计划提醒（4）============
    "plan.daily_tasks":     _t("plan", "今日任务已下发", link="/learning-plan"),
    "plan.study_reminder":  _t("plan", "该学习啦", link="/learning-plan"),
    "plan.phase_switch":    _t("plan", "计划进入新阶段", link="/plan-detail/{source_id}"),
    "plan.plan_ending":     _t("plan", "计划临近结束", link="/plan-detail/{source_id}"),
    "plan.plan_completed":  _t("plan", "计划完成", once=True,
                               link="/plan-detail/{source_id}"),

    # ============ evaluation 评估（3）============
    "evaluation.table_ready":  _t("evaluation", "评估表已生成", link="/evaluation-table"),
    "evaluation.report_ready": _t("evaluation", "评估报告可查看", link="/evaluation-report"),
    # 磨合引擎调参 —— 报告里「参数可解释的自适应」那条创新点的**通知载体**。
    # 六条规则分别调参，但**只发一条**：「磨合引擎为你调整了 N 项参数」，
    # 详情里列出每项改了什么、为什么（前端以竖线标注调整点与指标变化）。
    "evaluation.engine_tuning": _t("evaluation", "磨合引擎调整了参数", aggregate=True,
                                   link="/evaluation-center"),

    # ============ career 学程（13）============
    # 学程有四类任务：播种（首次体验 24）· 施肥（每日 47）· 发芽（阶段性 36）· 丰收（拾贝 25）
    # 触发点在 routers/career.py：actions/record 后检测达成，claims 三个领取接口。
    #
    # ⚠️ 为什么「任务达成」要聚合：一次动作可能同时达成好几个任务
    #    （做 5 道题可能同时完成「今日 5 题」和「累计 100 题」），
    #    每个发一条就是刷屏 —— 聚合行显示「今天完成 3 个任务」。
    "career.task_done":           _t("career", "任务达成", aggregate=True,
                                     link="/career/tasks"),
    # 阶段性目标（发芽类）单独发：它是有意义的里程碑，不该被聚合淹没
    "career.milestone_done":      _t("career", "阶段目标达成", once=True,
                                     link="/career/tasks"),
    "career.daily_all_done":      _t("career", "今日任务全清", once=True,
                                     link="/career/tasks"),
    "career.reward_claimed":      _t("career", "奖励到账", aggregate=True,
                                     link="/career"),
    "career.level_up":            _t("career", "等级提升", link="/career"),
    "career.phase_clear":         _t("career", "学程阶段通关", once=True,
                                     link="/career/tasks"),
    # 每日打卡本身就在页面上即时可见，发消息偏吵 → 默认关
    "career.checkin":             _t("career", "打卡成功", default_on=False,
                                     link="/career"),
    # ⚠️ 没有 career.checkin_milestone —— 打卡里程碑**已经被两处覆盖**：
    #    长线任务「累计打卡 7/30 天」（career.py:183-184）走 career.milestone_done，
    #    成就「持之以恒」走 career.achievement。再单独加一条 = 同一个事件发两条。
    #    （2026-10-07 接线时发现，直接把这一条删了，而不是硬接。）
    "career.achievement":         _t("career", "成就解锁", once=True,
                                     link="/career/achievements"),
    "career.rank_up":             _t("career", "段位晋升", once=True,
                                     link="/career/rank"),
    "career.inactive_care":       _t("career", "小基想你了", default_on=True,
                                     link="/home"),
    "career.weekly_report":       _t("career", "学习周报", default_on=False,
                                     link="/evaluation-report"),

    # ============ todo 待办型（5）============
    # 已读由「处理动作」驱动：接受/拒绝/回复了才算，看见不算。
    "todo.set_share":       _t("todo", "收到题集分享", todo=True, link="/set-detail?id={source_id}"),
    "todo.share_result":    _t("todo", "题集分享被处理", todo=True,
                               link="/set-detail?id={source_id}"),
    # 反馈是弹窗、不是路由（Sidebar / EdgeNavDock 的 showFeedback）——
    # 与时间胶囊同款处理：用 ?feedback=1 让 /home 自动打开它
    "todo.feedback_reply":  _t("todo", "反馈已回复", todo=True, link="/home?feedback=1"),
    "todo.qa_reply":        _t("todo", "提问已解答", todo=True, link="/qa"),
    "todo.report_result":   _t("todo", "举报已处理", todo=True, link="/community"),

    # ============ system 系统与账号（11）============
    # ⚠️ system 组不参与「走到页面即已读」（B 路径）—— 否则去 /settings 改个主题
    #    就把「你被禁言了」顺手清了。
    "system.announcement":      _t("system", "公告"),
    "system.sanction":          _t("system", "账号处置通知", priority="high", link="/settings"),
    # 内容被删也要告诉作者 —— 原来 admin 的 delete_content 分支只写处置记录、**不通知**，
    # 用户会发现帖子凭空消失。与 system.sanction 分开：一个是账号，一个是单条内容。
    "system.content_removed":   _t("system", "内容被删除", priority="high",
                                   link="/community"),
    "system.sanction_lifted":   _t("system", "处置已解除", priority="high", link="/settings"),
    "system.password_changed":  _t("system", "密码已修改", priority="high", link="/settings"),
    "system.new_device":        _t("system", "新设备登录", priority="high", default_on=False,
                                   link="/settings"),
    "system.email_bound":       _t("system", "邮箱绑定成功", priority="high", link="/settings"),
    "system.policy_update":     _t("system", "协议更新"),
    "system.account_deleted":   _t("system", "账号注销确认", priority="high"),
    # 时间胶囊不是独立路由，是 ToolPanel 这个面板（侧边栏/顶栏唤起）——
    # 所以用 `?tool=capsule` 让 /home 自动打开它，见设计文档 §八 的前端待办
    "system.capsule_due":       _t("system", "时间胶囊到期", once=True,
                                   link="/home?tool=capsule"),
    "system.desktop_update":    _t("system", "桌面端有新版本", default_on=False),
    "system.syllabus_updated":  _t("system", "收藏的考纲有更新", default_on=False,
                                   link="/subject-plan/{source_id}"),

    # ============ admin 管理端（4）============
    # 发给管理员（role=admin），不是普通用户
    "admin.new_report":     _t("admin", "新举报待处理", todo=True, link="/admin/reports"),
    "admin.new_feedback":   _t("admin", "新反馈待处理", todo=True, link="/admin/feedback"),
    "admin.new_qa":         _t("admin", "新提问待处理", todo=True, link="/admin/qa"),
    # ⚠️ 现在还没有独立的「待审队列」页面，先落到内容管理页；
    #    做出审核页之后只改这一行 link。
    "admin.content_review": _t("admin", "内容待审核", todo=True, link="/admin/videos"),
}


# ---------------------------------------------------------------- 工具
def spec(notif_type: str) -> dict:
    """取类型定义；未注册直接抛 —— 见文件头说明。"""
    s = TYPES.get(notif_type)
    if s is None:
        raise KeyError(
            f"未注册的消息类型 {notif_type!r}。"
            f"先在 backend/notification_registry.py 的 TYPES 里注册再发。"
        )
    return s


def group_of(notif_type: str) -> str:
    return spec(notif_type)["group"]


def switch_of(notif_type: str) -> str:
    """该类型归哪个开关管。"""
    return GROUPS[group_of(notif_type)]["switch"]


def resolve_link(notif_type: str, source_id: str = None, actor_id: str = None) -> str:
    """缺省跳转：模板里的 {source_id} / {actor_id} 用实际值填。"""
    tpl = spec(notif_type).get("link") or ""
    return tpl.replace("{source_id}", source_id or "").replace("{actor_id}", actor_id or "")


def public_registry() -> dict:
    """给前端的一份：Tab、角标归属、**配色**、跳转全从它推导。

    每个消息点带上 c1/c2（渐变两端）与组内序号，前端直接拿来渲染 ——
    配色公式只有本文件一份，前端不重写。
    """
    size = {}
    for v in TYPES.values():
        size[v["group"]] = size.get(v["group"], 0) + 1

    seen = {}
    types_out = {}
    for key, v in TYPES.items():
        g = v["group"]
        seen[g] = seen.get(g, 0) + 1
        d = {kk: vv for kk, vv in v.items() if kk != "payload_schema"}
        # 详情形态：前端只认这几个名字（见 MessageCenter.vue 的详情体）。
        # 注册表里可以逐条覆写，不写就按标志推导。
        d["shape"] = v.get("shape") or _shape_of(v)
        d.update(derive_color(g, seen[g], size[g]))
        d["index"] = seen[g]
        d["group_size"] = size[g]
        types_out[key] = d

    groups_out = {}
    for g, meta in GROUPS.items():
        groups_out[g] = {**meta, "size": size.get(g, 0)}

    return {
        "groups": groups_out,
        "types": types_out,
        "no_route_read": ["system", "todo"],   # 不参与「走到页面即已读」的组
        "no_delete": ["system"],               # 只能已读、不能删的组
    }
