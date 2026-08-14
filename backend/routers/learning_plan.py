"""学习规划 - AI 生成个性化学习计划"""
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from config import settings
import httpx
from datetime import datetime
import uuid, json, re
from utils.auth_middleware import get_current_user, verify_user_match
from services.supabase import get_supabase_headers
from logging_config import logger

router = APIRouter(prefix="/learning-plan", tags=["学习规划"])


class GenerateTasksRequest(BaseModel):
    keywords: str
    difficulty: int
    daily_minutes: int
    total_days: int


class CreatePlanRequest(BaseModel):
    user_id: str
    name: str
    stage: str
    grade: str
    major: str
    difficulty: int
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
3. 2 道与该日子知识点相关的练习题
4. 推荐一个 B站/YouTube 搜索关键词，用于找学习视频 (video_query)

每道题包含：
- type: "选择题"/"填空题"/"判断题"
- question: 题目文本
- options: 选择题提供["A","B","C","D"]，其他题型空数组
- answer: 正确答案
- difficulty_score: 1-10

知识点拆分原则：
- 第1天：基础概念入门
- 中间：逐步深入核心原理
- 最后1-2天：综合应用/实践

返回 JSON 数组，每天一个对象：
[
  {{
    "day": 1,
    "topic": "第1天子知识点",
    "content": "学习内容...",
    "video_query": "B站搜索关键词",
    "questions": [
      {{"type":"选择题","question":"...","options":["A","B","C","D"],"answer":"A","difficulty_score":5}},
      {{"type":"填空题","question":"...","options":[],"answer":"xxx","difficulty_score":6}}
    ]
  }},
  ...
]

只返回 JSON 数组，不要额外文字。"""

    try:
        from utils.volc_client import VolcClient
        client = VolcClient()
        response = client.chat([
            {"role": "system", "content": "你是学习规划专家，只返回 JSON 数组，不要额外文字。"},
            {"role": "user", "content": prompt}
        ], temperature=0.7)

        json_match = re.search(r'\[[\s\S]*\]', response)
        if json_match:
            days = json.loads(json_match.group())
            return {"success": True, "data": days, "source": "ai"}

    except Exception as e:
        logger.info(f"AI 生成失败，使用降级方案: {e}")

    # 降级方案
    fallback = []
    phases = ["基础概念", "核心原理"] + [f"进阶应用 ({i+3})" for i in range(max(0, req.total_days - 3))] + ["综合实践"]
    if len(phases) > req.total_days:
        phases = phases[:req.total_days]
    while len(phases) < req.total_days:
        phases.append(f"拓展学习 ({len(phases)+1})")

    for i, phase in enumerate(phases[:req.total_days]):
        fallback.append({
            "day": i + 1,
            "topic": f"{keyword} - {phase}",
            "content": f"{keyword} {phase}部分的核心内容，理解基本定义与应用场景。",
            "video_query": f"{keyword} {phase} 教程",
            "questions": [
                {"type": "选择题", "question": f"关于 {keyword} {phase}，以下说法正确的是？",
                 "options": ["A. 核心定义准确", "B. 理解有偏差", "C. 混淆了概念", "D. 以上都不对"], "answer": "A", "difficulty_score": 5},
                {"type": "判断题", "question": f"{keyword} {phase} 是学习的重要基础。",
                 "options": [], "answer": "对", "difficulty_score": 3},
            ]
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
