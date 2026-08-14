# 部署说明（2026-08-14 更新）

本文件夹为**公网部署版**：代码已与本地开发版（project1）同步至最新（含考纲体系、真题套卷、管理后台等），全部配置指向公网。

## 公网配置（已改好）

| 位置 | 配置 |
|---|---|
| `frontend/.env` | `VITE_BACKEND_URL=https://api.jizhi-learn.com` |
| `frontend/src/**` 所有兜底地址 | `https://api.jizhi-learn.com`（不再有 localhost 兜底） |
| `backend/config.py` | FRONTEND_URL 默认 `https://jizhi-learn.com`，BACKEND_EXTERNAL_URL 默认 `https://api.jizhi-learn.com` |
| `backend/.env` | 全部 API 密钥 + 微信测试号/小程序 + 新 JWT_SECRET + 公网域名 |
| `backend/main.py` CORS | 已含 jizhi-learn.com / www / vercel 域名 |

## 一、后端上传（服务器 8.134.157.214）

上传 `backend/` 整个文件夹（覆盖 `/www/wwwroot/backend/`），注意：
- **必须带上 `backend/data/`**（25MB 题库 JSON，含 `exam_papers/` 12 套真题卷）——没有它考纲/真题全是空的
- **必须覆盖 `backend/.env`**（新增了微信密钥、JWT_SECRET、公网域名配置）
- 不需要上传：`backend/utils/mingw.zip`、`tcc.exe`、`tcc.zip`（Windows 编译器，服务器用系统 GCC）

服务器上执行：

```bash
cd /www/wwwroot/backend
pip install -r requirements.txt        # 新依赖：PyJWT、qrcode（之前可能已装过，重复装无害）
export PYTHONIOENCODING=utf-8
# 重启 uvicorn（用你原来的启动方式/端口）
uvicorn main:app --host 0.0.0.0 --port 8000
```

启动后验证：访问 `https://api.jizhi-learn.com/health` 应返回 `{"status":"ok"}`，
`https://api.jizhi-learn.com/subject-plan/syllabi` 应列出 17 个考纲。

## 二、数据库（Supabase）——只需执行一次

如果还没在 Supabase SQL Editor 执行过 08-12 新增的迁移，执行 `backend/sql/` 里这 3 个文件：

1. `exam_paper_records.sql` — 答卷记录表（真题交卷用）
2. `migrate_plan_columns.sql` — subject_plans 补 syllabus_id、plan_daily_tasks 补列
3. `migrate_daily_learning.sql` — phase / learning_content / difficulty_level / daily_time_hint

检查方法：SQL Editor 里跑 `SELECT count(*) FROM exam_paper_records;` 不报错即已存在。

## 三、前端部署

`frontend/dist/` 已用生产配置重新构建（2026-08-14），两种方式任选：

- **Vercel**：在 `frontend/` 目录 `vercel --prod`（vercel.json 已配好 SPA rewrite），或推 GitHub 自动部署
- **服务器**：把 `frontend/dist/` 上传到网站目录

## 四、部署后检查清单

- [ ] 微信测试号后台「网页授权获取用户基本信息」域名改为 `api.jizhi-learn.com`（网页扫码登录用）
- [ ] 小程序后台 request 合法域名含 `https://api.jizhi-learn.com`
- [ ] 阿里云安全组放行 80/443（如尚未开放）
- [ ] 网页登录 → 考纲列表 → 做题 → 真题套卷交卷全链路验证
- [ ] 小程序对话/学习/资源库验证

## 五、本次同步说明（project1 → jizhi）

**同步进来的（运行相关）**：后端 routers（subject_plan / exam_papers / admin / community 包）、utils（code_runner / auth_middleware / admin_middleware / rate_limit）、services、agents、local_question_bank、logging_config、scripts、sql、data（题库+真题卷）；前端全部 src（含考纲/真题/设置/管理后台页面）、icons、api、router。

**排除的（与运行无关）**：mingw.zip / tcc.exe / tcc.zip（Windows 编译器）、expand_papers.py（一次性补题脚本）、tests/、旧版 streamlit 残留（根目录 pages/、utils/ 已删除）、未使用的旧视图（SubjectBank / SubjectPlan / SubjectPlanDetail / SubjectPlanDiagnosis）。

## 六、换 JWT_SECRET 的说明

本次生成了新的随机 JWT_SECRET（已写入 backend/.env）。上传后所有旧登录 token 失效，用户需重新登录——属正常现象，只需换这一次。
