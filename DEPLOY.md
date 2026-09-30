# 部署说明（2026-09-30 更新）

本文件夹为**公网部署版**：代码已与本地开发版（project1）同步，
全部配置指向公网。**只从这里上传，不要从 project1 上传** ——
`backend/.env`、`backend/config.py`、`frontend/.env` 三个文件是公网特供，
project1 那三份是本地开发用的（localhost、本地密钥、生产缺失的 JWT_SECRET 不一致），
覆盖上去会直接打挂线上。

> ⚠️ **旧版本文档的两个坑已作废，不要再照做**：
> ① 「微信测试号扫码登录」整条链路（含 `/wechat/*` 四个端点）**09-28 已删除**；
> ② 「必须覆盖 `backend/.env`」这句在换过服务器配置后**不成立**——
> 服务器上的 `.env` 若后来手工加过东西，覆盖会丢。**先 diff 再决定**。

---

## 一、本次（09-30）与历次未部署的改动

从 09-22 起累计六轮改动全压在本地，这是一次性补齐：

| 轮次 | 内容 |
|---|---|
| 09-22 / 09-23 | 小程序协议与视觉、后端 HTTPException 套娃修复 |
| 09-27 | 线上 8 个问题修复（导出颜色、知识点命名空间、`Depends` 直调、静默吞写入）+ 桌面版从零到可用 + 下载链路 |
| 09-28 | 账号体系重构（去微信绑定 → 微信建号 + 补邮箱密码）、删公众号测试号扫码、异步任务队列、自定义快捷键、桌宠 |
| 09-29 | 桌面端 dev 配置根因修复、桌宠轮盘、SQL 合集、文档同步 |
| 09-30 | **管理后台全面整改**、禁言/封禁处置闭环、145 个端点检测、滚动/留白/后台主题适配 |

---

## 二、后端上传（服务器 8.134.157.214）

上传 `backend/` 覆盖 `/www/wwwroot/backend/`。

**必须带上 `backend/data/`**（25MB 题库 JSON，含 `exam_papers/` 12 套真题卷）——
没有它考纲/真题全是空的。

**不要上传**（开发专用，已在同步时排除）：`tests/`、`shoot.py`、`shot_ids.json`、
`utils/jdk/`（303MB 的 JDK，误落在本地目录里）、`scripts/test_speech.wav`。

### ⚠️ 三件事，缺一件就出事

**1. `pip install -r requirements.txt` —— 新增了 `arq`**

```bash
cd /www/wwwroot/backend
pip install -r requirements.txt
export PYTHONIOENCODING=utf-8
# 重启 uvicorn（用你原来的启动方式/端口）
uvicorn main:app --host 0.0.0.0 --port 8000
```

**不装会怎样**：`routers/questions.py` 顶层 `from services import task_queue, video_gen`，
而 `task_queue.py` 顶层 `from arq import ...` → **ImportError → 整个后端起不来**。
不是某个接口坏，是全部。（这个项目在「服务器缺可选依赖」上已经栽过。）

**2. `backend/config.py` 必须一起上传**

这次给它**定点补了两行**（没有整体覆盖，公网值原样保留）：

```python
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
TASK_QUEUE_FALLBACK_INLINE = os.getenv("TASK_QUEUE_FALLBACK_INLINE", "false").lower() == "true"
```

`REDIS_URL` 有默认值，`.env` 不配也能跑。

**3. `.env` 要确认有 `SUPABASE_SERVICE_ROLE_KEY`**

微信建号（09-28 起新用户注册的唯一路径）靠它。已核验本仓库的 `.env` 里
它的 payload 是 `role=service_role`（不是 anon 冒充）。**没配的话新用户完全登不进去**（老用户不受影响）。

启动后验证：

```
https://api.jizhi-learn.com/health            → {"status":"ok"}
https://api.jizhi-learn.com/subject-plan/syllabi → 17 个考纲
https://api.jizhi-learn.com/openapi.json      → 路由数应明显多于旧版（含 /admin/settings、/download/latest）
```

---

## 三、Redis 与 worker（视频生成用，可选但建议）

**不装不会崩**：视频排产那条路径有 try/except，只会打 ERROR 日志，**出题不受影响**。
但不装 = 视频永远不会生成。

```bash
# 装 Redis 并常驻
redis-server --daemonize yes
# 另起一个常驻进程（建议交给 systemd / supervisor，别挂在 uvicorn 的终端里）
cd /www/wwwroot/backend && python worker.py
```

- 队列连不上时**默认抛错，不静默降级**（这是有意的）。真要退回进程内执行，
  必须显式设 `TASK_QUEUE_FALLBACK_INLINE=true`，日志里会有 ERROR。
- 验证：出题后看日志有没有 `📥 任务入队 video.generate`。

---

## 四、数据库（Supabase SQL Editor）

本次需要执行 **3 个**文件（都在 `backend/sql/`）：

| 文件 | 作用 | 备注 |
|---|---|---|
| `admin_rework_20260930.sql` | **补 GRANT**（6 张表 + `profiles`）、`content_reports` 补 3 列 + 索引、`reports` → `content_reports` 迁移、新建 `user_sanctions`、`profiles` 加 `muted_until`/`mute_scope` | **幂等，末尾自带检** |
| `user_shortcuts.sql` | 快捷键跟随账号的表 | 幂等 |
| `exam_paper_records.sql` | 修正 `uuid = text` 类型错（`auth.uid()::text = user_id`） | 幂等 |

### ⚠️ 这个文件是整轮整改的根 | 别跳过

`admin_tables.sql` 建了 5 张表却**一条 GRANT 都没有** → 服务端拿到 **42501**，
再被「非 200 降级成空列表」和「`except: pass`」两层掩盖 →
后台三个页面永远是空的、仪表盘恒 0、**用户反馈从来没存进过库**。

**GRANT 只给 `service_role`，不要给 `anon`**：这几张表的 RLS 是
`USING (true) WITH CHECK (true)`（全放行），GRANT 是唯一防线，
而 anon key 打包在前端产物里（谁都能扒出来）。授给 anon =
把用户反馈的邮箱正文和全部管理员审计日志对全网公开。

执行后自检（文件末尾自带，也可手工跑）：

```sql
SELECT table_name, grantee, privilege_type
FROM information_schema.role_table_grants
WHERE table_name IN ('user_feedback','user_qa','content_reports','user_sanctions','profiles')
ORDER BY 1,2,3;
```

---

## 五、前端部署

`frontend/dist/` **已在部署仓库内用生产配置重新构建**（09-30 14:55）。

- 产物地址核验：`api.jizhi-learn.com` **22 处** / `localhost:8000` **0 处**
- 该数字**必须在部署仓库里构建出来**，不能在 project1 构建完拷过来 ——
  Vite 在构建时把 `VITE_BACKEND_URL` 固化进产物。

两种方式任选：

- **Vercel**：在 `frontend/` 目录 `vercel --prod`（`vercel.json` 已配 SPA rewrite），或推 GitHub 自动部署
- **服务器**：把 `frontend/dist/` 上传到网站目录

---

## 六、⚠️ 桌面端与安装包 —— 有顺序依赖

**前端没部署完，不要发安装包。** Tauri 壳加载的是线上站点，
现在线上是旧前端 —— 装完看到的是所有修复之前的样子，
而且**窗口控制按钮是前端画的**，旧前端上它拖不动也关不掉。

正确顺序：

```
① 部署后端 + 前端（本文档第二、五节）
② 在 _devtools/jizhi-desktop 重新 tauri build（对着新前端验一遍）
③ 新 exe 放进 backend/static/downloads/
④ 落地页的 /download/latest 自动认最新的那个文件，链接一个字不用改
```

### ⚠️ 下载入口这次会一起上线，但安装包还没有

新 dist 里**已经包含**落地页的下载按钮（`download/JIZHI-setup.exe` + `download/latest`），
而后端读的是 `backend/static/downloads/`，**这个目录目前在本仓库里不存在**。

也就是说：**部署完前端，用户点「下载」会 404**，直到第 ③ 步把 exe 放上去。
不能接受的话，先别部署前端，或先把 `static/downloads/` 建好放一个 exe 进去。

---

## 七、部署后检查清单

- [ ] `/health` 正常、`/openapi.json` 是新版（有 `/admin/settings`、`/download/latest`）
- [ ] **用全新微信号登录小程序** —— 验证 `wx_{openid}@miniapp.local` 占位邮箱能否被 Supabase 接受
      （**这是账号体系重构后的第一个验收点**，报「创建账号失败」就是它）
- [ ] 管理员登录后台：仪表盘数字不再是 0、**反馈 / Q&A / 举报三个页面有数据**
- [ ] **点一次「举报 → 通过/驳回」** —— 这个按钮以前从来没工作过（命中同名 API 封装，发的是 `[object Object]`）
- [ ] 禁言 / 封禁各试一次（用测试账号，注意**还原**）
- [ ] 网页端三个导出按钮各点一次（资料卡 PDF / 评估报告 / 评估表）
- [ ] 一次社区收藏、一次取消收藏
- [ ] 桌面端三个验收信号：Vite/线上连接、不落落地页、右上角 6 个窗口按钮**真的能看见**
- [ ] 小程序后台 request 合法域名含 `https://api.jizhi-learn.com`
- [ ] 阿里云安全组放行 80/443

**已作废的旧检查项**（别再做）：~~微信测试号后台「网页授权域名」~~（测试号扫码 09-28 已删）。

---

## 八、本次同步清单（project1 → jizhi，09-30）

**后端 19 个**：`main.py`（CORS 加 Tauri 源）、`requirements.txt`（+arq）、
`routers/`（admin、admin_video、auth、download、feedback、questions、subject_plan、
community/{messages,posts}）、`services/`（supabase、**task_queue ← 新增**）、
`sql/`（**admin_rework_20260930 ← 新增**、**user_shortcuts ← 新增**、exam_paper_records）、
`utils/`（auth_middleware、**sanctions ← 新增**）、**worker.py ← 新增**

**前端**：`frontend/src` 全量（新增 `shortcuts/` 五个文件、`views/admin/AdminSettings.vue`），
`dist` 已重建。

**配置**：`backend/config.py` 定点补 2 行；`backend/.env`、`frontend/.env` **未动**（校验和逐位相同）。

**文档**：`SYSTEM_MANUAL.md`（5953 行）、`PROJECT_LOG.md`（1673 行）已更新到 09-30。

**未同步**：`backend/static/`（安装包，见第六节）、`tests/`、`shoot.py`、`utils/jdk/`。

---

## 九、历史遗留（本仓库独有，无人引用）

- `backend/utils/volc_client.py` —— 本地已无此文件，**全仓库零 import**，是早期版本的残留。
  确认后可以删。
