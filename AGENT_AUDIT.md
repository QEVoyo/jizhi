# 智能体协作审计（小基 × 其他智能体）

> ## 📌 文档状态：**2026-09-10 的快照。核心结论至 2026-10-16 仍未修复 —— 这是一份还没还的欠账清单。**
>
> **2026-10-16 逐条核过现状**，所以下面不是"可能过时"，是"确认还准"：
>
> | 结论 | 现状 |
> |---|---|
> | **§三 planner / generator / evaluator 是不可达死代码** | ✅ **仍成立**。三个文件仍各 25 行、mtime 仍是 **2026-07-18**（审计后没被碰过）；`routers/chat.py` 的三条 `if req.intent ==` 分支仍在；全仓仍无调用方 |
> | **§4.3 `agent_prefs` 只写不读** | ✅ **仍成立**。读取点仍只有 `agent_center.py` 自己的接口和 `tuning.py` 的规则比对；出题仍硬编码难度 |
> | **§4.4 磨合闭环的运维隐患** | ✅ **仍成立**。`tuning.py` 仍是 `while True: await asyncio.sleep(24*3600)` —— **先睡再干活**，重启即错一整天；活跃用户查询仍 `limit:5000` **无 order** |
>
> **已经变了的部分**（看这几节时要打折）：
> - §2「呼叫对象 5 项下拉 + 规划/评估纯说话」—— **09-10 当天就改成了自动判别分流**
> - §4.1 chat 空账的**依据**变了（现在有 `recordAction('chat')`，但不带 touchpoint，
>   **结论仍成立、理由已换**）
> - §4.5(c) 硬编码进度条 —— 已改成真实 `setStage`
> - §6 待决策五项：**① ② 已完成，④ 半完成**（`detect-intent` 端点 09-11 删了，
>   但三个文件 + 三条分支还在），③ ⑤ 未动
>
> ⚠️ **行号必然已漂移**，拿 `文件:行号` 定位代码前先确认。
> **内容一个字没删** —— 改它等于把有效的欠账擦掉。后续相关工作散在 `PROJECT_LOG.md` 和 `logs/` 里。

> 2026-09-10 · 起因：用户提出「小基与其他智能体的搭配配合，之前只搞了大概框架，其实并没有搞好」
> 本文为**现状实测记录**：每条结论均带 `文件:行号` 证据，区分「真实运行」与「声明但未落地」。
> 修复记录见 §5；方向选项见 §6（**待用户拍板**）。

---

## 一、一句话结论

> **框架的「记账层」建得完整且精致，但账记的不是真实发生的事；「干活层」只做了生成 Agent 一个；设计里承诺的「参数回流到调用时」从来没写；而页面画的协作链路，与用户实际走的路径是反的。**

---

## 二、真实运行的那套：小基的呼叫对象，深浅差一个数量级

Web 主界面就是小基（`views/Home.vue` 只有 `<XiaojiCall />`），没有别的对话入口。它的呼叫对象 5 项（`XiaojiCall.vue:874-880`）：

| 呼叫对象 | 后端真实行为 | 深度 |
|---|---|---|
| 队长（小基） | 陪伴人设 + 10 轮上下文 | ✅ 真聊天 |
| **规划 Agent** | 换人设 + 注入真数据（计划数/30天完成率/近7天/自定义计划）→ **纯说话** | ❌ 会说不会做 |
| **评估 Agent** | 换人设 + 注入真数据（做题/正确率/薄弱TOP5/真题卷）→ **纯说话** | ❌ 会说不会做 |
| **生成 Agent** | 选题（60天掌握度薄弱→错题主题→综合）→ 真实出题落库 → 题目卡 | ✅ 全链路 |
| 自定义出题 | 表单 → 同一个真出题管线 | ✅ 全链路 |

- `AGENT_PERSONAS` 只注册了 **plan / evaluate 两个**（`community/xiaoji.py:42-61`）——规划与评估**不产出结构化结果、不写任何数据、不触发任何动作**，是「带着真数据的聊天」。
- 只有生成 Agent 真干活（`/xiaoji/agent-generate` → `generate_question_core` 落库），**它是唯一范本**。
- 数据底座是真的：`_collect` 并发拉 16 张真实表（`agent_center.py:129+`）；反幻觉纪律写进了人设（`community/xiaoji.py:46-60`「只引用【真实数据】里的数字，绝不编造」）。

**缺的不是数据，是「干活」那一层——数据全在，队友们拿了数据只用来聊天。**

---

## 三、被登记为「智能体」的那套，是不可达死代码

`agents/planner.py` / `generator.py` / `evaluator.py` 各 25 行，**三份系统提示词只差一个词**（「规划专家」/「学习助手」/「评估专家」），其余逐字相同，且都不做实事。证据链：

| 环节 | 事实 |
|---|---|
| Web 端 | **零调用** `/chat/*`（全站搜索无结果；`api/chat.js`、`components/ChatArea.vue` 均已不存在） |
| 小程序 | 调 `/chat/send`，但请求体只有 `user_id/messages/temperature`（`jizhi-miniapp/src/pages/index/index.vue:138-142`）——**不传 `intent`** |
| 默认值 | `ChatRequest.intent` 默认 `"chat"`（`chat.py:29`）→ 永远走默认分支 |
| 意图路由 | `/chat/detect-intent`（`chat.py:58`）在**后端、Web、小程序里都是零调用** |

→ `chat.py:188-198` 的三条 `if req.intent == "plan"/"generate"/"evaluate"` **永远不执行**。

**附带硬伤**：这三个 agent 读 `user_profile.get('level', '中等')`（`planner.py:24`、`evaluator.py:24`），但 `get_user_profile` 返回的键是 `learning_stage/grade/major/learning_goal/weak_topics/…`——**`level` 不存在，恒为「中等」**；画像数据拉了一整路没人用。

---

## 四、智能体中心的账目问题

### 4.1 触点真伪（19 条声明）

| 状态 | 触点 |
|---|---|
| ✅ 真打点 | plan 4/4、generate 4/4、xiaoji 7/7、evaluate 仅「真题交卷分析」、chat 仅「词义讲解」 |
| ❌ **空账**（声明了但没有产生者） | chat「答疑对话」（主对话 UI 已删，前端无 `recordAction('chat')`）、chat「日志摘要」（`api/tools.js:42` 无调用方）、evaluate「做题提交批改」（`ai_feedback` 在 `subject_plan.py:1016` 算出，但落库 payload `:1025-1038` **不含该字段**→ 该触点结构上恒为 0）、evaluate「画像 AI 总结」（只写 `selected_topics/achievements`，从不写 `data` 列） |
| ⚠️ 多出一笔 | `Wordbook.vue:59` 写 `touchpoint='wordbook'`，但**无触点声明认它** |

### 4.2 协同增益（`agent_center.py:702-718`）

- 全部请求时实算，非硬编码；但**无最小样本门槛**（1 条 vs 1 条也能算出 +100%），返回体无样本量字段
- `generate × mastery` 一对 `base=None` → **delta 恒为 null**（设计稿第 74 行承诺「定向生成前后掌握度变化」，实现未做，代码注释自认「前后对比 v2」）
- `chat × practice` 的对照组基于 chat 打点，而 chat 打点为 0 → **空集在比**
- 正增益时文案固定输出「陪伴、讲解、批改、定向生成都在真实拉动」——不管实际哪对为正
- `evaluate` 路由 warn **硬编码 False**（`:739-740`）、`generate` warn 恒 False（`:737`）→ 「瓶颈链路结论」实际只可能由 plan 触发

### 4.3 磨合闭环是断的：参数**只写不读**

`agent_prefs` 的全部读取点只有两处——智能体中心的显示/写入接口（`agent_center.py:804/817`）与 tuning 自己写回时比对旧值（`tuning.py:167/188`）。

**没有任何 agent 在真正被调用时读它**：出题不看 `gen_difficulty`、规划不看 `plan_tasks`、小基不看 `xj_care`。

对照设计原话（PROJECT_LOG 第 83 条）：「规则引擎自动微调 agent 参数 → **下次调用实时拼装**」——**这一层从第一天就没落地**。智能体中心的「参数调节 / 自动托管」目前是装饰性的。

### 4.4 后台磨合循环的运维隐患

- `tuning.py:256` **先 `sleep(24h)` 再干活** → 每次重启计时清零；开发模式 `--reload` 下基本永远不会跑；生产也需进程连续存活 24h 才轮到第一次；多 worker 各跑一份
- `_active_users` limit 5000 且无 order → 任意截断

### 4.5 前端侧的「摆设」

- 「自动托管」开关**不调接口、无 watcher**，只有点保存才顺带落库
- chat / evaluate 的「一键应用」**只改文案不写参数**
- 小基页的智能体进度条是硬编码 4 步动画（`useXiaojiAvatar.js:33-38`），与真实 agent 无关
- `mockAgents.js` 的 `collaboration` 假数据已无 import（死代码）

### 4.6 小基压根不在协作链上（页面画的与真实路径相反）

智能体中心画的闭环链是 `chat → plan → evaluate → generate → 掌握度`（`agent_center.py:667-680`）——**小基不在链上**，被放在旁边叫「并行入口」（`:651-659`）。

全平台唯一把小基与其他 agent 连起来的表达，是协同增益里那一对 `["xiaoji","plan"]`。

**而现实相反**：Web 端小基是唯一的对话入口，`chat` agent 是空壳。

---

## 五、本轮修复（2026-09-10，用户「改」）

| # | 问题 | 修法 |
|---|---|---|
| ① | **同一次点击被记 3 次**：`_action_count` 不传 touchpoint 就不过滤来源（`agent_center.py:223-231`），而 `use_plan_agent` 同时挂在 chat/plan/xiaoji 三处；`total_calls` 又把各 agent 相加（`:649`）→ 整体虚高 | ①chat 三个「分流」改为 `action_meta` + `touchpoint: "chat_main"`（主对话的埋点约定；主对话不在则如实计 0）；chat 详情的「意图路由分布」图同步同口径<br>②新增 `_distinct_action_count()`：总调用数的 action 部分按**去重事件**统计，业务表部分正常相加<br>③`ACTION_SOURCES` 常量抽出复用 |
| ② | **闭环链配色全掉**：前端读 `l.agentKey`，后端返回 `agent_key`（`AgentCenter.vue:56` vs `agent_center.py:668`）→ `agentColor(undefined)` | 改为 `l.agent_key`（与同文件 `:108-110` 的 routing 用法一致） |
| ③ | **队员署名串台**：选中队员后发图片/视频，`pendingAgent` 在 `:1745` 置位后无人清理（图片/视频分支完全绕过角色），清零点只在流式成功路径上（`:1851`）→ 下一条消息被错误署名 | ①`streamXiaojiChat` 把清零点**提前到读取处立即消费**（请求失败也不残留）<br>②图片/视频分支显式 `pendingAgent = null`（该链路不经过队员人设） |

**验证**：构造假数据实测去重逻辑——chat 分流 4→**0**、plan 3、xiaoji 4 各归其位；总调用数 **9→5（真实值）**；`py_compile` ✅；`vite build` 1.32s ✅。

> 更正一处子代理结论：`generateFellowQuestion` 有 `finally { pendingAgent = null }`（`XiaojiCall.vue:1013-1014`），**不存在泄漏**。

---

## 六、待决策的方向（未动）

按优先级：

1. **评估 Agent 产出结构化评估卡**——复用 `/evaluation/deep-analysis` 的评级/核心问题/归因/行动，而不是另起一套；切口最小，顺手补上现在 `None` 的那条断链
2. **规划 Agent 真能建/改计划**，输出计划卡而不是建议文字
3. **让 `agent_prefs` 被读取**（至少出题难度、任务量各接一条），磨合才算闭环
4. **清账**：死掉的 `/chat` 三 agent 要么删、要么让小程序真正用起来；触点空账补齐或摘除
5. **「对话 Agent」的归属**要定：08-27 已拍板「并入队长小基」，但智能体中心仍把它当独立 agent 记分流的账——账要与事实对齐

**共通前提**：把「队友」从「换人设说话」升级为「带工具干活」，并让产出真的落库、能被下游读到——即把**生成 Agent 那套复制到规划/评估**。
