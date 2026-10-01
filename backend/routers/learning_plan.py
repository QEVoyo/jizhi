"""学习规划 - AI 生成个性化学习计划"""
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, field_validator
from config import settings
import httpx
from datetime import datetime
import uuid, json, re
from utils.auth_middleware import get_current_user, verify_user_match
from services.supabase import get_supabase_headers
from logging_config import logger

router = APIRouter(prefix="/learning-plan", tags=["学习规划"])

# 平台通用三档难度 → 数值中值（与出题提示词的 1-3 / 4-6 / 7-10 分档对齐）
_DIFFICULTY_WORDS = {"简单": 2, "容易": 2, "中等": 5, "普通": 5, "困难": 8, "难": 8}


class _DifficultyMixin(BaseModel):
    """difficulty 兼容「中文档位」与数值两种传法。

    小基规划卡一直按平台口语传 '中等'，而模型声明的是 int → pydantic 直接 422，
    导致「生成草稿」和「建计划」两步全断。收口语档位，别让调用方猜数字。
    """
    difficulty: int

    @field_validator("difficulty", mode="before")
    @classmethod
    def _norm_difficulty(cls, v):
        if isinstance(v, str):
            s = v.strip()
            if s in _DIFFICULTY_WORDS:
                return _DIFFICULTY_WORDS[s]
            try:
                return int(float(s))
            except ValueError:
                return 5
        if isinstance(v, float):
            return int(v)
        return v


class GenerateTasksRequest(_DifficultyMixin):
    keywords: str
    daily_minutes: int
    total_days: int


class CreatePlanRequest(_DifficultyMixin):
    user_id: str
    name: str
    stage: str
    grade: str
    major: str
    daily_minutes: int
    start_date: str
    end_date: str
    keywords: str
    tasks: list = []


class UpdateTaskStatusRequest(BaseModel):
    task_id: str
    status: str
    plan_id: str = ""


class TaskAnswerRequest(BaseModel):
    """一道题的作答结果（2026-10-01）。以前自定义计划做完什么也不记。"""
    user_id: str
    task_id: str
    is_correct: bool = False
    user_answer: str = ""
    time_spent: int = 0


# ============================================================
# 1. AI 生成任务（按学习周期拆分知识点）
# ============================================================
@router.post("/generate-tasks")
async def generate_tasks(req: GenerateTasksRequest):
    """AI 将知识点按总天数拆分为每日子任务，每日子任务 = 学习内容 + 题目 + 视频推荐"""
    keyword = req.keywords.strip()
    if not keyword:
        raise HTTPException(status_code=400, detail="请提供有效关键词")
    if ',' in keyword or '，' in keyword or '、' in keyword:
        keyword = re.split(r'[,，、\s]+', keyword)[0].strip()

    # 难度档位 → 文字描述。
    # ⚠️ 2026-10-01：这里是**第一次真正用上 req.difficulty**。
    #    在此之前 difficulty 被前端发送、被后端接收、被写进 learning_plans，
    #    但在这个 prompt 里出现 **0 次** —— 调难度滑块，生成的计划一模一样。
    diff = max(1, min(10, int(req.difficulty or 5)))
    if diff <= 3:
        diff_desc = "入门：概念与识记为主，题目以基础题为主，不要出现需要多步推导的综合题"
    elif diff <= 6:
        diff_desc = "中等：理解与应用为主，题目要能检验「是不是真的会用了」，允许少量综合题"
    else:
        diff_desc = "进阶：综合与迁移为主，题目要有区分度，包含多步推理或跨知识点结合的题"

    prompt = f"""你是学习规划专家。用户想学【{keyword}】，学习周期 {req.total_days} 天，每天可投入 {req.daily_minutes} 分钟。

【难度档位】{diff}/10 —— {diff_desc}
这个档位必须**贯穿始终**：知识点拆分的粒度、题目的 difficulty_score、每天的推进速度，都要按它来。

请生成 {req.total_days} 天的**大纲**，每天包含：
1. topic —— 该天的子知识点名称
2. summary —— 当天学什么的摘要，**60 字以内**。这里**不要展开写正文** ——
   详细教学正文由用户点进去时单独生成，列表里只显示这两行
3. knowledge_points —— 当天涉及的 1-3 个**具体知识点名称**。每个都会配一条讲解视频，
   所以要写能独立成篇的知识点名（如「二次函数顶点式」），**不要写「综合练习」「复习」这种不成篇的**
4. estimated_minutes —— 当天建议总时长，应当接近 {req.daily_minutes} 分钟
5. questions —— 当天的练习题

【题量与配比】
- 题目总耗时占当天时长的 **40%~60%**（其余留给看讲解视频和消化）
- **每道题都要给 estimated_minutes**（做完这道题大概几分钟）；所有题的 estimated_minutes
  加起来要落进上面那个区间 —— 这是硬要求
- 题型按学科实际的练习与考试形式决定，不要固定套用某几种：
  数学/理工计算类 → 计算题、填空题、选择题；英语/语言类 → 选择题、填空题、翻译题、写作题；
  编程/计算机类 → 编程题、代码填空、选择题；文史/理论类 → 简答题、材料分析题、选择题
- 题目要能检验当天所学，不要出与知识点无关的凑数题

【每道题包含】
- type: 题型名称（"选择题"/"计算题"/"翻译题"/"编程题"/"简答题" 等）
- question: 题目文本
- answer: 正确答案（选择题填选项字母；其他题型给参考答案或要点）
- difficulty_score: 1-10，**要和上面的难度档位 {diff} 对齐**
- estimated_minutes: 预计几分钟做完
- 仅当 type 为选择题时，才额外提供 options: ["A. ...","B. ...","C. ...","D. ..."]；
  其他题型不要输出 options 字段

【推进节奏】
- 第1天：基础概念入门；中间：逐步深入核心原理；最后1-2天：综合应用/实践
- 若该学科有更合适的节奏，可按学科惯例调整

返回 JSON 数组，每天一个对象。**不要照抄下面的结构占位**：
[
  {{
    "day": 1,
    "topic": "第1天子知识点",
    "summary": "当天学什么（60字以内）",
    "knowledge_points": ["知识点A", "知识点B"],
    "estimated_minutes": {req.daily_minutes},
    "questions": [{{"type": "选择题", "question": "...", "answer": "A", "difficulty_score": {diff}, "estimated_minutes": 3, "options": ["A. ...","B. ...","C. ...","D. ..."]}}]
  }},
  ...
]

只返回 JSON 数组，不要额外文字。"""

    sys_prompt = "你是学习规划专家，只返回 JSON 数组，不要额外文字。"
    response = ""
    try:
        # 2026-08-30：DeepSeek 生成整份计划需 70s+（实测 73.7s），切 qwen-flash（实测 7.1s，与小基同 key）
        from agents.qwen_client import call_qwen
        response = call_qwen(
            [{"role": "system", "content": sys_prompt}, {"role": "user", "content": prompt}],
            model=getattr(settings, "QWEN_CHAT_MODEL", "qwen-flash"),
            temperature=0.7)
    except Exception as e:
        logger.info(f"[learning-plan] qwen 生成失败，回退 DeepSeek: {e}")
        try:
            from agents.llm_client import call_llm
            response = call_llm([
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": prompt}
            ], temperature=0.7)
        except Exception as e2:
            logger.info(f"[learning-plan] DeepSeek 也失败: {e2}")
            response = ""

    try:
        json_match = re.search(r'\[[\s\S]*\]', response)
        if json_match:
            days = json.loads(json_match.group())
            if isinstance(days, list) and days:
                return {"success": True, "data": days, "source": "ai"}
    except Exception as e:
        logger.info(f"AI 生成失败，使用降级方案: {e}")

    # 降级方案：AI 两条路都挂了才走这里。结构必须和 AI 输出**同一套字段**
    # （summary / knowledge_points / estimated_minutes），否则前端拿到两种形状要写两遍。
    fallback = []
    for i in range(req.total_days):
        day_no = i + 1
        fallback.append({
            "day": day_no,
            "topic": f"{keyword}（第{day_no}天）",
            "summary": f"围绕「{keyword}」自主安排第 {day_no} 天的学习：先梳理核心概念，再结合例题加深理解，最后用自己的话总结要点。",
            "knowledge_points": [f"{keyword} 入门"],
            "estimated_minutes": req.daily_minutes,
            "questions": [{
                "type": "简答题",
                "question": f"用自己的话总结「{keyword}」第 {day_no} 天学习内容的核心要点，并举一个例子说明。",
                "answer": "能准确复述核心概念并举出恰当例子即可。",
                "difficulty_score": max(1, min(10, int(req.difficulty or 5))),
                "estimated_minutes": max(5, int(req.daily_minutes * 0.5)),
            }]
        })

    return {"success": True, "data": fallback, "source": "fallback"}


# ============================================================
# 题型归一（2026-10-01）
# ============================================================
# AI 出的是**中文题型名**，而做题页认的是英文枚举（见 utils/questionLabels.js）。
# 前端原来只映射了「填空 / 判断」，其余一律 'choice' —— 于是「计算题」「翻译题」
# 全被当成单选题渲染，出来的是错的。
_QTYPE_MAP = {
    '选择题': 'choice', '单选题': 'choice', 'choice': 'choice', 'choice_single': 'choice',
    '多选题': 'choice_multi', '不定项': 'choice_multi', 'choice_multi': 'choice_multi',
    '填空题': 'fill', 'fill': 'fill',
    '判断题': 'choice', 'judge': 'choice', 'judgement': 'choice', 'judgment': 'choice',
    '完形填空': 'cloze', '完形': 'cloze', 'cloze': 'cloze',
    '翻译题': 'translation', 'translation': 'translation',
    '写作题': 'essay', '作文': 'essay', 'essay': 'essay',
    '计算题': 'calculation', 'calculation': 'calculation',
    '编程题': 'programming', 'programming': 'programming',
    '简答题': 'short_answer', 'short_answer': 'short_answer',
    '论述题': 'analysis', '分析题': 'analysis', '材料分析题': 'analysis', 'analysis': 'analysis',
    '阅读理解': 'reading', 'reading': 'reading',
    '案例分析': 'case_analysis', 'case_analysis': 'case_analysis',
    '教学设计': 'teaching_design', 'teaching_design': 'teaching_design',
}

_TRUE_WORDS = {'对', '正确', '√', 'T', 'TRUE', '是'}


def _norm_qtype(t) -> str:
    return _QTYPE_MAP.get(str(t or '').strip(), 'choice')


def _fix_judge(options, answer):
    """判断题 → 补成一对 A/B 选项。

    判断题映射到 `choice`（做题页按选项渲染），但 AI 通常**不给 options**、
    答案写的是「对 / 错」而不是字母 —— 不补的话会出来一道**没有选项的单选题**。
    """
    opts = list(options) if options else ['A. 正确', 'B. 错误']
    a = str(answer or '').strip()
    if a and a[0].upper() not in ('A', 'B'):
        answer = 'A' if a in _TRUE_WORDS else 'B'
    return opts, answer


# ============================================================
# 2. 创建规划 + 保存任务
# ============================================================
@router.post("/create")
async def create_plan(req: CreatePlanRequest, current_user: str = Depends(get_current_user)):
    verify_user_match(req.user_id, current_user)
    if not req.tasks:
        raise HTTPException(status_code=400, detail="任务列表不能为空")

    headers = get_supabase_headers()
    now = datetime.now().isoformat()
    plan_id = str(uuid.uuid4())
    total = len(req.tasks)
    completed = sum(1 for t in req.tasks if t.get("status") == "completed")

    plan_data = {
        "id": plan_id, "user_id": req.user_id, "name": req.name,
        "stage": req.stage, "grade": req.grade, "major": req.major,
        "difficulty": req.difficulty, "daily_minutes": req.daily_minutes,
        "start_date": req.start_date, "end_date": req.end_date,
        "keywords": req.keywords, "status": "active",
        "progress": round(completed / total * 100) if total else 0,
        "created_at": now, "updated_at": now
    }

    async with httpx.AsyncClient() as client:
        url = f"{settings.SUPABASE_URL}/rest/v1/learning_plans"
        res = await client.post(url, headers=headers, json=plan_data)
        if res.status_code not in [200, 201]:
            raise HTTPException(status_code=400, detail=f"创建规划失败: {res.text}")

        for task in req.tasks:
            qtype = _norm_qtype(task.get("question_type"))
            q_options = task.get("options") or []
            q_answer = task.get("answer", "")
            task_qid = task.get("question_id") or None

            # ===== 题目落库（2026-10-01）=====
            # 两池模型：题库真题 → 学科计划；AI 生成题 → **资源库 + 自定义计划**。
            # 所以这里生成的题不留在任务行里当正文，而是写进 `questions` 表
            # （和资源库同一个池子），任务只存 `question_id` 引用。
            #
            # 三个好处：
            #   ① 做题页能按 id 取到题（以前任务 id 被当成题目 id 去查，**必然 404**）
            #   ② 这些题会出现在资源库的「生成历史」里，用户能找回、能再练
            #   ③ 题目有 id 之后，错题本（questions.is_mistake）才挂得上
            if task.get("type") == "做题" and not task_qid and task.get("question_content"):
                if qtype == "choice" and str(task.get("question_type", "")).strip() == "判断题":
                    q_options, q_answer = _fix_judge(q_options, q_answer)
                qid = str(uuid.uuid4())
                q_row = {
                    "id": qid, "user_id": req.user_id,
                    "title": task.get("question_content", ""),
                    "question_type": qtype,
                    "difficulty_score": task.get("difficulty_score", 5),
                    "category": req.keywords or "",
                    "topic": task.get("topic", ""),
                    "normalized_topic": str(task.get("topic", ""))[:12],
                    "options": q_options,
                    "answer": q_answer,
                    "source": "generated",
                }
                # 用 anon：`generation_history` 对 service_role 是 403（反向缺口，
                # 09-30 那轮见过同一类）。`questions` 两边都能写，就统一用 anon。
                qr = await client.post(f"{settings.SUPABASE_URL}/rest/v1/questions",
                                       headers=headers, json=q_row)
                if qr.status_code < 300:
                    task_qid = qid
                    # 同步进生成历史 —— 资源库的「生成历史」读的就是这张表
                    await client.post(f"{settings.SUPABASE_URL}/rest/v1/generation_history",
                                      headers=headers, json={
                                          "id": str(uuid.uuid4()), "user_id": req.user_id,
                                          "question_id": qid,
                                          "title": str(q_row["title"])[:200],
                                          "question_type": qtype,
                                          "category": q_row["category"],
                                          "topic": q_row["topic"], "status": "saved",
                                      })
                else:
                    # 题目落不进去不阻断建计划（任务还能做，只是没有 id），
                    # 但必须留痕 —— 别让它静默变成「做完记不了账」。
                    logger.warning(f"题目落库失败 [{qr.status_code}]: {qr.text[:200]}")

            task_data = {
                "id": str(uuid.uuid4()), "plan_id": plan_id, "user_id": req.user_id,
                "type": task.get("type", "做题"), "topic": task.get("topic", ""),
                "description": task.get("description", ""),
                "question_type": qtype,
                # question_content / options / answer 暂时保留着写（过渡期），
                # 阶段 3 把读取方全部切到 question_id 之后再停。
                "question_content": task.get("question_content", ""),
                "options": q_options,
                "answer": q_answer,
                "difficulty_score": task.get("difficulty_score", 5),
                "video_query": task.get("video_query", ""),
                # 2026-10-01 新增（列见 sql/learning_plan_rework.sql）：
                #   estimated_minutes —— 用来校验「当天题量是否配得上 daily_minutes」
                #   attempts/best_correct/last_correct —— 做题结果，算当日**最佳正确率**
                #     （最佳率：重做做错不回退，只从 false 变 true）
                "estimated_minutes": task.get("estimated_minutes"),
                "question_id": task_qid,
                "attempts": 0,
                "best_correct": False,
                "date": task.get("date", req.start_date),
                "status": "pending", "created_at": now, "updated_at": now
            }
            task_url = f"{settings.SUPABASE_URL}/rest/v1/learning_tasks"
            task_res = await client.post(task_url, headers=headers, json=task_data)
            if task_res.status_code not in [200, 201]:
                raise HTTPException(status_code=400, detail=f"任务保存失败: {task_res.text}")

        return {"success": True, "plan_id": plan_id, "message": "规划创建成功"}


# ============================================================
# 3. 规划列表
# ============================================================
@router.get("/list")
async def get_plans(user_id: str = Query(...), current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()
    url = f"{settings.SUPABASE_URL}/rest/v1/learning_plans?user_id=eq.{user_id}&order=created_at.desc"
    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        return {"plans": res.json() if res.status_code == 200 else []}


# ============================================================
# 4. 规划详情
# ============================================================
@router.get("/detail/{plan_id}")
async def get_plan_detail(plan_id: str):
    headers = get_supabase_headers()
    async with httpx.AsyncClient() as client:
        plan_url = f"{settings.SUPABASE_URL}/rest/v1/learning_plans?id=eq.{plan_id}"
        plan_res = await client.get(plan_url, headers=headers)
        if plan_res.status_code != 200 or not plan_res.json():
            raise HTTPException(status_code=404, detail="规划不存在")
        plan = plan_res.json()[0]

        task_url = f"{settings.SUPABASE_URL}/rest/v1/learning_tasks?plan_id=eq.{plan_id}&order=date.asc,created_at.asc"
        task_res = await client.get(task_url, headers=headers)
        plan["tasks"] = task_res.json() if task_res.status_code == 200 else []
        return plan


# ============================================================
# 5. 更新任务状态 + 同步规划进度
# ============================================================
async def _sync_plan_progress(client, plan_id: str, headers: dict, now: str) -> dict:
    """按「已完成任务数 / 总任务数」重算计划进度。

    `PUT /task/status` 和 `PUT /task/answer` 都要用 —— 抽出来免得两处口径跑偏
    （这个项目在「同一个算法写两遍」上吃过亏）。
    """
    if not plan_id:
        return {}
    # ⚠️ 这里**不能**写 `async with client:` —— 那会把调用方传进来的 client 关掉，
    #    它后面还要接着用。client 的生命周期归调用方管。
    all_res = await client.get(
        f"{settings.SUPABASE_URL}/rest/v1/learning_tasks?plan_id=eq.{plan_id}&select=status",
        headers=headers)
    if all_res.status_code != 200:
        return {}
    tasks = all_res.json()
    total = len(tasks)
    done = sum(1 for t in tasks if t.get("status") == "completed")
    progress = round(done / total * 100) if total else 0
    plan_status = "completed" if progress >= 100 else "active"
    await client.patch(f"{settings.SUPABASE_URL}/rest/v1/learning_plans?id=eq.{plan_id}",
                       headers=headers, json={"progress": progress, "status": plan_status,
                                              "updated_at": now})
    return {"progress": progress, "status": plan_status}


@router.put("/task/status")
async def update_task_status(req: UpdateTaskStatusRequest):
    headers = get_supabase_headers()
    now = datetime.now().isoformat()
    async with httpx.AsyncClient() as client:
        # 更新任务
        task_url = f"{settings.SUPABASE_URL}/rest/v1/learning_tasks?id=eq.{req.task_id}"
        res = await client.patch(task_url, headers=headers, json={
            "status": req.status, "updated_at": now
        })
        if res.status_code not in [200, 204]:
            raise HTTPException(status_code=400, detail="更新失败")

        # 同步规划进度
        await _sync_plan_progress(client, req.plan_id, headers, now)

        return {"success": True}


@router.put("/task/answer")
async def record_task_answer(req: TaskAnswerRequest, current_user: str = Depends(get_current_user)):
    """回写一道题的作答结果（2026-10-01）。

    自定义计划以前**做完什么也不记** —— `update_task_status` 只改一个 status 字段，
    既不记对错也不记次数，所以「当日正确率」根本无从算起。

    三个字段的语义要分清（用户定调）：
      · `attempts` / `last_correct` —— 每次作答都更新，记「最近一次」
      · `best_correct`             —— **只从 false 变 true，永不回退**
        用户要求的是**最佳率**：重做做错了不该把成绩拉下来

    **提交一次即视为该任务完成** —— 完成度管解锁次日，正确率管掌握，两回事。
    （用户原话「做题错了可以重做」，重做的动机是把正确率提上去，不是解锁。）
    """
    verify_user_match(req.user_id, current_user)
    headers = get_supabase_headers()
    now = datetime.now().isoformat()

    async with httpx.AsyncClient(timeout=25.0) as client:
        r = await client.get(
            f"{settings.SUPABASE_URL}/rest/v1/learning_tasks?id=eq.{req.task_id}&limit=1",
            headers=headers)
        rows = r.json() if r.status_code < 300 else []
        if not rows:
            raise HTTPException(status_code=404, detail="任务不存在")
        task = rows[0]

        attempts = (task.get("attempts") or 0) + 1
        best = bool(task.get("best_correct")) or bool(req.is_correct)

        patch = {
            "attempts": attempts,
            "last_correct": bool(req.is_correct),
            "best_correct": best,
            "user_answer": str(req.user_answer)[:2000],
            "updated_at": now,
        }
        if task.get("status") != "completed":
            patch["status"] = "completed"

        up = await client.patch(
            f"{settings.SUPABASE_URL}/rest/v1/learning_tasks?id=eq.{req.task_id}",
            headers=headers, json=patch)
        # ⚠️ 查状态码：httpx 对 4xx 不抛异常，不查就是静默丢失
        #    （这个项目已经栽过好几次，见 sql/fix_records_nullable_plan.sql）
        if up.status_code >= 300:
            logger.error(f"作答回写失败 [{up.status_code}]: {up.text[:200]}")
            raise HTTPException(status_code=502, detail="作答记录保存失败，请重试")

        plan_id = task.get("plan_id") or ""
        prog = await _sync_plan_progress(client, plan_id, headers, now)

    return {"success": True, "attempts": attempts, "best_correct": best, **prog}


# ============================================================
# 5b. 学习内容：按需生成完整教学正文（2026-10-01）
# ============================================================
@router.get("/task/{task_id}/lesson")
async def get_task_lesson(task_id: str):
    """取某天学习内容的**完整教学正文**；没有就按需生成并缓存。

    为什么按需，而不是建计划时一次生成：
      · 一次生成 N 天的正文会撑爆响应 —— 这条链路前端 90 秒超时，
        而出大纲只要 7 秒；N 天正文的 token 量是另一个数量级
      · 用户多半不会逐天看完，提前生成是白烧钱

    这个模式和学科计划的 `/plans/{id}/tasks/{id}/generate-learning` 是同一套
    （「首次生成后缓存到任务记录」），缓存列 `learning_tasks.lesson_content`。

    用户原话：「学习内容应该要详细教学，而不是概述知识点」——
    所以 prompt 明确要**分节正文 + 例子**，不要 bullet 式摘要。
    """
    headers = get_supabase_headers()

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(
            f"{settings.SUPABASE_URL}/rest/v1/learning_tasks?id=eq.{task_id}&limit=1",
            headers=headers)
        rows = r.json() if r.status_code < 300 else []
        if not rows:
            raise HTTPException(status_code=404, detail="任务不存在")
        task = rows[0]

        # 有缓存直接返回 —— 不重复烧钱
        cached = task.get("lesson_content")
        if isinstance(cached, str):
            try:
                cached = json.loads(cached)
            except Exception:
                cached = None
        if cached:
            return {"task_id": task_id, "topic": task.get("topic", ""), "lesson": cached, "cached": True}

        # 取计划拿难度与关键词 —— 正文深浅要跟难度档位对齐
        plan = {}
        if task.get("plan_id"):
            pr = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/learning_plans?id=eq.{task['plan_id']}&limit=1",
                headers=headers)
            if pr.status_code < 300 and pr.json():
                plan = pr.json()[0]

    topic = task.get("topic", "") or plan.get("keywords", "")
    keywords = plan.get("keywords", "")
    diff = plan.get("difficulty") or 5
    if diff <= 3:
        depth = "入门：把概念讲清楚，多用生活化的类比，不要堆术语"
    elif diff <= 6:
        depth = "中等：讲清原理和「为什么」，配合典型例题演示推导过程"
    else:
        depth = "进阶：讲透易错点和边界情况，要有综合性的例子和变式"

    prompt = f"""你是一位擅长把复杂东西讲明白的老师。请为下面这个学习主题写一份**详细的教学正文**。

主题：{topic}
所属：{keywords}
难度档位：{diff}/10 —— {depth}

【最重要的一条】这是给学生**自学用的教学正文**，不是知识点提纲。
要求：
- 分 3~6 个小节，**每节都要有完整的讲解段落**，把「是什么、为什么、怎么用」讲透
- **必须举具体例子**，例子要展开算/展开讲，不能只写「例如……」
- 不要用「本文将介绍」「综上所述」这类套话，直接讲内容
- 不要写成 bullet 要点列表 —— 那正是「概述知识点」，是我们要避免的

返回严格 JSON：
{{
  "summary": "一句话说明这份正文讲什么（40字内）",
  "sections": [
    {{"heading": "小节标题", "body": "这一节的完整讲解正文（可以很长，段落清晰）", "example": "这一节的例子（展开写的，没有就留空字符串）"}}
  ],
  "key_points": ["学完必须记住的要点", "..."],
  "common_mistakes": ["常见错误及为什么错", "..."]
}}

只返回 JSON，不要额外文字。"""

    lesson = None
    raw = ""
    try:
        from agents.qwen_client import call_qwen
        raw = call_qwen(
            [{"role": "system", "content": "你是教学正文写作者，只返回 JSON。"},
             {"role": "user", "content": prompt}],
            model=getattr(settings, "QWEN_CHAT_MODEL", "qwen-flash"),
            temperature=0.6)
    except Exception as e:
        logger.info(f"[learning-plan] 学习正文 qwen 失败，回退 DeepSeek: {e}")
        try:
            from agents.llm_client import call_llm
            raw = call_llm(
                [{"role": "system", "content": "你是教学正文写作者，只返回 JSON。"},
                 {"role": "user", "content": prompt}],
                temperature=0.6)
        except Exception as e2:
            logger.warning(f"[learning-plan] 学习正文 DeepSeek 也失败: {e2}")

    # 括号计数法提取 JSON —— 正文很长，模型很可能在前后带说明文字甚至被截断，
    # 简单的 re.search(r'\{.*\}') 遇到嵌套/截断就废（generate_tasks 那边同款处理）
    if raw:
        start = raw.find('{')
        if start >= 0:
            depth_n, in_str, esc, end = 0, False, False, -1
            for i in range(start, len(raw)):
                ch = raw[i]
                if esc:
                    esc = False; continue
                if ch == '\\':
                    esc = True; continue
                if ch == '"':
                    in_str = not in_str; continue
                if in_str:
                    continue
                if ch == '{':
                    depth_n += 1
                elif ch == '}':
                    depth_n -= 1
                    if depth_n == 0:
                        end = i + 1; break
            if end > 0:
                try:
                    lesson = json.loads(raw[start:end])
                except Exception as e:
                    logger.warning(f"[learning-plan] 学习正文 JSON 解析失败: {e}")

    if not lesson:
        raise HTTPException(status_code=502, detail="教学正文生成失败，请稍后重试")

    # 缓存回任务行
    async with httpx.AsyncClient(timeout=20.0) as c:
        up = await c.patch(
            f"{settings.SUPABASE_URL}/rest/v1/learning_tasks?id=eq.{task_id}",
            headers=headers, json={"lesson_content": lesson,
                                   "updated_at": datetime.now().isoformat()})
    if up.status_code >= 300:
        # 缓存写不进去不影响这次阅读，但要说出来 —— 否则下次又白烧一次钱
        logger.warning(f"学习正文缓存失败 [{up.status_code}]: {up.text[:200]}")

    return {"task_id": task_id, "topic": topic, "lesson": lesson, "cached": False}


# ============================================================
# 6. 删除规划
# ============================================================
@router.delete("/delete/{plan_id}")
async def delete_plan(plan_id: str):
    headers = get_supabase_headers()
    async with httpx.AsyncClient() as client:
        task_url = f"{settings.SUPABASE_URL}/rest/v1/learning_tasks?plan_id=eq.{plan_id}"
        await client.delete(task_url, headers=headers)
        plan_url = f"{settings.SUPABASE_URL}/rest/v1/learning_plans?id=eq.{plan_id}"
        res = await client.delete(plan_url, headers=headers)
        if res.status_code not in [200, 204]:
            raise HTTPException(status_code=400, detail="删除失败")
        return {"success": True}
