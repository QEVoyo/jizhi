from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from config import settings
import httpx
from datetime import datetime
import uuid
import json
import re

router = APIRouter(prefix="/learning-plan", tags=["学习规划"])


def get_supabase_headers():
    return {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json"
    }


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


class GenerateTasksRequest(BaseModel):
    keywords: str
    difficulty: int
    daily_minutes: int
    total_days: int


class UpdateTaskStatusRequest(BaseModel):
    task_id: str
    status: str


@router.post("/generate-tasks")
async def generate_tasks(req: GenerateTasksRequest):
    """AI 生成学习任务（只支持单个知识点）"""
    print("=" * 50)
    print("🔍 AI 生成任务请求")
    print(f"🔍 关键词: {req.keywords}")
    print(f"🔍 难度: {req.difficulty}")
    print(f"🔍 每日时长: {req.daily_minutes} 分钟")
    print(f"🔍 总天数: {req.total_days} 天")

    # 只取第一个关键词
    keyword = req.keywords.strip()
    if not keyword:
        raise HTTPException(status_code=400, detail="请提供有效关键词")

    # 如果有多个，只取第一个
    if ',' in keyword or '，' in keyword or '、' in keyword:
        keyword = re.split(r'[,，、\s]+', keyword)[0].strip()

    print(f"🔍 处理知识点: {keyword}")

    # ================ 修改后的通用 prompt ================
    prompt = f"""
    你是学习规划专家。用户的学习方向是【{keyword}】。

    请围绕这个方向，拆解出 4-6 个更细致的子知识点。
    每个子知识点生成：
    1. 学习内容（100-200字）
    2. 2 道练习题

    每道题必须包含以下完整字段：
    - type: "选择题" / "填空题" / "判断题"
    - question: 题目文本
    - options: 如果是选择题，提供 ["A选项", "B选项", "C选项", "D选项"]；其他题型为空数组
    - answer: 正确答案（选择题填 A/B/C/D，判断题填 "对"/"错"）
    - difficulty_score: 1-10 的整数，代表该题目的独立难度

    返回 JSON 格式：
    [
      {{
        "topic": "子知识点名称",
        "content": "学习内容",
        "questions": [
          {{ "type": "选择题", "question": "...", "options": ["A","B","C","D"], "answer": "A", "difficulty_score": 6 }}
        ]
      }}
    ]
    """
    # ====================================================

    try:
        from utils.volc_client import VolcClient
        client = VolcClient()
        response = client.chat([
            {"role": "system", "content": "你是学习规划专家，只返回 JSON 数据，不要添加任何额外文字。"},
            {"role": "user", "content": prompt}
        ], temperature=0.7)

        # 尝试从返回中提取 JSON 数组
        json_match = re.search(r'\[[\s\S]*\]', response)
        if json_match:
            tasks = json.loads(json_match.group())
            # 确保每个任务都有必要的字段
            for task in tasks:
                if not task.get("topic"):
                    task["topic"] = f"{keyword} - 子知识点"
                if not task.get("content"):
                    task["content"] = f"{task['topic']} 核心概念讲解"
                if not task.get("questions") or len(task.get("questions", [])) == 0:
                    task["questions"] = [
                        {"type": "选择题", "question": f"关于 {task['topic']}，以下说法正确的是？", "options": ["A. 正确描述", "B. 错误描述", "C. 不确定", "D. 以上都不是"], "answer": "A"}
                    ]
            print(f"✅ AI 生成成功，共 {len(tasks)} 个子知识点")
            return {"success": True, "data": {"tasks": tasks}}
        else:
            print("⚠️ AI 返回未找到 JSON 数组，使用降级方案")
            raise ValueError("未找到 JSON 数组")

    except Exception as e:
        print(f"❌ AI 生成失败: {str(e)}")
        # 降级方案：生成 3 个默认子知识点
        tasks = [
            {
                "topic": f"{keyword} - 基础概念",
                "content": f"{keyword} 基础概念是理解该学科的第一步，掌握核心定义与分类。",
                "questions": [
                    {"type": "选择题", "question": f"关于 {keyword} 基础概念，以下说法正确的是？", "options": ["A. 正确描述", "B. 错误描述", "C. 不确定", "D. 以上都不是"], "answer": "A"}
                ]
            },
            {
                "topic": f"{keyword} - 核心原理",
                "content": f"{keyword} 核心原理是学科的关键，理解其运行机制和逻辑。",
                "questions": [
                    {"type": "填空题", "question": f"{keyword} 的核心原理是____", "answer": ""}
                ]
            },
            {
                "topic": f"{keyword} - 应用实践",
                "content": f"{keyword} 应用实践将理论转化为实际能力，解决具体问题。",
                "questions": [
                    {"type": "判断题", "question": f"{keyword} 的应用实践非常重要。", "answer": "对"}
                ]
            }
        ]
        print(f"⚠️ 使用降级方案，生成 {len(tasks)} 个子知识点")
        return {"success": True, "data": {"tasks": tasks}, "warning": "使用默认任务"}


@router.post("/create")
async def create_plan(req: CreatePlanRequest):
    """创建学习规划"""
    print("=" * 50)
    print("🔍 收到创建规划请求")
    print(f"🔍 user_id: {req.user_id}")
    print(f"🔍 name: {req.name}")
    print(f"🔍 tasks 数量: {len(req.tasks)}")

    if not req.tasks:
        raise HTTPException(status_code=400, detail="任务列表不能为空")

    headers = get_supabase_headers()
    now = datetime.now().isoformat()

    plan_data = {
        "id": str(uuid.uuid4()),
        "user_id": req.user_id,
        "name": req.name,
        "stage": req.stage,
        "grade": req.grade,
        "major": req.major,
        "difficulty": req.difficulty,
        "daily_minutes": req.daily_minutes,
        "start_date": req.start_date,
        "end_date": req.end_date,
        "keywords": req.keywords,
        "status": "pending",
        "progress": 0,
        "created_at": now,
        "updated_at": now
    }

    async with httpx.AsyncClient() as client:
        url = f"{settings.SUPABASE_URL}/rest/v1/learning_plans"
        res = await client.post(url, headers=headers, json=plan_data)
        print(f"🔍 规划保存状态码: {res.status_code}")
        if res.status_code not in [200, 201]:
            print(f"❌ 创建规划失败: {res.text}")
            raise HTTPException(status_code=400, detail=f"创建规划失败: {res.text}")

        plan_id = plan_data["id"]

        for i, task in enumerate(req.tasks):
            task_data = {
                "id": str(uuid.uuid4()),
                "plan_id": plan_id,
                "user_id": req.user_id,
                "type": task.get("type", "做题"),
                "topic": task.get("topic", "基础知识点"),
                "description": task.get("description", ""),
                "question_count": task.get("question_count", 0),
                "question_type": task.get("question_type", ""),
                "question_content": task.get("question_content", ""),
                "options": task.get("options", []),
                "answer": task.get("answer", ""),
                "date": task.get("date", req.start_date),
                "status": "pending",
                "created_at": now,
                "updated_at": now
            }
            task_url = f"{settings.SUPABASE_URL}/rest/v1/learning_tasks"
            task_res = await client.post(task_url, headers=headers, json=task_data)
            if task_res.status_code not in [200, 201]:
                print(f"❌ 任务 {i+1} 保存失败: {task_res.text}")
                raise HTTPException(status_code=400, detail=f"任务保存失败: {task_res.text}")

        print(f"✅ 规划创建成功: {plan_id}")
        return {
            "success": True,
            "plan_id": plan_id,
            "message": "规划创建成功"
        }


@router.get("/list")
async def get_plans(user_id: str = Query(...)):
    headers = get_supabase_headers()
    url = f"{settings.SUPABASE_URL}/rest/v1/learning_plans?user_id=eq.{user_id}&order=created_at.desc"

    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            return {"plans": []}
        return {"plans": res.json()}


@router.get("/detail/{plan_id}")
async def get_plan_detail(plan_id: str):
    headers = get_supabase_headers()

    async with httpx.AsyncClient() as client:
        plan_url = f"{settings.SUPABASE_URL}/rest/v1/learning_plans?id=eq.{plan_id}"
        plan_res = await client.get(plan_url, headers=headers)
        if plan_res.status_code != 200 or not plan_res.json():
            raise HTTPException(status_code=404, detail="规划不存在")
        plan = plan_res.json()[0]

        task_url = f"{settings.SUPABASE_URL}/rest/v1/learning_tasks?plan_id=eq.{plan_id}&order=created_at.asc"
        task_res = await client.get(task_url, headers=headers)
        tasks = task_res.json() if task_res.status_code == 200 else []

        plan["tasks"] = tasks
        return plan


@router.put("/task/status")
async def update_task_status(req: UpdateTaskStatusRequest):
    headers = get_supabase_headers()
    url = f"{settings.SUPABASE_URL}/rest/v1/learning_tasks?id=eq.{req.task_id}"
    data = {
        "status": req.status,
        "updated_at": datetime.now().isoformat()
    }

    async with httpx.AsyncClient() as client:
        res = await client.patch(url, headers=headers, json=data)
        if res.status_code not in [200, 204]:
            raise HTTPException(status_code=400, detail="更新任务状态失败")
        return {"success": True}


@router.delete("/delete/{plan_id}")
async def delete_plan(plan_id: str):
    headers = get_supabase_headers()

    async with httpx.AsyncClient() as client:
        task_url = f"{settings.SUPABASE_URL}/rest/v1/learning_tasks?plan_id=eq.{plan_id}"
        await client.delete(task_url, headers=headers)

        plan_url = f"{settings.SUPABASE_URL}/rest/v1/learning_plans?id=eq.{plan_id}"
        res = await client.delete(plan_url, headers=headers)
        if res.status_code not in [200, 204]:
            raise HTTPException(status_code=400, detail="删除规划失败")
        return {"success": True}