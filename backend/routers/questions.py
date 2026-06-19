from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from config import settings
import httpx
from datetime import datetime
import json
import re

router = APIRouter(prefix="/questions", tags=["题目"])


# ========== 模型定义 ==========
class QuestionCreate(BaseModel):
    title: str
    question_type: str
    difficulty_score: float = 5.0
    category: str
    topic: str
    options: Optional[Dict[str, str]] = None
    answer: str
    explanation: Optional[str] = None
    hint: Optional[str] = None
    starter_code: Optional[str] = None
    test_cases: Optional[List[Dict]] = None
    source: str = "generated"
    parent_id: Optional[str] = None


class QuestionSetCreate(BaseModel):
    name: str
    description: Optional[str] = None
    set_type: str = "custom"


class QuestionSetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    question_ids: Optional[List[str]] = None


# ========== 解析函数 ==========
def extract_json_from_response(response: str) -> dict:
    """从 AI 返回中提取 JSON，只做最基础的清理"""
    # 去掉首尾空白
    text = response.strip()

    # 找到第一个 { 和最后一个 }
    start = text.find('{')
    end = text.rfind('}')

    if start == -1 or end == -1:
        raise ValueError("未找到 JSON 对象")

    json_str = text[start:end + 1]

    # 尝试解析
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"JSON 解析失败: {e}")
        print(f"问题字符串: {json_str[:500]}")
        raise ValueError(f"JSON 解析失败: {str(e)}")


# ========== 题目 CRUD ==========
@router.post("/create")
async def create_question(user_id: str, data: QuestionCreate):
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    question_data = {
        "user_id": user_id,
        "title": data.title,
        "question_type": data.question_type,
        "difficulty_score": data.difficulty_score,
        "category": data.category,
        "topic": data.topic,
        "options": data.options,
        "answer": data.answer,
        "explanation": data.explanation,
        "hint": data.hint,
        "starter_code": data.starter_code,
        "test_cases": data.test_cases,
        "source": data.source,
        "parent_id": data.parent_id
    }
    async with httpx.AsyncClient() as client:
        url = f"{settings.SUPABASE_URL}/rest/v1/questions"
        res = await client.post(url, headers=headers, json=question_data)
        if res.status_code not in [200, 201]:
            raise HTTPException(status_code=400, detail=f"创建题目失败: {res.text}")
        return res.json()


@router.get("/list/{user_id}")
async def list_questions(user_id: str, limit: int = 50):
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}"
    }
    url = f"{settings.SUPABASE_URL}/rest/v1/questions?user_id=eq.{user_id}&order=created_at.desc&limit={limit}"
    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        if res.status_code == 200:
            return res.json()
        return []


@router.get("/{question_id}")
async def get_question(question_id: str):
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}"
    }
    url = f"{settings.SUPABASE_URL}/rest/v1/questions?id=eq.{question_id}"
    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        if res.status_code == 200 and res.json():
            return res.json()[0]
        raise HTTPException(status_code=404, detail="题目不存在")


@router.delete("/{question_id}")
async def delete_question(question_id: str):
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}"
    }
    url = f"{settings.SUPABASE_URL}/rest/v1/questions?id=eq.{question_id}"
    async with httpx.AsyncClient() as client:
        res = await client.delete(url, headers=headers)
        if res.status_code in [200, 204]:
            return {"success": True}
        raise HTTPException(status_code=400, detail="删除失败")


# ========== 题集 CRUD ==========
@router.post("/set/create")
async def create_question_set(user_id: str, data: QuestionSetCreate):
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    set_data = {
        "user_id": user_id,
        "name": data.name,
        "description": data.description,
        "set_type": data.set_type,
        "question_ids": []
    }
    async with httpx.AsyncClient() as client:
        url = f"{settings.SUPABASE_URL}/rest/v1/question_sets"
        res = await client.post(url, headers=headers, json=set_data)
        if res.status_code not in [200, 201]:
            raise HTTPException(status_code=400, detail=f"创建题集失败: {res.text}")
        return res.json()


@router.get("/set/list/{user_id}")
async def list_question_sets(user_id: str):
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}"
    }
    url = f"{settings.SUPABASE_URL}/rest/v1/question_sets?user_id=eq.{user_id}&order=created_at.desc"
    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        if res.status_code == 200:
            return res.json()
        return []


@router.get("/set/{set_id}")
async def get_question_set(set_id: str):
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}"
    }
    url = f"{settings.SUPABASE_URL}/rest/v1/question_sets?id=eq.{set_id}"
    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        if res.status_code == 200 and res.json():
            return res.json()[0]
        raise HTTPException(status_code=404, detail="题集不存在")


@router.put("/set/{set_id}")
async def update_question_set(set_id: str, data: QuestionSetUpdate):
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    update_data = {}
    if data.name:
        update_data["name"] = data.name
    if data.description:
        update_data["description"] = data.description
    if data.question_ids is not None:
        update_data["question_ids"] = data.question_ids
    update_data["updated_at"] = datetime.now().isoformat()
    url = f"{settings.SUPABASE_URL}/rest/v1/question_sets?id=eq.{set_id}"
    async with httpx.AsyncClient() as client:
        res = await client.patch(url, headers=headers, json=update_data)
        if res.status_code in [200, 204]:
            return {"success": True}
        raise HTTPException(status_code=400, detail="更新失败")


@router.delete("/set/{set_id}")
async def delete_question_set(set_id: str):
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}"
    }
    url = f"{settings.SUPABASE_URL}/rest/v1/question_sets?id=eq.{set_id}"
    async with httpx.AsyncClient() as client:
        res = await client.delete(url, headers=headers)
        if res.status_code in [200, 204]:
            return {"success": True}
        raise HTTPException(status_code=400, detail="删除失败")


# ========== 题目加入题集 ==========
@router.post("/set/{set_id}/add/{question_id}")
async def add_question_to_set(set_id: str, question_id: str):
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}"
    }
    get_url = f"{settings.SUPABASE_URL}/rest/v1/question_sets?id=eq.{set_id}&select=question_ids"
    async with httpx.AsyncClient() as client:
        get_res = await client.get(get_url, headers=headers)
        if not get_res.json():
            raise HTTPException(status_code=404, detail="题集不存在")
        question_ids = get_res.json()[0].get("question_ids", [])
        if question_id not in question_ids:
            question_ids.append(question_id)
        update_url = f"{settings.SUPABASE_URL}/rest/v1/question_sets?id=eq.{set_id}"
        res = await client.patch(update_url, headers=headers, json={
            "question_ids": question_ids,
            "updated_at": datetime.now().isoformat()
        })
        if res.status_code in [200, 204]:
            return {"success": True}
        raise HTTPException(status_code=400, detail="添加失败")


@router.post("/set/{set_id}/remove/{question_id}")
async def remove_question_from_set(set_id: str, question_id: str):
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}"
    }
    get_url = f"{settings.SUPABASE_URL}/rest/v1/question_sets?id=eq.{set_id}&select=question_ids"
    async with httpx.AsyncClient() as client:
        get_res = await client.get(get_url, headers=headers)
        if not get_res.json():
            raise HTTPException(status_code=404, detail="题集不存在")
        question_ids = get_res.json()[0].get("question_ids", [])
        if question_id in question_ids:
            question_ids.remove(question_id)
        update_url = f"{settings.SUPABASE_URL}/rest/v1/question_sets?id=eq.{set_id}"
        res = await client.patch(update_url, headers=headers, json={
            "question_ids": question_ids,
            "updated_at": datetime.now().isoformat()
        })
        if res.status_code in [200, 204]:
            return {"success": True}
        raise HTTPException(status_code=400, detail="移除失败")


# ========== AI 生成题目 ==========
@router.post("/generate")
async def generate_question(data: dict):
    """AI 生成题目"""
    from utils.llm_client import call_llm

    user_id = data.get("user_id")
    category = data.get("category", "Python")
    topic = data.get("topic", "")
    question_type = data.get("question_type", "选择题")
    difficulty = data.get("difficulty", "中等")
    extra = data.get("extra", "")

    type_map = {
        "选择题": "choice",
        "填空题": "fill",
        "判断题": "judge",
        "简答题": "essay",
        "计算题": "calculation",
        "编程题": "coding"
    }
    q_type = type_map.get(question_type, "choice")

    type_instructions = {
        "选择题": "提供 4 个选项（A、B、C、D）",
        "填空题": "题目中留空（用 ____ 表示），只需提供正确答案",
        "判断题": "给出一个陈述，答案是'正确'或'错误'",
        "简答题": "给出开放性问题，提供参考答案要点",
        "编程题": "给出编程任务，提供 starter_code（初始代码模板）和 test_cases（测试用例）"
    }

    # 难度分数映射
    difficulty_map = {
        "简单": 2.0,
        "中等": 6.0,
        "困难": 8.5
    }
    difficulty_score = difficulty_map.get(difficulty, 6.0)

    prompt = f"""请生成 1 道 {difficulty} 难度的 {question_type} 题。

学科/领域：{category}
具体知识点：{topic}
{f"补充说明：{extra}" if extra else ""}

要求：
1. 题目清晰、准确
2. {type_instructions.get(question_type, '')}
3. 提供正确答案和详细解析
4. 这道题的难度固定为 {difficulty}，对应的 difficulty_score 为：简单=2.0，中等=6.0，困难=8.5，请使用 {difficulty_score} 作为 difficulty_score

5. 将用户输入的知识点 "{topic}" **归一化**为简洁的标准知识点名称：
   - 禁止直接复制用户输入
   - 提取核心关键词，去掉无关修饰词
   - 不要包含学科前缀（category 已经包含）
   - 示例："我想写列表相关的" → "列表操作"
   - 示例："装饰器" → "装饰器"
   - 示例："三角函数" → "三角函数"
   - 示例："Python集合" → "集合"
   - 最终名称必须在 2-6 个字之间

请只输出以下 JSON 格式，不要添加任何其他文字：

{{
    "title": "题目内容",
    "type": "{q_type}",
    "options": {{"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"}},
    "answer": "正确答案",
    "explanation": "详细解析",
    "hint": "解题提示（20字以内）",
    "difficulty_score": {difficulty_score},
    "category": "{category}",
    "topic": "{topic}",
    "normalized_topic": "归一化后的标准知识点名称"
}}"""

    try:
        response = call_llm([{"role": "user", "content": prompt}], temperature=0.7)
        print(f"=== AI 原始返回 ===\n{response}\n=== 结束 ===")

        # 提取 JSON
        try:
            result = extract_json_from_response(response)
        except ValueError as e:
            print(f"解析失败: {e}")
            raise HTTPException(status_code=500, detail=f"AI 返回格式错误: {str(e)}")

        # 确保字段存在
        if "title" not in result:
            result["title"] = "题目生成失败"
        if "type" not in result:
            result["type"] = q_type
        if "answer" not in result:
            result["answer"] = "请参考解析"
        if "explanation" not in result:
            result["explanation"] = "暂无解析"
        if "difficulty_score" not in result:
            result["difficulty_score"] = difficulty_score
        if "options" not in result:
            result["options"] = {}
        if "normalized_topic" not in result:
            result["normalized_topic"] = topic

        # 保存到数据库
        if user_id:
            print(f"=== 开始保存题目，user_id: {user_id} ===")
            headers = {
                "apikey": settings.SUPABASE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_KEY}",
                "Content-Type": "application/json"
            }
            question_data = {
                "user_id": user_id,
                "title": result.get("title"),
                "question_type": result.get("type"),
                "difficulty_score": result.get("difficulty_score", 5.0),
                "category": result.get("category"),
                "topic": result.get("topic"),
                "normalized_topic": result.get("normalized_topic"),  # 👈 新增
                "options": result.get("options"),
                "answer": result.get("answer"),
                "explanation": result.get("explanation"),
                "hint": result.get("hint"),
                "source": "generated"
            }
            print(f"=== 要保存的数据: {question_data} ===")

            # 添加 Prefer header 让 Supabase 返回插入的数据
            headers["Prefer"] = "return=representation"

            async with httpx.AsyncClient() as client:
                url = f"{settings.SUPABASE_URL}/rest/v1/questions"
                res = await client.post(url, headers=headers, json=question_data)
                print(f"=== 保存响应状态码: {res.status_code} ===")
                print(f"=== 保存响应内容: {res.text} ===")
                if res.status_code in [200, 201]:
                    try:
                        saved = res.json()
                        if isinstance(saved, list) and len(saved) > 0:
                            result["id"] = saved[0].get("id")
                        elif isinstance(saved, dict):
                            result["id"] = saved.get("id")
                        print(f"=== 保存成功，id: {result.get('id')} ===")
                    except Exception as e:
                        print(f"=== 解析响应失败: {e} ===")
                        # 如果响应为空，尝试查询
                        if user_id and result.get("title"):
                            query_url = f"{settings.SUPABASE_URL}/rest/v1/questions?user_id=eq.{user_id}&title=eq.{result.get('title')}&order=created_at.desc&limit=1"
                            query_res = await client.get(query_url, headers=headers)
                            if query_res.status_code == 200 and query_res.json():
                                result["id"] = query_res.json()[0].get("id")
                                print(f"=== 查询到的 id: {result['id']} ===")
                else:
                    print(f"保存题目失败: {res.text}")
                    raise HTTPException(status_code=400, detail=f"保存题目失败: {res.text}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        print(f"生成题目失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


# ========== AI 评估 ==========
@router.post("/evaluate")
async def evaluate_answer(data: dict):
    """评估用户答案"""
    from utils.llm_client import call_llm

    question = data.get("question", {})
    user_answer = data.get("user_answer", "")

    title = question.get("title", "")
    q_type = question.get("type", "choice")
    correct_answer = question.get("answer", "")
    explanation = question.get("explanation", "")

    prompt = f"""请评估用户的答题情况：

【题目】
{title}

【题型】{q_type}

【正确答案】
{correct_answer}

【用户答案】
{user_answer}

{f"【解析】{explanation}" if explanation else ""}

请只输出以下 JSON 格式：
{{
    "is_correct": true/false,
    "mastery_score": 85,
    "evaluation": "评估文字内容",
    "suggestion": "学习建议"
}}"""

    try:
        response = call_llm([{"role": "user", "content": prompt}], temperature=0.5)

        try:
            result = extract_json_from_response(response)
        except ValueError as e:
            raise HTTPException(status_code=500, detail=f"AI 返回格式错误: {str(e)}")

        if "is_correct" not in result:
            result["is_correct"] = False
        if "mastery_score" not in result:
            result["mastery_score"] = 50
        if "evaluation" not in result:
            result["evaluation"] = "评估完成"
        if "suggestion" not in result:
            result["suggestion"] = "继续练习"

        return result

    except HTTPException:
        raise
    except Exception as e:
        print(f"评估失败: {e}")
        raise HTTPException(status_code=500, detail=f"评估失败: {str(e)}")


# ========== 生成历史 ==========
@router.post("/history/save")
async def save_generation_history(data: dict):
    """保存生成历史"""
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    history_data = {
        "user_id": data.get("user_id"),
        "question_id": data.get("question_id"),
        "title": data.get("title"),
        "question_type": data.get("question_type"),
        "category": data.get("category"),
        "topic": data.get("topic"),
        "status": "pending"
    }
    async with httpx.AsyncClient() as client:
        url = f"{settings.SUPABASE_URL}/rest/v1/generation_history"
        res = await client.post(url, headers=headers, json=history_data)
        if res.status_code in [200, 201]:
            return {"success": True}
        return {"success": False}


@router.get("/history/{user_id}")
async def get_generation_history(user_id: str, limit: int = 50):
    """获取生成历史"""
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}"
    }
    url = f"{settings.SUPABASE_URL}/rest/v1/generation_history?user_id=eq.{user_id}&order=created_at.desc&limit={limit}"
    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        if res.status_code == 200:
            return res.json()
        return []