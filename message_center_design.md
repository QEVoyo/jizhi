# 消息中心设计（2026-10-07 立项）

> 目标：**一处入口、一张表、一个读接口**；加新消息点 = 注册表加一行 + 事件处调一次 `notify()`，前端零改动。
>
> 本文是**实施契约**：数据模型 / 消息点清单 / 显示位置 / 已读语义 / 进入方式 / 接口清单。
> 现状问题见 `logs/2026-10-07.md` 之后的分析 —— 简言之：3 套读法、5 个写入方（2 个绕过公共入口）、
> 线上全表只有 5 行，且聚合更新因 `updated_at` 列不存在而**静默失败**。

---

## 一、现状（改造前，留档）

| 读路径 | 位置 | 算法 | 病 |
|---|---|---|---|
| `GET /messages/unread/summary` | 消息中心列表 | 按 type 分组，`message_count = len(rows)` | 只查未读 → **点一下就没**；聚合列 `msg_count` 被忽略 |
| `GET /sidebar-badges` | 侧边栏角标 | 另一套：chat 按 sender 去重、好友请求直接查 `friendships` | **与消息中心算法不同 → 数字必然对不上** |
| `GET /admin/announcements/active` | 公告 Tab | 前端直接 fetch | `is_read: true` 写死；徽标用**总数**当未读数 |
| `GET /messages/history` | — | 带分页 | **前端从未调用** |

写入方 5 个，其中 `tools.py:_notify_due_capsules`、`services/daily_generator.py` **绕过** `utils/notification.py` 自己插。

**线上实测**：`notifications` 全表 5 行（system 3 / chat 2，最近 08-24），前端却有 10 个 Tab。

---

## 二、数据模型

### 2.1 表：`notifications`（唯一收件箱）

保留现有列，**去掉 `updated_at`**（该列根本不存在，正是静默失败的根因），新增：

| 列 | 类型 | 用途 |
|---|---|---|
| `type` | text | 注册表里的类型键（见 §三） |
| `group` | text | 大类：`chat` / `social` / `learning` / `plan` / `evaluation` / `system` / `todo` / `admin` |
| `actor_id` | uuid | 触发者（点赞的人、发消息的好友），无则 null |
| `source_id` | text | 聚合键（好友 id / 帖子 id / 计划 id …） |
| `title` `content` `image_url` | text | 展示 |
| `link` | text | 点击跳转（前端注册表兜底） |
| `msg_count` | int | 聚合条数（**读接口必须用它，不是 len(rows)**） |
| `created_at` | timestamptz | 首次 |
| `last_at` | timestamptz | 最近一条（聚合时更新） |
| `is_read` | bool | |
| `read_at` | timestamptz | |
| `is_todo` | bool | 待办型（好友请求/题集分享/管理员队列）—— 已读由**处理动作**驱动 |
| `handled_at` | timestamptz | 待办处理完成时间 |
| `deleted_at` | timestamptz | 软删（system 类不可删） |

唯一索引：`(user_id, type, source_id) where is_read = false and deleted_at is null` → 聚合 upsert 靠它。
保留天数按 `notification_settings.retention_days`。

### 2.2 写入契约

```python
# backend/utils/notification.py —— 唯一入口
async def notify(
    to_user: str,
    type: str,                 # 必须已在 REGISTRY 里注册，否则抛错（开发期直接拒绝写入）
    actor_id: str | None = None,
    source_id: str | None = None,
    title: str = "",
    content: str = "",
    link: str = "",
    image_url: str = "",
) -> bool:                     # 失败必须抛，禁止静默降级
```

三条硬规矩（都是这轮踩出来的）：

1. **类型必须注册**。未注册的 type 直接抛 —— 现在 `task_done` 这种"后端在写、前端没定义"的类型就是漏网的。
2. **失败必须响**。现在 `_upsert` 返回 False 而调用方不检查 → 静默了两个月。改为抛异常，调用方决定是拦请求还是记 ERROR。
3. **不许绕过**。`tools.py` / `daily_generator.py` 的直接插入全部收编。

### 2.3 注册表（后端 `backend/notification_registry.py`，前端 `frontend/src/utils/messageTypes.js`）

一行一个消息点，字段：

```python
{
  "key": "video.ready",              # 类型键
  "group": "learning",               # 大类（决定 Tab 与角标归属）
  "aggregate": False,                # 是否按 source_id 聚合
  "todo": False,                     # 是否待办型
  "default_on": True,                # 默认开关
  "priority": "normal",              # high → 强制桌面通知 + 邮件
  "label": "讲解视频已就绪",
  "link": "/video/{source_id}",      # 缺省跳转，消息自带 link 优先
}
```

前端只认注册表：图标、配色、Tab、角标归属、跳转**全部由它推导**，
所以后端加一个消息点、前端不需要改任何代码。

---

## 三、消息点清单（**65 个 / 9 大类**，以 `backend/notification_registry.py` 为准）

> ⚠️ **2026-10-16 按注册表重新点过数**（写脚本直接读 `TYPES` 统计的，不是手数）：
>
> `learning` 14 · `system` 12 · `career` **11** · `social` 7 · `plan` 5 ·
> `todo` **5** · `admin` 4 · `chat` 4 · `evaluation` **3** = **65**
>
> 本章之前有几处对不上，都已订正：
> - 标题原写「66 个」，但各分节标题相加是 69、正文实列是 67 —— **三个数互相打架**
> - `career` 标 12、实为 11；`todo` 标 4、实为 5（漏了 `todo.report_result`）
> - **`evaluation` 整组（3 个）本章原先没有**，现已补上
> - 末尾「其他（7）」**不是额外的 7 个** —— 那是**改名对照表**（旧名 → 现名），
>   列的名字在注册表里一个都不存在，**不该计入总数**

> 用户已确认"都有必要"。#39–42 为不推荐项（做题/出题完成页面内已有反馈、好友上线需先建在线状态、空内容定时消息为负体验），暂不实现。

### chat 好友消息（4）
`chat.message` 私信 · `chat.friend_request` 好友请求(待办) · `chat.friend_accepted` 请求被接受 ·
`chat.friend_removed` 被移出好友（**默认关** —— 社交上敏感，想开自己开）

### social 社区互动（7）
`social.post_like` 帖子被赞(聚合) · `social.post_collect` 被收藏(聚合) · `social.post_comment` 被评论 ·
`social.comment_reply` 评论被回复 · `social.video_like` 视频被赞(聚合) · `social.video_comment` 视频被评论 ·
`social.rank_pass` 好友榜被超越

### learning 学习闭环（14）
`video.ready` 讲解视频就绪 · `video.failed` 生成失败 · `plan.generated` 计划已生成 · `plan.diagnosis_done` 摸底完成 ·
`exam.graded` 交卷批改完成 · `evaluation.ready` 评估表已生成 · `evaluation.report` 评估报告可查看 ·
`mastery.jump` 掌握度跃升 · `mastery.weak_alert` 薄弱知识点堆积 · `mistake.conquered` 错题被征服 ·
`mistake.threshold` 错题本达阈值 · `plan.phase_switch` 阶段切换 ·
`learning.wordbook_review` 词条该复习了（遗忘曲线到期）

### plan 计划提醒（5）
`plan.daily_tasks` 今日任务已下发 · `plan.study_reminder` 每日学习提醒(定时) · `plan.plan_ending` 计划临近结束 ·
`plan.plan_completed` 计划完成（三阶段走完）

### career 学程（11）
> 学程有四类任务：**播种**（首次体验 24）·**施肥**（每日 47）·**发芽**（阶段性 36）·**丰收**（拾贝 25）。
> 触发点在 `routers/career.py`：`actions/record` 之后检测达成，三个 claim 接口管领取。

**任务与奖励**：`career.task_done` 任务达成（**聚合** —— 一次动作可能同时达成好几个任务，
每个发一条就是刷屏）· `career.milestone_done` 阶段目标达成（发芽类，单独发）·
`career.daily_all_done` 今日任务全清 · `career.reward_claimed` 奖励到账（聚合）·
`career.phase_clear` 学程阶段通关（如播种 24/24 → 进入施肥期）

**成长**：`career.level_up` 等级提升 · `career.rank_up` 段位晋升 ·
`career.achievement` 成就解锁 · `career.checkin_milestone` 打卡里程碑 ·
`career.checkin` 打卡成功（**默认关** —— 页面上即时可见，发消息偏吵）

**陪伴**：`career.inactive_care` 断更关心（连续 3 天）· `career.weekly_report` 学习周报

### system 系统与账号（12）
`system.announcement` 公告 · `system.sanction` 封禁/禁言/警告 · `system.sanction_lifted` 解禁 ·
`system.password_changed` 密码修改 · `system.new_device` 新设备登录 · `system.email_bound` 补邮箱成功 ·
`system.policy_update` 协议更新 · `system.account_deleted` 注销确认 ·
`system.content_removed` 内容被删除（原来 delete_content 只写处置记录、**不通知**）·
`system.capsule_due` 时间胶囊到期 · `system.desktop_update` 桌面端有新版本 ·
`system.syllabus_updated` 收藏的考纲有更新

### todo 待办型（5，已读由处理动作驱动）
`todo.set_share` 收到题集分享 · `todo.share_result` 分享被接受/拒绝 · `todo.feedback_reply` 反馈被回复 ·
`todo.qa_reply` 提问被回答 · `todo.report_result` 举报已处理

> ⚠️ **`todo` 既是组名、也是一个标记位**，别混：组的成员是上面这 **5** 个；
> 而带 `todo: true` 标记的有 **10** 个（`chat.friend_request`、`admin.*` 那四个等也常驻待办）。
> 「已读由处理动作驱动」说的是那个标记位，不是这个组。

### evaluation 评估（3）
`evaluation.report_ready` 评估报告可查看 · `evaluation.table_ready` 评估表已生成 ·
`evaluation.engine_tuning` 磨合引擎调整了参数（**聚合** —— 一次调教可能连改几个参数）

### admin 管理端（4）
`admin.new_report` 新举报 · `admin.new_feedback` 新反馈 · `admin.new_qa` 新提问 · `admin.content_review` 待审内容

### 附：改名对照表（**不是额外的消息点，不计入 65**）

下面这 7 个是**旧名**，在 `notification_registry.py` 里**一个都不存在**了 ——
它们按「组.动作」规范化时改成了右边那些名字。列在这里只是为了查旧日志/旧代码时能对上：

| 旧名 | 现名（归哪个组） |
|---|---|
| `task.done` / `task.failed` | `learning.task_done` / `learning.task_failed`（learning） |
| `daily.rec` | `learning.daily_rec` —— 每日学习推荐三合一，见 §六 |
| `daily.summary` | `learning.daily_summary`（learning） |
| `capsule.due` | `system.capsule_due`（system） |
| `syllabus.updated` | `system.syllabus_updated`（system，**广播型，单独设计**） |
| `desktop.update` | `system.desktop_update`（system） |

---

## 四、消息点 = 显示位置（哪里出现红点）

**硬规矩：所有位置的数字必须来自同一个接口 `GET /messages/badges`。**
（现在侧边栏和消息中心两套算法，数字永远对不上。）

| # | 位置 | 显示 | 数字 | 点击 → |
|---|---|---|---|---|
| 1 | 侧边栏「消息中心」 | 角标 `99+` 封顶 | `total` | `/message` |
| 2 | 侧边栏「社区」 | 角标 | `group.community` = chat + social + 好友请求 + 题集分享 | `/community` |
| 3 | 侧边栏「学程」 | 角标 | `group.career` | `/career` |
| 4 | 侧边栏「学科计划」 | 角标 | `group.plan` | `/learning-plan` |
| 5 | 侧边栏「评估中心」 | 角标 | `group.evaluation` | `/evaluation-center` |
| 6 | 消息中心 Tab 栏 | 每类角标 | `byType[type]` | 切到该 Tab |
| 7 | 社区 → 好友列表每人 | 头像小红点 | 该好友未读条数 | 进会话 |
| 8 | 社区 → 好友请求 | 数字 | `todo.friend_request` | `/community/friends` |
| 9 | 顶栏铃铛（EdgeNavDock） | 红点 | `total > 0` | `/message` |
| 10 | 浏览器标题（Web / 桌面端） | `(3) 基智…` | `total` | — |
| 11 | **桌宠（桌面端）** | 小基头顶红点 + 轮盘新增「消息」项 | `total` | 唤起主窗口并进消息中心 |
| 12 | **桌面端系统通知** | 原生弹窗（不显示数字） | 实时事件 | 深链到对象 |
| 13 | 小程序 tabBar「我的」 | 红点 | `total` | 消息中心页 |
| 14 | 管理后台侧边栏 | 各项角标 | `admin.*` | `/admin/reports` 等 |

刷新：进页面拉一次 + 30 秒轮询（现状），后续可换 SSE。桌面端可由主窗口经配置桥把 `total` 推给桌宠。

---

## 五、已读语义：三条路径（2026-10-07 定稿）

**总则**
- **进消息中心 ≠ 全部已读**（现在的实现一进就清空，是"消息消失"的根源）
- **已读后不消失**，留在列表里（未读置顶 + 高亮），进历史
- 可执行操作：单条已读 / 单条删除 / 分类全部已读 / 分类清空 / 全部已读
- `system` 类**只能已读、不能删除**（处置与安全通知要留底）

### 5.1 三种变成"已读"的方式

| 路径 | 触发 | 说明 |
|---|---|---|
| **A. 点消息 → 看详情 →（可选）跳转** | 在消息中心点某条 → **打开详情**（这就是"看了"）→ 该条置已读；详情里的主按钮再跳到目标页 | 最常见的一条。**聊天例外：直接进会话**，不经过详情 |
| **B. 直接走到目标页面** | 不经消息中心，自己从别的入口进到那个页面（如直接打开好友会话、打开评估报告）→ **指向该页面的未读消息自动置已读** | 用户已经看到内容了，不该还挂着红点 |
| **C. 在消息中心直接标记** | 单条已读 / 分类全部已读 / 全部已读 / 分类清空 | 不跳转也能清 |

### 5.2 B 的实现：全局路由守卫（一处代码，覆盖全部消息点）

不写在每个页面里，而是挂在路由 `afterEach`：

```
每次路由变化 →
  PUT /messages/read-by-route { url: 当前完整路径 }
  服务器：把 link 与当前 url 匹配的未读行置已读
```

- **匹配规则**：消息的 `link` 与当前 url **路径段逐段相等**（最后一段允许是前缀，`/plan-detail/abc` 命中 `/plan-detail/abc`）。
  这样 `/career` 不会把 `/career/achievements` 的消息清掉 —— **必须真的走到那一页**。
- **⚠️ 两个组不参与 B**：
  - `system`（处置/安全/协议）—— 路过 `/settings` 就把"你被禁言了"清掉是不可接受的，**只能 A 或 C**
  - `todo`（好友请求/题集分享/管理员队列）—— 待办型**必须由处理动作驱动**，否则角标没了事还在

### 5.3 分类规则（与三条路径的关系）

| 类型 | A 点击 | B 到页即读 | C 直接标记 |
|---|---|---|---|
| 私信 chat | ✅ 进会话 | ✅ 进会话（同上） | ✅ |
| 聚合型 social（赞/收藏） | ✅ | ✅ 进到那个帖子/视频 | ✅ |
| 单条 social（评论/回复） | ✅ | ✅ 进到那条内容 | ✅ |
| learning / plan / evaluation | ✅ | ✅ 进到目标页 | ✅ |
| 公告 announcement | ✅ | ✅ 进公告页 | ✅（现在写死 `is_read:true` 是错的） |
| **todo 待办型** | ❌ 不算 | ❌ 不算 | ⚠️ **只有"处理动作"才算**（接受/拒绝/回复） |
| **system 处置/安全** | ✅ 点开即读 | ❌ 不参与 | ✅ 可标记（不可删） |
| admin 队列 | ✅ | ❌ | ⚠️ 同上，处理完才算 |

**幂等**：重复点击不重复计数；聚合行 `msg_count` 归零但行保留。

---

## 六、每日学习推荐（三合一）

**现状**：`services/daily_generator.py:127` 的 `generate_daily_recommendation()` 只生成**一段 120 字文字**，
`action_link: /resource-lib`；线上 0 行（只挂在一个手动端点上，没有定时任务）。

**新设计：一条消息 = 一套可直接执行的任务（学习内容 + 题目 + 视频）**

> **本质**：和「学科计划的每日任务」**是同一套东西** —— 学习内容、题目、视频三件套，
> 做完一样回流作答与掌握度。**唯一的区别是内容随机挑**（不需要先生成计划，
> 也不挂在任何 plan 上）。所以它不是"一条通知"，而是**把一个每日任务塞进了消息里**。

> **⚠️ 2026-10-08 两处订正**（实现与本文档分叉，以本节为准）：
>
> **① 交互形态改了。** 本文档原写「**详情里可以直接做，不是跳出去做**，弹层即执行面板」。
> **用户 2026-10-08 明确改成独立全屏页 `/daily-learn`** —— 首页「小基推荐」卡片和消息中心
> 那条**点进的是同一个页面**；消息中心弹层里只留三块预览 + 「去学习」按钮，不再就地做题。
> 原因：做题和看视频在居中弹层里太局促。
> （消息中心原来那套就地执行面板是**空壳** —— 「提交这 N 题」只做了
> `recDone.questions = true`，零 API 调用，连提示语「作答会写入你的做题记录」都是假的。）
>
> **② schema 漏了 `syllabus_id`。** 见下面标注。

```
type = learning.daily_rec        ← 一条，不是三条（注册表里的键名是 learning.daily_rec，
                                    本文档早先写的 daily.rec 是简写，代码里不存在）
payload(jsonb) = {
  content:  {title, kp_id, minutes, basis, sections?}   ① 学习内容（正文按需生成，见下）
  questions:[{qid, stem, type, difficulty, syllabus_id}] ② 3~5 道题
  video:    {video_id, title, duration, duration_sec, state} | null  ③ 讲解视频
  progress: {content, questions, video}                 哪一块做完了（三块齐 → handled_at）
}
```

⚠️ **`questions[].syllabus_id` 是 2026-10-08 补的，原 schema 漏了 —— 不补会判错题。**
题库 18,711 题里 **497 个 id 横跨多个库**（见 `local_question_bank.find_question_unique`），
做题端 `subject_plan.submit_answer` 靠 `syllabus_id` 定位题目，不带就会跨库猜 ——
**拿 A 科目的题判 B 科目的分**。

⚠️ **`content.sections`（正文）不在发送时生成** —— 那要多烧一次 LLM，而大多数用户当天未必点开。
首次打开学习页时按需生成并**写回 payload**（幂等：已有 `sections` 就直出）。
每日推荐**没有任务行**可以当缓存载体（学科计划缓存在 `plan_daily_tasks.learning_content`、
自定义计划在 `learning_tasks.lesson_content`），所以只能回写进 payload 自己。

⚠️ **每道题的 `syllabus_id` 决定它从哪个库取题面** —— 学习页的 `/{id}/questions`
是按每题自己的 `syllabus_id` 取的，不能统一传一个（`score_by_kp` 是跨库扫的，命中的题可能来自不同考纲）。

- **数据回流**：这三块的作答**照常写 `question_records` / 掌握度** ——
  无计划练习的 `plan_id` 为空，依赖已修好的 `fix_records_nullable_plan.sql`（10-01），
  所以"随机来的题"和"计划里的题"进的是同一个数据底座。
- **生成**：扩展 `generate_daily_recommendation()` → 三块一起产出；内容复用"摘要 + 按需生成详细正文"那套
- **触发**：`notification_settings.daily_rec_enabled` + `daily_rec_time`
  ✅ **2026-10-08 接上了**：`services/daily_scheduler.py` **每 10 分钟轮询**一次，
  把「开着开关 + 到点了 + 今天还没生成」的用户挑出来生成。
  为什么是轮询不是定点：发送时间是**每用户自己设的**，全局定时器表达不了；
  用 `>=` 而非 `==`，服务器重启期间错过的时间点下一轮能补上。
  默认值 08:00 / 07:00，定义在 `utils/notification.DEFAULT_SETTINGS`（**只有这一份**）。
  另有手动生成 `POST /daily-learn/generate`（首页推荐卡空态那个按钮），
  `force` 只忽略时间、**去重照旧**。
- **⭐ 推荐的依据可以在设置里选**（`daily_rec_source`，见 §十）：

  | 取值 | 含义 | 用什么挑知识点 |
  |---|---|---|
  | `mix`（默认） | 结合 | 有做题记录就按错的来，没有就按资料 |
  | `profile` | 按个人信息 | 学习阶段 / 年级 / 专业 / 学习目标 |
  | `history` | 按做题记录 | 错题与薄弱知识点，不看资料 |

  ⚠️ **两条回落规则是必须的**，否则新用户选了 `history` 会**永远收不到推荐**：
  选 `history` 但一条做题记录都没有 → 退回 `profile`；选 `profile` 但资料没填全 → 退回 `history`。
  两个都空 → 当天不发（宁缺毋滥，不发空壳推荐）。回落会记 INFO 日志，便于排查"为什么今天没推"。
- **去重**：同一用户当天只发一条。
  ✅ 实现是 `daily_generator.has_today()` —— **生成之前先查库**，而不是靠唯一键撞。
  两个理由：① 省 LLM（推荐和总结都要调模型）② `learning.daily_rec` **不是聚合类型**，
  同一天再发一次会撞未读聚合的部分唯一索引 → 409 → 非聚合类型**不走聚合回退、直接抛
  `NotifyError`**（10-08 在 `social.rank_pass` 上踩过同一个坑）。
- **⚠️ 空则不发**：**题目与视频至少得有一块**，否则当天不发。
  ⚠️ 2026-10-08 实测补丁：依据挑出的知识点**未必在题库里有题** —— topic 来自 `questions` 表的
  AI 生成题 topic，而检索匹配的是题库的 `kp_name`，**是两套词汇**。实测 9 个真实 topic 里
  **3 个一道题都搜不到**（`Shell编程` / `切片赋值的长度变化影响` / `比较大小`）。
  只试第一个的话约 **1/3 的用户会永远收不到推荐** —— 所以候选要**一串、从前往后试**。
- **⚠️ 视频只做"命中复用"，不为每日推荐排产** —— 一次给全体用户排产会把 worker 压垮。
  ✅ 实现是 `video_gen.find_ready_video()`（**纯只读**）。⚠️ **绝不能用 `ensure_videos()` 代替** ——
  那个是「查 + 补产」二合一，查不到就插一行 `generating` 并丢进生成队列。
  （实测：调用前后 `video_library` 行数不变，确认没排产。）
- **已读**：开始做任意一块 → **整条已读**；但**没做完不算完成**（完成态是另一回事，见 §5.4 的待办语义）

**顺带发现一个 bug**：`get_active_users()` 拿 **`questions` 表**（AI 生成题）当"最近 7 天活跃用户"的来源，
语义就不对 —— 应该是 `question_records`（作答）或 `user_actions`。这条要做定时任务前先修。

✅ **2026-10-08 已修**，而且它比记录的更糟，是三处叠加：

1. **查错了表**（如上）。
2. **完全没有时间过滤** —— `?select=user_id&limit=500` 一个时间条件都没有，方法名里的
   "最近 7 天"是假的。
3. **profiles 被硬截断到 100 个**（`list(user_ids)[:100]`）—— 活跃用户一多，
   后面的**静默收不到推荐**。改成按 100 一批查全。
   现按 `agents/tuning.py:_active_users` 的口径改为 `user_actions?action_at=gte.…`。

### ⚠️ 真跑时才暴露的两个崩溃（都不是这轮引入的）

这两条印证了同一件事：**这条链路从来没在真库上跑过**，只编译、只跑过假 HTTP 的单测。

1. **`get_user_yesterday_activity()` 直接崩**：
   `all_scores = sum((sum(s) for s in topic_scores.values()), [])` ——
   `topic_scores` 的值是**分数列表**（`{'foo': [80, 60]}`），内层 `sum(s)` 已把列表压成 int，
   外层再拿 `[]` 去「拼」int → `TypeError: can only concatenate list (not "int") to list`。
   本意是拍平，`sum(topic_scores.values(), [])` 就是拍平。
   **一旦真推给用户就是 100% 失败。**
2. **时间戳拼进 URL 被解码**：`datetime.now(timezone.utc).isoformat()` 带 `+00:00`，
   裸拼进 query 时那个 `+` 变成空格 → PostgREST 报
   `invalid input syntax for type timestamp: "... 00:00"` → 整个查询 400。
   **必须走 `params=` 让 httpx 编码**。`agents/tuning.py` 一直是这么写的。

### 🚨 部署阻塞：`notifications.type` 上的陈年 CHECK（2026-10-08 发现）

真跑每日推荐时六条通知**全部**写入失败：`POST /rest/v1/notifications → 400 {"code":"23514"}`。
`23514` 是 **check_violation**（外键是 23503、非空是 23502）。

只读排查：`notifications` 全表 5 行，`type` **只有 `chat` 和 `system` 两个无点号的老值**；
而 10-07 引入的 66 个新类型全是 `组.动作` 形式。**建表时（早于本仓库所有迁移文件）
按当时的类型加过一个白名单 CHECK**，新类型一条都插不进去。

**也就是说：10-07 的 66 个消息点、之后所有接线，在真实库上从来没成功发出过一条通知。**

修：`backend/sql/notifications_drop_stale_type_check.sql`（先打印现有 CHECK 再删，
只删提到 `type`/`group_key` 的，其余保留）。**不再补新的类型白名单** ——
类型合法性由 `notification_registry.spec()` 把关；在数据库里再维护一份 = 同一个概念两个副本，
注册表加了 66 个而 DB 白名单没跟着动，正是这次踩的坑。

## 七、视觉规范：大类主题色 + 消息点渐变色

### 7.1 九个大类，各一个主题色（**固定语义色，不随品牌色变**）

理由同"危险/成功/警告"：这是**分类标识**，不是品牌表达。其中 5 个沿用线上已有的配色，不另起一套：

| 大类 | 色值 | 语义 | 沿用 |
|---|---|---|---|
| chat 好友消息 | `var(--brand)` | 最常用的入口，跟品牌色 | ✅ 现有 |
| social 社区互动 | `#E6A23C` | 人际互动 | ✅ 现有 |
| learning 学习闭环 | `#67C23A` | 学习行为 | ✅ 现有 |
| plan 计划提醒 | `#F56C6C` | 时间/催促 | ✅ 现有 |
| evaluation 评估 | `#8B5CF6` | 分析结论 | ✅ 现有 |
| career 学程 | `#F59E0B` | 奖励/荣誉 | ✅ 现有 |
| todo 待办 | `#06B6D4` | 需要你动手 | 🆕 |
| system 系统与账号 | `#64748B` | 中性、留底 | 🆕 |
| admin 管理端 | `#6366F1` | 管理员专属 | 🆕 |

### 7.2 组内每个消息点 = 该大类色的**渐变色**（每个点颜色都不一样）

不做 53 个手写色值 —— **从 (大类, 组内序号) 派生**：

```
组内共 n 个消息点，第 k 个（k 从 1 起）：
  色相   h = h_base + (k - (n+1)/2) × 6°        // 步长 6°，组内最多跨 ±33°，仍认得出大类
  明度   l = 40% + (k-1)/(n-1) × 22%            // 40% → 62% 线性铺开
  渐变   linear-gradient(135deg,
           hsl(h-6, s,      l+8%)   →   hsl(h+6, s+6%, l-6%))

已读态   filter: saturate(.25) opacity(.8)       // 保留色相，明显退色
未读     满色渐变 + 左侧 3px 色条
```

例（learning 组，n=12）：`video.ready` 偏青绿 → `exam.graded` 居中正绿 → `career` 边界偏黄绿。
**看色相认大类，看深浅认具体消息点。**

### 7.3 用在哪

| 位置 | 用法 |
|---|---|
| 消息中心 Tab 图标 + 下划线 | 大类主题色 |
| 消息卡片左侧色条（未读） | 该消息点的渐变色 |
| 卡片内图标底色 | 该消息点的渐变色（低透明度 + 圆形） |
| 列表右上圆点 `type-dot` | 该消息点的渐变色 |
| 侧边栏角标 | 所属大类主题色 |
| 桌宠红点 / 桌面端系统通知图标 | 所属大类主题色 |
| 三合一推荐卡（§六 三块） | 学习内容/题目/视频各取 learning 组内三个相邻色 |

**实现**：注册表声明 `group` + 注册顺序即 `k`，前端一个 `deriveColor(group, k, n)` 出全部色值，
CSS 变量 `--mc-c1 / --mc-c2`。**加消息点只加一行，配色自动生成。**

## 八、进入方式

**入口 4 个**

1. 侧边栏「消息中心」→ `/message`，默认 Tab「全部」（未读置顶，已读在后）
2. 分类角标（社区/学程/计划/评估）→ 进**对应功能页**，不进消息中心
3. 消息中心内 Tab → 切分类
4. 桌面端系统通知 → **深链直达对象**（不进消息中心中转）

**点击跳转表**（`link` 字段优先，缺失时用注册表缺省值）

| 类型 | 目标 |
|---|---|
| `chat.*` | `/community/chat/{actor_id}` |
| `social.post_*` | `/community?post={id}&comment={cid}` —— **帖子锚点已定：要做**（帖子没有独立路由，需给 `/community` 加 query 锚点，打开帖子详情并滚到该评论、高亮）。不做的话评论/点赞类消息无处可跳，B 路径（到页即读）也断在这里 |
| `social.video_*` | `/video/{video_id}` |
| `learning.video.ready` | `/video/{id}`（计划内则回做题页） |
| `learning.plan.*` `plan.*` | `/plan-detail/{plan_id}` |
| `evaluation.*` | `/evaluation-report` · `/evaluation-table` |
| `career.*` | `/career/achievements` · `/career/tasks` · `/career/rank` |
| `todo.friend_request` | `/community/friends` |
| `todo.set_share` | `/set-detail?id={set_id}` |
| `system.sanction` `system.*` | `/settings` |
| `admin.*` | `/admin/reports` · `/admin/feedback` · `/admin/qa` |

**返回**：消息中心记录来源，`router.back()` 可用则回退，直接进入才回 `/home`。
（现在写死 `goBack → /home`，从社区点进来再返回就丢了上下文。）

---

## 九、接口清单（替代现有 4 个读路径）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/messages` | 分页列表：`?group=&type=&unread_only=&page=&page_size=`，返回 `total` 与 `unread` |
| GET | `/messages/badges` | **唯一角标来源**：`{total, group:{...}, byType:{...}}` |
| PUT | `/messages/{id}/read` | 单条已读 |
| PUT | `/messages/read` | 批量：`{ids:[]}` 或 `{group|type}` 或 `{all:true}` |
| DELETE | `/messages/{id}` | 单条删除（`system` 类拒绝，返回 400） |
| DELETE | `/messages` | 清空：按 group/type，`system` 类保留 |
| GET | `/messages/settings` · PUT 同 | 分类级订阅开关 + 免打扰时段（替代现有 8 个没人读的开关） |

**计划废弃**：`/messages/unread/summary`、`/messages/unread/count`、`/sidebar-badges`、`/messages/clear`、
`/messages/read-all`、`/messages/history`、`/admin/announcements/active`（公告并入 `notifications`）。

> ⚠️ **2026-10-16 核实：上面这些是「计划」不是「已完成」。** 写「废弃」会让后来人以为已经没人调了。
>
> 还在被真实调用的（**清理掉之前不能当作废弃**）：
> - **`/community/sidebar-badges`** —— 后端 `routers/community/notifications.py:134` 端点仍在，
>   前端 **`CareerSidebar.vue:287`** 和 **`CommunitySidebar.vue:66`** 两处仍在调
>   （都走 `api/community.js` 的 `getSidebarBadges`）。
>   后果就是本节开头那条硬规矩说的：**这两个侧边栏的角标与消息中心对不上**。
>   `Sidebar.vue` 已经切到 `/messages/badges` 了，剩下这两个。
> - `/admin/announcements/active`：新前端已不再调（全面改用 `/messages/*` 一套），**这条可以算废弃**。
>
> 顺带：`api/community.js` 里的 `getUnreadSummary` / `markAllRead` / `clearMessages`
> 已是**死导出**（无任何调用方），可以一起清掉。

---

## 十、设置（唯一入口：设置页）

**现状：同一个设置在两个地方各写一遍**，写的是同一张表、同一批键：

| 位置 | 内容 | 问题 |
|---|---|---|
| `views/Settings.vue` §5 通知设置 | 8 个开关 + 2 个时间 | 保存是 400ms 防抖，`catch {}` **静默失败** |
| `components/MessageCenter.vue` 齿轮面板 | **同样 8 个开关 + 同样 2 个时间** | 两处 UI 一套数据，改一处另一处不同步 |

**做法**：
1. **消息中心的设置面板删掉**，齿轮改成「消息设置」→ 跳 `/settings#sec-notify`
2. 开关粒度改成 **9 个大类**（chat / social / learning / plan / evaluation / career / todo / system / admin），
   加两个独立项：**每日学习推荐**（三合一）、**每日总结**
3. 新增 **免打扰时段**（起止时间，此时段内不弹桌面通知，站内照收）
4. 设置项描述要跟着新语义改（例：`daily_rec_enabled` 现在写"每日个性化题目推荐"，
   实际是**学习内容 + 题目 + 视频三合一**）

**新增设置项：每日推荐的「推荐依据」**（`daily_rec_source`）——
三选一：**结合**（默认）/ **按我的资料** / **按做题记录**，见 §六。

**表列变更**（`notification_settings`）：现有 8 列之外补
`career_enabled` / `todo_enabled` / `admin_enabled` / `dnd_start` / `dnd_end` / `daily_rec_source`。
**后端必须真的读这些开关**（现在没有任何代码读它们 —— 开关全是装饰，这是本轮要修的）

✅ **2026-10-08 接上了**，读开关的地方统一在 `daily_generator.deliver()`：

| 键 | 谁读 | 说明 |
|---|---|---|
| 九个大类开关 | `notify()` 的 `switch_of(notif_type)` | 改造前没有任何代码读，**开关全是装饰** |
| `daily_rec_enabled` / `daily_summary_enabled` | `daily_generator.deliver()` | 两条生成链路各判各的 |
| `daily_rec_time` / `daily_summary_time` | 同上 | 调度器按它决定「到点没」。**此前全仓零消费方** |
| `daily_rec_source` | `_pick_focus`（原本就生效） | mix / profile / history + 两条回落 |

⚠️ **默认值只有一份**：`utils/notification.DEFAULT_SETTINGS`。
设置页（`GET /messages/settings`）与调度器都从它取 ——
此前设置页里硬编码了一份 `{"daily_rec_time": "08:00", …}`，而调度器读的
`DEFAULT_SETTINGS` 里**没有**这两个键，于是**设置页显示 08:00、后台按「随时发」跑**。

⚠️ **两个时间键的列默认值**在建列语句里（`sql/fix_settings_tables.sql`：`08:00` / `07:00`），
与 `DEFAULT_SETTINGS` 保持一致。库里存回来的是 `08:00:00`（带秒），
判断时取前 5 位（`time_reached` 已处理）。

## 十一、实施顺序

1. **SQL 迁移**（幂等）：`notifications` 加列（`group/actor_id/last_at/read_at/is_todo/handled_at/deleted_at/payload`）
   + 唯一索引 + 补 GRANT；`notification_settings` 加分类开关与免打扰列；
   线上 5 行旧数据回填 `group`/`last_at`
2. **后端**：注册表 → `notify()` 收编 5 个写入方 → 新读接口（含 `read-by-route`）→ 废弃旧接口
3. **前端骨架**：消息中心重写（注册表驱动 Tab/图标/跳转/**配色**）→ 角标统一走 `/messages/badges`
   → 全局路由守卫接 B 路径 → 侧边栏/桌宠/浏览器标题接入
4. **帖子锚点**：`/community?post={id}&comment={cid}`（评论类消息的落点，B 路径依赖它）
5. **接消息点**：按 §三 清单逐个接线（每个点 = 一行注册 + 一次 `notify()`），
   分批：先 **待办型 + 好友 + 学习闭环**，再社交聚合，最后运营类
6. **每日学习推荐三合一**（§六）：先修 `get_active_users()` 取错表，再接定时任务与设置开关
7. **通道**：桌面端原生通知（Tauri notification）、邮件兜底（`system` 类 high priority）

### 5.4 详情视图（2026-10-07 补）

**为什么必须有这一层**：列表里的聚合行只有一句「3 人赞了你的帖子」——
**不打开详情根本看不到是谁赞的、赞的哪条**。全站 54 个消息点里，
聚合类（点赞/收藏）和长文本类（处置通知、公告、周报）都需要一个能读完的地方。

**形态**：**居中的毛玻璃弹层**（宽 660px / 高 ≤84vh / 圆角 18px），
与现有 `MessageCenter.vue` 的 `.mc-container`、以及全站毛玻璃视觉体系同一套观感：
`backdrop-filter: blur(24px) saturate(1.5)` + 半透明白底 + 柔和描边 + 大阴影，
顶部一条**该消息点渐变色**的 3px 细线（`--c1 → --c2`）。
移动端同款，只是宽度收到 94vw。

⚠️ 不是右侧抽屉 —— 2026-10-07 更正。（全站没有侧滑抽屉这种形态，别为消息中心单开一个。）

内容：

| 区块 | 内容 |
|---|---|
| 头部 | 大类标签 + 组内序号（如「学习 · 组内第 1/13 个」）+ 图标（**该消息点的渐变色**）+ 标题 + 时间 |
| 正文 | 完整内容（比列表摘要长），左侧用渐变色竖条 |
| 聚合明细 | `payload.actors`（最近 5 个触发者 + 时间）—— 由 `notify()` 累积 |
| ~~元信息~~ | ~~类型 key、点击去向、已读规则、删除规则、渐变色值~~ **2026-10-08 删掉** —— 见下方「用户不用知道这些」 |

**⚠️ 2026-10-08 两处订正：**

**① 「元信息」那一行整块删掉了。** 用户原话：「每条消息的下面有个类型，去向，规则，
这些当然不需要的，**消息只需要给有需要的**」。那是给开发和排查看的
（`learning.daily_rec` 这种类型键、`/community/chat/xxx` 这种落点、
三种已读规则的文字说明），用户看了既不懂也没用。
**列表每行下面的原始类型键也一并删了**，还有详情里「· 组内第 N/M 个」
（10-07 验配色派生时留下的调试信息）。

**② 详情体不再是「一个模子」，按内容归成七种形态。**
用户：「每一个消息都要排版好」。但**不能 66 个点各写一套模板** —— 那会毁掉
「加一个消息点 = 注册表加一行，前端零改动」这条契约。所以：

形态由**后端从注册表已有的标志推导**（`notification_registry._shape_of`），
前端只认形态名（`GET /messages/registry` 返回的 `shape` 字段）：

| 形态 | 判据 | 渲染 |
|---|---|---|
| `rec` | `payload_schema == daily_rec` | 三块预览 + 正文 + 通栏「去学习」 |
| `summary` | `payload_schema == daily_summary` | 数字卡片 + 知识点标签 + 三段文字。⚠️ 2026-10-16 起 `stats` 是**列表** `[{label,value,unit,hint}]`（张数由后端定，**取不到的指标不放卡而不是填 0**），新增 `prose_source`（ai/template/mixed）与 `bucket`；库里还留着老通知的对象形状 `{questions,mastery}`，**前端两种都认** |
| `actors` | `aggregate` | 大号数字 + 带头像圆点的名字标签 + 正文 |
| `todo` | `todo` | 「处理完才算已读」提示条 + 正文 |
| `notice` | `group == system` | 图标 + 类型名 + 正文 |
| `celebrate` | `group == career` | 居中大徽章 + 居中正文 |
| `plain` | 其余 | 分段正文（兜底） |

⚠️ **顺序有意义**：先看 payload，再看 `aggregate` / `todo`，最后按大类兜底 ——
例如 `todo.set_share` 既是 todo 又在 todo 组，应该走 todo 分支。
注册表里可以**逐条覆写**（`_t(..., shape="...")`），某个点想特殊处理不用改前端。

**实测分布**：`rec 1 · summary 1 · actors 9 · todo 10 · notice 12 · celebrate 9 · plain 23`。

⚠️ **通用修复**：详情正文原来直接 `{{ content }}` 渲成一整块，而 `.modal-text` 上
**没有 `white-space`** —— 模型写的 `\n\n` 被 HTML 折叠成空格，**多段并成一段**。
现在按空行切成 `<p>`（段内保留单换行）。这一条对**所有**形态都生效。
| 底部操作 | 主按钮 = 跳转目标页；次按钮 = 标记已读；`system` 组无删除 |
| 待办型 | 主按钮换成**处理动作**（接受 / 拒绝 / 去处理）→ 调 `PUT /messages/{id}/handled` |

**与已读的关系**：
- 非待办：**打开详情 = 已读**（路径 A）
- 待办：打开详情**不算**已读，点处理按钮才算 —— 抽屉正是"处理动作"的落点
- `system`：打开即已读，但详情里**没有删除按钮**（要留底）

**交互细节**：
- 聊天类不打开详情，直接进会话（聊天是"用"，不是"看"）
- 详情里点「去看看」→ 关闭抽屉 + 跳转目标页
- Esc / 点遮罩关闭

> 预览：`_devtools/message-center-preview.html` —— 点任意卡片即可看详情长什么样。
