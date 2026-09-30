# 基智学习助手 (Jizhi Learn) — 项目总日志

> 架构演进 / 关键决策 / 文件索引 · 最后更新：2026-09-30
> 每日变更记录见：[logs/](./logs/)
> 系统说明书见：[SYSTEM_MANUAL.md](./SYSTEM_MANUAL.md)

---

## 项目架构（考纲体系）

```
┌──────────────────────────────────────────────────┐
│              考纲列表（15 个高频考试）              │
│  CET-4 / CET-6 / 考研 / 雅思 / 托福 / 计算机二级... │
│         搜索 · 筛选 · 收藏                         │
└────────────────────┬─────────────────────────────┘
                     │ 点击考纲
                     ▼
┌──────────────────────────────────────────────────┐
│              考纲详情页                            │
│  ┌──────┬──────┬──────┬──────┬──────┐            │
│  │ 概览  │ 题库  │每日  │知识点│错题  │ ← Tab     │
│  │(首页)│(始终)│任务* │(计划)│本*   │            │
│  └──────┴──────┴──────┴──────┴──────┘            │
│  概览：说明书式介绍 + 摸底/题库/真题入口按钮         │
│  题库：题目作答状态(薄弱/待巩固/优势) + 每题练习按钮   │
│  * 需先生成计划后才出现                            │
└────────────────────┬─────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────┐
│          诊断摸底 → AI 批改 → 生成计划              │
│          每日任务 → 做题 → AI 批改 → 掌握度         │
└──────────────────────────────────────────────────┘
```

### 数据存储

| 存储 | 用途 | 详情 |
|---|---|---|
| **本地 JSON** | 题库数据 | 17 考纲 × JSON 文件，启动时全量加载到内存 |
| **本地 JSON** | 考纲配置 | `backend/data/syllabi.json` — 17 考纲元数据（含 target_count / exam_papers / intro） |
| **Supabase** | 用户数据 | subject_plans / diagnosis_results / plan_daily_tasks / question_records / user_kp_mastery |
| **localStorage** | 考纲收藏 / 题目收藏 | 前端持久化，jizhi-fav-syllabi / jizhi-fav-questions |
| **localStorage** | 全局搜索数据 | gs_recent_pages / gs_search_history / gs_custom_entries_{uid}（自定义项按用户隔离） |
| **Supabase** | 管理后台 | user_feedback / user_qa / content_reports / system_announcements / admin_audit_logs |

### 备考计划双通道（2026-08-12 新增）

```
生成备考计划
├── 通道一：摸底生成 — 诊断答题 → AI 评估 → 生成计划
└── 通道二：答卷生成 — 已完成真题卷 → AI 分析错题 → 生成计划
                        （未完成的卷子灰色禁用）

计划生成时（快）：AI 只分配题目任务
  三阶段：基础期(易,补弱项) → 强化期(中,全覆盖) → 冲刺期(难,综合实战)
  任务带 category + question_type + question_count → 可被 bank_query 查到真实题目

每日进入时（懒加载）：
  📖 学习讲解 — AI 按本日题目实时生成（目标/知识点/方法/易错点）→ 缓存
  ✏️ 去练习 — 带真实题目跳做题页
  🎬 视频推送 — 灰色占位（即将上线）
```

### 角色体系（2026-07-26 新增）

```
super_admin (超级管理员)
  └─ 全部权限 + 可设/撤管理员
      │
      admin (管理员)
        └─ 管理用户 & 内容，不能管其他管理员
            │
            user (普通用户)
              └─ 无管理后台权限
```

- profiles 表新增 `role` 字段（TEXT DEFAULT 'user'），兼容旧 `is_admin`
- 超级管理员在用户管理页可看到「设为管理/撤管理」按钮

### 题库数据分布（19,338 题，17 考纲全部达标）

| 维度 | 数量 | 题型 |
|---|---|---|
| 15 个传统考纲 | 16,651 | 11 种题型（choice/fill/cloze/translation/essay/calculation/programming...） |
| 2 个算法考纲 | 1,669 | programming（带测试用例 + 多语言判题） |

**目标**：全部 17 考纲 ≥ 18,900 题（target_count 合计），2026-09-15 复核**已全部达标** ✅

### 真题套卷（2026-08-12 新增）

`backend/data/exam_papers/` — 每套真题一个 JSON，12 套覆盖全部中国考试考纲：

| 考纲 | 题数 | 说明 |
|---|---|---|
| CET-4 / CET-6 | 32q | 听力跳过（缺音频），可练 568/532.5 分 |
| 考研英语/数学/政治 | 52/22/38q | 全卷完整 |
| 法考（卷一）| 100q | 全卷完整 |
| 教资 / CPA | 36/28q | 全卷完整 |
| 二级 Python/C | 33q | 精选（差~10选择）|
| 二级 Office | 20q | 选择题全（操作题跳过）|
| 公务员行测 | 101q | 精选（差~34题）|

- 卷面分区 sections + 不可练卷面 `disabled` 标记 + `available_score`
- 主观题带评分标准 `grading_rubric`，客观题带中文解析 + `ai_analysis_hint`
- 双通道：做题模式（隐藏答案+计时+交卷出分）/ 解析模式（历史答案+正确率+AI 错因分析）
- 交卷后错题 AI 批量分析（异步），缓存到 `exam_paper_records` 秒开

### 全局搜索（2026-08-23 新增）

```
入口一：主界面侧边栏顶部搜索框
入口二：任意页面 Ctrl+K（命令面板）

空态 ── 最近访问（✕单删/清空） · 搜索历史（chip ✕/清空） · 自定义（＋添加→选择器点选）
输入 ── 实时模糊匹配，五组索引：页面 / 自定义 / 考纲(17) / 真题(12) / 智能体(5) / 词条本
跳转 ── Enter / 点击直达；词条跳 /wordbook?q= 定位+高亮
```

- 命名册 `utils/pageMeta.js` 单一数据源：全站页面（含侧边栏没有的）名称 + 别名（中文/英文/拼音首字母），供搜索（及未来面包屑/标题）共用
- 索引数据零后端改动：考纲+真题一次 `GET /subject-plan/syllabi` 全拿（过滤 grey 占位卷）；词条本 `/vocab/wordbook`
- 自定义项为「钉选式」：选择器列出全部可快捷进入页面，点选收录/移除，名称路径零手填；重命名旧名自动保留进别名

### 考纲卡片（17 个）

| ID | 名称 | 题库 | 目标 | 状态 |
|---|---|---|---|---|
| cet4 | CET-4 英语四级 | 1098 | 1000 | ✅ 110% |
| cet6 | CET-6 英语六级 | 1073 | 1000 | ✅ 107% |
| grad-english | 考研英语 | 819 | 800 | ✅ 102% |
| ielts | 雅思 IELTS | 1020 | 1000 | ✅ 102% |
| toefl | 托福 TOEFL | 1019 | 1000 | ✅ 102% |
| grad-math | 考研数学 | 1209 | 1200 | ✅ 101% |
| grad-politics | 考研政治 | 1523 | 1500 | ✅ 102% |
| ncre2-python | 计算机二级 Python | 1017 | 1000 | ✅ 102% |
| ncre2-c | 计算机二级 C语言 | 818 | 800 | ✅ 102% |
| ncre2-office | 计算机二级 MS Office | 1014 | 1000 | ✅ 101% |
| public-service | 公务员 行测 | 2017 | 2000 | ✅ 101% |
| teacher-cert | 教师资格证 | 817 | 800 | ✅ 102% |
| cpa | 注册会计师 CPA | 1217 | 1200 | ✅ 101% |
| judicial | 法律职业资格 | 1528 | 1500 | ✅ 102% |
| mandarin | 普通话水平测试 | 619 | 600 | ✅ 103% |
| algorithm-ds | 算法与数据结构 | 2001 | 2000 | ✅ 100% |
| acm-icpc | ACM-ICPC 竞赛 | 529 | 500 | ✅ 106% |
| **总计** | — | **19,338** | **18,900** | **102%** |

> 上表 2026-09-15 按 `backend/data/*.json` 实际条数重算（旧表是批量扩产前的快照，public-service / cpa / algorithm-ds 三行当时还没跑完，总计误记作 18,320）。**17 个考纲现已全部达标。**

---

## 前端页面

| 路由 | 文件 | 说明 | 状态 |
|---|---|---|---|
| `/` | `Landing.vue` | 🆕 落地页（访客首页）— 长滚动叙事 + CSS 科幻 mockup 轮播 + 星空/打字机/轨道线/小基伴游等交互 | ✅ |
| `/qa` `/open-source` | QAPage.vue / OpenSource.vue | 🆕 已公开（无需登录） | ✅ |
| `/subject-plan` | `SyllabusHub.vue` | 考纲列表：搜索+筛选+收藏（N+1 已优化） | ✅ |
| `/subject-plan/:syllabusId` | `SyllabusDetail.vue` | 考纲详情：概览首页 + 题库（含题目状态）+ 每日/知识/错题 + 🆕 生成计划双通道弹窗 + 🆕 每日学习讲解 | ✅ |
| `/subject-plan/:syllabusId/practice` | `SubjectPractice.vue` | 做题页：11 种题型 + 编程题左右分栏 OJ（洛谷风）+ 做题倒计时 + 科幻毛玻璃 | ✅ |
| `/subject-plan/:syllabusId/exam/:paperId` | `ExamPaper.vue` | 🆕 真题套卷：做题模式（计时+交卷出分）/ 解析模式（历史答案+正确率+AI 错因分析）+ 生成计划 | ✅ |
| `/settings` | `Settings.vue` | 统一设置中心：**10 模块**（个人/偏好/外观/桌宠(仅桌面壳)/隐私/通知/快捷键/安全/AI/关于）。**全站唯一入口**，首页齿轮也指向它 | ✅ |
| `/agent-center` | `AgentCenter.vue` | 🆕 智能体中心：5 agent 效果统计 + 对比图 + 卡片（点击进详情）——2026-08-23 已接真实数据 | ✅ |
| `/agent-center/:agentKey` | `AgentDetail.vue` | 🆕 智能体细节调节：趋势图 + 触点明细 + 参数调节（自动托管）+ 磨合时间线——2026-08-23 已接真实数据 | ✅ |
| `/wordbook` | `Wordbook.vue` | 🆕 词条本：统计/筛选/复习模式/薄弱词出题 + 搜索跳转定位高亮（2026-08-23） | ✅ |
| `/guide` | `Guide.vue` | 🆕 使用说明书：封面/简介/快速上手/功能速览/常用操作/注意事项（侧边栏底部入口，2026-08-23） | ✅ |
| `/xiaoji/search` | `XiaojiSearch.vue` | 🆕 小基搜索页：实时模糊搜索 + 抖音风搜索历史 + 点结果跳回聊天页定位高亮 | ✅ |
| `/xiaoji/voice-call` | `XiaojiVoiceCall.vue` | 🆕 语音通话（2026-08-25）：千问 realtime 实时语音对话 + 实时字幕 + 抢话打断 + 静音/挂断 | ✅ |
| `/profile-card` | `ProfileCard.vue` | 个人画像：维度宇宙（九颗程序化星球 + 中央黑洞，点黑洞退出；侧边栏独立入口） | ✅ |
| `/evaluation-center` | `EvaluationCenter.vue` | 评估中心：3 竖排卡片（学情报告/评估表/学习规划） | ✅ |
| `/qa` | `QAPage.vue` | 帮助中心：7 分类 29 FAQ + 搜索 + 提问 | ✅ |

**已删除的路由**：`/subject-plan/bank`、`/subject-plan/diagnosis`

### 管理后台页面（2026-07-26 新增）

| 路由 | 文件 | 说明 | 状态 |
|---|---|---|---|
| `/admin` | `AdminDashboard.vue` | 主面板：统计卡片 + 快捷入口 | ✅ |
| `/admin/users` | `AdminUsers.vue` | 用户管理：搜索/封禁/设管理员（超管）/详情 | ✅ |
| `/admin/reports` | `AdminReports.vue` | 内容审核：举报/反馈/Q&A 三 Tab | ✅ |
| `/admin/questions` | `AdminQuestions.vue` | 题库管理：CRUD + 筛选 + 批量导入 | ✅ |
| `/admin/announcements` | `AdminAnnouncements.vue` | 公告管理 + 图片上传 | ✅ |
| `/admin/logs` | `AdminLogs.vue` | 操作日志 | ✅ |

### 登录页（2026-07-26 重设计）

三栏 Tab：用户登录 / 🛡管理员登录 / 用户注册。管理员登录直接跳转 `/admin`。

---

## 后端 API

全部在 `backend/routers/subject_plan.py`。

### 考纲相关

| 方法 | 路径 | 说明 | 状态 |
|---|---|---|---|
| GET | `/subject-plan/syllabi` | 考纲列表（批量查计划，1次 HTTP） | ✅ |
| GET | `/subject-plan/syllabi/{syllabus_id}` | 考纲详情 + 计划（含 max_score/pass_score） | ✅ |
| GET | `/subject-plan/syllabi/{syllabus_id}/questions` | 题库查询（本地内存分页） | ✅ |
| GET | `/subject-plan/syllabi/{syllabus_id}/diagnosis/start` | 诊断题目抽取 | ✅ |
| POST | `/subject-plan/syllabi/{syllabus_id}/diagnosis/submit` | 提交诊断→AI 批改→生成计划（防重复） | ✅ |

### 计划相关

| 方法 | 路径 | 说明 | 状态 |
|---|---|---|---|
| GET | `/subject-plan/plans/{plan_id}` | 计划详情 | ✅ |
| PUT | `/subject-plan/plans/{plan_id}` | 更新计划 | ✅ |
| DELETE | `/subject-plan/plans/{plan_id}` | 删除计划 | ✅ |
| GET | `/subject-plan/plans/{plan_id}/tasks` | 全部任务 | ✅ |
| GET | `/subject-plan/plans/{plan_id}/tasks/today` | 今日任务+题目（去重） | ✅ |
| GET | `/subject-plan/plans/{plan_id}/done-ids` | 已完成题目 ID 列表 | ✅ |
| GET | `/subject-plan/plans/{plan_id}/questions-count` | 题目统计 | ✅ |
| POST | `/subject-plan/plans/{plan_id}/submit` | 提交答案→AI 批改→掌握度聚合 | ✅ |
| GET | `/subject-plan/plans/{plan_id}/mastery` | 知识点掌握度（EWMA 聚合） | ✅ |
| GET | `/subject-plan/plans/{plan_id}/mistakes` | 错题本 | ✅ |
| GET | `/subject-plan/mistakes/overview` | 总错题概览 | ✅ |
| GET | `/subject-plan/mistakes/practice` | 随机错题练习（批量查） | ✅ |

### 代码判题

| 方法 | 路径 | 说明 | 状态 |
|---|---|---|---|
| GET | `/subject-plan/code/languages` | 返回可用语言列表 | ✅ |
| POST | `/subject-plan/code/run` | 运行代码（自定义输入）· 免登录 | ✅ |
| POST | `/subject-plan/code/submit` | 提交判题→逐测试点评分（AC/WA/TLE/RE）· 免登录。**题库优先，回落到 Supabase `questions` 表**（AI 生成的题走这条） | ✅ |

沙箱策略：Python → subprocess；C/C++ → MinGW；**Java → 仓库内置 OpenJDK 17**（`backend/utils/jdk/`，免管理员 zip 解压，已 gitignore）→ 无外部 API 依赖。

> 2026-09-11 更正：原写法里的「winget 装 JDK」实为**假成功**——MSI 请求管理员提权但非交互会话里 UAC 弹不出来，安装器根本没执行（MSI 日志没生成、注册表/磁盘/`winget list` 三处查无此物），winget 却回报「已成功安装」。

### 题库工具

| 方法 | 路径 | 说明 | 状态 |
|---|---|---|---|
| GET | `/subject-plan/questions/by-ids` | 按 ID 批量取题 · 免登录 | ✅ |
| GET | `/subject-plan/plans/{plan_id}/question-states` | 题目作答状态（薄弱/待巩固/优势） | ✅ |

### 真题套卷（2026-08-12 新增，`routers/exam_papers.py`）

| 方法 | 路径 | 说明 | 状态 |
|---|---|---|---|
| GET | `/subject-plan/syllabi/{id}/exam-papers` | 卷子列表（含用户完成状态+最新分数）| ✅ |
| GET | `/subject-plan/exam-papers/{paper_id}?mode=` | 做题模式（去答案）/ 解析模式（全量+历史）| ✅ |
| POST | `/subject-plan/exam-papers/{paper_id}/submit` | 交卷：客观自动判+主观AI批改+错题AI分析 | ✅ |
| POST | `/subject-plan/exam-papers/{paper_id}/generate-plan` | 答卷→AI分析→生成备考计划 | ✅ |
| POST | `/subject-plan/plans/{plan_id}/tasks/{task_id}/generate-learning` | 每日任务按需AI生成学习讲解（缓存）| ✅ |

---

## 关键文件清单

### 后端
| 文件 | 说明 |
|---|---|
| `backend/routers/subject_plan.py` | 主路由 — 全部 API + 代码判题端点（~1200 行） |
| `backend/routers/auth.py` | 认证路由 — 邮箱密码/验证码 + 小程序微信一键登录（**首次自动建号**）+ 补邮箱密码 + 快捷键设置。~~微信扫码/绑定~~ 09-28 已移除 |
| `backend/utils/auth_middleware.py` | 认证中间件 — 自签 JWT + Supabase 双重验证 |
| `backend/local_question_bank.py` | 本地题库 — 多考纲内存加载，11 种题型 |
| `backend/utils/code_runner.py` | 代码执行沙箱 — Python subprocess + 本地 GCC/G++/Java（零外部依赖） |
| `backend/data/syllabi.json` | 考纲配置 — 17 考纲，含 intro/target/exam_papers/languages/grey dims |
| `backend/data/*.json` | 题库文件 — 17 个 JSON，共 19,338 题（目标 18,900 · 102%） |
| `backend/scripts/seed_all_banks.py` | 批量生成脚本 v2 — 读 target_count 自动算差值 |
| `backend/scripts/check_progress.py` | 题库进度查看脚本 |
| `backend/agents/llm_client.py` | LLM 调用 — DeepSeek V4.1 Flash（文本·识图同一模型，思考默认关，60s 超时） |
| `backend/sql/subject_plan_tables.sql` | Supabase 建表 DDL（6 张核心表） |
| `backend/sql/admin_tables.sql` | 管理员系统建表 DDL（5 张表 + profiles 扩展） |
| `backend/sql/add_wechat_columns.sql` | 🆕 profiles 加 wechat_openid/unionid 列 |
| `backend/routers/exam_papers.py` | 🆕 真题套卷路由 — 列表/双模式详情/交卷/答卷生成计划 |
| `backend/data/exam_papers/*.json` | 🆕 12 套真题卷数据 |
| `backend/sql/exam_paper_records.sql` | 🆕 答卷记录表 DDL |
| `backend/sql/migrate_plan_columns.sql` | 🆕 subject_plans/plan_daily_tasks 补列迁移 |
| `backend/sql/migrate_daily_learning.sql` | 🆕 phase/learning_content/difficulty_level 迁移 |
| `backend/sql/xiaoji_rls_policies.sql` | 🆕 xiaoji_messages/xiaoji_config RLS 放行策略（记忆链路修复） |
| `backend/routers/admin.py` | 管理员全部 API — 22 个端点 |
| `backend/utils/admin_middleware.py` | 管理员鉴权中间件（三级角色） |

### 前端
| 文件 | 说明 |
|---|---|
| `frontend/src/views/Landing.vue` | 🆕 落地页 — 长滚动叙事 + 科幻交互全套（2026-08-22 改版） |
| `frontend/src/views/AgentCenter.vue` | 🆕 智能体中心 — 5 agent 统计/对比/卡片（2026-08-23 接真实数据） |
| `frontend/src/views/AgentDetail.vue` | 🆕 智能体细节调节 — 参数调节 + 自动托管 + 磨合时间线（2026-08-23 接真实数据） |
| `frontend/src/utils/mockAgents.js` | 智能体中心静态元数据 — 图标/文案/参数定义/规则文案（数值由 /agent-center 接口提供） |
| `frontend/src/components/GlobalSearch.vue` | 🆕 全局搜索命令面板 — 侧边栏搜索框 + Ctrl+K + 五组模糊索引 + 历史/自定义管理（增删改查） |
| `frontend/src/utils/pageMeta.js` | 🆕 页面命名册 — 搜索/面包屑/标题单一数据源（名称/别名/拼音首字母） |
| `frontend/src/stores/nav.js` | 🆕 导航 store — 搜索开关 + 考纲/词条缓存 + 最近访问/搜索历史/自定义项（localStorage） |
| `frontend/src/views/Wordbook.vue` | 🆕 词条本 — 统计/筛选/复习/薄弱词出题 + 搜索 ?q= 定位高亮 |
| `frontend/src/views/Guide.vue` | 🆕 使用说明书 — 产品说明书形式（封面/简介/快速上手/功能速览/注意事项） |
| `frontend/src/components/VocabCard.vue` | 🆕 词条卡 — 释义/例句/认识打分（挂载自动记录触点） |
| `frontend/src/components/Starfield.vue` | 🆕 canvas 星空组件 — 视差/流星/主题调色 |
| `frontend/src/views/SubjectPractice.vue` | 做题页 — 编程题左右分栏 OJ（洛谷风）+ Tab缩进/Enter自动缩进 + 语言记忆/考纲限制 |
| `frontend/src/views/ExamPaper.vue` | 🆕 真题套卷页 — 做题/解析双模式 + 交卷出分 + 生成计划按钮 |
| `frontend/src/views/XiaojiSearch.vue` | 🆕 小基搜索页 — 实时模糊搜索 + 搜索历史 + 跳转定位高亮 |
| `frontend/src/views/Login.vue` | 登录页 — 三栏 Tab（用户/管理员/注册）。~~微信扫码面板~~ 09-28 已移除 |
| `frontend/src/views/Profile.vue` | 个人中心 — 信息展示页（头像/账号/邮箱 + 学习画像 + 跳设置） |
| `frontend/src/views/SyllabusHub.vue` | 考纲列表 — 搜索/筛选/收藏 |
| `frontend/src/views/SyllabusDetail.vue` | 考纲详情 — Tab 总控台 + 动态分数 + 删除计划 |
| `frontend/src/views/ProfileCard.vue` | 个人画像 — 维度宇宙（程序化星球 + 中央黑洞 + 详情面板） |
| `frontend/src/utils/procedural.js` | 程序化生成基础件：3D 值噪声 / fBm / 脊状噪声 / 色彩转换 |
| `frontend/src/utils/planetTexture.js` | 九颗行星的程序化地表 + 云层 + 光环贴图 |
| `frontend/src/utils/blackHole.js` | 中央黑洞（视界 + 光子环 + 吸积盘）+ 星尘粒子系统 |
| `frontend/src/utils/questionLabels.js` | 共享题型标签 + 分类映射 + 判断工具 |
| `frontend/src/api/auth.js` | 认证 API — 邮箱登录/注册 + 账号状态 + 补邮箱密码 |
| `frontend/src/api/subjectPlan.js` | API 调用封装（含 code/submit） |
| `frontend/src/stores/auth.js` | 认证状态 — Pinia store + 🆕 微信登录/绑定方法 |
| `frontend/src/components/Sidebar.vue` | 侧边栏 — App 图标网格 + 工具面板 + 对话面板 |
| `frontend/src/components/QAPage.vue` | 帮助中心 — 10 分类 44 FAQ + 跳转按钮（2026-08-23 全面更新对齐现状） |
| `frontend/src/components/MessageCenter.vue` | 消息中心 — 含公告 Tab |
| `frontend/src/components/AppLayout.vue` | 布局 — 毛玻璃侧边栏 + 淡彩流光 |
| `frontend/public/assets/icons/sidebar/*.png` | 侧边栏 App 图标 — 13 张 |
| `frontend/src/router/index.js` | 路由注册 + 全局守卫 |
| `frontend/src/utils/request.js` | Axios 请求实例（401 自动登出） |
| `frontend/src/views/admin/*` | 管理后台页面（7 个） |

---

## 设计规范

- **UI 风格**：科幻毛玻璃（backdrop-filter: blur(24px) saturate(1.2)）+ 深空底（#080d18）
  - 粒子网格背景动画（60px grid + radial mask）
  - 呼吸渐变光晕边框（border-sweep animation）
  - 按钮光泽扫光效果（::after translateX）
  - 卡片入场动画（card-enter + 交错 row-reveal）
- **侧边栏**：App 图标网格（3 列，52×52 圆角方块 + 双色渐变底 + 玻璃高光）
  - 毛玻璃侧边栏背景（淡彩流光紫→蓝→青→绿→紫）
  - 工具图标点击 → 右侧滑出面板
  - 角标悬在图标右上角不被切割
- **交互**：所有可交互元素有 hover（位移/光晕/边框变色）和 active 态
- **考纲图标**：缩写标（abbr）+ 颜色（color），不用 emoji
- **收藏**：localStorage 持久化，考纲级别 + 题目级别
- **题库**：启动时从 JSON 全量加载到内存，所有查询零延迟
- **代码编辑**：深色终端风格（#0a0f1a）+ 等宽字体 + 绿色边框光晕
- **判题动画**：逐测试点顺序揭示（AC 绿 / WA 红 / TLE 黄 / RE 紫）

---

## 已解决的问题

### 1. 路由冲突 → 404
- **问题**：`/{plan_id}` 动态路由注册在 `/questions` 前面，`/questions` 被当 plan_id 匹配
- **修复**：将 `/questions` 移到 `/{plan_id}` 之前
- **文件**：`backend/routers/subject_plan.py`

### 2. 题库页不可用
- **问题**：题库藏在"已生成计划"后面，无计划时无法浏览
- **修复**：题库 Tab 始终可见，无计划时只隐藏任务/知识/错题 Tab
- **文件**：`frontend/src/views/SyllabusDetail.vue`

### 3. 前端 emoji 不可扩展
- **问题**：考纲图标用 emoji，考纲多了找不出合适的 emoji
- **修复**：改为缩写 + 颜色方案（syllabi.json 中配置 abbr + color）
- **文件**：`backend/data/syllabi.json`

### 4. Supabase 延迟
- **问题**：每次查询都 HTTP 请求 Supabase，110 题也要走网络
- **修复**：创建本地题库模块，启动时加载 JSON 到内存，所有筛选搜索在 Python 内存完成
- **文件**：`backend/local_question_bank.py`

### 5. 做题页路由参数错误
- **问题**：`route.params.id` 在新路由下是 undefined
- **修复**：改为 `route.query.plan_id`
- **文件**：`frontend/src/views/SubjectPractice.vue`

### 6. 后端包结构、Supabase 权限、AI 格式、Pydantic 兼容等（详见旧版日志）

### 7. SubjectPractice 完形填空渲染错误（2026-07-28 修复）
- **问题**：`isSingleChoice` 包含 `cloze`，导致完形填空被渲染为单选按钮而非下拉框
- **修复**：`isSingleChoice` 移除 `cloze`，cloze 走自己的 v-else-if 分支
- **文件**：`frontend/src/views/SubjectPractice.vue`、`frontend/src/utils/questionLabels.js`

### 8. 知识点掌握度不聚合（2026-07-28 修复）
- **问题**：每次答题都 INSERT 新行，字段名也不匹配 DB schema（total_attempts vs total_count）
- **修复**：先查已有记录 → 存在则 PATCH 聚合更新（EWMA 算法），不存在则 INSERT；字段名统一为 schema 定义的 total_count / correct_count / mastery_score
- **文件**：`backend/routers/subject_plan.py`

### 9. 可重复创建计划（2026-07-28 修复）
- **问题**：submit_diagnosis 不检查已有活跃计划，同一考纲可堆积多个计划
- **修复**：提交诊断前先查 _get_user_plan，已存在则返回已有 plan_id（already_exists: true）
- **文件**：`backend/routers/subject_plan.py`

### 10. 每日任务题目无去重（2026-07-28 修复）
- **问题**：同日不同任务可能分配到相同题目
- **修复**：先取已答题 ID 作为 exclude_ids，每个任务抽取后累计 used_ids 传递给后续任务
- **文件**：`backend/routers/subject_plan.py`

### 11. 跨考纲错题练习 N+1 查询（2026-07-28 修复）
- **问题**：对每个 plan_id 单独 HTTP 请求查 syllabus_id
- **修复**：使用 Supabase `in.()` 语法批量查询所有 plan → syllabus_id 映射
- **文件**：`backend/routers/subject_plan.py`

### 12. 考纲分数范围硬编码 300-710（2026-07-28 修复）
- **问题**：诊断 Step 2 目标分数滑块只适用于 CET，其他考试无意义
- **修复**：syllabi.json 添加 max_score / pass_score 字段，前后端均动态读取
- **文件**：`backend/data/syllabi.json`、`backend/routers/subject_plan.py`、`frontend/src/views/SyllabusDetail.vue`

### 13. 题库收藏筛选时分页总数错误（2026-07-28 修复）
- **问题**：收藏模式用当前页数据长度（≤20）作为 total
- **修复**：收藏模式下全量拉取 → 客户端过滤 → 客户端分页，total 取过滤后总数
- **文件**：`frontend/src/views/SyllabusDetail.vue`

### 14. categoryLabel/typeLabel 硬编码散落（2026-07-28 修复）
- **问题**：两个 Vue 文件各维护 50 行硬编码映射，加新考纲需改三处
- **修复**：创建 `frontend/src/utils/questionLabels.js` 共享工具，category 映射从 syllabus.dimensions 动态构建
- **文件**：`frontend/src/utils/questionLabels.js`、`SyllabusDetail.vue`、`SubjectPractice.vue`

### 15. 其他修复（2026-07-28）
- v-html XSS 风险：fillStemHtml 添加 HTML 标签剥离
- 前端新增「删除计划」按钮（plan-bar 区域，带确认弹窗）
- 做题页传递 dimensions 参数用于动态分类标签
- 掌握度前端展示兼容 mastery_score/mastery_level 双字段名
- analysis 题型加入 AI 批改类型列表

### 16. 题库数量不足（2026-07-28 批量生成）
- **问题**：10 考纲仅 534 题，5 考纲完全空，不足以备考
- **修复**：三阶段批量生成 → 4,144 题 / 15 考纲（5 CS 生成中）
  - 第一阶段 --per-dim 20：填坑 5 个空考纲（460 题）
  - 第二阶段 --per-dim 10：补强 7 个低量考纲（258 题）
  - 第三阶段 --per-dim 70：全量冲刺 14 考纲（~2,892 题）
- **文件**：`backend/scripts/seed_all_banks.py`、`backend/data/*.json`

### 17. API 调用无超时（2026-07-28 修复）
- **问题**：OpenAI client 无 timeout，API 卡死导致生成脚本永久挂起
- **修复**：llm_client.py 添加 client timeout=60s + request timeout=55s
- **文件**：`backend/agents/llm_client.py`

### 18. 编程题无判题环境（2026-07-28 新增）
- **问题**：编程题只能 AI 文字批改，没有真实代码执行和测试点评分
- **修复**：
  - 新建 `backend/utils/code_runner.py`：本地 Python subprocess + Piston API 云端沙箱
  - 新增 `POST /subject-plan/code/submit` 判题端点
  - 前端代码编辑器（暗色终端 + 语言选择 + 测试结果面板）
  - 支持 9 语言：Python/C++/Java/JS/TS/C/Go/Rust
- **文件**：`backend/utils/code_runner.py`、`subject_plan.py`、`SubjectPractice.vue`

### 19. 缺少 CS/ACM 方向考纲（2026-07-28 新增）
- **问题**：考纲全为传统考试，ACM 社长需要编程算法题库
- **修复**：新增 5 个 CS 考纲
  - 算法与数据结构（LeetCode 风格，7 维）
  - ACM-ICPC 竞赛（6 维）
  - C++ 程序设计（5 维）
  - Java 程序设计（4 维）
  - 前端 Web 开发（4 维）
- **文件**：`backend/data/syllabi.json`

### 20. 评估中心维度宇宙耦合（2026-07-28 重构）
- **问题**：个人画像藏在评估中心里，入口不直观
- **修复**：侧边栏新增「个人画像」独立入口（紫色渐变高亮），评估中心卡片改为快捷引导
- **文件**：`frontend/src/components/Sidebar.vue`、`EvaluationCenter.vue`

### 21. 侧边栏传统列表样式 → App 图标网格（2026-07-30）
- **问题**：侧边栏 10+ 导航项竖排列表，桌面端传统风格，与 app 定位不符
- **修复**：
  - 13 张自定义 PNG 图标，3 列网格布局
  - 每个图标 52×52 圆角 + 双色渐变底 + 玻璃高光 `::after`
  - 导航区 / 工具区分区，带区域标签
  - 工具图标点击 → 右侧滑出毛玻璃面板
  - 对话区简化为新对话 + 历史对话两个按钮
  - 收缩模式可滚动
- **文件**：`Sidebar.vue`、`AppLayout.vue`、`public/assets/icons/sidebar/*.png`

### 22. 考纲详情页缺少概览入口 + 题目无状态追踪（2026-07-30）
- **问题**：每次进考纲直接跳到题库，没有说明书式介绍；题库题目没有作答状态
- **修复**：
  - 新增「概览」Tab 作为默认首页：intro + suitable_for + 维度/题库规模 + 行动按钮
  - 真题套卷独立按钮区（灰色占位）
  - 题库左侧颜色条（红/黄/绿）+ 作答次数标签
  - 灰色维度（听力等）标 🚧 + 说明文字
  - 新增 `GET /plans/{plan_id}/question-states` API
- **文件**：`SyllabusDetail.vue`、`subject_plan.py`、`syllabi.json`

### 23. syllabi.json 配置不完整（2026-07-30）
- **问题**：考纲缺少目标题量、真题套卷、灰色占位维度、介绍文案
- **修复**：17 考纲全部扩展 — 加 `intro` / `suitable_for` / `target_count` / `exam_papers` / `question_types_enabled` / `grey` 维度
- **文件**：`backend/data/syllabi.json`

### 24. 做题页无时间追踪（2026-07-30）
- **问题**：做题过程没有计时，用户无法跟踪每道题耗时
- **修复**：SubjectPractice 顶部加正向计时器 ⏱，换题自动重置，提交停止
- **文件**：`frontend/src/views/SubjectPractice.vue`

### 25. Q&A 内容过时、缺少学科计划分类（2026-07-30）
- **问题**：FAQ 引用已删除的学情报告、旧工作台入口；缺少学科计划大类
- **修复**：完全重写 — 7 分类 29 条 FAQ，新增学科计划(7条)，修正所有过时引用，每条配跳转按钮
- **文件**：`frontend/src/components/QAPage.vue`

### 26. 管理后台多项功能不可用（2026-07-30）
- **问题**：
  - 题库管理无考纲选择器，维度/题型写死，创建/导入不传 syllabus_id → 400
  - 公告发布 500：`system_announcements` 表缺 `image_url` 列；RLS 权限不足
  - admin.js API 返回格式不一致，多页面解构错误
  - `loadBadges` 401 导致自动退出登录
- **修复**：
  - AdminQuestions 全部重写：加考纲下拉 + 动态维度/题型 + syllabus_id
  - SQL 补 image_url 列 + GRANT service_role
  - admin.js 统一 `.then(res => res.data)`
  - loadBadges 改用原生 fetch 绕过 axios 401 拦截器
  - 所有 admin 页面修正解构
- **文件**：`AdminQuestions.vue`、`AdminAnnouncements.vue`、`admin.js`、`admin_tables.sql`、`Sidebar.vue`

### 27. 公告无法触达用户（2026-07-30）
- **问题**：管理员发公告后用户看不到，消息中心无公告入口
- **修复**：消息中心加「公告」Tab，调公开 API 拉取有效公告；全部 Tab 合并公告 + 消息；点击公告展开详情；公告头像用 logo.png
- **文件**：`MessageCenter.vue`

### 28. 评估中心页面空间浪费（2026-07-30）
- **问题**：4 张卡片网格布局，个人画像入口重复
- **修复**：去掉个人画像，3 张竖排毛玻璃卡片（学情报告/评估表/学习规划），各有专属渐变色
- **文件**：`frontend/src/views/EvaluationCenter.vue`

### 29. Supabase 不可用导致全站无法使用（2026-08-01）
- **问题**：Supabase 项目暂停，所有 `Depends(get_current_user)` 端点全部 401/500，jizhi-backend Docker 容器代码未挂载
- **修复**：
  - 读操作端点（题库列表/详情/题目查询）去认证，user_id 可选
  - 代码沙箱端点（/code/run + /code/submit）去认证 + 不依赖 plan_id
  - 前端 authStore.user 全部改为 `.user?.id || ''` 兜底
  - Docker 容器停止，改 uvicorn 源码 `--reload` 直接运行
- **文件**：`subject_plan.py`、`SyllabusHub.vue`、`SyllabusDetail.vue`、`SubjectPractice.vue`

### 30. 编程题做题页布局混乱（2026-08-01）
- **问题**：编程题和非编程题共用一个窄栏布局；代码编辑器只占中间一小块；旧模板残留导致两套 UI 同时显示；页面整体滚动无法固定
- **修复**：
  - 编程题全宽左右分栏：左 34% 题目面板（独立滚动）+ 右 66% 编辑器（占主体）
  - 自定义输入折叠为 `<details>` 避免干扰
  - ▶ 运行（自定义输入）+ 提交 双按钮
  - 整页 `100vh` 固定，内部面板独立滚动
  - 删除旧 `q-programming` 残留代码
- **文件**：`frontend/src/views/SubjectPractice.vue`

### 31. 编程题缺少本地编译器（2026-08-01）
- **问题**：Piston 公共 API 2026年2月关闭；在线编译 API 全部超时（GFW）；无本地 gcc/g++/javac
- **修复**：
  - Python → sys.executable 内置
  - C/C++ → winget 安装 WinLibs MinGW，code_runner 自动检测 winget 安装路径
  - Java → 待装 JDK
  - 编译器查找优先级：内置路径 → winget 目录 → PATH
  - 新增 `GET /code/languages` 返回可用语言
- **文件**：`backend/utils/code_runner.py`

### 32. 题库生成 JSON 解析大量失败（2026-08-01）
- **问题**：非贪婪正则遇嵌套数组截断；markdown 代码块包裹；DeepSeek 输出截断(~8K)；GBK 编码错误
- **修复**：括号计数法提取 JSON + 剥离 \`\`\` + `max_tokens=8192` + 尾逗号修复 + 逐字符回退 + 类型过滤 + BATCH_SIZE=6
- **文件**：`backend/scripts/seed_all_banks.py`、`llm_client.py`、`local_question_bank.py`

### 33. 编程题语言选择无限制（2026-08-01）
- **问题**：所有考纲默认显示全部语言；语言选择不持久化；计算机二级 C 语言也能选 Python
- **修复**：
  - syllabi.json 新增 `languages` 字段，每个考纲限定可用语言
  - 做题页从 URL 参数读取 `langs`，与可用语言取交集
  - localStorage 记住用户语言选择
  - 默认语言自动选考纲第一个可用语言
- **文件**：`syllabi.json`、`SyllabusDetail.vue`、`SubjectPractice.vue`

### 34. 缺少微信扫码登录（2026-08-01/02）

> ⚠️ **2026-09-28 该功能已整条移除** —— 见 #134。保留此条仅为记录当时的决策。
- **问题**：小程序有微信登录，网页版没有；微信开放平台需企业资质，个人无法使用
- **方案**：公众号测试号 OAuth 2.0（免费、个人可用）+ 扫码轮询
  - 测试号获取：https://mp.weixin.qq.com/debug/cgi-bin/sandbox?t=sandbox/login
  - OAuth scope: `snsapi_userinfo`（获 openid + 昵称 + 头像）
  - 交互：网页生成二维码 → 手机微信扫码 → 授权 → 网页轮询拿到 session
- **修复**：
  - 后端 5 个新端点：qrcode / bind-qrcode / callback / poll / wx-login
  - 自签 JWT（PyJWT HS256）不依赖 Supabase Auth
  - 中间件双重认证：优先验证自签 JWT → 失败再走 Supabase
  - 前端登录页加二维码面板 + 轮询 + 未绑定处理
- **文件**：`auth.py`、`auth_middleware.py`、`config.py`、`Login.vue`、`Profile.vue`

### 35. 微信登录不能自动创建用户（2026-08-02）
- **问题**：扫码即自动创建用户不安全，应该必须绑定已有账号
- **修复**：
  - callback 区分 login / bind 两种模式（state 中记录 mode）
  - login 模式：查 openid → 已绑定则登录，未绑定返回 `bound:false`（前弹 toast）
  - bind 模式：🔒 已登录用户扫码 → 写 openid 到 profiles
  - 个人中心 Profile.vue 加「🔗 微信绑定」卡片
- **文件**：`auth.py`、`Login.vue`、`Profile.vue`、`auth.js`（store）

### 36. 测试号 OAuth 回调域名不匹配（2026-08-02）
- **问题**：error 10003 "redirect_uri域名与后台配置不一致"，非标准端口 8000 不被微信接受
- **修复**：后端切到 HTTP 默认端口 80，`BACKEND_EXTERNAL_URL=http://192.168.10.104`（无端口号）
- **文件**：`.env`

### 37. 题库缺口补齐（2026-08-01/02）
- **问题**：6 考纲缺口 ~5,000 题（13,875 → 18,900）
- **修复**：第三轮批量生成
  - acm-icpc: 445 → 529 ✅
  - mandarin: 235 → 595 ✅
  - teacher-cert: 279 → 789 ✅
  - public-service: 1,511 → 1,769 🟡
  - cpa: 311 → 644 🔄（生成中）
  - judicial: 354 → 1,090 🔄（生成中）
  - algorithm-ds: 172 → 863 🔄（生成中）
  - 总题量：13,875 → 16,889（+3,014，完成率 73% → 89%）
- **文件**：`seed_all_banks.py`、`check_progress.py`、`data/*.json`

### 38. 诊断测试显示在页面底部（2026-08-03 修复）
- **问题**：点击「摸底诊断」按钮后，诊断题目渲染在 Tab 内容下方，考纲头部、Tab 栏等内容仍在上面，体验不像是独立的测试页
- **修复**：诊断模式改为全屏渲染 — `showDiagnosis && !plan` 时用 `v-if` 独占整个 `sd-container`，隐藏考纲头部/Tab/题库等内容。诊断页有自己的顶栏（面包屑 + 返回按钮）、进度条、题目面板和目标设定面板
- **文件**：`frontend/src/views/SyllabusDetail.vue`

### 39. SYSTEM_MANUAL.md 核心业务模块文档偏薄（2026-08-04 修复）
- **问题**：第 5 章 12 个业务模块中，仅 5.1「学科计划」有深度（含流程图、算法公式、代码级实现），其余 11 个模块内容偏薄——5.10 API 中心只有 ~30 行，5.9 工具箱 ~60 行，普遍缺乏架构图、数据流、错误处理矩阵等工程细节
- **修复**：
  - 5.2 AI 对话：+4 子节（SSE 全链路 / System Prompt 构建 / Vision 多模态 / 后处理集成）
  - 5.3 学程系统：+ASCII 数据流全景图
  - 5.4 社区模块：+后端包架构图 / 批量查询优化 / 排行算法 / 举报邮件通知
  - 5.5 资源库：+2 子节（生成 Agent 流水线 / 数据模型与持久化）
  - 5.9 工具箱：完全重写 8 子节（~250 行，架构图 + JSONB schema + 状态机 + Upsert 模式）
  - 5.10 API 中心：完全重写 8 子节（~220 行，架构图 + Provider 路由 + 安全模型 + DDL + 状态矩阵）
  - 5.11 微信登录：+4 子节（状态管理 / 错误矩阵 / 安全加固 / 小程序差异）
  - 5.12 管理后台：+3 子节（辅助函数层架构 / 仪表盘聚合算法 / 批量导入全链路）
  - 文档规模：3,557 → 5,036 行（+1,479 行，+42%），TOC 同步更新至三级目录
  - 所有新增内容基于源码验证（chat.py / tools.py / admin.py / auth.py / career.py / questions.py）
- **文件**：`SYSTEM_MANUAL.md`, `logs/2026-08-04.md`

### 40. 小程序账号与网页端同步（2026-08-04）

- **问题**：小程序微信登录自动创建 `wxmp_` 前缀独立用户，与网页端账号体系割裂
- **修复**：
  - 后端 `POST /auth/wx-bind` 新端点：小程序 openid + 网页邮箱/密码 → Supabase 验证 → 写入 wechat_openid → 签发 JWT
  - `wx-login` 改为不自动创建用户：已绑定 openid → 直接登录；未绑定 → 返回 `need_bind: true`
  - 小程序登录页两步流程：微信授权 → 绑定已有账号表单
  - 绑定后网页端和小程序端均可微信登录，共享同一用户数据
  - `.env` 填入 `WECHAT_MP_SECRET`
- **文件**：`auth.py`, `Login.vue`, `stores/auth.js`

### 41. 小程序 API 路径全错（2026-08-04）

- **问题**：`subjectPlan.js` 调 `/subject-plan/plan/{id}`、`/subject-plan/{id}/questions` 等不存在路径；`career.js` 调 `/career/achievements/{uid}` 等不存在端点；`chat/sessions` 后端无此端点
- **修复**：
  - `api/subjectPlan.js` 全重写：所有路径对齐后端路由（`/syllabi/{id}`, `/syllabi/{id}/questions`, `/plans/{id}/submit` 等）
  - `api/career.js` 全重写：成就从 `stats.achievements` 提取，任务用 `/task-progress/{uid}`
  - `stores/session.js` 全重写：会话管理改用本地 storage（无需后端）
  - `getSyllabusDetail` 自动解包 `data.syllabus`
- **文件**：`api/subjectPlan.js`, `api/career.js`, `stores/session.js`

### 42. 题库端点需登录才能查（2026-08-04）

- **问题**：`GET /syllabi/{id}/questions` 有 `Depends(get_current_user)`，但题库是本地 JSON，不应要求登录
- **修复**：去掉 `current_user` 依赖和 `verify_user_match`，`user_id` 改为可选空字符串
- **文件**：`backend/routers/subject_plan.py`

### 43. 小程序 UI 适配（2026-08-04）

- **问题**：
  - 全页面大量彩色 emoji 图标，视觉效果不专业
  - 聊天页顶栏 flex 布局挤走 logo 图片
  - 聊天输入栏被 TabBar 固定定位覆盖
  - 右上角按钮被小程序胶囊按钮遮挡
  - 全局缺 `box-sizing: border-box` 导致右侧内容被裁切
  - `showLoading/hideLoading` 配对报错
  - `safe-area-bottom` spacer 受 border-box 影响变短，TabBar 图标被压扁
- **修复**：
  - 17 个网页端侧边栏 PNG 图标 → 小程序 `/static/icons/`，TabBar + 菜单全部替换
  - Chat/Study 顶栏 logo 加 `flex-shrink: 0`，`gap` + `margin-left: auto` 替代 `space-between`
  - 聊天页高度：`calc(100vh - 100rpx - env(safe-area-inset-bottom))`
  - 胶囊按钮：`uni.getMenuButtonBoundingClientRect()` 动态 `paddingRight`
  - 全局 `box-sizing: border-box`，TabBar/spacer 例外加 `content-box`
  - 输入重构：`handleSend()` 独立方法避免 `@confirm` 内联传参时序问题
- **文件**：`App.vue`, `CustomTabBar.vue`, `index/index.vue`, `request.js`, `stores/auth.js`, 全页面 emoji 清理

### 44. 工具功能桩代码全部实现（2026-08-04）

- **问题**：打卡/倒计时/计时器/学情报告/评估表/诊断全部 toast "开发中"
- **修复**：
  - 打卡：调用 `/tools/checkin` API，显示今日打卡状态
  - 倒计时：底部弹层 + 事件列表 + 添加（名称 + YYYY-MM-DD 日期）
  - 计时器：底部弹层 + 预设 5/25/45/60 分钟 + 开始/停止
  - 学情报告：弹窗显示真实做题/正确率/学习天数
  - 评估表：跳转个人画像页
  - 学程成就：跳转成就任务页
  - 诊断流程：practice.vue 诊断模式 → 逐题作答 → 批量提交 → 生成计划
- **文件**：`profile/index.vue`, `evaluation.vue`, `career/index.vue`, `study/detail.vue`, `study/practice.vue`

### 45. 小程序会话存储（2026-08-04）

- **问题**：会话调用 `/chat/sessions` 端点，后端无此 API
- **修复**：`stores/session.js` 全重写为本地 storage 方案，含 `createSession/deleteSession/switchSession/addMessage/getMessages/updateTitle`
- **文件**：`stores/session.js`, `index/index.vue`

### 46. 小程序图片资源超限（2026-08-06 修复）

- **问题**：18 张 PNG 图标全部 600KB-1.3MB，远超微信单文件 200KB 限制，上传被拒
- **修复**：Pillow 批量压缩 1254×1254 → 200×200，PNG optimize，全部压至 24-44KB
- **文件**：`src/static/icons/*.png`, `src/static/logo.png`

### 47. request.js ↔ auth.js 循环依赖导致所有 API 崩溃（2026-08-06 修复）

- **问题**：`request.js` 和 `stores/auth.js` 互相 require，CommonJS 初始化时 `useAuthStore` 为 undefined，所有 API 调用在发请求前静默崩溃，学习页显示「加载失败」
- **修复**：`request.js` 直接从 `uni.getStorageSync('token')` 读 token，不再引用 authStore；401 改用直接清 storage
- **文件**：`src/utils/request.js`

### 48. 学科计划相关 API 数据 key 全错（2026-08-06 修复）

- **问题**：小程序读 API 响应用的 key 名与后端实际返回不匹配 — 题目状态 `state`→`level`、错题本 `questions`→`mistakes`、掌握度 `map`→`mastery`、删计划 PUT→DELETE、做题页传 syllabusId 作 planId
- **修复**：`detail.vue`/`practice.vue`/`api/subjectPlan.js` 中 6 处修正，全部对齐后端真实字段
- **文件**：`api/subjectPlan.js`, `detail.vue`, `practice.vue`

### 49. 服务器后端代码过旧（2026-08-06 修复）

- **问题**：服务器后端无 `subject_plan` 路由、无 `local_question_bank` 模块、无 `data/` 题库文件、缺 `services/supabase.py` — 小程序核心 API 全部 404
- **修复**：上传全套新版代码 + 安装 supabase 包 + 设 UTF-8 编码重启，后端恢复 17 考纲 19,338 题
- **文件**：服务器 `/www/wwwroot/backend/`

### 50. 学习页只有学科计划（2026-08-06 修复）

- **问题**：底部 Tab 只有 4 个，资源库藏在个人中心里，网页版的资源库是独立模块
- **修复**：底部 Tab 扩展为 5 个（对话/学习/资源库/学程/我的），资源库全重写对齐网页版 5 功能（掌握度看板/生成题目/我的题集/错题本/生成历史/评估中心）
- **文件**：`CustomTabBar.vue`, `pages.json`, `profile/resource-lib.vue`, `study/index.vue`

### 51. 题库页面图标过大（2026-08-06 修复）

- **问题**：`study/index.vue` 顶栏 logo 图片无 CSS 尺寸约束，200×166px 自然尺寸在小程序中显示过大
- **修复**：添加 `width: 56rpx; height: 56rpx; border-radius: 12rpx`
- **文件**：`study/index.vue`

### 52. 设置项分散在 5 个位置（2026-08-06 修复）

- **问题**：设置分散在侧边栏（主题/状态）、个人中心（昵称/密码/微信）、引导页（学习偏好）、小基设置（AI 配置），通知设置有后端 API 但无前端 UI
- **修复**：
  - **网页版**：新建 `frontend/src/views/Settings.vue`（899 行），7 大模块（个人信息/学习偏好/外观/隐私/通知/账号安全/AI与API）
  - **小程序**：新建 `src/pages/profile/settings.vue`（398 行），5 大模块（个人信息/学习偏好/通知/账号安全/关于），uni-app `<picker>` 适配
  - 侧边栏新增设置图标入口（紫蓝渐变）
  - 通知设置首次有了前端 UI（8 开关 + 2 时间选择器）
- **文件**：`Settings.vue`（web+小程序）、`router/index.js`、`Sidebar.vue`、`pages.json`、`profile/index.vue`

### 53. XiaojiSettings 用 emoji 代替实际图片（2026-08-06 修复）

- **问题**：小基设置页标题用 🤖 emoji，明明项目有 5 张小基形象 PNG（idle/thinking/speaking/happy/sleeping）
- **修复**：`XiaojiSettings.vue` 标题 🤖 → `xiaoji_idle.png`（32×32 圆角）；设置页 AI 卡片 🤖 → 小基图片
- **文件**：`XiaojiSettings.vue`、`Settings.vue`（web）

### 54. 小程序 AI 对话无流式输出（2026-08-06 修复）

- **问题**：`uni.request` 不支持分块传输，AI 回复等完整响应才展示，和网页版逐字输出体验差距大
- **修复**：
  - 用 `wx.request` + `enableChunked: true` + `onChunkReceived` 实现 SSE 流式
  - UTF-8 ArrayBuffer 手动解码兼容旧版基础库
  - 逐字追加到气泡 + 闪烁光标
  - 发送最近 10 轮对话历史作为上下文
  - 首条消息自动调 `/chat/title` 生成标题
  - `requestTask.abort()` 页面卸载时取消
- **文件**：`pages/index/index.vue`（410 行全重写）

### 55. 小程序无生产环境配置（2026-08-06 修复）

- **问题**：`BASE_URL` 写死为 `http://localhost:8000`，无法真机使用
- **修复**：改为 `https://api.jizhi-learn.com`，保留注释掉的 localhost 供本地开发
- **文件**：`utils/constants.js`

### 56. 小程序缺少小基 AI 形象（2026-08-06 修复）

- **问题**：网页版有小基 AI 助手（形象/语音/性格），小程序完全没有
- **修复**：
  - 复制 5 张小基 PNG 到小程序 static 目录
  - 聊天页新增小基模式：点击顶栏 logo/标题在「基智」「小基」之间切换
  - AI 回复前显示小基头像，根据状态切换形象（thinking→speaking→happy）
  - 欢迎页显示 160rpx 大头像 + 专属快捷提问
  - 顶栏紫色「AI」badge 标识
- **文件**：`pages/index/index.vue`、`static/xiaoji_*.png`

### 57. 真题套卷功能空缺（2026-08-12 新增）

- **问题**：`syllabi.json` 的 `exam_papers` 全是 `grey: true` 占位，`goExamPaper()` 空函数；概览 Tab 真题按钮全部灰色禁用
- **方案**：真题必须真实、非盈利用途、来源合法 — 中国国家考试（教育部/部委组织）真题公开转载广泛，无侵权风险；雅思/托福受版权保护需仿真卷另标；普通话纯口语不适合文字练习
- **实现**：
  - `backend/data/exam_papers/` 12 套真题 JSON（卷面分区+评分标准+解析）
  - 新路由 `routers/exam_papers.py`：列表/详情（双模式）/交卷/答卷生成计划
  - 前端 `ExamPaper.vue`：做题模式（计时+交卷出分）+ 解析模式（历史答案+正确率+AI 错因分析）
  - 交卷后异步批量 AI 分析错题 → 缓存 → 解析秒开
- **文件**：`routers/exam_papers.py`、`views/ExamPaper.vue`、`data/exam_papers/*.json`

### 58. 计划任务无内容 — 生成的是 AI 编的文字描述（2026-08-12 修复）

- **问题**：答卷生成计划的任务只有 description/focus 文字，无 `category`/`question_type` 查询字段 → `bank_query` 查不到题目 → 每日任务空
- **修复**：AI 收到考纲真实维度/题型列表只能从中选；任务带 category+question_type+question_count 可查询；fallback 按维度生成；三阶段设计（基础期→强化期→冲刺期）从易到难
- **文件**：`routers/exam_papers.py`

### 59. `plan_daily_tasks` 表缺 `user_id` 列导致任务静默失败（2026-08-12 修复）

- **问题**：代码插入任务带 `user_id`，但 Supabase 实际表无此列 → 400 被静默吞掉 → 计划建了、任务 0 条
- **修复**：任务插入去掉 user_id（plan_id 已足够）+ 失败状态日志
- **文件**：`routers/subject_plan.py`、`routers/exam_papers.py`

### 60. `subject_plans` 表缺 `syllabus_id` 列（2026-08-12 修复）

- **问题**：SQL 文件用 `subject` 列，代码写 `syllabus_id` → 插入 400，诊断生成计划 500
- **修复**：迁移 SQL 补列 + 旧数据回填（`migrate_plan_columns.sql`）
- **文件**：`sql/migrate_plan_columns.sql`

### 61. 旧计划拦截新生成（2026-08-12 修复）

- **问题**：7月23日旧计划（goal=500、无任务）一直存活，重新生成时 `already_exists` 返回旧计划，前端不处理 → 用户以为生成了 425 计划，实际显示旧计划 500 分 + 空任务
- **修复**：诊断和答卷两个通道都检查 `already_exists`，弹窗询问"删除旧计划重建？"，确认后删除级联数据再重建
- **文件**：`views/SyllabusDetail.vue`

### 62. 删除计划不彻底（2026-08-12 修复）

- **问题**：删除不检查结果、不清理关联表（孤儿任务/诊断/答题记录/掌握度）；前端删除后 computed 赋值失败状态残留
- **修复**：后端级联清理 4 张表 + 状态码检查；前端清空全部相关状态 + 重新加载考纲
- **文件**：`routers/subject_plan.py`、`views/SyllabusDetail.vue`

### 63. AI 返回 JSON 解析脆弱（2026-08-12 修复）

- **问题**：AI 输出被截断/带 ```json 包裹/尾逗号 → `json.loads` 直接挂 → 走 fallback 或 500
- **修复**：代码块剥离 + 括号计数法提取 + 尾逗号修复 + 逐层回退修复
- **文件**：`routers/subject_plan.py`

### 64. 答卷生成跳错页面（2026-08-12 修复）

- **问题**：跳 `/plan-detail/{id}`（旧 learning-plan 系统读另一张表），计划详情空
- **修复**：改为回考纲页切「每日任务」Tab（和诊断流程一致）
- **文件**：`views/SyllabusDetail.vue`

### 65. 个人中心与设置功能重叠（2026-08-17 修复）

- **问题**：Profile 与 Settings 均有头像/昵称/简介/改密/微信绑定，违背"设置页统一收拢"初衷
- **修复**：Profile.vue 重写为信息展示页（只读账号信息 + 学习画像 + 退出登录 + 「编辑资料与设置」跳转）；编辑操作全部收进 /settings
- **文件**：`views/Profile.vue`

### 66. 网页版死代码清理（2026-08-17）

- **问题**：全量盘点发现 10 个零引用文件 + 约 40 个零引用函数（api 模块内）
- **修复**：删除 4 个旧版 Subject*.vue、4 个孤儿组件、api/index.js、stores/index.js；8 个 api 模块死函数清理；stores/auth.js 未使用 import；exam_papers.py 死 import。每步构建验证
- **文件**：frontend 多个 + `backend/routers/exam_papers.py`

### 67. 小基前端 API 断链（2026-08-17 修复）

- **问题**：`api/xiaoji.js` 写"community 前缀 + path 参数"杂交体（后端 community 用 query 参数、顶层用 path 参数）→ 小基设置/语音页运行时 404
- **修复**：4 处路径对齐后端真实端点（config/messages 改 query 参数、清空指顶层端点）
- **文件**：`api/xiaoji.js`

### 68. 小基无上下文记忆（2026-08-17 修复）

- **问题**：日志显示 `保存用户消息状态: 401` — xiaoji_messages 表存在但 RLS 无策略（读空、写拒）；全项目 SQL 无该表 DDL。后端本身有最近 10 条上下文逻辑
- **修复**：新增 `backend/sql/xiaoji_rls_policies.sql`（xiaoji_messages/xiaoji_config 放行策略，与 community 其他表匿名 key 惯例一致），用户在 Supabase 执行后写入 201
- **文件**：`sql/xiaoji_rls_policies.sql`

### 69. 进入小基页停在顶部（2026-08-17 修复）

- **问题**：`loading.value = false` 在 finally 中、滚动之后才执行 → 滚动时消息未渲染，scrollHeight 无效
- **修复**：先关 loading → nextTick → 瞬时滚动到底部；删除重复的 watch(messages)
- **文件**：`components/XiaojiCall.vue`

### 70. 小基搜索全部失败（2026-08-17 修复）

- **问题**：PostgREST 模糊匹配通配符是 `*`，代码写 `ilike.%kw%` → 500 → 静默返回空。实测 `ilike.*kw*` 正常
- **修复**：community/xiaoji.py 与顶层 xiaoji.py 两处改 `ilike.*{kw}*`；community messages 端点补 search 参数
- **文件**：`routers/community/xiaoji.py`、`routers/xiaoji.py`

### 71. 小基搜索页 + 聊天增强（2026-08-17 新增）

- **问题**：搜索内嵌在聊天页不符合使用习惯；缺日期分隔；点击结果无法定位原文
- **实现**：
  - 新建 `/xiaoji/search` 独立搜索页：输入自动聚焦、防抖 350ms 实时模糊搜索（过期结果丢弃）、结果列表（头像+我/小基标签+时间+摘要）、抖音风搜索历史（localStorage 去重最近优先 10 条）
  - 点结果 → `/xiaoji/call?highlight={msg_id}` → 滚动定位居中 + 黄色高亮闪烁 2.4s
  - 聊天页跨天消息插入日期分隔线（今天/昨天/M月D日 周几/跨年带年份）
- **文件**：`views/XiaojiSearch.vue`、`components/XiaojiCall.vue`、`router/index.js`

### 72. 待处理遗留（2026-08-17 盘点发现）

- 旧 learning-plan 系统（LearningPlan/PlanDetail/PlanPreview + learning_plan.py）去留
- 路由遮蔽 bug：`GET /community/messages/history` 被 `/messages/{friend_id}` 抢先匹配
- 顶层 xiaoji.py 与 community/xiaoji.py 双模块重叠；`/do-question` 路由重复注册；`/animation-demo` 无鉴权无入口
- 部分端点鉴权偏松（questions.py 11 个、learning_plan.py 4 个公开端点）

### 73. 落地页内容过时（2026-08-22 修复）

- **问题**：搜索落地页（`/`）还是老版本"多智能体"技术叙事，未提学科计划/真题/每日任务等当前主力功能；title 只有「基智」两字
- **修复**：Hero/5 张轮播/页脚全部重写对齐产品主线「选考纲 → AI 诊断 → 三阶段计划 → 每日任务 → 真题冲刺」；index.html 补 description/keywords/og
- **文件**：`views/Landing.vue`、`index.html`

### 74. 落地页 77MB 视频拖垮首屏（2026-08-22 修复）

- **问题**：5 个 mp4（旧 UI 录屏）共 77MB 且全 `preload=auto`，搜索访客秒退
- **修复**：删除 videos 目录，轮播改为 5 个纯 CSS 科幻 mockup 面板（考纲芯片/试卷卡/分数环/任务清单/领奖台），零资源、秒加载
- **文件**：`views/Landing.vue`、`public/videos/`（删除）

### 75. 落地页结构单薄（2026-08-22 重构）

- **问题**：页面只有 Hero+轮播+5 卡+一行页脚，缺长滚动叙事、数字条、FAQ、完整页脚
- **修复**：重构为「导航锚点 → Hero → 功能卡 → 数字条(滚动计数) → 三步流程 → 功能深展区×5 → FAQ×7 → 页脚」；滚动入场 reveal + 计数动画 + 手风琴
- **文件**：`views/Landing.vue`

### 76. 登录注册按钮过多（2026-08-22 修复）

- **问题**：整页 8 个明示登录/注册按钮 + 5 个功能按钮撞登录墙，访客被反复推销注册
- **修复**：只保留导航「登录+免费注册」一对；Hero 改「了解功能↓」；底部 CTA 区块删除；页脚去登录链接
- **文件**：`views/Landing.vue`

### 77. 帮助中心/开源文档需登录才能看（2026-08-22 修复）

- **问题**：页脚链接 /qa、/open-source 被登录墙挡住，访客体验差
- **修复**：两路由 `requiresAuth: false`（OpenSource 零登录依赖；QAPage 后端兼容空 user_id）；QAPage 返回改 history.back，访客提问提示登录后可收邮件回复
- **文件**：`router/index.js`、`components/QAPage.vue`

### 78. 浅色模式 mockup 对比度不合格（2026-08-22 修复）

- **问题**：CDP 实测浅色主题下 mockup 近白底+淡蓝字（对比度 2.2:1），科幻风硬编码色未适配浅色
- **修复**：`.mockup`/`.feat-visual` 加深色底板（#0e1728→#0a1120），做成"暗色屏幕"，双主题都成立；实测轮播区深色占比 0%→56%
- **文件**：`views/Landing.vue`

### 79. 落地页缺科幻视觉与交互（2026-08-22 新增）

- **问题**：用户要"流畅+有意思+科幻"的落地页体验
- **实现**：星空星尘 canvas（🆕 `components/Starfield.vue`：3 层视差/闪烁/流星/主题调色）+ 打字机 HUD + 考试倒计时 + 旅程轨道线（滚动画线点站）+ 磁性按钮 + 光标光效 + 小基伴游 + 连点 logo 流星雨彩蛋；触屏/reduced-motion 降级；headless Chrome CDP 实测全通过
- **文件**：`views/Landing.vue`、`components/Starfield.vue`

### 80. 待处理（2026-08-22 更新，08-23 追加）

- 域名网站 ICP 备案未完成（实测 jizhi-learn.com 挂 Vercel 境外免备案可访问、api 子域名宝塔 403 拦截；小程序备案已完成但不等于网站备案，备案号不能互用）——备案后页脚填号+工信部链接；小程序 API 域名同样依赖此备案
- 真实产品截图替换 CSS mockup；social proof 数据
- /subject-plan 访客开放浏览（已提方案，用户暂否）
- font-awesome CDN 全量加载未优化；本会话改动未同步 jizhi 仓库/服务器
- 全局搜索遗留：全局词库搜索端点（`GET /vocab/search`，`/vocab/entries/{word}` 是「查不到就生成」的昂贵端点不能用于搜索）；顶栏 + 面包屑 + document.title 同步（命名册 pageMeta.js 已预留数据源）

### 81. 识图视觉模型切换：豆包 → DeepSeek（2026-08-22 修复）

- **问题**：图片理解走火山引擎豆包（`/chat/vision` 用视觉接入点、小基识图用角色接入点多模态），需额外维护 ARK key + endpoint；DeepSeek 08-21 上线官方视觉模型 `deepseek-v4-flash-vision-exp` 后无理由继续用第三方
- **修复**：
  - `agents/llm_client.py` 新增 `call_llm_vision` / `call_llm_vision_stream`（OpenAI SDK 多模态消息，支持 URL/base64），模型名 env 可覆盖 `DEEPSEEK_VISION_MODEL`，复用现有 `DEEPSEEK_API_KEY`
  - `/chat/vision`、`/community/xiaoji/vision` 两个识图端点全部切 DeepSeek
  - 删豆包视觉死代码：`volc_client.vision_stream`、`doubao_stream_generator`、`VOLC_VISION_ENDPOINT_ID`
  - ApiCenter 图片理解加 DeepSeek 选项（默认）；QAPage FAQ 文案更新
  - 冒烟测试通过（base64 data URL 直连）；注意模型带 Exp 后缀为实验性标记
- **文件**：`agents/llm_client.py`、`config.py`、`routers/chat.py`、`routers/community/xiaoji.py`、`utils/volc_client.py`、`views/ApiCenter.vue`、`components/QAPage.vue`

### 82. 对话 SSE 无超时挂起（2026-08-22 修复）

- **问题**：用户发对话长时间无响应。排查确认后端/DeepSeek 链路正常（端到端复测 200 首字节 2.5s）；根因一是 `--reload` 会话中改后端文件触发 worker 重启杀掉在途请求，二是前端 SSE 读取无任何超时——连接半挂时界面无限「调用 Agent」且不报错
- **修复**：`api/chat.js` `sendChatMessage` 支持 AbortSignal；`ChatArea.vue` 加 120s 流超时保护（AbortController），超时提示「响应超时，请重试」
- **文件**：`api/chat.js`、`components/ChatArea.vue`

### 83. 智能体中心（2026-08-22 新增，概念 + 硬编码预览）

- **背景**：现 5 个智能体（对话/规划/生成/评估/小基）是写死的 system prompt，散落在 ~20 个触点（聊天/资源库/做题页/真题/小基），且大部分触点是各 router 里的匿名 LLM 调用（未走 agents 包）。用户要一个「智能体中心」：查看不同智能体在各场景的使用情况，并持续「调教」出贴合用户自身的智能体
- **讨论结论（整体方案）**：
  - 定位：双视角（用户个人中心 + 管理后台全局统计）；范围：核心 5 个智能体
  - 核心 = **磨合引擎**：不做模型微调，做参数自适应——行为数据（正确率/完成率/👍👎）→ 规则引擎自动微调 agent 参数 → 下次调用实时拼装 → 中心展示磨合时间线
  - 数据原则：每个数字要么解释学习效果、要么导向动作；统计只是调整效果的证据
  - 工程第一步 = 「收编」：匿名 LLM 调用统一走 agents 包，参数/打点才能统一
- **本日产出（预览版）**：
  - `views/AgentCenter.vue`：KPI 行（范围筛选联动）+ 效果对比条形图（图表/表格双视图 + 悬停 tooltip）+ 5 张 agent 卡（效果指标/触点明细/共享参数/建议一键应用/磨合记录）→ 点击进详情
  - `views/AgentDetail.vue`：细节调节页——Hero + 统计格 + 近 30 天满意度折线图（SVG 十字准线 + tooltip）+ 触点明细表 + **参数调节**（分段/滑块/开关三类控件，每参数独立「自动托管」开关 + 磨合规则 + 上次调整记录）+ 磨合时间线
  - `utils/mockAgents.js`：共享硬编码演示数据；`agent-center.png`：Pillow 占位图标
  - 图表遵循数据可视化规范：验证过的参考调色板、细标记、十字准线、图表/表格双视图
- **遗留（后端全部未做）**：三张表 DDL（`agent_prefs` 含触点维度 / `agent_usage` 含 touchpoint / `agent_tuning_log`）、~20 触点打点、匿名调用收编、管理端全局视角
- **文件**：`views/AgentCenter.vue`、`views/AgentDetail.vue`、`utils/mockAgents.js`、`router/index.js`、`components/Sidebar.vue`

### 84. 智能体中心后端全量落地（2026-08-23 新增，08-22 预览 → 真实数据）

- **数据设计落地**：`sql/agent_center_tables.sql` — 新建仅 2 表（`agent_prefs` 参数持久化 / `agent_tuning_log` 磨合记录）+ 2 补列（`xiaoji_messages.kind` 触点区分、`subject_plans.source` 计划来源）；调用计数复用 `user_actions`、效果指标复用业务表，0 张计数专用表
- **聚合路由** `routers/agent_center.py`（挂载 `/agent-center`）：19 触点全清单；`GET /overview`（KPI 六格 + 协作闭环 5 步 + 协同增益 5 对跨表对照 + 路由转化 + 动态结论）、`GET /agents/{key}`（30 天趋势 + 触点计数 + 特点面板）、`GET/PUT prefs`、`GET/POST tuning`、`POST /tuning/run`；15 张表单连接 asyncio.gather 并发拉取（串行要 10s+），跨表联合全在 Python 侧，任何查询失败优雅降级
- **磨合规则引擎** `agents/tuning.py`：6 条规则（任务量/阶段节奏/出题难度/错题针对性/错因颗粒度/关心频率）按行为数据自动微调参数；自动托管开关尊重、7-14 天冷却期、新用户不打扰；触发 = 详情页「立即评估」+ **后台每日任务**（main.py lifespan 启动，24h 循环，近 14 天活跃用户，限速 1s/人）
- **前端接真实数据**：`api/agentCenter.js` 七个封装；AgentCenter/AgentDetail 参数真读写、磨合记录真写入；补埋点（对话分流 use_*_agent、xiaoji kind、定向生成 touchpoint）
- **遗留**：管理端全局视角；协同增益 2 对 v2（生成×掌握度前后对比、评估产出独立记录）
- **文件**：`routers/agent_center.py`、`agents/tuning.py`、`sql/agent_center_tables.sql`、`api/agentCenter.js`、`views/AgentCenter.vue`、`views/AgentDetail.vue`、`main.py`、`agent_center_design.md`

### 85. 词条本全新功能（2026-08-23 新增：查词 → 抓取 → 熟练度 → 复习 → 定向出题）

- **数据设计**：3 表 — `vocab_entries`（词条本体全局共享，word 唯一，AI 生成一次全员复用）、`vocab_lookups`（抓取记录 + 触点，兼作智能体中心计数源）、`word_mastery`（每人每词熟练度，EWMA 与知识点掌握度同构）
- **后端** `routers/vocab.py`：查词（无则 call_llm 生成 + 容错 JSON 提取 + 全局缓存）、触点记录、EWMA 打分（新分 = 旧分×0.7 + 目标×0.3，认识 100/不认识 20）、词条本统计与列表（释义 in() 批量补全）、薄弱词定向出题（写入 questions + generation_history → 资源库练习）
- **前端**：`ChatArea.vue` 词条提取三模式（问词义 / 整句单词 / 识图从 AI 回复提词 + stopwords）→ 回复下方渲染 `VocabCard.vue`（音标释义例句 + 认识/不认识打分实时熟练度）；`Wordbook.vue` 词条本页（统计 → 筛选 → 列表 → 薄弱词复习模式 → 薄弱词出题）；侧边栏 + `/wordbook` 路由
- **文件**：`routers/vocab.py`、`sql/vocab_tables.sql`、`views/Wordbook.vue`、`components/VocabCard.vue`、`api/vocab.js`、`components/ChatArea.vue`、`components/Sidebar.vue`

### 86. API 模型中心预览改版（2026-08-23 重构，同日）

- **问题**：预览是静态文字块（`问：…\n答：…`），效果差
- **修复**：预览结构化 `preview: {type,...}` 五类渲染 — 对话气泡（小基头像 + 展开打字机重播）/ 识图（纸质截图 mockup + 解析气泡）/ TTS（真实调 `/xiaoji/tts` 讯飞合成播放，缓存复用）/ 状态行 / 视频占位帧；自配 Key 保持 localStorage 演示
- **后期规划（未实施）**：用户自带 Key 优先、平台 Key 兜底（`user_api_keys` 表 + RLS + 掩码 + 加密；前端演示表单改接后端接口）
- **文件**：`views/ApiCenter.vue`、`SYSTEM_MANUAL.md`（5.10 章节同步重写）

### 87. 全局搜索（2026-08-23 新增）

- **背景**：全局导航（App 图标网格）只存在于主界面 `/home` 侧边栏，40+ 页面各自为政、无位置指示、无全局搜索——找「词条本」「评估表」这类不在侧边栏入口的页面得先回主界面。用户要求「每个页面都有自己的命名」+ 侧边栏搜索 + 模糊搜索直达
- **实现**：
  - `utils/pageMeta.js` **页面命名册（单一数据源）**：30 静态页 + 6 管理页 + 5 智能体，各带名称/路径/搜索别名（中文关键词/英文缩写）+ 拼音首字母；供搜索及未来面包屑/标题共用
  - `components/GlobalSearch.vue` 命令面板：侧边栏顶部搜索框（主界面）+ **Ctrl+K 任意页面全局唤起**；五组索引（页面/考纲 17/真题 12/智能体 5/词条本）；模糊打分（标题全等 > 前缀 > 包含 > 别名 > 首字母）；↑↓ 循环/Enter 跳转/Esc 关闭；空态显示最近访问 + 搜索历史
  - **索引零后端改动**：考纲+真题一次 `GET /subject-plan/syllabi` 全拿（会话缓存，过滤 grey 占位卷）；词条本 `GET /vocab/wordbook`
  - 词条结果跳 `/wordbook?q=词` → 定位滚动 + 高亮闪烁 2.4s + 提示条（watch query 支持同页二次跳转）
- **文件**：`utils/pageMeta.js`、`stores/nav.js`、`components/GlobalSearch.vue`、`App.vue`、`components/Sidebar.vue`、`views/Wordbook.vue`

### 88. 搜索输入无实时结果（2026-08-23 修复）

- **问题**：输入后结果区无反应，停留在「输入关键词…」空态。构建通过、静态检查无果，CDP 真机复现定位
- **根因**：`GlobalSearch.vue` `agentItems` 字段笔误 `title: a.name`（命名册字段是 `title`）→ 5 个智能体条目 title 全 undefined → `matchScore` 读 `entry.title.toLowerCase()` 抛 TypeError → 结果区渲染崩溃、DOM 停留空查询视图
- **修复**：`title: a.title`；`matchScore` 加坏条目防御（console.error + 跳过，面板不再可能整体崩溃）；真题卷别名补考纲名（搜「四级」同时命中考纲和四级真题卷）
- **验证**：CDP 端到端复测——输入实时出结果、改输实时刷新、零控制台错误
- **文件**：`components/GlobalSearch.vue`

### 89. 搜索增删改查（2026-08-23 新增）

- **历史记录管理**：最近访问/搜索历史 hover ✕ 单删 + 组头「清空」一键清（localStorage）
- **自定义搜索项**：增/查/改/删全流程——收录后作为「自定义」组参与模糊匹配；localStorage 按用户隔离（`gs_custom_entries_{uid}`）
- **文件**：`stores/nav.js`、`components/GlobalSearch.vue`

### 90. 自定义项交互重构：手填表单 → 点选收录（2026-08-23 重构）

- **问题**：用户反馈「自定义就是给出全部的可快捷进入的页面，然后点击自定义添加才对，而不是自己添加」——手填名称/别名/路径的表单不符合预期
- **修复**：废弃自由表单 → **快捷入口选择器**：
  - 「＋ 添加」打开选择器：分组列出全部可快捷进入的页面（页面/考纲 17/真题 12/智能体 5），上方搜索框实时筛选
  - 每条「＋ 添加」点选收录 → 变「✓ 已添加」，再点一次移除（钉选式 toggle）
  - 名称/路径/别名全部取自索引，**用户零手填**
  - 重命名保留为「改」：✎ 内联输入，旧名自动保留进别名（改名后仍可被旧名搜到）
  - 选择器内 Esc 先退选择器、Enter/↑↓ 不触发跳转
- **验证**：CDP 端到端 12 项全过，零控制台错误（测试初期两轮失败均为测试脚本时序问题——考纲异步加载未等、Chrome 残留进程复用端口，应用本身无 bug）
- **文件**：`components/GlobalSearch.vue`、`stores/nav.js`

### 91. 帮助中心全面更新 + 使用说明书页（2026-08-23 更新）

- **问题**：帮助中心停留在 07-30 版本——15 考纲/1252 题旧数据、无真题/词条本/智能体中心/全局搜索条目、账号编辑入口还指向旧个人中心（08-17 已重写为设置页）、题集分享 FAQ 指向已删除的死功能、API 配置描述与「平台官方 Key 现状 + 自带 Key 后期规划」不符
- **修复**：
  - 分类 7 → 10（+词条本/智能体中心），新增 9 条 FAQ（全局搜索/真题套卷/词条本 4 条/智能体中心 4 条），修正过时内容 ~15 处（考纲数、题量、双通道诊断、每日任务学习讲解、账号编辑入口 → 设置页、社区收藏替代已废弃题集分享、API 配置对齐 08-23 现状）
  - 新建独立**使用说明书页** `/guide`（与帮助中心无关，按产品说明书形式：封面/产品简介/快速上手 5 步/功能速览 12 模块可点击/常用操作/注意事项/更多帮助）；侧边栏底部新增「使用指引」入口按钮（意见反馈与开源文档之间）
- **文件**：`components/QAPage.vue`、`views/Guide.vue`、`components/Sidebar.vue`、`router/index.js`、`utils/pageMeta.js`

### 92. 设置页新增「关于」模块 + 版本口径统一（2026-08-24 新增）

- **问题**：网页设置页无任何版本/关于信息（小程序端反而有「关于」区）；且三处版本口径不一致——package.json `1.0.0`、Guide.vue 封面 `v1.0.0-alpha`、OpenSource.vue 页脚 `v1.0.0-alpha` 各写各的。代码分布在本地/jizhi 部署仓库/宝塔服务器/Vercel 五处，用户报障时无版本号难以判断跑的是哪一版（历史多次「服务器代码过旧」故障）
- **修复**：
  - Settings.vue 新增第 8 个模块「关于」：当前版本行（Beta 角标）+ 使用指引/帮助中心/开源文档三张跳转链接卡（复用 link-grid 样式，零后端依赖）
  - 版本号三处统一从 `frontend/package.json` 的 `version` 字段读取（Vite JSON import，构建时注入），发版只改一处
  - SYSTEM_MANUAL 5.13.1 七大 → 八大模块，相关引用同步
- **验证**：vite build 通过；dist 中 `v1.0.0-alpha` 硬编码全部消失，版本经独立 package chunk 注入
- **文件**：`views/Settings.vue`、`views/Guide.vue`、`views/OpenSource.vue`、`SYSTEM_MANUAL.md`、`logs/2026-08-24.md`

### 93. 讯飞语音客户端重写（WebSocket v2）+ 小基「不能用」大修复（2026-08-24 修复）

- **问题**：小基多处「开发中」死按钮；实测发现讯飞语音客户端（TTS+ASR）整体坏的——老版 HTTP 接口（api.xfyun.cn/v1/service/v1/*）对该 appid 已不可用（10105/10106/10107 系列错误），08-23 的 API 模型中心「语音预览」实际一直 500
- **修复**：
  - `utils/xunfei_client.py` 按官方现行 WebSocket v2 协议重写：TTS `wss://tts-api.xfyun.cn/v2/tts`（lame→mp3，短文本单帧 status=2）、ASR `wss://iat-api.xfyun.cn/v2/iat`（raw 16k 40ms/帧 + rpl 渐进拼接 + wav 自动转 16k）；鉴权 authorization 为 `api_key="..."` 字符串形式 base64（写成 JSON 会报 host 签名错误）
  - XiaojiCall：麦克风「开发中」→ 实时语音听写（PCM 流 → `WS /xiaoji/asr-ws` 中转 → 讯飞 iat 逐字回传填输入框，同日升级为流式）；播报 speechSynthesis → 讯飞 TTS（音色/语速/音量读配置 + 缓存 + 浏览器降级）；主动问候按设置门控；播报开关双向同步配置
  - XiaojiSettings：历史检索死按钮 → `/xiaoji/search`；试听改真实 TTS；高级功能组「开发中」标签移除
  - 后端 `/community/xiaoji/chat`：读 xiaoji_config 注入 personality（4 风格）+ 自定义名称（之前写死）
  - CommunityChat：点小基资料 → 跳 `/xiaoji/settings`
- **验证**：TTS 实测出 mp3；ASR 用 SAPI 真实中文语音识别出「你好我是小鸡」（机器音鸡/基之误，链路正确）；HTTP 端点端到端 200
- **遗留**：录音浏览器端到端需真机手动验证；讯飞 TTS 免费 500 次/天；数字人仍占位（腾讯云）
- **文件**：`utils/xunfei_client.py`、`routers/community/xiaoji.py`、`components/XiaojiCall.vue`、`components/XiaojiSettings.vue`、`components/community/CommunityChat.vue`、`api/xiaoji.js`、`logs/2026-08-24.md`

### 94. 音色列表实测修正（2026-08-25）

- **问题**：音色列表有重复（xiaoxuan≡xiaoyan、xiaoyu≡xiaofeng 音频字节完全相同）和方言（xiaokun=河南话、xiaomei=粤语，原标签误写童声/甜美女声）；xiaorui 未授权（licc failed）导致静默降级浏览器音
- **修复**：列表收敛为 5 个真实音色并正确标注（小燕标准女声/小峰标准男声/小萌活力女声/小坤河南话/小梅粤语）；前后端两处 voiceList 同步；已保存失效音色的用户加载时自动重置为 xiaoyan 并回写
- **验证**：8 音色两轮合成 md5 对比 + 讯飞官方发音人表
- **文件**：`components/XiaojiSettings.vue`、`utils/xunfei_client.py`、`logs/2026-08-25.md`

### 95. LLM 全量收编：豆包 → DeepSeek（2026-08-25）

- **背景**：运行时残留 2 处豆包调用（评估中心学情报告 AI 总结、旧 learning-plan 系统）+ 1 处生成脚本，用户决定收编
- **修复**：三处全部换 `agents/llm_client.call_llm`（DeepSeek），失败降级逻辑不变；`utils/volc_client.py` 保留但零引用（备而不用）
- **收编后**：全平台 = DeepSeek Chat（文本）+ DeepSeek Vision（识图）+ 讯飞 TTS/ASR（语音），两个供应商
- **文件**：`routers/evaluation.py`、`routers/learning_plan.py`、`scripts/seed_cet4_questions.py`、`logs/2026-08-25.md`

### 96. 小基「语音通话」独立界面（2026-08-25 新增，千问 Qwen-Audio-3.0-Realtime）

- **背景**：用户指出语音通话 ≠ 语音读文字，应是独立界面（原「语音通话」按钮只跳聊天页）；并指定用千问 `qwen-audio-3.0-realtime-plus` 实时语音对话模型（key 存 `.env` DASHSCOPE_API_KEY）
- **架构**：千问 realtime 为语音到语音原生模型（自带 server_vad 断句 + 自动打断），后端只做薄中转：浏览器 ↔ `WS /xiaoji/call-ws`（鉴权/人设/上下文/落库）↔ 千问 realtime WS
  - 音频进 16k PCM16、出 24k PCM16；音色 = 设置页千问音色（与 TTS 共用同一列表）
  - 通话人设 = 聊天页 system prompt 同源 + 语音短句要求；最近 6 条聊天记录预载为上下文（剥 emoji 不被读出来）；问候由「电话刚接通」触发器 + response.create 生成
  - 用户抢话：前端 RMS 检测 → interrupt → response.cancel + 清播放队列 + 丢弃在途音频（千问 cancel 只停生成不停已生成音频）；空闲 cancel 会触发 invalid_request_error（已规避）
  - 防回声（官方示例同款）：小基播报期间麦克风不发帧；AEC 回声消除双保险
  - 消息落库 kind=voice_call，聊天页可见通话记录；智能体中心新增「语音通话」触点
- **前端**：`views/XiaojiVoiceCall.vue` 独立通话界面（头像+脉冲光环+计时+实时字幕「我/小基」+静音+挂断）；设置页「拨打」入口 + 聊天页工具栏电话按钮；命名册收录
- **验证**：裸协议探测 + SAPI 真实语音端到端（问候/渐进字幕/完整识别/语音回复/打断/挂断全过）
- **文件**：`routers/xiaoji.py`、`routers/agent_center.py`、`views/XiaojiVoiceCall.vue`、`components/XiaojiSettings.vue`、`components/XiaojiCall.vue`、`router/index.js`、`utils/pageMeta.js`、`scripts/test_call_ws.py`、`logs/2026-08-25.md`

### 98. 主界面导航轮盘化（2026-08-26）

- **定稿**：边缘半椭圆中枢轮盘（贴屏幕左缘，左半弧裁掉）——中枢=Logo/用户完整信息/搜索竖排浮层；可视窗口 9 个图标（导航+工具+底部链接全上轨道，56px）；小基为轮盘正前方第一项；箭头+全局滚轮旋转（滚动区不抢事件）
- **组件**：EdgeNavDock.vue（主界面）、NavWheel.vue（学程/社区侧边栏）、ToolPanel.vue（工具面板抽出共用）
- **迭代插曲**：「小基居屏幕正中」多轮理解偏差，最终全部回退到轮盘正前方方案
- **文件**：`components/EdgeNavDock.vue`、`components/NavWheel.vue`、`components/ToolPanel.vue`、`components/Sidebar.vue`、`components/XiaojiCall.vue`、`logs/2026-08-26.md`

### 97. 小基全量收编阿里云千问（2026-08-25：推理 + 识图 + 读文字，价格优惠）

- **背景**：用户要求小基的读文字（TTS）、推理（聊天）、识图全部用阿里云同一个 key，选性价比高的模型，设置页全部可用、关联处全部理顺
- **模型选型（全部实测）**：
  - 小基聊天 = `qwen-flash`（¥0.15/1.5 每百万，实测首字节 0.93s，比 plus 便宜 5 倍、冷启动快 4 倍）
  - 评价题目/题集 = `qwen-plus`（四维度分析要推理质量）
  - 识图 = `qwen3-vl-flash`（¥0.367/2.94，比 qwen-vl-plus 便宜约 4 倍）
  - TTS = `qwen-audio-3.0-tts-plus`（~¥1.4/万字符，输出 mp3 前端零改动）
  - 语音通话 = `qwen-audio-3.0-realtime-plus`（#96）
  - 全部 env 可换（QWEN_CHAT_MODEL / QWEN_REASON_MODEL / QWEN_VISION_MODEL）
- **TTS 协议（实测）**：`wss://dashscope.aliyuncs.com/api-ws/v1/inference`，run-task（text 在 input）+ 二进制 MP3 帧 + task-started/finished；4 个可用音色（longanqian/lingxin/lingxi/lufeng，xiaoxin 在 TTS 报 411 排除），与通话共用音色列表
- **关键修复**：
  - **emoji 不朗读**：TTS 客户端合成前剥 emoji + 通话历史预载剥 + 前端播报入口剥（覆盖浏览器降级朗读路径）
  - **旧 bug**：evaluate-question-stream 把文本片段当 OpenAI 对象取 `chunk.choices`（必炸）→ 直接拼接
  - **流式提速**：profile/config/history 三查 gather 并发 + 用户消息落库不阻塞首字节（4.6s → 3.4s）
  - **通话落库容错**：Supabase 保存失败不再断开通话
- **关联处理顺**：设置页音色列表/默认值/老音色自动迁移、聊天页播报、ApiCenter 语音卡改千问、QAPage FAQ、OpenSource 依赖列表；讯飞仅保留 ASR（听写），讯飞 TTS 代码零引用备而不用
- **验证**：后端冒烟 4 项（TTS/音色列表/流式 18 chunks/qwen3-vl-flash 识图）+ 通话端到端回归 + vite build 全过
- **文件**：`utils/qwen_tts_client.py`、`agents/qwen_client.py`、`config.py`、`routers/xiaoji.py`、`routers/community/xiaoji.py`、`components/XiaojiSettings.vue`、`components/XiaojiCall.vue`、`api/xiaoji.js`、`views/ApiCenter.vue`、`components/QAPage.vue`、`views/OpenSource.vue`、`scripts/test_qwen_stack.py`、`logs/2026-08-25.md`

### 99. 出题/难度系数双修（2026-08-30）

- **出题偏 Python**：category 默认值写死 "Python"、提示词无学科锚定、示例全 Python 味、角度池含编程术语。修复：默认「通用」+ 【学科自定·最高优先】规则（按知识点判定学科语境，非编程知识点严禁代码/算法概念）+ 中性示例 + 编程角度转译。实测「函数」→数学题、「定语从句」→英语题
- **难度系数改三档区间**（用户定稿）：简单 1-3 / 中等 4-6 / 困难 7-10，AI 在区间内按题目实际难易判分，后端钳制（缺值取中值/越界收回）；换题逻辑改区间映射（原精确匹配 2/6/8.5 其余全归中等）
- **文件**：`routers/questions.py`、`views/DoQuestion.vue`

### 100. 做题页提交友好加载（2026-08-30）

- 提交评估期间答题区切换 LoadingSpinner orbit 动画 + 阶段文案轮换（批改/掌握度/讲视频），失败答案不丢
- **文件**：`views/DoQuestion.vue`

### 101. 评估中心全局化 + 全平台数据底座（2026-08-30）

- **位置**：评估中心进轮盘/侧边栏（新画 evaluation.png），资源库移除评估 Tab；入口卡定名「自定义计划」（=旧 learning-plan，与学科计划互补的自定义体系）
- **后端**：`GET /evaluation/overview`（全平台聚合：做题 30 天逐日/掌握度+错题画像/真题战绩/学科+自定义计划/词条/90 天节奏/engagement 全产品使用）+ `GET /evaluation/deep-analysis`（LLM 总结+人格+诊断 cause/advice_actions，15 分钟缓存）；节奏数据源 activities → user_actions（北京时区）
- **排查附带**：exam_paper_records 无 GRANT（真题交卷落库/历史成绩一直静默失败）→ `sql/grant_exam_paper_records.sql` 待执行
- **文件**：`routers/evaluation.py`、`components/EdgeNavDock.vue`、`components/Sidebar.vue`、`views/ResourceLib.vue`、`sql/grant_exam_paper_records.sql`

### 102. 学情报告重做：一页式长报告（2026-08-30）

- AI 解读 → 3 总览卡 → 30 天趋势双小图（无双轴混图）→ 掌握度分布 → 薄弱点（一键练习）→ 错题画像 → 真题战绩 → 节奏日历 → 计划进度 → 知识点详情（垫底，默认 20 条可展开）
- 假数据/冗余清理：报告死模块（近期动态）、总览 6→3、词条卡删除等；PDF 导出保留
- **文件**：`views/EvaluationReport.vue`

### 103. 评估表重设计：纯结论页 + 动效（2026-08-30）

- 三轮演进：数据版 → 诊断决策页 → **纯评估结论页**（用户拍板「评估表不出数据，数据归学情报告」）：评级徽章（光环脉冲）+ AI 深度诊断（核心问题/归因/优势/行动×3 错峰浮现）+ 待攻克清单 + 生成自定义计划主 CTA；prefers-reduced-motion 降级
- 假数据清理：学习行为卡（硬编码 12/7/8/96）、维度 55 写死、Math.random() 随机人格全部移除
- **文件**：`views/EvaluationTable.vue`、`routers/evaluation.py`（诊断字段扩展）

### 104. 自定义计划「生成不出」修复（2026-08-30）

- **慢**：DeepSeek 生成整份计划实测 73.7s → 切 qwen-flash 实测 **8.75s**（DeepSeek 后备 + 本地降级）
- **保存必败**：learning_tasks 缺 video_query 列（PGRST204）→ `sql/fix_learning_tasks.sql` 待执行；前端原静默吞失败 → 加 90s 超时 + 失败/保存失败明确提示
- **文件**：`routers/learning_plan.py`、`views/PlanPreview.vue`、`sql/fix_learning_tasks.sql`

### 105. 轮盘落款去底片改蓝字（2026-08-30）

- 「基智」艺术字删墨黑金印底片，改回渐变蓝 `#9cc4ff→#4d8dff→#2f6fe0`，深浅主题通用
- **文件**：`components/EdgeNavDock.vue`

### 106. 主题定制：自定义主题色 + 字体色（2026-09-02/03 新增）

- **用户拍板**：自定义主题色 + 字体色、舍弃现有背景图——品牌色/字体方案存账号跨设备同步，背景氛围由品牌色前端派生
- **后端**：`sql/fix_user_theme.sql` 建 `user_theme_settings` 表（brand_color / text_scheme / text_overrides，幂等）；`auth.py` 新增 `GET /auth/theme/{user_id}` + `PUT /auth/theme`
- **前端**：`stores/theme.js` 全链路（BRAND_PRESETS 7 预设 / FONT_SCHEMES 5 字体档 + 自定义三档 / hexToRgb·mixColor·contrastRatio 工具 / injectCustomVars 注入 --brand 系列 + --text-* / loadFromAccount 登录+路由双挂载 + localStorage 缓存）/ `Settings.vue` 外观模块（色板 + 取色器 + 字体档 + 对比度徽章）/ `api/auth.js` 两个封装
- **全站生效**：`_sweep.py` 批量替换 46 文件（#409EFF→var(--brand)、rgba(64,158,255,α)→color-mix）；canvas 艺术字渐变等 5 处保留硬编码（canvas 不认 CSS 变量）
- **断电续接修复**：ProfileCard.vue `themeStore` 引用缺声明（白屏级）；ECharts canvas 不认 var()/color-mix → 两处图表色改为 `brandSoft(alpha)` JS 解析 rgba
- **待办**：执行 fix_user_theme.sql；后端重启；真机确认全站联动
- **文件**：`sql/fix_user_theme.sql`、`routers/auth.py`、`api/auth.js`、`stores/theme.js`、`views/Settings.vue`、`styles/theme.css` + 46 组件/视图、`logs/2026-09-02.md`

### 107. 主题定制补全四轴（背景/组件/主题/字体）+ 实时预览 + 舍弃背景图（2026-09-03）

- **用户定调（两轮）**：① 定制项应是「背景色 + 主题色 + 字体色」——预设好的、**预设一套的**、**高级 rgb 选色**，加适配度提醒（会不会看不清，按百分比 + 清楚建议）；② 再加**组件色（毛玻璃）**共四轴，高级调色区下面加**实时预览小界面**，四种色 + 适配度一起显示
- **设置页「外观」结构**（`Settings.vue`）：
  - **预设一套**：`THEME_SETS` 6 套（深空蓝/纯净白/星云紫/冰川青/暖沙棕/曜黑金），bg+surface+brand+scheme 逐套预校验对比度，一键换四轴；色卡缩略图四色（背景底+组件块+主题圆点+字体横条）+ 激活描边
  - **背景色**：跟随主题（默认 null）+ `BG_PRESETS` 浅/深系各 5 预设 + 高级 el-color-picker；`setBg` 覆盖 `--bg-color`
  - **组件色**：`SURFACE_PRESETS` 浅/深系各 5 + 高级选色；`setSurface` 注入 `--surface` 并按模式重算 `--card-bg`/`--input-bg`（withAlpha 0.8/0.4 深、0.85/0.7 浅）
  - **主题色 / 字体色（自定义=高级）**：沿用 09-02
  - **实时预览 + 适配度合并块**：预览小界面 = 背景底色（品牌微光氛围）+ 毛玻璃卡片（组件色 + blur）+ 主/次/弱三档字 + 主题按钮/主题链接，四色实时跟手；适配度百分比 + 进度条 + 逐项建议 + 一键「自动调整字体色」紧跟预览
  - **适配度 5 组加权 → 百分比**：主文字×组件 38% / 主题色×组件 20% / 组件×背景 17% / 次文字×组件 15% / 弱文字×组件 10%（文字主要落在卡片上，基准从背景改为组件色）；建议清晰到动作，如「组件色与背景色过于接近，毛玻璃卡片会融进背景」「主题色与组件色过于接近，按钮和选中态会不明显」；一键修正按组件亮度选 paper/ink
- **组件色全站收编（批量替换）**：`_sweep_surface.py` 62 文件 523 处 `background(:-color)?: rgba(255,255,255,α)` → `color-mix(in srgb, var(--surface, #ffffff) α%, transparent)`——默认 #ffffff 渲染与原来完全一致，自定义组件色后全站玻璃卡片/输入框/浮层/悬停描层联动；color/边框/阴影不动（分别归字体色/结构色管）
- **舍弃背景图**：`constants.js` 删 BG_MAP、`App.vue` 去照片层、`theme.css` `.app-container` 改「品牌色两层径向微光 + 背景色上下明暗渐变」纯 CSS 氛围（color-mix 实时联动）、8 个页面自带 `/assets/bg/*` 背景 CSS 全部移除、**public/assets/bg 26MB 图片资产物理删除**
- **后端**（`routers/auth.py` + `sql/fix_user_theme.sql`）：五字段（brand/scheme/overrides/bg/surface，hex 校验、null=跟随主题）；PUT 改**全量保存**（null 即清空）——顺手修了旧 bug「恢复默认不清 text_overrides，跨设备还是会载回旧字色」
- **验证**：vite build 通过、auth.py py_compile 通过；dist 实测含 `var(--surface,#fff)` 与预览样式
- **待办**：① 执行 `fix_user_theme.sql`（四轴列齐全，未执行则只差账号同步）② 后端重启 ③ 真机确认：四轴全站联动（尤其组件色全站收编观感）、预览跟手、适配度百分比与建议 ④ **主题码分享功能**（用户已拍板，晚间做——四轴导出成分享码 + `/theme?code=` 直达，v1 纯前端；详见 logs/2026-09-03.md 记录）
- **文件**：`stores/theme.js`、`styles/theme.css`、`views/Settings.vue`、`App.vue`、`utils/constants.js`、`_sweep_surface.py` + 62 组件/视图、`routers/auth.py`、`sql/fix_user_theme.sql`、`logs/2026-09-03.md`

### 108. DeepSeek 模型升级至 V4.1 Flash（文本 + 识图合并）（2026-09-10）

- **背景**：DeepSeek 09-10 发布 **V4.1 Flash**（API 名 `deepseek-flash`，552B MoE、原生多模态），旧 V4 Flash 与 V4 Flash Vision Exp 已下线（旧名仅临时路由）；代码里的 `deepseek-chat`、`deepseek-v4-flash-vision-exp` 全是遗产名
- **实测（平台 key 直连官方接口）**：
  - `GET /models` 仅剩 `deepseek-flash` + `deepseek-v4-pro`（后者 09-14 12:00 起也路由到 Flash，按 Flash 计费）
  - **V4.1 Flash 默认开思考模式**：流式首字 0.6s → **1~13s**（闲聊 5.6s / 批改 3.1s / 解释概念 1.1s / 学情总结 3.8s / 出题 12.4s）；思考计入 `max_tokens`（额度给小会**只思考不出正文**）；`extra_body={"thinking":{"type":"disabled"}}` 可关（token 73→13），`reasoning_effort=none` 等效，`chat_template_kwargs` 无效
  - **识图无需单独模型**：V4.1 Flash 原生多模态，文本与识图同一个模型（实测识图正确）
- **改动**：`llm_client.py` 新增 `get_model()`（env `DEEPSEEK_MODEL`，默认 `deepseek-flash`）+ `_thinking_kwargs()`（**思考默认关** = 与迁移前 `deepseek-chat` 非思考档行为一致；env `DEEPSEEK_THINKING=1` 可开启）；`get_vision_model()` 默认同文本模型；四个调用（非流式/流式/识图/识图流式）全部接入
- **同步清理**：`config.py`（+DEEPSEEK_MODEL/DEEPSEEK_THINKING）、`.env.example`、ApiCenter.vue（2 卡片 + 概览 + 豆包卡文案）、QAPage.vue、SYSTEM_MANUAL 6 处、PROJECT_SUMMARY；**顺手修正文档笔误**：小基识图实际走千问 qwen3-vl-flash（08-25 已收编），文档原写 DeepSeek Vision
- **验证**：模块真实调用链三路实测——非流式 1.4s / 流式首字 **0.63s** / 识图答案正确
- **文件**：`agents/llm_client.py`、`config.py`、`.env.example`、`views/ApiCenter.vue`、`components/QAPage.vue`、`SYSTEM_MANUAL.md`、`PROJECT_SUMMARY.md`、`logs/2026-09-10.md`

### 109. 智能体协作审计（小基 × 其他智能体）+ 三处账目修复（2026-09-10）

- **起因**：用户「小基与其他智能体的搭配配合，之前只搞了大概框架，其实并没有搞好」→ 全链路审计，产出 **`AGENT_AUDIT.md`**（含每条结论的 `文件:行号` 证据）
- **核心结论**：
  - **Web 主界面就是小基**（`Home.vue` 只有 `<XiaojiCall />`）；呼叫对象 5 项里**只有生成 Agent 真干活**（真出题落库），规划/评估是「换人设 + 注入真数据 → 纯说话」——不产出结构化结果、不写数据、不触发动作（`AGENT_PERSONAS` 仅注册 plan/evaluate）
  - **`agents/planner|generator|evaluator.py` 是不可达死代码**：三份提示词只差一个词；Web 零调用 `/chat/*`，小程序调 `/chat/send` 但不传 `intent`（默认 `chat`），`/chat/detect-intent` 全平台零调用 → `chat.py:188-198` 三条分支永不执行；且三者读的 `user_profile.get('level')` 键**不存在**，恒为「中等」
  - **磨合闭环断在最后一环**：`agent_prefs` **只写不读**——没有任何调用点读它，设计承诺的「下次调用实时拼装」从未落地，「参数调节/自动托管」是装饰性的
  - **页面画的协作链与真实路径相反**：闭环图画的是 `chat → plan → evaluate → generate`，小基不在链上（被标为「并行入口」），而现实中 chat 是空壳、小基才是唯一入口
  - **设计稿 vs 实现**：`generate × mastery` 协同对设计承诺「前后对比」，实现 `base=None` → delta 恒 null；「同一动作两视角」双计是设计如此，但依附的主对话已死，账没跟着改
- **修复（用户「改」）**：
  1. **同一点击记 3 次 → 1 次**：chat 三个「分流」加 `touchpoint: "chat_main"` 过滤（主对话不在则如实计 0）+ 新增 `_distinct_action_count()` 让总调用数的 action 部分按**去重事件**统计 + 详情页「意图路由分布」同步口径
  2. **闭环链配色失效**：`AgentCenter.vue:56` 的 `l.agentKey` → `l.agent_key`（后端返回下划线命名）
  3. **队员署名串台**：`pendingAgent` 在图片/视频分支残留 → `streamXiaojiChat` 改为读取处立即消费 + 图片/视频分支显式清零
- **验证**：假数据实测去重（chat 分流 4→0、plan 3、xiaoji 4 各归其位；总调用数 9→5 真实值）；`py_compile` ✅；`vite build` 1.32s ✅
- **待决策（未动）**：①评估 Agent 产出结构化评估卡 ②规划 Agent 真建/改计划 ③让 agent_prefs 被读取 ④清理死掉的三 agent 与空账触点 ⑤对话 Agent 归属对齐——详见 `AGENT_AUDIT.md` §6
- **文件**：`AGENT_AUDIT.md`（新增）、`routers/agent_center.py`、`views/AgentCenter.vue`、`components/XiaojiCall.vue`、`logs/2026-09-10.md`

### 110. 小基对话自动化：删下拉框改自动判别 + 三张卡片 + 长期记忆（2026-09-10）

- **用户拍板**：「一定要自动判别，下拉框太掉价了」——删掉手动「呼叫对象」，按用户说的内容自动分流；规划/评估/生成不再输出大段文字，改出**可执行卡片**；上下文要压缩、不能越聊越贵
- **意图判别**（`agents/intent_router.py` 新增）三级阶梯：①规则层（明确指令词，**0 元 0ms**）→ ②关键词门 + **疑问词排除**（「这道题怎么做」是在问不是在派活，**0 元 0ms**）→ ③qwen-flash 兜底（仅「像派活但规则没抓住」，~0.004 分/次）。**默认闲聊**（判错代价最小）。实测 23 条真实消息仅 2 条进第③层
- **接入**：新增 `POST /community/xiaoji/route`（`deep=false` 供输入框实时预判）；`chat-stream` **内部判别**，派活时直接返回 JSON 路由指令（**不额外增加网络往返**）；`force_chat` 给陪伴 chips 跳过判别
- **三张卡片**（全复用既有链路）：生成卡（知识点自动预填 → 出题 → **跳做题界面**，与资源库同款）/ 规划卡（聊天内填参数 → 真实调 `/learning-plan/generate-tasks` → 建计划 → 跳详情）/ 评估卡（复用 `/evaluation/deep-analysis`）
- **状态与按键**：识别状态 chip + 状态/placeholder 随模式变；**拆掉假进度戏**——原 `setInterval` 每 1.5s 推进四个写死的「Agent」格，换成真实阶段（「正在出第 2/3 道题…」）；顺修进度条百分比绑定不存在导出（恒 `undefined`）的老 bug
- **长期记忆**（`services/xiaoji_memory.py` + `sql/create_xiaoji_memory.sql` 新增）三层上下文成本恒定：事实档案（增量抽取）+ 滚动摘要 + 最近 10 条原文；压缩**回复后台跑**、只读游标之后的新消息、`asyncio.to_thread` 不卡事件循环；**表未建优雅降级**（已实测）
- **验证**：判别/分流/兜底/force_chat 端到端 HTTP 四组全过；知识点预填 11 条全对；降级路径实测；压缩提示词真实调 qwen-flash 产出合法 JSON 且事实抽取准确；聊天链路回归正常流式；`py_compile` ✅、`vite build` 1.37s ✅
- **待办**：① 用户执行 `create_xiaoji_memory.sql` ② 用户真机验收四张卡片（浏览器渲染与点击流转未验）
- **文件**：`agents/intent_router.py`、`services/xiaoji_memory.py`、`sql/create_xiaoji_memory.sql`（三者新增）、`routers/community/xiaoji.py`、`components/XiaojiCall.vue`、`composables/useXiaojiAvatar.js`、`api/xiaoji.js`、`logs/2026-09-10.md`

### 111. 出题提示词重构：题型轴 × 学科轴 + 编程题质检闸（2026-09-11）

- **起因**：用户「生成的编程题运行报错」→ 逐题型实测，发现**旧版一套 JSON 模板套所有题型**造成的实际伤害：**判断题与计算题的 answer 双双被污染成选项字母 `A`**（模板硬塞 `options:{A,B,C,D}`）；编程题的 `starter_code`/`test_cases` 在模板里根本没有（`questions` 表其实有这两列，白留）
- **改法**：`QTYPE_SPECS`（7 种题型各自的输出字段表 + 答案写法 + 禁止项，只有选择题带 options）/ `SUBJECT_DISCIPLINE`（11 学科纪律，代码概念只在计算机学科出现）/ `ANGLES_COMMON|ANGLES_CS`（按学科选角度池，取代旧的「编程角度再转译」补丁）/ `PROGRAMMING_JSON_TEMPLATE`（沿用 `seed_all_banks.py` 已有的标准 schema，类型名改回题库的 `programming`）；落库补 `starter_code`/`test_cases`
- **质检闸**：实测模型自算的期望值 **17 条用例只有 13 条对得上（76%）**，光校验 JSON 结构看不出来。生成后真跑参考答案 → 不一致就带实跑证据让模型修（≤2 轮）→ 仍不过 502，不落库。**落库题通过率 76% → 100%（15/15）**
- **踩坑**：修复轮**从来没生效过**——修复调用是不带 schema 的全新对话，模型只能自己编格式。补 schema + 键名归一后才起作用
- **配套**：`EVAL_SPECS` 按题型分派评估字段（选择题 `option_analysis` 逐项对错、计算题 `steps` 分步对错）；`/code/submit` 支持 Supabase 生成题（原先只查本地题库必然 404）+ 认 `output` 键；`DoQuestion` 编程题加代码编辑器 + 运行 + 逐测试点判分
- **文件**：`routers/questions.py`、`routers/subject_plan.py`、`views/DoQuestion.vue`、`logs/2026-09-11.md`

### 112. 代码沙箱：Java 全线修复（2026-09-11）

- **现象**：四种语言只有 Java 坏（`代码执行服务暂不可用`）。根因链：本机无 javac/java → 回退 Piston → `localhost:2000` 无服务；而前端 `CODE_LANGS` 硬编码四种语言、从不问后端
- **winget 装 JDK 是假成功**：MSI 要管理员提权，非交互会话里 UAC 没弹出来，安装器根本没执行（注册表/磁盘/`winget list` 三处查无此物），winget 却报成功 → 改走免管理员 zip 解压到代码预留的 `backend/utils/jdk/`（OpenJDK 17.0.20.1 LTS，已 gitignore）
- **顺带修两个 Java 真 bug**：① 源码按 UTF-8 落盘而 javac 跟随平台编码（中文 Windows 是 GBK）→ 含中文注释/字符串的代码必然编译失败且只报「找不到主类」→ 补 `-encoding UTF-8` ② javac 结果被丢弃直接跑 java → 补 returncode 检查，与 C/C++ 对齐
- **文件**：`utils/code_runner.py`、`.gitignore`、`logs/2026-09-11.md`

### 113. 提示词去重 + 计划/评分适配（2026-09-11，两批并行子代理）

- **去重 5 组**：① 死端点 `/chat/detect-intent` 删除（全站零引用）② 小基人设抽 `services/xiaoji_persona.py` 单一来源 ③ 记忆 facts JSON 骨架由 `_FACT_LABELS` 生成 ④ 视频 `_SCRIPT_SCHEMA` 三处共用 ⑤ 题评四维度合一
- **`learning_plan.py`**：题型不再锁死三种、示例题从模板删除。实测考研数学→选择/填空/计算、英语→选择/填空/**翻译/改错/写作**、Python→**编程题×3**
- **`exam_papers.py`**：`syllabus_id` 形参以前**完全没用上**（雅思、考研英语都在套 CET-4 标准）→ 按考纲解析学科族，六套口径，真题自带 `grading_rubric` 优先
- **子代理挖出的真 bug**：`learning_plan` 的 `difficulty` 声明是 `int`，而小基规划卡两步都传中文档位 `'中等'` → **规划卡从 09-10 做出来就是坏的、一次都没成功过**。加 `_DifficultyMixin` 收平台档位词汇
- **文件**：`routers/chat.py`、`services/xiaoji_persona.py`（新增）、`services/xiaoji_memory.py`、`services/video_gen.py`、`routers/learning_plan.py`、`routers/exam_papers.py`

### 114. 个人画像：三个「显示不了」的根因（2026-09-11）

- **起因**：用户「为什么还有非流式」→ 转「维度宇宙怎么还是这么多没有数据，你是不是看错地方了」
- **三层根因**：① **前后端字段名对不上**（前端读 `cognitive_preference`/`mistake_map`/`growth_trajectory`，后端给 `cognitive_style`/`mistake_pattern`，第三个**压根没算过**）→ 三块整块不显示 ② 后端读 `activities` 表——**这张表从未建过**（sql 里没有），PostgREST 直接 401 → 学习节奏全 0（`messages.py`、`daily_generator.py` 同病）③ `t["name"]` 对元组取字符串键 → AI 总结**从来没生成过**，永远占位文案
- **第四层**：`mastery_score = 0` 是「还没作答」的默认值，却被当真分数算 → 200 道题里 161 道未作答把平均掌握度拉到 0。按已作答过滤后 **0 → 87**
- **第五层**：能力维度靠知识点关键词硬匹配，「集合」「微积分」一个词都命中不了 → 改关键词优先 + 题型兜底
- **AI 洞见重构**：用户质疑「这个意义有什么呢」——原版确实只是复述其他维度的数字。改成 LLM 出「一条非显而易见的洞察 + 2~3 条可执行行动」，失败时规则兜底
- **实测**：用户账号九维全有数据（知识 25 均 87 / 能力 2 轴 / 活跃 51 天 / 认知 6 类 / 错题 58 / 成长 19 点 / 兴趣 12 / AI 行动 3 条）
- **文件**：`routers/evaluation.py`、`routers/community/messages.py`、`services/daily_generator.py`、`logs/2026-09-11.md`

### 115. 维度宇宙重做：星图化 + 进场/出场转场（2026-09-12）

- **起因**：数据修通后用户反馈「画面效果很差，我是说点击详情的里面展示不好看」
- **详情面板**：`dim-card` 容器 + KPI 摘要行 + 统一 tooltip/轴样式；**知识星系改极坐标星爆图**（原来是 `Math.random()` 假连线 + 50px 节点挤成一团）；能力雷达 <3 轴降级条形；易错地图改「色相表攻克、明度表数量」；成长轨迹加均值线
- **宇宙本体**：九星加 **emissive 自发光**（原来只用中心点光源 decay=1.5，外圈星球照不到光近乎全黑——**这就是「没数据」观感的真正来源**）；加**侧栏维度清单**（标 9/9 有数据）；加**极坐标星图网格**；每条轨道独立**倾角**（原来全在同一平面）；加**右上角坐标面板**（R/θ/i/y 实时跳动）；**恒星联动用户外观色**
- **交互**：去掉返回键，改**点击中央恒星退出**；加**维度深链** `?dim=xxx`
- **转场**（用户改了四轮，最终定稿）：进场**从虚空推进**（星空扩到 ±1600、关闭距离衰减、起点 1100 落在星空内部——用户拍板「不是改成球状，是机位位于虚空内」）；出场**放大中心球体**后闪白切主页
- **踩的坑（都是硬伤）**：① 相机 `far = 60` —— 超过 60 单位**根本不渲染**，进场大部分路程是空白，用户感觉「太近」② `controls.maxDistance = 35` **写死** —— OrbitControls 每帧把相机拽回来，起点设 900/2600 全被夹掉，用户直接问「你是不是写死了什么」③ 距离线性插值 → 观感是硬切，改**对数插值**才是视觉匀速 ④ `SpriteMaterial` 缺 `depthWrite:false` 写深度缓冲 → 整屏随机糊成灰色（已移除该精灵）
- **未解决**：整屏随机发灰未能根治，**怀疑是 `--disable-gpu` + SwiftShader 软件渲染的测试环境假象**（用户从没报过），已停止盲改；退出转场偶发误触发原因不明，已加自愈兜底
- **文件**：`views/ProfileCard.vue`、`logs/2026-09-12.md`

---

### 116. 维度宇宙二改：程序化星球 + 中央黑洞 + 螺旋吸入转场（2026-09-15）

- **起因**：用户「星球都是简单的球体加颜色，是不是太简单了」→ 做完又提「中间的点击退出球体能不能做成黑洞」→ 转场来回改了六轮
- **定调**（问过用户）：视觉走**程序化真实感**；外观**纯装饰、不承载分数**
- **程序化星球**（新模块 `utils/planetTexture.js` + `utils/procedural.js`）：
  - 关键做法：**不按 (u,v) 平面采噪声**，而是先把每个纹素换算成球面上的真实单位方向，再拿这个方向采 3D 噪声——噪声本身就定义在球面上，等距圆柱投影的**接缝与两极挤压**自然都不存在
  - 六生成器 × 九配方（terran / gas / ice / rock / lava / ocean），九颗不重样；另有独立云层球（转得比地表快 → 视差）+ 径向分带光环
  - 性能：九颗 512×256 同步算要 0.5s 会卡住首帧 → 先挂 1×1 占位贴图让着色器按「有贴图」编译好，再**一次算一颗、算好一颗换一颗**，藏进 3.4s 的进场动画里
  - 资源管理：补 `destroySolar` 纹理 dispose（九颗约 5MB）+ `texRunToken` 任务令牌（贴图没算完就切走时作废在途任务，否则显存回收不掉）
- **中央天体改黑洞**（新模块 `utils/blackHole.js`）：① 事件视界纯黑球（`MeshBasicMaterial` 不受光照，把背后星空彻底吃掉）② 光子环 + 透镜弧（**billboard 贴图**而非真做引力透镜；真透镜要单独一整套后处理）③ 赤道吸积盘（缓慢自转，内缘白热向外冷却 + 角向湍流条纹）。配色仍跟随用户外观色（09-12 那条「中央天体联动外观色」依然成立），中心点光源保留
- **去掉大气球壳**（用户「为什么星球上有一层球状环」）：那是 1.32 倍半径的菲涅尔壳，亮环出现在**它自己的边缘**上，跟星球之间隔着一道暗缝，看着像套了个玻璃泡
- **出场转场**（用户改了**六轮**，最终版）：行星依次**螺旋坠入**（内圈先落、角速度随半径暴涨）→ 星尘**从远处旋转着涌来**一股 → 直接切主页。全程在 3D 里完成，**不盖 DOM 遮罩**
  - 两个关键项：角速度必须随半径暴涨（少了它行星只是沿半径笔直滑向中心，像掉下去而不是被卷进去）；缩放跟着**半径**而非时间走（行星半径与视界相当，不收掉就是行星盖住黑洞）
  - 黑洞**全程不放大、不变色**——第 ②~⑤ 轮试过「黑洞放大吞屏」「粒子填满屏幕化作外观色」，都被用户否掉，详见 `logs/2026-09-15.md`
- **顺手**：底栏加「点中央黑洞退出」（黑洞比原来的亮恒星暗得多，而返回键 09-12 已拆，这是唯一出口）
- **踩的坑**：① `_ridge` 噪声取值挤在 0.5 附近，直接 `pow()` 曲线被压平 → 冰星/海洋星渲染成纯色球 ② 行星在**视界内部还在显示**（数值核对才发现，肉眼量像素发现不了）③ 星尘粒子初版每颗 30+ 像素，比行星还大、叠成一片糊白 ④ dev server 缓存了链式 `sed` 的中间态，报 `Export 'makeAtmosphereMaterial' is not defined`
- **文件**：`utils/planetTexture.js`、`utils/procedural.js`、`utils/blackHole.js`（三个新模块）、`views/ProfileCard.vue`、`logs/2026-09-15.md`

---

### 117. 小程序功能全面对接（2026-09-18）
- **问题**：小程序停在早期版本，与网页端差距大（25 页 vs 41 页需求）
- **修复**：页面扩到 41 个，逐模块对齐网页端；导航形态同步重做
- **文件**：`D:\jizhi-miniapp\src\pages\*`

### 118. 小程序导航改版：撤 TabBar（2026-09-18）
- **问题**：底部 5 Tab 承载不了 41 个页面
- **修复**：撤掉 TabBar，改成与网页端对齐的导航；首页宫格 = 网页端弧形轮盘的对应物
- **文件**：`src/pages.json`、`src/utils/constants.js`

### 119. 小程序小基主界面照网页端重做（2026-09-18）
- **修复**：气泡/列表双模 + 意图分流 + 识图 + TTS，对齐网页端 `XiaojiCall.vue`
- **文件**：`src/pages/index/index.vue`

### 120. 小程序隐私合规整改（2026-09-22）
- **问题**：提审被驳回（个人主体 + 隐私合规红线）
- **修复**：协议占位全部填完（含存储地域 AWS 东京 `ap-northeast-1`）；隐私接口清单核对（仅 `chooseMedia`/`chooseImage` + `setClipboardData` 两类）；`src/` 下「待填」占位归零
- **文件**：`src/pages/agreement/index.vue`、`src/pages/privacy/*`

### 121. 小程序个人中心照网页端重做（2026-09-23）
- **问题**：小程序「我的」是「头像 + 3 格统计 + 17 项菜单」，网页端是**资料卡为主体**（卡内只放展示内容，给好友/陌生人看）
- **修复**：新增资料卡组件，撤 17 项菜单（14 项首页宫格已有、2 项设置页已有、退出登录移到卡外）
- **文件**：`src/components/ProfileCard/ProfileCard.vue`、`src/api/profileCard.js`、`src/pages/profile/index.vue`

### 122. 小程序 emoji → uni-icons（2026-09-23）
- **问题**：26 个 WebP 图标混了四种风格（3D 渲染插画 / 扁平单色），当 UI 小图标不合适
- **修复**：改用 `uni-icons`。**先验证字体会不会加载** —— 微信 `loadFontFace` 不认本地文件路径，若从 CDN 取字体小程序里会整片豆腐块；实测产物是 **base64 内联**（161 图标 / 54 KB），不依赖网络、不需要配域名白名单
- **文件**：`src/**/*.vue`、`src/utils/icons.js`

### 123. 胶囊按钮遮挡：几何计算抽成 helper（2026-09-23）
- **问题**：`env(safe-area-inset-top)` 在安卓上常常是 0，自定义导航栏页面的顶栏顶进胶囊里。全项目 18 个页面自绘顶栏，5 个自定义导航栏页面里**有 4 个各算各的** —— 首页有留白、搜索页漏了
- **修复**：抽成 `getNavMetrics()`，全项目只剩一处算胶囊几何
- **文件**：`src/utils/constants.js` + 4 个页面

### 124. 小程序全项目放大 + 上色（43 页）（2026-09-23）
- **问题**：用户「放大一些、多彩一些，按两种背景色分配不同多彩」。审计发现**九色分类色板基本是死代码**（`var(--c-*)` 全项目只有 2 处活引用）、`--tone-soft` **0 消费者**（而它正是用来做彩色底托的）
- **修复**：36 文件 / 117 条尺寸规则（进度条 8→14rpx、控件 72→88、主按钮 80→96、状态点 14→20）；浅色主题 15 处真 bug；根背景新增三档彩色氛围光（深浅两套**不同值**，浅色必须压更低）；一条 `.sec-title` 等规则点亮 29 页
- **⚠️ 未验证**：全部只验到「编译通过」，没进过开发者工具、没真机实测
- **文件**：`src/**/*.vue`、`src/App.vue`

### 125. 小程序图标 500：WebP 转换漏了一行（2026-09-23）
- **问题**：`Failed to load local image resource /static/xiaoji_thinking.png` → 500
- **根因**：09-18 把 5 张形象图转 WebP 时**漏了 `pages/index/index.vue:204`** —— 同文件下面的 `getXiaojiState()` 是对的，唯独顶部头像那行走漏。`static/` 下只有 webp
- **修复**：改 `.webp`；全项目扫过只有这一处漏网
- **文件**：`src/pages/index/index.vue`

### 126. TTS / ASR 双双 500：服务器缺一个库（2026-09-23）
- **问题**：`/xiaoji/tts` 与 `/xiaoji/asr` 都 500，且**耗时都只有 0.12 秒**
- **根因**：两个**不同厂商**的接口以同样方式、同样耗时失败 —— 共同点只有 `websocket-client`。0.12s 说明**根本没走网络**，两个客户端里能瞬时返回 None 的只有 `except ImportError: return None` 那一条。**服务器从来没执行过 `pip install`**（`requirements.txt:13` 早就声明了）
- **修复**：用户侧执行 `pip install websocket-client` + 重启服务
- **顺带**：`routers/xiaoji.py:328` 自己抛的 `HTTPException` 被 338 行的宽泛 `except Exception` 又包一层，客户端收到套娃信息；加 `except HTTPException: raise`

### 127. 导出失败：html2canvas 不认 color-mix（2026-09-27）
- **问题**：个人中心 PDF/图片导出、评估表与学情报告 PDF 导出全部失败，界面只有「导出失败」四个字
- **根因**：`html2canvas@1.4.1` 的颜色表**只有 `hsl/hsla/rgb/rgba`**，而 Chrome 在 computed value 阶段就把 `color-mix()` 算成 **`color(srgb …)`** → 解析器直接 `throw`。项目里 `color-mix()` 用了 **1124 处 / 74 个文件**
- **修复**：不加依赖，把**浏览器已经算好的**颜色降级成 inline `rgba()` 写回（`utils/exportColor.js`）。**两趟**：先全读收集、再全写（边读边写会反复强制重排）
- **顺带**：`EvaluationReport.vue` / `EvaluationTable.vue` 的 `pdfExporting` 在 `return` **之后**才置位，报告加载中点导出**什么都不会发生**（无 toast / 无 loading / 无报错）
- **文件**：`frontend/src/utils/exportColor.js` + 三个导出组件

### 128. 视频库检索不到：命名空间错配（2026-09-27）
- **问题**：答题错误时给的自营视频一直加载不出来
- **根因**：`knowledge_key = f"{subject}:{sha1(知识点)[:12]}"` —— **前缀一变整个键就变**。前端传 `category`，视频库存的是 syllabus id。**第二个致命处**：`video_gen.py` 的兜底写在 `if subject:` 分支里，而前端**永远传非空 subject** → 兜底永远走不到。前端拿到 0 条后轮询 5×8s=40s，而实测生成一条要 **4 分 14 秒** → 必然耗尽
- **修复**：前端改传 `syllabus_id`；后端兜底重写为三档降级（90 知识点哈希 / 70 同学科 / 55 全局）
- **验证**：喂入 32 条真实视频行 —— `excel:5ca68d755414` 修复前 0 条 → 修复后 **6 条**
- **文件**：`DoQuestion.vue:764`、`routers/video.py`

### 129. 奖励成就领取不了：Depends 对象被直调（2026-09-27）
- **问题**：学程里奖励和成就一律 403「无权操作其他用户的数据」
- **根因**：`claim_task` 等**直接调用**了同样带 `Depends(get_current_user)` 的路由函数 —— `current_user` 落到 Depends 默认值，比对必然不等
- **修复**：拆「路由壳 + 核心逻辑」，核心函数不带 Depends、不自行鉴权
- **⚠️ 扫出 4 处而不是 3 处**：第一版扫描正则 `[^)]*` 处理不了 `Depends(...)` 的嵌套括号，报「0 处」；修好后才扫出真数
- **⚠️ 历史脏数据未处理**：`claim_achievement` 的 403 晚于写 `user_achievements` → **成就行已落库但积分没发**，重试命中「已领取」永久卡死
- **文件**：`backend/routers/career.py:409/448/500/539`

### 130. 微信绑定「假成功」：anon key + 不看状态码（2026-09-27）
- **问题**：绑定微信后提示成功，下次登录又让绑
- **根因**：`auth.py:1034` PATCH `profiles` **用 anon key**（service key 存在却没用），且 **`patch_res` 赋值后从不检查状态码**。而 UPDATE 被 RLS 拦是**「静默 0 行、返回 204」** → 客户端照样拿到 200 + JWT。`:1058` 回显的还是**请求里的** openid 而非库里的值，**更坐实假象**
- **修复**：换 service headers + 状态码判断 + **回读校验**；返回值改为回显库里的值
- **⚠️ 引入部署硬依赖**：生产 `.env` 必须有 `SUPABASE_SERVICE_ROLE_KEY`，否则会拼出 `Bearer None`，**比改之前更糟** —— 已加显式闸门（key 为空直接 500）

### 131. 社区收藏「假成功」：错误对象被当真值（2026-09-27）
- **问题**：收藏失败但提示成功
- **根因**：`posts.py:334` 的 `if check_res.json():` **没判状态码** —— 表不存在时返回 404 + `{"code":"42P01"}`，**这是个真值 dict** → 被当成「已有收藏记录」→ 返回 `{"success": false, "message": "已收藏"}` + **HTTP 200**；`:338` INSERT 返回值**直接丢弃**；`:354` **无条件**返回成功
- **修复**：补状态码判断（非 200/201/204 抛 502）+ `logger.error` 留痕。`collect_count` 的 PATCH 失败**只留痕不让整个操作失败**
- **✅ 2026-09-29 更新**：用户执行 SQL 后确认 **`post_collects` 表存在** → 排除「缺表」，真因回到 anon key 的权限/RLS

### 132. 本地开发全线 503：按 SNI 定向阻断（2026-09-27 夜）
- **问题**：前端所有请求 503，登录报 `httpx.ConnectError`
- **排查**：本机 8000 在监听、接口不带 token 返回 401（**说明接口没坏**）；而 `*.supabase.co` 的 TLS 握手被 **reset**。**同 IP 只把 SNI 换成 `supabase.com` → 握手成功** → 是按 SNI 定向阻断
- **为什么浏览器却打得开**：Chrome 走 HTTP/3，**QUIC 把 SNI 也加密了**；curl/Python 走 TCP TLS，SNI 明文一眼认出来
- **处理**：换回平时网络即消失，代码一行没动。另留 `_devtools/supabase-h3-bridge/`（**永不部署**）

### 133. 一次样式事故：死规则不能批量改活（2026-09-27 夜）
- **问题**：意见反馈弹窗是透明毛玻璃，看不清
- **第一轮错**：扫出 25 处低透明度浮层批量提到 94% —— 用户说「你一点都没改动」。运行时诊断显示弹窗背景一直是 `rgba(0,0,0,0)`：`.feedback-dialog-wrapper .el-dialog` 是**死规则**（class 落在 `.el-dialog` **元素自身**上，而选择器要求「后代」）。**我改了值，但从没验证过规则是活的。同一模式全项目 17 处**
- **第二轮更错**：把那 17 条改活 → 用户「这里简直是灾难区」。**死规则不是「坏了」，是「没生效所以没影响」**；激活它 = 把没人验证过的自定义配色强行套上去 = 引入回归
- **处理**：全部回退，只留一处 —— `--el-dialog-bg-color: transparent` → `var(--el-bg-color)`。**真正的根因是那个变量**
- **文件**：`frontend/src/styles/*.css`

### 134. 账号体系重构：去掉「微信绑定」（2026-09-28）
- **问题**：用户「个人开发，不是企业，不能直接绑微信」。查下来**对一半** —— 小程序 `wx.login` 个人主体**能做**；受限的只有网页/APP 的微信登录（要企业 + 300 元/年）。而网页端当时用**公众号测试号**兜着，那是开发调试工具不该上生产
- **修复**：小程序两条路径（微信一键登录**首次直接建号** / 邮箱密码）；**整条删掉**「need_bind → 绑定」流程与公众号测试号扫码（**路由 22 → 18**）
- **⚠️ 有个洞，以及不用「账号合并」的补法**：微信建的号没有邮箱密码，其他端够不着 → 改成「建号后可在设置页补真实邮箱 + 密码」；占位邮箱 `wx_{openid}@miniapp.local`（RFC 6762 保留 TLD）
- **向后兼容**：老版本小程序拿到 `need_bind:false` + `access_token` 会**直接登录成功**，不会出现「更新前完全登不进去」
- **文件**：`backend/routers/auth.py`、`frontend/src/views/{Login,Settings}.vue`、`D:\jizhi-miniapp\src\pages\login\index.vue`

### 135. 异步任务队列：Redis + arq（2026-09-28）
- **问题**：用户「最好先架构好这个消息队列，不然后期麻烦一大堆」。`video_gen.py` 的进程内队列有四个洞：重启全丢 / 多 worker 不协调 / 无统一重试 / 前端轮询会提前放弃（见 128）
- **修复**：`services/task_queue.py` + `worker.py`；**Redis 连不上默认抛错，不静默降级**（要退回进程内必须显式开 `TASK_QUEUE_FALLBACK_INLINE`）
- **⚠️ 不是所有 create_task 都该迁**：用户等着的长任务进队列；藏延迟的优化（记忆压缩、grounding 预取）**留在原地**
- **⚠️ 考试批量分析没迁**：它吃内存里的列表、且记录还没入库，worker 无从按 ID 重读 —— **排队的前提是「任务能被标识符重新捞起来」**
- **文件**：`backend/services/task_queue.py`、`backend/worker.py`、`backend/config.py`

### 136. 桌面版从零到可用（Tauri v2）（2026-09-27 / 28）
- **设计**：**壳加载线上站点**，不重写 UI —— 零 CORS、网站更新客户端即最新
- **踩过的坑**：① Git Bash 的 `link` 抢 MSVC 链接器；② Tauri v2 的 ACL **默认拒绝所有插件命令且静默失效**；③ 权限对远程页面默认不生效，必须写 `remote.urls`；④ **CSS `zoom` 做不了等比缩放**（不放大布局视口，`100vh` 与媒体查询仍按真实宽算）；⑤ 小基页在 ≤1500px 会右偏 210px（`padding-left` 把内容中心推到 `视口中心 + P/2`）
- **产物**：无边框窗口 + 悬浮控制键、跳过落地页、窄窗口等比缩放、窗口状态记忆、单实例、原生另存为、外链走系统浏览器。安装包 **1.4 MB**
- **文件**：`_devtools/jizhi-desktop/`（**在 project1 仓库之外**）

### 137. 桌面端设置合并 + 自定义快捷键（2026-09-28）
- **设置合并**：首页齿轮指向 `/xiaoji/settings`，而左侧轮盘的「设置」指向 `/settings` —— **同一个东西两个页面**。改成小基设置内嵌进主设置、`/xiaoji/settings` 改重定向
- **滚动模式**：项目有两种滚动写法（`AppLayout` 的内层自滚 vs 普通页的窗口滚）。无边框壳里窗口级滚动条贴着窗口边、和应用是两截 → 设置页改成 `AppLayout` 那种。**顶栏因此天然固定，不需要 `position: sticky`**
- **快捷键**：键盘事件原来散在三处、先后取决于注册顺序 → 收进唯一分发器，优先级写成常量。**⚠️ ① 内置屏蔽必须排在 ② 输入态判断之前** —— F5/F12 是裸键，顺序反了在输入框里就漏网（已实测确认）
- **⚠️ 我编过一个不存在的功能**：按惯例加了 `action.theme`「切换深浅色」，查了才发现项目 09-03 就去掉了浅/深开关，theme store 里根本没这个方法
- **文件**：`frontend/src/shortcuts/*`、`backend/sql/user_shortcuts.sql`、`backend/routers/auth.py`

### 138. 桌宠（桌面级）（2026-09-28）
- **形态**：独立透明置顶窗口，关掉主程序也还在（用户明确选的）
- **两条技术约束**：桌宠窗口是**独立 origin**（本地页），与主窗口（远程站点）**不共享 localStorage**；后端 CORS 白名单原本只有 jizhi-learn.com 那几个源 → 主窗口把 `{token, apiBase}` 推给壳（存内存不落盘），桌宠问壳要；后端 CORS 加 `http://tauri.localhost` / `tauri://localhost`
- **拖拽/点击/长按三者共存**：都从 `mousedown` 开始，**不能立刻 `startDragging`**（一交给系统拖拽 webview 就收不到后续事件）；先起 550ms 计时器，真移动（>4px）才交控制权
- **文件**：`_devtools/jizhi-desktop/ui/pet.html`、`src-tauri/{main.rs,tauri.conf.json,permissions/}`

### 139. ⚠️ 桌面版 dev 配置从来没生效过（2026-09-29）
- **问题**：`tauri dev` 起来后主窗口显示**落地页**、右上角**没有窗口控制按钮**、Vite 上**没有任何连接**；而 09-28 的截图里是好的
- **根因**：**`tauri.dev.conf.json` 不是 Tauri 认的配置名。** Tauri v2 只认 `tauri.{linux,windows,macos,android,ios}.conf.json` 五个平台名，**没有 `.dev.` 这一档**。这个文件**从来没被读过**，主窗口一直按 base 配置加载线上站（09-18 版，零桌面端代码）
- **修法**：走 CLI 的 `--config`（`package.json` 的 dev 脚本）。**不能改名成 `tauri.windows.conf.json`** —— 那个名字在 `tauri build` 时也生效，会把生产安装包指到 localhost
- **⚠️ 排查时我自己错了两次**：① 用「在二进制里搜配置字符串」判断，补对照组才发现 base 配置独有的 `12121e`/`currentUser` **同样搜不到**（配置根本不以明文存进二进制），那个方法无效；② 以为 09-28 那条「dev 配置把窗口数组整个盖掉」是原因 —— **那是误诊**
- **验收信号**：Vite 出现 ESTABLISHED 连接 / 落地页消失 / 右上角出现窗口控制按钮
- **文件**：`_devtools/jizhi-desktop/package.json`

### 140. 修好 dev 配置，炸出两个被掩盖的 bug（2026-09-29）
- **问题**：修好 `--config` 后主窗口第一次真的加载本地前端，`isDesktop` 第一次为 true → 当场抛 `getActivePinia() was called but there was no active Pinia`
- **两个 bug**：① `main.js` 的 `const _authForPet = useAuthStore()` 在模块顶层执行，而 `app.use(pinia)` 在**第 73 行**；② `pushPetApiBase(BACKEND_URL)` —— **`BACKEND_URL` 在 main.js 里从来没被 import**（另一处消费点「更新提示的 onClick」只在你点它时才炸）
- **为什么一直没暴露**：dev 配置坏 → `isDesktop` 恒为 false → 顶层那段代码永远不执行。**两个 bug 互相掩盖，修好 A 才炸出 B**
- **文件**：`frontend/src/main.js`

### 141. 桌宠悬停轮盘（2026-09-29）
- **交互（用户定）**：鼠标移进小基 → 轮盘展开 → **滚轮转着选** → **左键确认**；每一层都这样做；右键/Esc 退回
- **先测了一条会推翻设计的假设**：Windows 的滚轮默认发给**有焦点**的窗口。实测（保持 PyCharm 有焦点）—— 悬停时 **+5 格收到 5 次**、移开后 **+0 次**，`hasFocus=false` 照样收得到 → **不需要移入时抢焦点**
- **⚠️ 第一遍是脏数据**：诊断只记总数不记坐标，读数 44→73→106 而我只滚了 5 格。加上 `clientX/clientY` 判别（落在窗口内才算）后结论才干净。**观测手段分不清来源，数据就不能用**
- **两种特殊的层**：`look`（滚动即预览，小基当场变脸）/ `dial`（转盘，滚动连续调时长，当前值固定在上方）
- **自己踩的三个坑**：① 鼠标移开不收 —— 判断用了**最后记录的鼠标坐标**，而 `mousemove` 只在窗口内触发，`mouseleave` 来时它必然在窗口内；② 「松开往左下角挪一点」 —— 展开用 `center`、收起用默认右下角，120px 的差变成位移；③ 小基贴屏幕右缘时轮盘被切掉 —— 窗口按显示器范围夹取
- **文件**：`_devtools/jizhi-desktop/ui/pet.html`、`src-tauri/src/main.rs`

### 142. 设置不联动：轮询守卫写反了（2026-09-29）
- **问题**：设置页改了开关，桌宠毫无反应
- **根因**：桌宠的配置轮询写成了 `if (!cfg.token) await loadCfg()` —— 语义变成「**只有还没拿到才去要**」，token 一到就再也不回读
- **修复**：改成**事件驱动**（`set_pet_prefs` 存下后 `emit("pet-prefs")`，桌宠监听后立刻重渲染），轮询去掉守卫只作兜底
- **⚠️ 我埋过一个更糟的坑**：给「先躲起来」做了开关 —— 而它是**收起桌宠的唯一入口**（没有托盘图标、没有别的恢复路径）。用户一关，桌宠就再也收不起来。已改成 `pinned`（不提供开关，永远在，且存坏的旧值会被纠正回来）
- **文件**：`ui/pet.html`、`frontend/src/desktop/index.js`、`frontend/src/views/Settings.vue`

### 143. SQL 合集：23 个脚本幂等合并 + uuid/text 类型错（2026-09-29）
- **背景**：用户「现在需要数据库的都给我，我一起执行了」
- **做法**：合并 23 个脚本。逐个核对幂等性 —— **19 个本来就能重复跑**；3 个（`agent_center_tables`/`subject_plan_tables`/`vocab_tables`）的 `CREATE POLICY` 没有 DROP 保护，**在合集里给每个补上匹配的 `DROP POLICY IF EXISTS`**
- **第一次执行报错**：`42883: operator does not exist: uuid = text` → `exam_paper_records.sql` 的 `user_id` 是 **TEXT**，而 `auth.uid()` 返回 **uuid**。**`uuid = '字面量'` 能跑（字面量会推断类型），只有跟另一列比才炸**，所以写的时候不容易发现
- **修法**：`auth.uid()::text = user_id`，**不是**反过来 `user_id::uuid`（后者表里只要有一行不是合法 uuid 就直接抛错）。扫了全部策略，只有这一处
- **✅ 顺带结掉 09-27 的悬案**：确认 **`post_collects` / `countdowns` 表都在** → #7/#8 不是缺表（见 131）
- **文件**：`backend/sql/exam_paper_records.sql`、`待执行SQL_20260929.sql`、`_probe_20260929/gen_sql.py`

### 144. 文档同步：三份文档 + 小吉错字（2026-09-29）
- **用户点出**：「查看是否有名称错误，类似小基写成小吉」→ **「小吉」23 处**（代码里前端 160 处「小基」/ 0 处「小吉」，后端 80/0）
- **顺带查出**：`5.1` 和 `6` **只有子节、没有父标题**（目录链接指向空气）；`9.4 微信 OAuth 接入`、`5.11.6/5.11.7` **整三节在讲已删除的扫码流程**；核心能力矩阵/架构图/技术栈表/目录树/模块职责表/故障排查表/环境变量表…… **30+ 处残留**；目录断链 6 条
- **新增**：`18. 桌面版（Tauri 壳）`（8 子节）、`5.17 自定义快捷键`、`5.18 异步任务队列`、`14.5 导出与截图的现代颜色适配`、`17.10 小程序视觉大轮`；重写 `5.11 账号体系`
- **⚠️ 我的检测器又错了一次**：目录锚点检测器第一版用 `\s+` 合并空格，而 GitHub 是**每个空格各转一个连字符** → 报了 **10 条假断链**，差点让我去"修"一堆本来正确的东西
- **文件**：`SYSTEM_MANUAL.md`（5597→5952）、`WORKFLOW_STANDARD.md`（269→315）、`PROJECT_SUMMARY.md`（09-15→09-29）

### 145. 🎯 管理后台三个页面全空：缺 GRANT（2026-09-30）
- **现象**：反馈 / Q&A / 举报三个页面永远是空的；仪表盘「待处理反馈」恒 0
- **根因**：`sql/admin_tables.sql` 建了 5 张表，**整个文件一条 GRANT 都没有**。而项目里其它 7 个 SQL 文件都有 —— `grant_exam_paper_records.sql` 甚至就是为修同一个坑建的
- **实测（service_role 探测线上）**：`user_feedback` / `user_qa` / `content_reports` / `reports` → **403 / 42501**；`admin_audit_logs` / `system_announcements` → 200 ✓
- **为什么是缺 GRANT 不是 RLS**：Supabase 的 `service_role` 自带 `BYPASSRLS`；RLS 拦截的表现是「200 + 空数组」，**42501 是表级 `insufficient_privilege`**
- **⚠️ 三层掩盖**：① 缺 GRANT → 42501 → ② 后端 `if status_code != 200: return []` 伪装成「暂无数据」→ ③ 仪表盘 `except: pass` 伪装成「业务上就是 0」
- **更严重**：`feedback.py:29-43` **不接收响应、不看状态码**，而 httpx 对 4xx **不抛异常** → except 永不触发 → 用户看到「感谢反馈」，**库里一行没有**
- **⚠️ 第一轮探测漏了 `profiles`**（只测了 SELECT）：它的 UPDATE/INSERT/DELETE **全是 403**，**卡死禁言 / 封禁 / 改角色三件事**
- **文件**：`sql/admin_rework_20260930.sql`（新增）

### 146. 反向缺口：社区表 service_role 没授权（2026-09-30）
- **镜像问题**：社区那批表当年授权给了 anon，却**从没给 service_role** —— `posts` / `comments` / `post_likes` / `post_collects` / `friendships` / `private_messages` / `messages` / `notifications` / `user_actions` / `user_stats` 全部 403
- **后果**：`GET /admin/users/{id}` 的发帖数用 service_role 查 `posts`，查询本身被 403 挡住 —— **即便把列名从 `author_id` 改成 `user_id` 也白搭**
- **背景**：后端正在往 service_role 迁移（09-27 安全整改方向），但这批老表的授权没跟上

### 147. 处置闭环：禁言 / 封禁真的生效（2026-09-30）
- **背景**：禁言**全仓库零实现**（搜 `禁言|mute|silence|restrict` 只命中 CSS 变量名）；封禁只有一个 `profiles.is_active` 布尔，**而排除 admin.py 后全后端没有任何地方读它** —— 是个纯标签
- **设计取舍**：状态落 `profiles`（认证中间件本来每次请求就要查一次判角色，零额外开销）；`user_sanctions` 只存历史，不参与热路径；加 **30 秒进程内缓存**
- **生效点**：封禁接在 `get_current_user` 的**两个**认证出口（自签 JWT 是本地验证的，只挂一处会漏）；禁言接在发帖/评论入口，按 scope + 到期时间拦，**到期自动失效、无需定时任务**
- **举报处置一步到位**：`PUT /admin/reports/{id}/resolve` 支持 `dismiss` / `mark` / `warn` / `delete_content` / `mute`(1·7·30天·永久) / `ban`，含回读校验 + 审计留痕 + 站内信
- **端到端实测**（库里现成的「测试用户」账号，用完还原）：禁言 → 发评论 **403**「你已被禁言，暂时无法评论（解禁时间 2026-10-07 12:03）」；封禁 → 发评论 **403**「账号已被封禁」
- **⚠️ 顺序缺陷**：处置历史先写、状态后写，状态失败会留下「声称已禁言、其实没生效」的孤儿记录（实测踩到）→ 改成**先落状态、再写历史**
- **文件**：`utils/sanctions.py`（新增）、`utils/auth_middleware.py`、`routers/admin.py`、`routers/community/posts.py`

### 148. 全面 API 检测：145 个端点（2026-09-30）
- **原则**：GET 全真调；写操作用空 body 或幽灵 UUID，只验校验与错误处理
- **最终**：`200×82 / 403×23 / 404×30 / 400×5 / 422×5`，**5xx 为 0**
- **⚠️ 我自己引入的回归**：把 7 处「非 200 降级成空」改成抛 502 时**漏了 `206 Partial Content`** —— 带 `count=exact` + `limit` 的查询只要总数超过一页就恒为 206 → `GET /admin/users` **502**、仪表盘**全 0**。已修 16 处检查
- **⚠️ 我误建的脏数据**：探 `POST /admin/questions` 时发空 body，**它当场建了一道 content 全 null 的题**（已删，题库回到 19338）
- **修掉**：`DELETE /admin/announcements/{不存在}` 200「已删除」、`PUT /admin/feedback/{不存在}` 200「已处理」、`PUT /admin/qa/{不存在}` 200「已处理」→ 全部 404（根因：PostgREST 的 PATCH/DELETE **不区分「改了 1 行」和「匹配 0 行」**，都是 204）；`GET /admin/settings` 的 `syllabus_count` 硬编码 0 → 17

### 149. 社区模块：anon key 权限不足（09-27 悬案结案）（2026-09-30）
- **实测**：anon **读不了** `comments` / `post_likes` / `post_collects` / `messages`（401），只有 service_role 能读
- **修掉**：`GET /community/collections` 502→200；`DELETE /post/{id}/collect` 502→200；`DELETE /community/comment/{id}` **500 `KeyError: 0`**→403（查询失败返回的是错误**对象**，代码直接 `check_res.json()[0]`）
- **⚠️ 顺带挖出一个从没被发现的**：`get_posts` 里查点赞/收藏/评论状态也用的 anon、失败被 `if status_code == 200 else []` 吞掉 → **动态流里 `is_liked` / `is_collected` 永远是 false、每条帖子评论永远是空的**
- **⚠️ 修法是切 service_role，不是给 anon 开权限**（anon key 打包在前端产物里，开权限 = 公开全站私信）。但**没有无差别替换全部 16 处** —— 只改了「查询自带 user_id 归属过滤」的端点，`private_messages` 相关留待确认 RLS
- **文件**：`routers/community/posts.py`、`routers/community/messages.py`

### 150. 管理后台界面整改（2026-09-30）
- **举报/反馈按钮从来没工作过**：模板调 `resolveReport`，而 `:155` 从 `@/api/admin` **import 了同名函数** → 命中的是 API 封装，发出 `PUT /admin/reports/[object Object]/resolve` → 422 静默失败。真正的处理函数 `resolveReportItem` 是死代码
- **超管闸门是装饰性的**：`get_current_super_admin` 在 33 个端点的文件里**只有 import、零调用** → 任何管理员都能自提权。已接回 + 加回读校验
- **侧边栏错位**：`/admin/reports` 与 `/admin/feedback` 指向**同一个组件**，而标签初值写死 `ref('reports')` —— 加上 Vue Router 复用实例不重挂载，**错位是永久性的**。改成标签由路由决定 + 侧边栏拆三项
- **⚠️ 顺带拦下自己引入的坑**：`isActive` 用 `startsWith`，而 `/admin/questions` 也以 `/admin/qa` 开头 → 进题库会让「Q&A 帮助」一起高亮
- **补齐**：管理员身份 / 退出登录 / **系统信息页**（后端 `GET /admin/settings` 此前连封装都没有、全站零调用）
- **编辑题目会毁数据**：表单把 `content` 重建成 `{stem, options?}`，后端整体替换 → 编程题的 `test_cases` 直接没。改成在原始 content 上合并
- **action 枚举化**：`admin_video` 的 5 个 action 原是自由文本（`f"视频审核 {action}: {id}"`），**根本没法筛选**；`AdminLogs` 的「编辑题目」写的是 `edit_question` 而后端写 `update_question` → 该筛选永远 0 条

### 151. 滚动 / 留白 / 主题：后台跟随管理员外观（2026-09-30）
- **窗口滚动**：`.admin-layout` 用 `min-height:100vh` → 容器随内容长高 → 内层 `overflow-y:auto` 永不生效 → 滚动条贴着窗口边；`Community.vue` 同病（包装壳 + AppLayout 内层 = 文档高两屏）
- **为窗口 6 键让出留白**：新增 `--jz-top`（桌面壳 `html.jz-desktop` 下 48px，网页版 0px），`.app-container` 加对应 padding，同时把**全站 55 处**「满屏高度」改成 `calc(100vh - var(--jz-top, 0px))`。**⚠️ 必须除以 `--jz-scale` 反向补偿**，否则窗口一缩小留白跟着缩、按钮不变、又压回内容
- **后台主题适配**：**142 处 / 10 个文件** —— `#0a0e17`→`var(--bg-color)`、`#e0e0e0`→`var(--text-primary)`、`rgba(255,255,255,α)` 按文字/边框分流、`#409EFF`→`var(--brand)`、`#111827`→`var(--card-bg)`。**保留语义色**（危险/成功/警告不跟品牌色走）
- **⚠️ grep 会连注释一起命中**：我用 `min-height:100vh` 扫出「32 处要改」，其中一部分是**我自己写在注释里的解释文字**（`Settings.vue` 就是这么被误报的，它 09-28 已修好）。**真正有问题的只有 `Community.vue` 一处**

## 桌面版架构（Tauri 壳，2026-09-29 更新）

> 产物在 `_devtools/jizhi-desktop/` —— **刻意放在 `project1` 仓库之外**，不会被提交或部署。
> 完整规格见 [SYSTEM_MANUAL.md](./SYSTEM_MANUAL.md) 第 18 节。

### 定位

**不是重写 UI，是壳。** 主窗口直接加载线上站点 `https://www.jizhi-learn.com`：

- 零 CORS 问题（来源即站点自身）
- 网站一更新客户端就是最新的，**不需要做前端更新机制**
- 代价：**桌面版依赖网页端已部署** —— 这是打包流程的硬约束

### 目录

| 路径 | 说明 |
|---|---|
| `package.json` | `dev` 脚本带 `--config`（**关键**，见下） |
| `ui/index.html` | 壳的占位页 |
| `ui/pet.html` | **桌宠本体**（本地页，独立 origin） |
| `ui/pet/*.webp` | 小基形象 5 态（用 WebP 不用 PNG：136KB vs 1MB，安装包才 1.4MB） |
| `src-tauri/tauri.conf.json` | 主配置：双窗口 + 打包（NSIS / currentUser） |
| `src-tauri/permissions/app-commands.toml` | **自定义命令的 ACL 白名单**（不写就调不了） |
| `src-tauri/capabilities/default.json` | `remote.urls` 声明 + 权限清单 |
| `src-tauri/src/main.rs` | 全部 Rust 命令 |

### 双窗口

| | `main` | `pet` |
|---|---|---|
| 内容 | 远程站点 | 壳内本地 `ui/pet.html` |
| 尺寸 | 1600×1000（**设计宽度**） | 220×220 基准，可被设置页缩放（0.6–1.6） |
| 装饰 | 无边框（窗口按钮由**网页端**画） | 无边框 / 透明 / `alwaysOnTop` / `skipTaskbar` / `focus:false` |

**设计宽度 1600 不是随手定的**：项目里有一条 `@media (max-width:1500px) { .call-main { padding-left:420px } }`，
`padding-left: P` 会把内容中心推到 `视口中心 + P/2`（实测 1440 宽时右偏 210px）。
桌面版用 Tauri 的**浏览器缩放**把视口钉在 1600，那条媒体查询永不触发，小基才是真居中。
⚠️ **不能用 CSS `zoom` 代替** —— 它不放大布局视口，`100vh` 仍按真实视口算，且媒体查询照样按真实宽触发。

### 配置桥：为什么需要

**桌宠窗口与主窗口是两个不同的 origin**，同源策略下桌宠**读不到主窗口的 localStorage**。
所以由主窗口把三样推给壳（只存内存、不落盘），桌宠再问壳要：

| 通道 | 内容 | 为什么不能写死 |
|---|---|---|
| `set_pet_token` | 登录 JWT | 退出登录时推空串 |
| `set_pet_api_base` | 后端地址 | 开发 `localhost:8000` / 生产 `api.jizhi-learn.com` |
| `set_pet_prefs` | 轮盘项开关、尺寸 | 改动即 `emit("pet-prefs")` 广播，**事件驱动不是轮询** |

### Rust 命令清单

`save_file`（原生另存为）/ `open_external`（外链走系统浏览器，只放行 http/https）/
`app_version`（壳的版本号，网页端无从得知）/ `show_main_window`（**当前无调用方**）/
`set_pet_visible` / `is_pet_visible` / `set_pet_token` / `set_pet_api_base` / `set_pet_prefs` /
`get_pet_config`（一次性取回，少一轮 IPC）/ `set_pet_size`（带 `anchor`：`center` 或右下角）+ 屏幕范围夹取

### ⚠️ 三个必须记住的坑

**1. `tauri.dev.conf.json` 是死文件。** Tauri v2 只认 `tauri.{linux,windows,macos,android,ios}.conf.json`
五个平台名，**没有 `.dev.` 这一档**。写了不会被读，**且完全静默**。
必须走 CLI 的 `--config`；**不能改名成 `tauri.windows.conf.json`** —— 那个在 `tauri build` 时也生效，
会把生产安装包指到 localhost。

**2. ACL 报错说反话。** 自定义 `#[tauri::command]` 不会自动获得许可，未声明时报
`<命令名> not allowed. plugin not found` —— **"plugin not found" 极具误导性**，
它让人以为插件没装，实际是「这个命令不在许可名单里」。另需 `remote.urls` 声明远程源，否则等于没配。

**3. 打包顺序是硬约束：先部署前端 → 再打安装包。**
顺序反了，用户拿到的是**旧前端 + 新壳**：一个**没有窗口控制按钮的无边框窗口 —— 拖不动也关不掉**。

### 桌宠

桌面级：独立透明置顶窗口，关掉主程序也还在。

**交互（2026-09-29 定稿）**：鼠标移入 → 轮盘展开 → 滚轮转着选 → 左键确认；
每一层都这样做；右键 / Esc 退回；鼠标移开收起。

- 第一层四项（可在设置页逐项开关）：`🎙 语音` · `🎨 换个样子` · `⏱ 专注计时` · `👋 先躲起来`
- `kind: 'look'` —— **滚动即预览**，滚到哪小基当场变脸，确认才固定
- `kind: 'dial'` —— **转盘**，滚动连续调时长，当前值固定在正上方
- **「先躲起来」不给开关**（`pinned`）—— 它是收起桌宠的唯一入口

**两条实测结论**：
- 无焦点窗口**照样收得到滚轮**（悬停时 +5 格收到 5 次，移开后 +0 次）→ 不需要移入时 `setFocus()` 抢焦点
- 展开与收起**必须用同一个锚点**（都是 `center`），否则小基会整个平移一下

**已删除**：右键菜单、550ms 长按 —— 它们和拖动抢同一个计时器，是「手抖就误触」的根源。

### 桌宠设置（设置中心第 4 个模块）

显示开关 / **操作对照表**（唯一说明书）/ **轮盘项开关** / **大小滑杆**（0.6–1.6，一个 `--s` CSS 变量贯穿全尺寸）/ **开机自启**（`tauri-plugin-autostart`，状态**问壳要** —— 注册表 Run 项才是真相）。

## 小程序架构（2026-09-18 更新）

基于 uni-app 3.0 + Vue 3 的微信小程序版本，复用主站 FastAPI 后端。
源码在 `D:\jizhi-miniapp`（**不在本仓库内，不受版本控制**）。

### 导航形态：与 Web 一致 —— 小基主界面 + 全部功能 + 全局搜索

**底部 Tab 栏已撤**（2026-09-18，用户定调）。Web 端的导航是常驻轮盘 + 小基主界面，
小程序用「小基首页承载 18 项功能宫格 + 全局搜索页」承载同一套 IA。

| 层 | 小程序 | 对应 Web |
|---|---|---|
| 主界面 | `pages/index/index`（小基，登录直达） | `/home` → `XiaojiCall.vue` |
| 全部功能 | 小基顶栏 ⊞ 面板，18 项与轮盘一一对应 | `EdgeNavDock` 弧形轮盘 18 项 |
| 全局搜索 | `pages/search/index`（页面/考纲/真题/智能体/词条） | `GlobalSearch.vue`（Ctrl+K） |

**跳转语义**（`utils/constants.js`）：
- `goTop(url)` —— 一级模块平级切换用 `redirectTo`（栈深恒为 2，**原生返回箭头正常**）；回首页才用 `reLaunch`
- `goBackHome()` —— 自定义导航栏页面的返回，能退就退、退不了回首页
- 一级模块页面顶栏左上角都有返回（`学科计划`/`我的` 是 `navigationStyle: custom`，自绘 `‹`）

### 小基主界面（照 `XiaojiCall.vue` 逐条对齐）

**默认气泡模式**（Web 端默认也是 `bubble`，聊天列表 `v-if="chatMode === 'list'"` 默认不渲染）：

```
      [小基最新回复的气泡]  ← 常驻，最高 34vh 可滚，下带小三角
              ▼
   ✨  240rpx 小基形象  ✨     ← 双层光环：脉冲 3s / 旋转 20s
          [状态: 在线]
      [我说的最后一句]
      [背个单词] [求安慰]      ← Web 端那两个陪伴类快捷问（force_chat 跳过分流）
```

- 形象按状态机切图（idle/thinking/speaking/happy/sleeping）
- 点形象随机冒一句短语（Web 端 `onAvatarClick` 同款）
- 推荐 / 关心 / 使用日志收进「小基面板」（Web 端在右栏，窄屏 `display:none`）
- **无「新对话 / 历史对话」** —— 与 Web 一致，只有一条连续线程，历史存服务端

### 关键文件（`D:\jizhi-miniapp`）

| 文件 | 说明 |
|---|---|
| `src/pages/index/index.vue` | **小基主界面** — 气泡/列表双模 + 意图分流 + 识图 + TTS |
| `src/pages/search/index.vue` | 全局搜索 — 页面/考纲/真题/智能体/词条 |
| `src/pages/study/exam.vue` | 真题套卷 — 部分导航 + 答题卡 + 全题型作答 + 交卷出分 + 解析模式 |
| `src/pages/study/*` | 考纲列表/详情/做题/每日任务/错题/知识点/掌握度看板/题集详情/学习规划三页 |
| `src/pages/community/*` | 动态广场/好友/排行/收藏/我的发布/用户主页/私聊（4s 轮询） |
| `src/pages/profile/*` | 个人中心/设置/个人画像 2D 九维/评估中心三页/消息中心/Q&A |
| `src/pages/career/*` | 学程总览/段位/勤耕(任务)/拾贝(成就) |
| `src/pages/wordbook`、`agent-center`、`api-center`、`guide`、`open-source`、`tools` | 词条本/智能体中心/API 模型中心/使用指引/开源文档/工具箱 |
| `src/utils/constants.js` | `BASE_URL` 环境切换 + `FEATURES`（18 项主导航唯一数据源）+ `goTop`/`goBackHome` |
| `src/utils/request.js` | uni.request 封装 + JWT + 可覆盖 timeout/retries |
| `src/api/*.js` | 11 个模块，全部对齐后端真实路由 |

### 与 Web 版差异

| 特性 | Web | 小程序 |
|---|---|---|
| 主界面 | 小基（three.js 无关，DOM 气泡） | ✅ 小基气泡模式 |
| 轮盘导航 | 弧形轮盘 18 项（canvas） | 宫格 18 项 + 全局搜索页 |
| AI 对话 | `fetch` + `ReadableStream` | `wx.request` + `enableChunked`（手写 UTF-8 分片解码） |
| 意图分流 | ✅ chat-stream 返回 JSON 路由指令出卡片 | ✅ 同 |
| 图像识别 | `FileReader` dataURL | ✅ `wx.chooseMedia` + 压缩 + base64 |
| 语音播报 | `Audio` + dataURL | ✅ 临时文件 + `InnerAudioContext` |
| 语音通话 / ASR | WebAudio 原始 PCM + WebSocket | ❌ 不上（小程序录音无 AEC，外放必自激） |
| **视频库** | canvas 实时绘制（mp3 + JSON 分镜脚本） | ❌ 不上（无 mp4 源，`<video>` 放不了；要上需后端加 mp4 合成产线） |
| 个人画像 | three.js 3D 维度宇宙 | 2D 九维 Tab（信息量不减，去掉 3D 外壳） |
| 编程题沙箱 | 9 语言 | 跳过（`SKIP_QUESTION_TYPES`） |
| 算法考纲 | algorithm-ds / acm-icpc | 跳过（`SKIP_SYLLABUS_IDS`） |
| 主题定制 | 四轴 + 外观码 | ❌ 不做；但 **09-23 已全量 token 化**（双主题 + 九色分类色板 + 根背景三档氛围光） |
| 管理后台 | 8 页面 | 不需要 |
| 账号 | 邮箱密码 / 验证码 | 微信一键登录（**首次自动建号**）+ 可补邮箱密码打通其他端 |

### 小程序复用的后端新端点

`/community/xiaoji/*`（chat-stream / vision / config / messages / evaluate-question）、
`/xiaoji/daily/{id}`、`/vocab/*`、`/agent-center/*`、`/evaluation/overview`、`/subject-plan/exam-papers/*`、
`/learning-plan/*`、`/questions/*`、`/community/*`（动态/好友/私聊/通知）、`/tools/*`。
