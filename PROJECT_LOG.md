# 基智学习助手 (Jizhi Learn) — 项目总日志

> 架构演进 / 关键决策 / 文件索引 · 最后更新：2026-08-12
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

**目标**：全部 17 考纲 ≥ 18,900 题（target_count 合计），已全部达标 ✅

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
| acm-icpc | ACM-ICPC 竞赛 | 529 | 500 | ✅ 106% |
| mandarin | 普通话水平测试 | 619 | 600 | ✅ 103% |
| teacher-cert | 教师资格证 | 817 | 800 | ✅ 102% |
| public-service | 公务员 行测 | 1925 | 2000 | 🟡 96% |
| judicial | 法律职业资格 | 1528 | 1500 | ✅ 102% |
| cpa | 注册会计师 CPA | 1152 | 1200 | 🟡 96% |
| algorithm-ds | 算法与数据结构 | 1140 | 2000 | 🔴 57% |
| **总计** | — | **18,320** | **18,900** | **97%** |

---

## 前端页面

| 路由 | 文件 | 说明 | 状态 |
|---|---|---|---|
| `/subject-plan` | `SyllabusHub.vue` | 考纲列表：搜索+筛选+收藏（N+1 已优化） | ✅ |
| `/subject-plan/:syllabusId` | `SyllabusDetail.vue` | 考纲详情：概览首页 + 题库（含题目状态）+ 每日/知识/错题 + 🆕 生成计划双通道弹窗 + 🆕 每日学习讲解 | ✅ |
| `/subject-plan/:syllabusId/practice` | `SubjectPractice.vue` | 做题页：11 种题型 + 编程题左右分栏 OJ（洛谷风）+ 做题倒计时 + 科幻毛玻璃 | ✅ |
| `/subject-plan/:syllabusId/exam/:paperId` | `ExamPaper.vue` | 🆕 真题套卷：做题模式（计时+交卷出分）/ 解析模式（历史答案+正确率+AI 错因分析）+ 生成计划 | ✅ |
| `/settings` | `Settings.vue` | 🆕 统一设置中心：7 模块（个人/偏好/外观/隐私/通知/安全/AI） | ✅ |
| `/profile-card` | `ProfileCard.vue` | 个人画像：维度宇宙学习星图（侧边栏独立入口） | ✅ |
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
| POST | `/subject-plan/code/submit` | 提交判题→逐测试点评分（AC/WA/TLE/RE）· 免登录 | ✅ |

沙箱策略：Python → subprocess; C/C++/Java → 本地编译器（winget MinGW / 内置路径 / PATH）→ 无外部 API 依赖。

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
| `backend/routers/auth.py` | 认证路由 — 邮箱登录/注册 + 微信扫码登录/绑定 + 小程序登录 |
| `backend/utils/auth_middleware.py` | 认证中间件 — 自签 JWT + Supabase 双重验证 |
| `backend/local_question_bank.py` | 本地题库 — 多考纲内存加载，11 种题型 |
| `backend/utils/code_runner.py` | 代码执行沙箱 — Python subprocess + 本地 GCC/G++/Java（零外部依赖） |
| `backend/data/syllabi.json` | 考纲配置 — 17 考纲，含 intro/target/exam_papers/languages/grey dims |
| `backend/data/*.json` | 题库文件 — 17 个 JSON，共 16,889 题（目标 18,900 · 89%） |
| `backend/scripts/seed_all_banks.py` | 批量生成脚本 v2 — 读 target_count 自动算差值 |
| `backend/scripts/check_progress.py` | 题库进度查看脚本 |
| `backend/agents/llm_client.py` | LLM 调用 — DeepSeek API（60s 超时） |
| `backend/sql/subject_plan_tables.sql` | Supabase 建表 DDL（6 张核心表） |
| `backend/sql/admin_tables.sql` | 管理员系统建表 DDL（5 张表 + profiles 扩展） |
| `backend/sql/add_wechat_columns.sql` | 🆕 profiles 加 wechat_openid/unionid 列 |
| `backend/routers/exam_papers.py` | 🆕 真题套卷路由 — 列表/双模式详情/交卷/答卷生成计划 |
| `backend/data/exam_papers/*.json` | 🆕 12 套真题卷数据 |
| `backend/sql/exam_paper_records.sql` | 🆕 答卷记录表 DDL |
| `backend/sql/migrate_plan_columns.sql` | 🆕 subject_plans/plan_daily_tasks 补列迁移 |
| `backend/sql/migrate_daily_learning.sql` | 🆕 phase/learning_content/difficulty_level 迁移 |
| `backend/routers/admin.py` | 管理员全部 API — 22 个端点 |
| `backend/utils/admin_middleware.py` | 管理员鉴权中间件（三级角色） |

### 前端
| 文件 | 说明 |
|---|---|
| `frontend/src/views/SubjectPractice.vue` | 做题页 — 编程题左右分栏 OJ（洛谷风）+ Tab缩进/Enter自动缩进 + 语言记忆/考纲限制 |
| `frontend/src/views/ExamPaper.vue` | 🆕 真题套卷页 — 做题/解析双模式 + 交卷出分 + 生成计划按钮 |
| `frontend/src/views/Login.vue` | 登录页 — 三栏 Tab（用户/管理员/注册）+ 微信扫码登录（二维码 + 轮询） |
| `frontend/src/views/Profile.vue` | 个人中心 — 头像/昵称/简介 + 🆕 微信绑定卡片 |
| `frontend/src/views/SyllabusHub.vue` | 考纲列表 — 搜索/筛选/收藏 |
| `frontend/src/views/SyllabusDetail.vue` | 考纲详情 — Tab 总控台 + 动态分数 + 删除计划 |
| `frontend/src/views/ProfileCard.vue` | 个人画像 — 维度宇宙学习星图 |
| `frontend/src/utils/questionLabels.js` | 共享题型标签 + 分类映射 + 判断工具 |
| `frontend/src/api/auth.js` | 认证 API — 邮箱登录/注册 + 🆕 微信扫码/绑定/轮询 |
| `frontend/src/api/subjectPlan.js` | API 调用封装（含 code/submit） |
| `frontend/src/stores/auth.js` | 认证状态 — Pinia store + 🆕 微信登录/绑定方法 |
| `frontend/src/components/Sidebar.vue` | 侧边栏 — App 图标网格 + 工具面板 + 对话面板 |
| `frontend/src/components/QAPage.vue` | 帮助中心 — 7 分类 29 FAQ + 跳转按钮 |
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

---

## 小程序架构（2026-08-06 更新）

基于 uni-app 3.0 + Vue 3 的微信小程序版本，复用主站 FastAPI 后端。

### 5 Tab 架构

| Tab | 路由 | 功能 |
|---|---|---|
| 对话 | `pages/index/index` | **SSE 流式 AI 对话** + 小基模式（形象/状态切换）+ 本地会话管理 |
| 学习 | `pages/study/` | 考纲列表/详情/做题/每日任务/错题/知识点/诊断 |
| 资源库 | `pages/profile/resource-lib` | 掌握度看板/AI 生成题目/题集管理/错题本/生成历史/评估中心入口 |
| 学程 | `pages/career/` | 段位卡片 + 统计 + 成就 + 排行 + 任务 |
| 我的 | `pages/profile/` | 个人中心 + 设置 + 画像 + 评估 + 打卡/倒计时/计时器 |

### 与 Web 版差异

| 特性 | Web | 小程序 |
|---|---|---|
| AI 对话 | SSE 流式逐字输出 | ✅ SSE 流式（`wx.request` + `enableChunked`）|
| 小基 AI | 独立页面 + 语音设置 | ✅ 聊天页内模式切换（5 状态形象）|
| 编程题 | 代码沙箱 9 语言 | 跳过（SKIP_QUESTION_TYPES） |
| 算法考纲 | algorithm-ds, acm-icpc | 跳过（SKIP_SYLLABUS_IDS） |
| 设置页 | `/settings` 7 模块毛玻璃 | `pages/profile/settings` 5 模块原生风格 |
| 主题 | 浅/深/跟随系统 | 固定深色 |
| 毛玻璃 | backdrop-filter | 降级为半透明背景 |
| OCR 拍照 | 无 | 微信原生 OCR + 后端降级 |
| 管理后台 | 7 页面 | 不需要 |
| 资源库 | 侧边栏入口 | 独立 Tab |
| 账号 | 邮箱/微信扫码 | 微信登录 + 网页账号绑定 |
| 通知设置 | ✅ 8 开关 + 时间 | ✅ 8 开关 + 时间（复用后端）|

### 关键文件（D:\jizhi-miniapp）

| 文件 | 说明 |
|---|---|
| `src/pages/index/index.vue` | AI 对话页 — SSE 流式 + 小基模式 + 历史管理（410 行） |
| `src/pages/login/index.vue` | 微信登录 + 网页账号绑定表单 |
| `src/pages/study/detail.vue` | 考纲详情 5 Tab + 诊断入口 |
| `src/pages/study/practice.vue` | 做题页 11 种题型 + 诊断模式 |
| `src/pages/profile/index.vue` | 个人中心 — 打卡/倒计时/计时器 + 设置入口 |
| `src/pages/profile/settings.vue` | 🆕 统一设置页 — 5 模块（398 行）|
| `src/pages/career/index.vue` | 学程 — 段位/统计/成就 |
| `src/components/CustomTabBar.vue` | 自定义 TabBar — PNG 图标 |
| `src/stores/auth.js` | 认证 — 微信登录 + bindAccount |
| `src/stores/session.js` | 会话管理 — 本地 storage（含 updateTitle）|
| `src/api/subjectPlan.js` | 考纲/题库/诊断/计划 API |
| `src/api/career.js` | 学程 API |
| `src/utils/request.js` | uni.request 封装 + JWT 传参 |
| `src/utils/constants.js` | BASE_URL 生产域名 + 常量 |
| `src/static/icons/*.png` | 18 个图标（+settings）|
| `src/static/xiaoji_*.png` | 🆕 5 张小基形象 |
| `src/static/logo.png` | 应用 logo |

### 后端新增端点

| 端点 | 说明 |
|---|---|
| `POST /auth/wx-bind` | 小程序绑定网页账号（openid + 邮箱/密码 → JWT） |
| `wx-login` 改进 | 不再自动创建用户，未绑定返回 `need_bind` |
| `/syllabi/{id}/questions` 去鉴权 | 本地 JSON 读取无需登录 |
| `GET/PUT /community/notification-settings` | 🆕 小程序复用通知设置（之前有 API 无前端）|
