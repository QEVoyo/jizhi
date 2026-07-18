import sys
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from config import settings
import httpx
from datetime import datetime, timezone
import json
import re
from utils.sensitive_words import check_content_safety

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

    async with httpx.AsyncClient() as client:
        # 1. 先从 questions 表查
        url = f"{settings.SUPABASE_URL}/rest/v1/questions?id=eq.{question_id}"
        res = await client.get(url, headers=headers)
        if res.status_code == 200 and res.json():
            return res.json()[0]

        # 2. 从 generation_history 表按 id 查
        history_url = f"{settings.SUPABASE_URL}/rest/v1/generation_history?id=eq.{question_id}"
        history_res = await client.get(history_url, headers=headers)
        if history_res.status_code == 200 and history_res.json():
            history = history_res.json()[0]
            return {
                "id": history.get("id"),
                "title": history.get("title"),
                "question_content": history.get("title"),
                "question_type": history.get("question_type"),
                "category": history.get("category"),
                "topic": history.get("topic"),
                "difficulty_score": 5,
                "source": "generation_history"
            }

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

        # 如果响应为空，手动查询刚创建的题集
        if res.status_code == 201 and not res.text:
            get_url = f"{settings.SUPABASE_URL}/rest/v1/question_sets?user_id=eq.{user_id}&order=created_at.desc&limit=1"
            get_res = await client.get(get_url, headers=headers)
            if get_res.status_code == 200 and get_res.json():
                return get_res.json()[0]
            return {"success": True, "message": "题集已创建"}

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
    # ✅ 内容安全过滤
    topic = data.get("topic", "")
    extra = data.get("extra", "")

    if topic:
        safe, reason = check_content_safety(topic)
        if not safe:
            raise HTTPException(status_code=400, detail=f"知识点包含敏感信息：{reason}")

    if extra:
        safe, reason = check_content_safety(extra)
        if not safe:
            raise HTTPException(status_code=400, detail=f"补充说明包含敏感信息：{reason}")

    from agents.llm_client import call_llm
    import random

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
        "论述题": "essay",
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

    difficulty_map = {
        "简单": 2.0,
        "中等": 6.0,
        "困难": 8.5
    }
    difficulty_score = difficulty_map.get(difficulty, 6.0)

    angles = [
        "概念理解",
        "代码示例",
        "易错点辨析",
        "实际应用场景",
        "与其他概念的对比",
        "底层原理",
        "最佳实践",
        "常见面试题变形",
        "边界情况考察",
        "性能分析"
    ]
    angle = random.choice(angles)
    seed = random.randint(1, 10000)

    prompt = f"""请生成 1 道 {difficulty} 难度的 {question_type} 题。

学科/领域：{category}
具体知识点：{topic}
出题角度：{angle}
随机种子：{seed}
{f"补充说明：{extra}" if extra else ""}

要求：
1. 从「{angle}」这个角度出题，不要和之前的题目重复
2. 题目清晰、准确
3. {type_instructions.get(question_type, '')}
4. 提供正确答案和详细解析
5. 如果是选择题，选项要有迷惑性
6. 难度固定为 {difficulty}，difficulty_score 使用 {difficulty_score}
7. 将用户输入的知识点 "{topic}" 归一化为简洁的标准知识点名称：
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
        response = call_llm(
            [{"role": "user", "content": prompt}],
            temperature=0.9,
            use_cache=False
        )
        print(f"=== AI 原始返回 ===\n{response}\n=== 结束 ===")

        try:
            result = extract_json_from_response(response)
        except ValueError as e:
            print(f"解析失败: {e}")
            raise HTTPException(status_code=500, detail=f"AI 返回格式错误: {str(e)}")

        if "title" not in result:
            result["title"] = "题目生成失败"
        if "type" not in result:
            result["type"] = q_type
        result["question_type"] = result.get("type", q_type)
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
                "normalized_topic": result.get("normalized_topic"),
                "options": result.get("options"),
                "answer": result.get("answer"),
                "explanation": result.get("explanation"),
                "hint": result.get("hint"),
                "source": "generated"
            }
            print(f"=== 要保存的数据: {question_data} ===")

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
    print("=== evaluate_answer 被调用了 ===")  # 👈 加这行
    from agents.llm_client import call_llm
    from datetime import datetime

    question = data.get("question", {})
    user_answer = data.get("user_answer", "")
    user_id = data.get("user_id")

    title = question.get("title", "")
    q_type = question.get("question_type", "choice")
    correct_answer = question.get("answer", "")
    explanation = question.get("explanation", "")
    normalized_topic = question.get("normalized_topic", "")

    prompt = f"""请评估用户的答题情况，并提供详细的题目解析。

【题目】
{title}

【题型】{q_type}

【正确答案】
{correct_answer}

【用户答案】
{user_answer}

{f"【解析】{explanation}" if explanation else ""}

请输出以下 JSON 格式（不要添加任何其他文字）：

{{
    "is_correct": true/false,
    "mastery_score": 0-100 的整数,
    "evaluation": "一句话总结用户答得怎么样",
    "suggestion": "针对性的学习建议",
    "correct_answer": "正确答案（显示给用户看）",
    "detailed_analysis": "详细的题目解析，根据题型输出不同内容：选择题逐一分析每个选项为什么对/错；判断题说明为什么正确或错误；填空题说明正确答案及为什么填这个；简答题给出参考答案要点；计算题给出解题步骤和关键公式；编程题给出解题思路和代码要点",
    "knowledge_points": ["知识点1", "知识点2"]
}}"""

    try:
        response = call_llm([{"role": "user", "content": prompt}], temperature=0.5)
        print(f"=== AI 原始返回: {response} ===")  # 👈 加这行
        try:
            result = extract_json_from_response(response)
        except ValueError as e:
            raise HTTPException(status_code=500, detail=f"AI 返回格式错误: {str(e)}")

        # 确保所有字段存在
        if "is_correct" not in result:
            result["is_correct"] = False
        if "mastery_score" not in result:
            result["mastery_score"] = 50
        if "evaluation" not in result:
            result["evaluation"] = "评估完成"
        if "suggestion" not in result:
            result["suggestion"] = "继续练习"
        if "correct_answer" not in result:
            result["correct_answer"] = correct_answer or "无"
        if "detailed_analysis" not in result:
            result["detailed_analysis"] = "暂无详细解析"
        if "knowledge_points" not in result:
            result["knowledge_points"] = [normalized_topic] if normalized_topic else []

        # ====== 保存掌握度 + 错题本逻辑 ======
        if user_id and question.get("id"):
            headers = {
                "apikey": settings.SUPABASE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_KEY}",
                "Content-Type": "application/json"
            }
            question_id = question.get("id")
            mastery_score = result.get("mastery_score", 50)

            async with httpx.AsyncClient() as client:
                # 先查询当前错题状态
                check_url = f"{settings.SUPABASE_URL}/rest/v1/questions?id=eq.{question_id}&select=is_mistake,mistake_status"
                check_res = await client.get(check_url, headers=headers)
                current = check_res.json()[0] if check_res.json() else {}
                current_is_mistake = current.get('is_mistake', False)
                current_status = current.get('mistake_status', 'none')

                # 判断错题本逻辑
                if mastery_score < 60:
                    update_data = {
                        "mastery_score": mastery_score,
                        "is_mistake": True,
                        "mistake_status": "learning",
                        "mistake_added_at": datetime.now().isoformat()
                    }
                else:
                    if current_is_mistake and current_status == "learning":
                        update_data = {
                            "mastery_score": mastery_score,
                            "is_mistake": True,
                            "mistake_status": "conquered"
                        }
                    else:
                        update_data = {
                            "mastery_score": mastery_score,
                            "is_mistake": False,
                            "mistake_status": "none"
                        }

                update_url = f"{settings.SUPABASE_URL}/rest/v1/questions?id=eq.{question_id}"
                await client.patch(update_url, headers=headers, json=update_data)
                print(f"✅ 已更新掌握度: {mastery_score}%, 错题状态: {update_data.get('mistake_status')}")
        print(f"=== 评估结果完整返回: {result} ===")
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


@router.get("/mastery/{user_id}")
async def get_mastery_data(user_id: str):
    """获取用户所有知识点的掌握度（按 normalized_topic 聚合）"""
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}"
    }

    url = f"{settings.SUPABASE_URL}/rest/v1/questions?user_id=eq.{user_id}&select=normalized_topic,mastery_score"

    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            return []

        questions = res.json()

        # 按 normalized_topic 聚合
        topic_map = {}
        for q in questions:
            topic = q.get('normalized_topic')
            if not topic:
                continue
            if topic not in topic_map:
                topic_map[topic] = {'total': 0, 'count': 0}
            topic_map[topic]['total'] += q.get('mastery_score', 0)
            topic_map[topic]['count'] += 1

        result = []
        for topic, data in topic_map.items():
            avg = round(data['total'] / data['count']) if data['count'] > 0 else 0
            result.append({
                'topic': topic,
                'mastery_score': avg,
                'question_count': data['count']
            })

        # 按掌握度从低到高排序（0% 排最前面）
        result.sort(key=lambda x: x['mastery_score'])

        return result


# ========== 错题本 ==========
@router.get("/mistakes/{user_id}")
async def get_mistakes(user_id: str):
    """获取用户的错题本"""
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}"
    }

    # 获取所有错题
    url = f"{settings.SUPABASE_URL}/rest/v1/questions?user_id=eq.{user_id}&is_mistake=eq.true&order=created_at.desc"

    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        if res.status_code == 200:
            return res.json()
        return []


@router.post("/mistakes/conquer/{question_id}")
async def conquer_mistake(question_id: str):
    """标记错题为已攻克"""
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    update_url = f"{settings.SUPABASE_URL}/rest/v1/questions?id=eq.{question_id}"
    update_data = {
        "is_mistake": False,
        "mistake_status": "conquered"
    }

    async with httpx.AsyncClient() as client:
        res = await client.patch(update_url, headers=headers, json=update_data)
        if res.status_code in [200, 204]:
            return {"success": True}
        return {"success": False}