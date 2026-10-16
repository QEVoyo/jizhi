# 智能体中心 — 数据设计（触点清单 + 数据源映射）

> 原则：**能用现有表就不建新表**。调用计数统一走 `user_actions`（metadata 已支持），
> 效果指标统一走业务表。新建表只有 2 张（`agent_prefs` / `agent_tuning_log`）+ 2 个补列。
> DDL 见 `backend/sql/agent_center_tables.sql`。

---

## 一、触点清单（**25 个** —— 以 `routers/agent_center.py` 的 `TOUCHPOINTS` 为准）

> ⚠️ **2026-10-16 按代码重新点过数。** 本节原写 19 个，实际是 **25 个**：
> chat 6 · plan 4 · generate 4 · evaluate 4 · xiaoji 7。
>
> 差的 6 个来自两处，性质不同：
> - **+3 是计数口径变了** —— 三个「分流」触点（规划/生成/评估）
>   现在**在 chat 和对应 Agent 下各记一次**（同一个动作、两个视角），本节原来只记一次。
> - **+3 是小基真的多了触点** —— 语音通话、工具使用、快捷提问分流。
>
> 另外：本节原来所有 🔶/🆕 标记**现在都已落地**（`agent_center_tables.sql` 的
> `xiaoji_messages.kind` 与 `subject_plans.source` 两个补列、词条三件套、
> `GenerateFromMastery.vue` 的 `touchpoint: 'mastery_generate'`），下面已相应更新。

打点方式两选一：**A. user_actions 埋点**（统一计数来源）/ **B. 业务表直接计数**（已天然记录）。

### 对话 Agent（chat）
| # | 触点 | 场景 | 打点 | 状态 |
|---|---|---|---|---|
| 1 | 答疑对话 | 主对话区 | A `chat` + metadata.touchpoint=`chat_main` | ✅ 已埋 |
| 2 | 词义讲解 | 对话·词条卡 | B `vocab_lookups` | ✅ 已落地（词条三件套早已建表） |
| 3 | 规划分流 | 对话→规划 Agent | A `use_plan_agent` + touchpoint=`chat_main` | ✅ 已埋（与 plan #4 是同一动作的两视角） |
| 4 | 生成分流 | 对话→生成 Agent | A `use_generate_agent` + touchpoint=`chat_main` | ✅ 已埋（与 generate #8 同一动作） |
| 5 | 评估分流 | 对话→评估 Agent | A `use_evaluate_agent` + touchpoint=`chat_main` | ✅ 已埋（与 evaluate #12 同一动作） |
| 6 | 日志摘要 | 自动 | B `learning_logs` 计数 | ✅ 无需埋点 |

> ⚠️ 答疑对话那个触点带 `touchpoint='chat_main'` 过滤**不是可有可无的**：
> 不带过滤的话，小基队友栏写的 `use_*_agent` 也会被算进「对话 Agent」，
> 而那是小基的分流、不是对话 Agent 的。Web 端主对话已由小基取代，**如实计 0**。

### 规划 Agent（plan）
| # | 触点 | 场景 | 打点 | 状态 |
|---|---|---|---|---|
| 7 | 聊天里问规划 | 对话（= chat #3「规划分流」，同一动作两视角） | A `use_plan_agent` | ✅ 已埋 |
| 8 | 诊断生成计划 | 考纲页 | B `diagnosis_results` 计数 | ✅ 无需埋点 |
| 9 | 答卷生成计划 | 真题卷 | B `subject_plans.source='exam_paper'` | ✅ 补列已加 |
| 10 | 每日学习讲解 | 每日任务 | B `plan_daily_tasks.learning_content` 非空 | ✅ 无需埋点 |

### 生成 Agent（generate）
| # | 触点 | 场景 | 打点 | 状态 |
|---|---|---|---|---|
| 11 | 聊天里出题 | 对话（= chat #4「生成分流」） | A `use_generate_agent` | ✅ 已埋 |
| 12 | 资源库生成 | 资源库 | A `generate_question` + touchpoint=`reslib_generate` | ✅ 已埋 |
| 13 | 掌握度定向生成 | 资源库 | A `generate_question` + touchpoint=`mastery_generate` | ✅ 已补（`GenerateFromMastery.vue:234`） |
| 14 | 题集创建 | 资源库 | A `create_set` | ✅ 已埋 |

### 评估 Agent（evaluate）
| # | 触点 | 场景 | 打点 | 状态 |
|---|---|---|---|---|
| 15 | 聊天里问评估 | 对话（= chat #5「评估分流」） | A `use_evaluate_agent` | ✅ 已埋 |
| 16 | 做题提交批改 | 做题页 | B `question_records.ai_feedback` 非空 | ✅ 无需埋点 |
| 17 | 真题交卷分析 | 真题卷 | B `exam_paper_records` | ✅ 无需埋点 |
| 18 | 画像 AI 总结 | 个人画像 | B `profile_card_settings` | ✅ 无需埋点 |

### 小基（xiaoji）
| # | 触点 | 场景 | 打点 | 状态 |
|---|---|---|---|---|
| 19 | 小基聊天 | 小基页 | B `xiaoji_messages.kind='chat'` | ✅ 补列已加 |
| 20 | **语音通话** | 通话页 | B `call_logs` | ✅ 已落地（**本节原先没有这一条**） |
| 21 | **工具使用** | 小基工具区 | A `action` | ✅ 已落地（原先没有） |
| 22 | 词条抓取 | 识图拍题提词 | B `vocab_lookups` | ✅ 已落地 |
| 23 | 小基识图 | 小基页 | B `xiaoji_messages.kind='vision'` | ✅ 补列已加 |
| 24 | 评价题目/题集 | 小基页 | B `xiaoji_messages.kind='evaluate'` | ✅ 补列已加 |
| 25 | **快捷提问分流** | 小基页·队友栏 | A `action_touch` | ✅ 已落地（原先没有） |

**结论（2026-10-16 更新）**：**25 个触点全部已落地**，**0 个需要为计数建新表** ——
当初那句「能用现有表就不建新表」守住了。

> 原写的是「19 个里 12 个现成可计数，4 个小改动，2 个随词条走」。
> 那 4 个小改动（2 个补列 + 1 个 metadata + 小基 kind 写入）和词条三件套**现在都完成了**：
> `agent_center_tables.sql` 加了 `xiaoji_messages.kind` 与 `subject_plans.source`，
> `GenerateFromMastery.vue` 补了 `touchpoint`，词条三件套在 `vocab_tables.sql` 里。

---

## 二、指标 → 数据源映射（中心页 + 详情页全部字段）

### 中心页（协作分析）
| 展示 | 数据源 | 查询方式 |
|---|---|---|
| KPI 总调用次数 | `user_actions` | 按 action_type 聚合（chat/use_*_agent/generate_question/create_set） |
| KPI 活跃智能体 | 同上 | 时间范围内 distinct action_type |
| KPI 平均计划完成率 | `plan_daily_tasks` | completed=true 占比（全用户/单用户） |
| KPI 生成题目 / 批改题量 | `generation_history` / `question_records.ai_feedback` 非空 | 计数 |
| KPI 词条抓取 | `vocab_lookups` 🆕 | 第二阶段 |
| 协作闭环各环节数字 | 各业务表（同上表） | 计数/去重 |
| 协同增益 ×5 | 跨表 join（见下） | 对照组 vs 协同组 |
| 路由转化 | `user_actions.use_*_agent` × 产出表 | join |

**协同增益 5 个联合查询**：
1. 小基 × 规划：`xiaoji_messages` 有消息的日期 → `plan_daily_tasks` 当日完成率 vs 无消息日
2. 规划 × 练习：`plan_daily_tasks.learning_content` 非空的任务完成率 vs 为空
3. 评估 × 练习：`question_records` 同 question_id 首答 vs 末次作答正确率
4. 生成 × 掌握度：定向生成前后 `user_kp_mastery.mastery_score` 变化
5. 对话 × 练习：`user_actions.chat` 当日 × `question_records` 当日做题量 vs 无对话日

### 详情页（单智能体）
| 展示 | 数据源 |
|---|---|
| 主指标趋势（30 天） | 各业务表按 created_at 日聚合 |
| 特点面板 1/2 | 各业务表分组聚合（phase / difficulty / 来源构成） |
| 磨合记录 + 趋势图 markLine | `agent_tuning_log` 🆕 |
| 参数调节 | `agent_prefs` 🆕 |

---

## 三、接入步骤（后端）

1. ✅ **执行 DDL**：`backend/sql/agent_center_tables.sql`（2 表 + 2 补列 + GRANT，可重复执行）
2. ✅ **补埋点**：
   - `GenerateFromMastery.vue` → recordAction 带 `metadata: { touchpoint: 'mastery_generate' }`
   - `community/xiaoji.py` 写消息时带 `kind`（chat/vision/evaluate）
   - `exam_papers.py` 答卷生成计划写 `subject_plans.source='exam_paper'`（代码早有，建列即生效）
3. ✅ **聚合路由** `backend/routers/agent_center.py`：
   - `GET /agent-center/overview` — KPI + 闭环 + 协同增益 + 路由转化（单连接 gather 并发）
   - `GET /agent-center/agents/{key}` — 主指标趋势 + 特点面板 + 触点计数
   - `GET/PUT /agent-center/agents/{key}/prefs` — 参数读写（agent_prefs）
   - `GET/POST /agent-center/agents/{key}/tuning` — 磨合记录（agent_tuning_log）
   - `POST /agent-center/tuning/run` — 立即执行磨合规则评估
4. ✅ **磨合规则引擎**（`backend/agents/tuning.py`）：
   - 6 条规则（任务量/阶段节奏/出题难度/错题针对性/错因颗粒度/关心频率）
   - 触发：详情页「立即评估」按钮 + 后台每日任务（近 14 天活跃用户，main.py lifespan）
   - 保护：自动托管开关、7-14 天冷却期、新用户不打扰
5. ✅ **前端接入**：`api/agentCenter.js` + AgentCenter/AgentDetail 全部真实数据驱动，参数/磨合真读写

### 剩余（第二阶段）—— 2026-10-16 核实

- [x] ~~词条三件套（`vocab_entries` / `vocab_lookups` / `word_mastery`）随词条功能立项~~
      —— **已做完**。三张表在 `backend/sql/vocab_tables.sql`，
      功能也齐了（`routers/vocab.py` + `views/Wordbook.vue`）
- [ ] **聊天内评估产出独立记录**（v2 补埋）—— **仍未做**。
      `agent_center.py` 里明写「暂未单独统计」
- [ ] **管理端全局视角** —— **仍未做**

---

## 四、与前端预览的对应关系

- `utils/mockAgents.js` 每个字段的注释（✅/🔶/🆕/⚠️）就是本清单的字段级映射
- ✅ 词条三件套（`vocab_entries` / `vocab_lookups` / `word_mastery`）**已随词条功能建好**
- ✅ 页面无需再改：**mock → 真实 API 的替换早已完成**，展示结构已定稿

> ⚠️ **2026-10-16**：`mockAgents.js` 里**仍残留过期注释**（「词条表待建」、
> 「`subject_plans` 需加 source 列」这类）—— 正是上面说的那批字段级映射，
> **现在与实际状态脱节了**。映射关系本身还对，只是状态描述该清了。
