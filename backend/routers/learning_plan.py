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

    prompt = f"""你是学习规划专家。用户想学【{keyword}】，学习周期 {req.total_days} 天，每天 {req.daily_minutes} 分钟。

请生成 {req.total_days} 天的学习计划，每天包含：
1. 该天的子知识点名称 (topic)
2. 学习内容 (content, 100-200字)
3. 与该日子知识点相关的练习题 (questions)
4. 推荐一个 B站/YouTube 搜索关键词，用于找学习视频 (video_query)

出题要求：
- 先判断【{keyword}】所属的学科/知识领域，再按该学科实际的练习与考试形式决定题型，不要固定套用某几种题型：
  数学/理工计算类 → 计算题、填空题、选择题；英语/语言类 → 选择题、填空题、翻译题、写作题；
  编程/计算机类 → 编程题、代码填空、选择题；文史/理论类 → 简答题、材料分析题、选择题；
  其他学科按该领域常见题型出题
- 每天的题量与题型配比由你根据当天知识点的特点和 {req.daily_minutes} 分钟的可用时长自行决定，各天不必相同
- 题目要能检验当天所学，不要出与知识点无关的凑数题

每道题包含：
- type: 题型名称（按学科惯例命名，如 "选择题"/"计算题"/"翻译题"/"编程题"/"简答题" 等）
- question: 题目文本
- answer: 正确答案（选择题填选项字母；计算题/编程题/简答题给出参考答案或要点）
- difficulty_score: 1-10
- 仅当 type 为选择题时，才额外提供 options: ["A. ...","B. ...","C. ...","D. ..."]；其他题型不要输出 options 字段

知识点拆分原则：
- 第1天：基础概念入门
- 中间：逐步深入核心原理
- 最后1-2天：综合应用/实践
（若该学科有更合适的学习节奏，可按学科惯例调整）

返回 JSON 数组，每天一个对象。questions 中的题型与题量请按上述要求自行决定，不要照抄下面的结构占位：
[
  {{
    "day": 1,
    "topic": "第1天子知识点",
    "content": "学习内容...",
    "video_query": "B站搜索关键词",
    "questions": [{{"type": "按学科决定的题型", "question": "...", "answer": "...", "difficulty_score": 5}}]
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

    # 降级方案：不预设学科、题型与示例题，只给通用的「自学 + 自测」结构
    fallback = []
    for i in range(req.total_days):
        day_no = i + 1
        fallback.append({
            "day": day_no,
            "topic": f"{keyword}（第{day_no}天）",
            "content": f"围绕「{keyword}」自主安排第 {day_no} 天的学习：先梳理当天要掌握的核心概念，再结合例题或实践加深理解，最后用自己的话总结要点。",
            "video_query": f"{keyword} 教程",
            "questions": [{
                "type": "简答题",
                "question": f"用自己的话总结「{keyword}」第 {day_no} 天学习内容的核心要点，并举一个例子说明。",
                "answer": "能准确复述核心概念并举出恰当例子即可。",
                "difficulty_score": 5,
            }]
        })

    return {"success": True, "data": fallback, "source": "fallback"}


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
            task_data = {
                "id": str(uuid.uuid4()), "plan_id": plan_id, "user_id": req.user_id,
                "type": task.get("type", "做题"), "topic": task.get("topic", ""),
                "description": task.get("description", ""),
                "question_type": task.get("question_type", ""),
                "question_content": task.get("question_content", ""),
                "options": task.get("options", []),
                "answer": task.get("answer", ""),
                "difficulty_score": task.get("difficulty_score", 5),
                "video_query": task.get("video_query", ""),
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
        if req.plan_id:
            all_url = f"{settings.SUPABASE_URL}/rest/v1/learning_tasks?plan_id=eq.{req.plan_id}&select=status"
            all_res = await client.get(all_url, headers=headers)
            if all_res.status_code == 200:
                tasks = all_res.json()
                total = len(tasks)
                done = sum(1 for t in tasks if t.get("status") == "completed")
                progress = round(done / total * 100) if total else 0
                plan_status = "completed" if progress >= 100 else "active"
                plan_url = f"{settings.SUPABASE_URL}/rest/v1/learning_plans?id=eq.{req.plan_id}"
                await client.patch(plan_url, headers=headers, json={
                    "progress": progress, "status": plan_status, "updated_at": now
                })

        return {"success": True}


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
