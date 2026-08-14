"""学科计划 — 考纲架构版本
每个考纲(syllabus)一个计划，题库/诊断/任务全在考纲下
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime, timedelta, timezone
import httpx, json, uuid, random, re
from pathlib import Path
from config import settings
from services.supabase import get_supabase_headers
from utils.auth_middleware import get_current_user, verify_user_match
from agents.llm_client import call_llm
from logging_config import logger
from local_question_bank import (
    query as bank_query,
    get_random as bank_random,
    count as bank_count,
    get_by_ids as bank_get_by_ids,
    has_bank,
    _banks,  # 用于跨考纲查题
)
from utils.code_runner import run_code, judge_test_case, LANGUAGE_LABELS, get_available_languages

router = APIRouter(prefix="/subject-plan", tags=["学科计划"])

# ===================== 考纲配置 =====================
_syllabi_file = Path(__file__).parent.parent / "data" / "syllabi.json"
SYLLABI = []
_syllabi_by_id = {}
try:
    with open(_syllabi_file, "r", encoding="utf-8") as f:
        SYLLABI = json.load(f)
    _syllabi_by_id = {s["id"]: s for s in SYLLABI}
    logger.info(f"已加载 {len(SYLLABI)} 个考纲")
except Exception as e:
    logger.warning(f"考纲配置加载失败: {e}")


# ===================== Pydantic 模型 =====================
class DiagnosisAnswer(BaseModel):
    question_id: str
    user_answer: Any
    time_spent: int = 0

class DiagnosisSubmit(BaseModel):
    user_id: str
    answers: List[DiagnosisAnswer]
    preferences: dict = {}

class AnswerSubmit(BaseModel):
    user_id: str
    plan_id: str
    question_id: str
    user_answer: Any
    source: str = "daily"
    task_id: Optional[str] = None
    time_spent: int = 0

class PlanUpdate(BaseModel):
    name: Optional[str] = None
    goal_score: Optional[int] = None
    daily_minutes: Optional[int] = None
    status: Optional[str] = None


# ==================== 辅助函数 ====================
def _normalize_choice(s: str) -> str:
    """把 'A' / 'A.' / 'A) ' 统一成 'A'"""
    s = str(s).strip()
    if s and s[0].upper() in "ABCDEFGH":
        return s[0].upper()
    return s.upper()


def _parse_choice_list(val) -> set:
    """解析多选答案 → {'A','B','C'}"""
    if isinstance(val, list):
        return {_normalize_choice(v) for v in val}
    s = str(val).strip().upper()
    # "AB" / "A,B" / "A、B" / "ABC"
    s = s.replace(",", "").replace("、", "").replace(" ", "")
    if all(c in "ABCDEFGH" for c in s):
        return set(s)
    return {s}


def _check_answer(user_answer, correct_answer, question_type: str) -> bool:
    """判断用户答案是否正确"""
    qt = (question_type or "").lower()

    # ---- 单选题 ----
    if qt in ("choice", "choice_single"):
        ua = _normalize_choice(user_answer)
        ca = _normalize_choice(correct_answer)
        return ua == ca

    # ---- 多选题 / 不定项 ----
    if qt in ("choice_multi", "choice_indefinite"):
        ua_set = _parse_choice_list(user_answer)
        ca_set = _parse_choice_list(correct_answer)
        return ua_set == ca_set

    # ---- 完形填空 ----
    if qt == "cloze":
        ua = str(user_answer).strip()
        if isinstance(correct_answer, list):
            return ua.lower() in [str(a).strip().lower() for a in correct_answer]
        return ua.lower() == str(correct_answer).strip().lower()

    # ---- 填空题 ----
    if qt == "fill":
        ua = str(user_answer).strip().lower()
        ca = str(correct_answer).strip().lower()
        return ua == ca

    # ---- 计算题 — 数值容差比较 ----
    if qt == "calculation":
        try:
            ua_num = float(str(user_answer).strip().replace(",", ""))
            ca_num = float(str(correct_answer).strip().replace(",", ""))
            return abs(ua_num - ca_num) < 1e-6 or ua_num == ca_num
        except (ValueError, TypeError):
            return str(user_answer).strip().lower() == str(correct_answer).strip().lower()

    # ---- 以下题型交给 AI 批改，自动判否 ----
    if qt in ("translation", "essay", "short_answer", "case_analysis",
              "teaching_design", "programming"):
        return False

    # 未知题型，宽松比较
    return str(user_answer).strip().lower() == str(correct_answer).strip().lower()


# AI 批改题型列表
AI_JUDGE_TYPES = {"translation", "essay", "short_answer", "case_analysis",
                  "teaching_design", "programming", "calculation", "analysis"}


def _calc_daily(period_days: int, daily_minutes: int) -> int:
    base = int((daily_minutes / 60) * 30)
    if period_days <= 30:
        base = int(base * 1.1)
    return max(10, min(60, base))


async def _get_done_ids(headers, plan_id, user_id) -> set:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{settings.SUPABASE_URL}/rest/v1/question_records?plan_id=eq.{plan_id}&user_id=eq.{user_id}&select=question_id"
            res = await client.get(url, headers=headers)
            return {r["question_id"] for r in (res.json() if res.status_code == 200 else [])}
    except Exception:
        return set()


async def _get_user_plan(syllabus_id: str, user_id: str) -> Optional[dict]:
    """获取用户在某个考纲下的活跃计划"""
    headers = get_supabase_headers()
    url = (
        f"{settings.SUPABASE_URL}/rest/v1/subject_plans"
        f"?syllabus_id=eq.{syllabus_id}&user_id=eq.{user_id}"
        f"&status=neq.archived&limit=1"
    )
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(url, headers=headers)
            data = res.json() if res.status_code == 200 else []
            return data[0] if data else None
    except Exception:
        return None


async def _get_plan_by_id(plan_id: str, user_id: str) -> Optional[dict]:
    """按 plan_id 获取计划（含 syllabus_id）"""
    headers = get_supabase_headers()
    url = f"{settings.SUPABASE_URL}/rest/v1/subject_plans?id=eq.{plan_id}&user_id=eq.{user_id}&limit=1"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(url, headers=headers)
            data = res.json() if res.status_code == 200 else []
            return data[0] if data else None
    except Exception:
        return None


# ====================================================================
# 1. 考纲列表
# ====================================================================
@router.get("/syllabi")
async def list_syllabi(user_id: str = Query("")):
    """列出所有考纲 + 该用户的计划（无需登录，计划查询失败时降级）"""
    plans_by_syllabus = {}
    if user_id:
        try:
            headers = get_supabase_headers()
            async with httpx.AsyncClient(timeout=10.0) as client:
                plan_url = (
                    f"{settings.SUPABASE_URL}/rest/v1/subject_plans"
                    f"?user_id=eq.{user_id}&status=neq.archived"
                    f"&select=id,syllabus_id,goal_score,period_days,daily_minutes,status,created_at"
                )
                plan_res = await client.get(plan_url, headers=headers)
                if plan_res.status_code == 200:
                    for p in (plan_res.json() or []):
                        sid = p.get("syllabus_id", "")
                        if sid not in plans_by_syllabus:
                            plans_by_syllabus[sid] = p
        except Exception:
            pass

    result = []
    for s in SYLLABI:
        plan = plans_by_syllabus.get(s["id"])
        result.append({
            "id": s["id"],
            "name": s["name"],
            "abbr": s.get("abbr", s["name"][:2]),
            "color": s.get("color", "#6c8cff"),
            "description": s["description"],
            "intro": s.get("intro", s.get("description", "")),
            "suitable_for": s.get("suitable_for", ""),
            "has_plan": plan is not None,
            "plan": {
                "id": plan["id"],
                "goal_score": plan.get("goal_score"),
                "period_days": plan.get("period_days"),
                "daily_minutes": plan.get("daily_minutes"),
                "status": plan.get("status"),
                "created_at": plan.get("created_at"),
            } if plan else None,
            "question_count": bank_count(s["id"]) if s.get("question_bank") else 0,
            "question_types": s.get("question_types", []),
            "question_types_enabled": s.get("question_types_enabled", s.get("question_types", [])),
            "dimensions": s.get("dimensions", []),
            "languages": s.get("languages", ["python"]),
            "target_count": s.get("target_count"),
            "max_score": s.get("max_score"),
            "pass_score": s.get("pass_score"),
            "exam_papers": s.get("exam_papers", []),
        })
    return {"syllabi": result}


# ====================================================================
# 2. 考纲详情（含计划、题库入口、诊断入口）
# ====================================================================
@router.get("/syllabi/{syllabus_id}")
async def get_syllabus_detail(
    syllabus_id: str,
    user_id: str = Query(""),
):
    """获取考纲详情 + 该用户的计划（无需登录）"""
    s = _syllabi_by_id.get(syllabus_id)
    if not s:
        raise HTTPException(status_code=404, detail="考纲不存在")

    plan = await _get_user_plan(syllabus_id, user_id) if user_id else None

    # 计划摘要
    plan_summary = None
    diagnosis = None
    if plan:
        plan_summary = {
            "id": plan["id"],
            "name": plan.get("name"),
            "goal_score": plan.get("goal_score"),
            "period_days": plan.get("period_days"),
            "daily_minutes": plan.get("daily_minutes"),
            "status": plan.get("status"),
            "created_at": plan.get("created_at"),
        }
        # 获取诊断结果
        headers = get_supabase_headers()
        diag_url = f"{settings.SUPABASE_URL}/rest/v1/diagnosis_results?plan_id=eq.{plan['id']}&limit=1"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                diag_res = await client.get(diag_url, headers=headers)
                diag_data = diag_res.json() if diag_res.status_code == 200 else []
                diagnosis = diag_data[0] if diag_data else None
        except Exception:
            pass

    return {
        "syllabus": {
            "id": s["id"],
            "name": s["name"],
            "abbr": s.get("abbr", s["name"][:2]),
            "color": s.get("color", "#6c8cff"),
            "description": s["description"],
            "intro": s.get("intro", s.get("description", "")),
            "suitable_for": s.get("suitable_for", ""),
            "dimensions": s.get("dimensions", []),
            "question_types": s.get("question_types", []),
            "question_types_enabled": s.get("question_types_enabled", s.get("question_types", [])),
            "has_question_bank": bool(s.get("question_bank")),
            "question_count": bank_count(syllabus_id) if s.get("question_bank") else 0,
            "languages": s.get("languages", ["python"]),
            "target_count": s.get("target_count"),
            "max_score": s.get("max_score"),
            "pass_score": s.get("pass_score"),
            "exam_papers": s.get("exam_papers", []),
        },
        "plan": plan_summary,
        "diagnosis": diagnosis,
    }


# ====================================================================
# 3. 题库查询（考纲下的题目浏览/搜索/筛选/分页）
# ====================================================================
@router.get("/syllabi/{syllabus_id}/questions")
async def get_syllabus_questions(
    syllabus_id: str,
    user_id: str = Query(""),
    category: str = Query(None),
    sub_category: str = Query(None),
    question_type: str = Query(None),
    difficulty: int = Query(None),
    search: str = Query(None),
    limit: int = Query(20),
    offset: int = Query(0),
    random_order: bool = Query(False),
):
    """考纲题库查询 — 纯内存操作，免登录"""
    s = _syllabi_by_id.get(syllabus_id)
    if not s:
        raise HTTPException(status_code=404, detail="考纲不存在")
    if not s.get("question_bank") or not has_bank(syllabus_id):
        raise HTTPException(status_code=400, detail="该考纲暂未配置题库")

    questions, total = bank_query(
        syllabus_id=syllabus_id,
        category=category,
        sub_category=sub_category,
        question_type=question_type,
        difficulty=difficulty,
        search=search,
        limit=limit,
        offset=offset,
        random_order=random_order,
    )
    return {"questions": questions, "total": total}


# ====================================================================
# 4. 诊断 - 获取题目
# ====================================================================
@router.get("/syllabi/{syllabus_id}/diagnosis/start")
async def start_diagnosis(syllabus_id: str):
    """从题库随机抽取诊断题目（无需鉴权）"""
    s = _syllabi_by_id.get(syllabus_id)
    if not s:
        raise HTTPException(status_code=404, detail="考纲不存在")

    config = s.get("diagnosis_config", [])
    if not config:
        raise HTTPException(status_code=400, detail="该考纲暂不支持诊断")

    questions = []
    for cfg in config:
        qs, _ = bank_query(
            syllabus_id=syllabus_id,
            category=cfg["category"],
            sub_category=cfg["sub"],
            question_type=cfg["type"],
            limit=cfg["count"] + 3,
            random_order=True,
        )
        questions.extend(qs[: cfg["count"]])

    random.shuffle(questions)
    return {
        "questions": questions,
        "total": len(questions),
        "dimensions": s.get("dimensions", []),
    }


# ====================================================================
# 5. 诊断 - 提交 → AI 批改 → 生成计划
# ====================================================================
@router.post("/syllabi/{syllabus_id}/diagnosis/submit")
async def submit_diagnosis(
    syllabus_id: str,
    data: DiagnosisSubmit,
    current_user: str = Depends(get_current_user),
):
    """提交诊断答案 → AI 批改 → 生成学习计划"""
    verify_user_match(data.user_id, current_user)
    s = _syllabi_by_id.get(syllabus_id)
    if not s:
        raise HTTPException(status_code=404, detail="考纲不存在")

    headers = get_supabase_headers()

    # ---- 0. 检查是否已有活跃计划，避免重复创建 ----
    existing_plan = await _get_user_plan(syllabus_id, data.user_id)
    if existing_plan:
        # 已有活跃计划，返回已有 plan_id（不重复创建）
        return {
            "plan_id": existing_plan["id"],
            "plan_name": existing_plan.get("name"),
            "accuracy": 0,
            "correct_count": 0,
            "total_count": 0,
            "already_exists": True,
        }

    # ---- 1. 获取诊断题目详情（按 ID 精确查） ----
    q_ids = [a.question_id for a in data.answers]
    questions = bank_get_by_ids(syllabus_id, q_ids)
    q_map = {q["id"]: q for q in questions}

    # ---- 2. AI 批改 ----
    answer_details = []
    correct_count = 0
    for ans in data.answers:
        q = q_map.get(ans.question_id)
        if not q:
            continue
        is_correct = _check_answer(ans.user_answer, q.get("answer"), q.get("question_type", ""))
        if is_correct:
            correct_count += 1
        answer_details.append({
            "question_id": ans.question_id,
            "stem": (q.get("content", {}) or {}).get("stem", "") if isinstance(q.get("content"), dict) else "",
            "category": q.get("category"),
            "sub_category": q.get("sub_category"),
            "question_type": q.get("question_type"),
            "user_answer": ans.user_answer,
            "correct_answer": q.get("answer"),
            "is_correct": is_correct,
        })

    accuracy = int(correct_count / len(data.answers) * 100) if data.answers else 0

    # ---- 3. AI 生成学习计划 ----
    prefs = data.preferences or {}
    goal_score = prefs.get("goal_score", 425)
    period_days = prefs.get("period_days", 30)
    daily_minutes = prefs.get("daily_minutes", 60)

    # 构建题型提示
    dim_names = ", ".join(d.get("name", d.get("category", "")) for d in s.get("dimensions", []))
    qtypes = ", ".join(s.get("question_types", []))

    plan_prompt = f"""
你是学习规划专家。根据以下诊断结果生成一个 {period_days} 天的 {s['name']} 备考计划：

- 考纲: {s['name']}
- 考察维度: {dim_names}
- 可用题型: {qtypes}
- 目标分数: {goal_score}
- 每天学习: {daily_minutes} 分钟
- 诊断正确率: {accuracy}%

诊断详情:
{json.dumps(answer_details, ensure_ascii=False, indent=2)}

请生成：
1. 计划名称（简短有力）
2. 每日任务列表 ({period_days} 天，每天 2-4 个任务)
3. 每个任务包含：标题、题型、题目数量、预计分钟数。题型必须从可用题型中选。

返回严格的 JSON，格式如下：
```json
{{
  "plan_name": "xxx",
  "daily_tasks": [
    {{
      "day_number": 1,
      "tasks": [
        {{"title": "xxx", "type": "choice", "category": "vocabulary", "question_count": 5, "minutes": 15}},
        ...
      ]
    }},
    ...
  ]
}}
```
"""
    plan_data = None
    try:
        ai_resp = call_llm([
            {"role": "system", "content": "你是学习规划专家。只能输出 JSON，不做说明。"},
            {"role": "user", "content": plan_prompt}
        ], temperature=0.7)
        # 提取代码块中的 JSON（```json ... ```）
        fence = re.search(r'```json\s*([\s\S]*?)```', ai_resp)
        raw = fence.group(1) if fence else ai_resp
        # 括号计数法提取 JSON（处理截断和嵌套）
        start = raw.find('{')
        if start >= 0:
            depth = 0
            in_str = False
            escape = False
            end = -1
            for i in range(start, len(raw)):
                ch = raw[i]
                if escape:
                    escape = False
                    continue
                if ch == '\\':
                    escape = True
                    continue
                if ch == '"':
                    in_str = not in_str
                    continue
                if not in_str:
                    if ch == '{':
                        depth += 1
                    elif ch == '}':
                        depth -= 1
                        if depth == 0:
                            end = i + 1
                            break
            if end > 0:
                candidate = raw[start:end]
                # 修复常见问题：尾逗号
                candidate = re.sub(r',\s*([}\]])', r'\1', candidate)
                try:
                    plan_data = json.loads(candidate)
                except json.JSONDecodeError as je:
                    # 尝试修复截断的 JSON：在第一个未闭合处截断
                    logger.warning(f"AI 计划 JSON 解析失败({je})，尝试修复")
                    # 简单修复：找最后一个完整的 } 结尾
                    trimmed = candidate
                    while trimmed:
                        try:
                            plan_data = json.loads(trimmed + '}')
                            break
                        except json.JSONDecodeError:
                            if '}' in trimmed:
                                trimmed = trimmed.rsplit('}', 1)[0]
                            else:
                                trimmed = ''
    except Exception as e:
        logger.error(f"AI 生成计划失败: {e}")

    # fallback: 简单默认计划
    if not plan_data:
        dims = s.get("dimensions", [])
        plan_data = {
            "plan_name": f"{s['name']} 备考计划",
            "daily_tasks": [
                {
                    "day_number": d + 1,
                    "tasks": [
                        {"title": f"{dim.get('name', '练习')}练习", "type": "choice",
                         "category": dim.get("category", ""), "question_count": 5, "minutes": 15}
                        for dim in dims[:3]
                    ] or [
                        {"title": "综合练习", "type": "choice", "category": "", "question_count": 5, "minutes": 15},
                    ]
                }
                for d in range(period_days)
            ]
        }

    # ---- 4. 写入 Supabase ----
    plan_id = str(uuid.uuid4())
    plan_name = (plan_data or {}).get("plan_name", f"{s['name']} 备考计划")
    now = datetime.now(timezone.utc).isoformat()
    end_date = (datetime.now(timezone.utc) + timedelta(days=period_days)).strftime("%Y-%m-%d")

    plan_row = {
        "id": plan_id,
        "syllabus_id": syllabus_id,
        "user_id": data.user_id,
        "name": plan_name,
        "subject": syllabus_id,
        "goal_score": goal_score,
        "period_days": period_days,
        "daily_minutes": daily_minutes,
        "status": "active",
        "created_at": now,
        "end_date": end_date,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            f"{settings.SUPABASE_URL}/rest/v1/subject_plans",
            headers=headers,
            json=plan_row
        )
        if r.status_code not in (200, 201):
            logger.error(f"创建计划失败: {r.status_code} {r.text}")
            raise HTTPException(status_code=500, detail="创建计划失败")

        # 写入诊断记录
        diag_row = {
            "id": str(uuid.uuid4()),
            "plan_id": plan_id,
            "user_id": data.user_id,
            "answers": json.dumps(answer_details, ensure_ascii=False),
            "accuracy": accuracy,
            "correct_count": correct_count,
            "total_count": len(data.answers),
            "created_at": now,
        }
        await client.post(
            f"{settings.SUPABASE_URL}/rest/v1/diagnosis_results",
            headers=headers,
            json=diag_row
        )

        # 写入每日任务
        daily_tasks = (plan_data or {}).get("daily_tasks", [])
        for day_block in daily_tasks:
            for task in day_block.get("tasks", []):
                task_row = {
                    "id": str(uuid.uuid4()),
                    "plan_id": plan_id,
                    "day_number": day_block["day_number"],
                    "title": task["title"],
                    "question_type": task.get("type", "choice"),
                    "category": task.get("category", ""),
                    "question_count": task.get("question_count", 5),
                    "estimated_minutes": task.get("minutes", 15),
                }
                await client.post(
                    f"{settings.SUPABASE_URL}/rest/v1/plan_daily_tasks",
                    headers=headers,
                    json=task_row
                )

    return {
        "plan_id": plan_id,
        "plan_name": plan_name,
        "accuracy": accuracy,
        "correct_count": correct_count,
        "total_count": len(data.answers),
    }


# ====================================================================
# 6. 计划详情（兼容旧路由 /{plan_id}）
# ====================================================================
@router.get("/plans/{plan_id}")
async def get_plan_detail(plan_id: str, user_id: str = Query(...), current_user: str = Depends(get_current_user)):
    """获取计划详情"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()
    url = f"{settings.SUPABASE_URL}/rest/v1/subject_plans?id=eq.{plan_id}&user_id=eq.{user_id}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200 or not res.json():
            raise HTTPException(status_code=404, detail="计划不存在")
        plan = res.json()[0]

        diag_url = f"{settings.SUPABASE_URL}/rest/v1/diagnosis_results?plan_id=eq.{plan_id}&limit=1"
        diag_res = await client.get(diag_url, headers=headers)
        diagnosis = diag_res.json()[0] if diag_res.status_code == 200 and diag_res.json() else None

        return {"plan": plan, "diagnosis": diagnosis}


@router.put("/plans/{plan_id}")
async def update_plan(plan_id: str, user_id: str = Query(...), data: PlanUpdate = None,
                      current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()
    url = f"{settings.SUPABASE_URL}/rest/v1/subject_plans?id=eq.{plan_id}&user_id=eq.{user_id}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        check = await client.get(url, headers=headers)
        if check.status_code != 200 or not check.json():
            raise HTTPException(status_code=404, detail="计划不存在")
        patch = {k: v for k, v in (data.model_dump() if data else {}).items() if v is not None}
        if patch:
            r = await client.patch(url, headers=headers, json=patch)
            return r.json()
        return check.json()


@router.delete("/plans/{plan_id}")
async def delete_plan(plan_id: str, user_id: str = Query(...), current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()
    deleted = {"tasks": 0, "diagnosis": 0, "records": 0, "mastery": 0}
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. 先删计划（验证存在且属于该用户）
        plan_url = f"{settings.SUPABASE_URL}/rest/v1/subject_plans?id=eq.{plan_id}&user_id=eq.{user_id}"
        plan_res = await client.delete(plan_url, headers=headers)
        if plan_res.status_code not in (200, 204):
            raise HTTPException(status_code=plan_res.status_code, detail="删除计划失败")

        # 2. 清理关联数据（尽力而为，失败不阻塞）
        for table, key in [
            ("plan_daily_tasks", "plan_id"),
            ("diagnosis_results", "plan_id"),
            ("question_records", "plan_id"),
            ("user_kp_mastery", "plan_id"),
        ]:
            try:
                r = await client.delete(
                    f"{settings.SUPABASE_URL}/rest/v1/{table}?{key}=eq.{plan_id}",
                    headers=headers
                )
                if r.status_code in (200, 204):
                    deleted[key] = r.json() if isinstance(r.json(), int) else 0
            except Exception as e:
                logger.warning(f"清理 {table} 失败: {e}")

        return {"message": "已删除", "cleaned": deleted}


# ====================================================================
# 7-8. 每日任务
# ====================================================================
@router.get("/plans/{plan_id}/tasks")
async def get_all_tasks(plan_id: str, user_id: str = Query(...), current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()
    url = f"{settings.SUPABASE_URL}/rest/v1/plan_daily_tasks?plan_id=eq.{plan_id}&order=day_number.asc"
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(url, headers=headers)
        return {"tasks": res.json() if res.status_code == 200 else []}


@router.get("/plans/{plan_id}/tasks/today")
async def get_today_tasks(plan_id: str, user_id: str = Query(...), current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()
    # 计算今天是计划的第几天
    plan_url = f"{settings.SUPABASE_URL}/rest/v1/subject_plans?id=eq.{plan_id}&select=created_at,period_days,syllabus_id"
    async with httpx.AsyncClient(timeout=30.0) as client:
        plan_res = await client.get(plan_url, headers=headers)
        if plan_res.status_code != 200 or not plan_res.json():
            raise HTTPException(status_code=404, detail="计划不存在")
        plan = plan_res.json()[0]
        created = datetime.fromisoformat(plan["created_at"].replace("Z", "+00:00"))
        day_number = (datetime.now(timezone.utc) - created).days + 1
        day_number = max(1, min(day_number, plan.get("period_days", 30)))

        sid = plan.get("syllabus_id", "")

        task_url = f"{settings.SUPABASE_URL}/rest/v1/plan_daily_tasks?plan_id=eq.{plan_id}&day_number=eq.{day_number}"
        task_res = await client.get(task_url, headers=headers)
        tasks = task_res.json() if task_res.status_code == 200 else []

        # 附上题目内容 — 按考纲题库查题，排除已做和已分配题目
        # 先获取已做题目 ID
        done_set = await _get_done_ids(headers, plan_id, user_id)
        used_ids = set(done_set)  # 排除已做过的题

        task_with_questions = []
        for t in tasks:
            qs, _ = bank_query(
                syllabus_id=sid,
                category=t.get("category") or None,
                question_type=t.get("question_type"),
                limit=t.get("question_count", 5),
                random_order=True,
                exclude_ids=used_ids,
            )
            # 记录本任务所用 ID，避免后续任务重复
            for qq in qs:
                used_ids.add(qq["id"])
            task_with_questions.append({**t, "questions": qs})

        return {"tasks": task_with_questions, "day_number": day_number}


class LearningContentRequest(BaseModel):
    user_id: str


@router.post("/plans/{plan_id}/tasks/{task_id}/generate-learning")
async def generate_task_learning(plan_id: str, task_id: str, data: LearningContentRequest,
                                 current_user: str = Depends(get_current_user)):
    """按需 AI 生成任务学习讲解（首次生成后缓存到任务记录）"""
    verify_user_match(data.user_id, current_user)
    headers = get_supabase_headers()

    # 1. 取任务 + 计划
    async with httpx.AsyncClient(timeout=30.0) as client:
        task_res = await client.get(
            f"{settings.SUPABASE_URL}/rest/v1/plan_daily_tasks?id=eq.{task_id}&limit=1",
            headers=headers)
        if task_res.status_code != 200 or not task_res.json():
            raise HTTPException(status_code=404, detail="任务不存在")
        task = task_res.json()[0]

        # 已有缓存直接返回
        if task.get("learning_content"):
            lc = task["learning_content"]
            if isinstance(lc, str):
                lc = json.loads(lc)
            return {"task_id": task_id, "learning_content": lc, "cached": True}

        plan_res = await client.get(
            f"{settings.SUPABASE_URL}/rest/v1/subject_plans?id=eq.{plan_id}&limit=1",
            headers=headers)
        if plan_res.status_code != 200 or not plan_res.json():
            raise HTTPException(status_code=404, detail="计划不存在")
        plan = plan_res.json()[0]
        sid = plan.get("syllabus_id", "")

        # 2. 取该任务的实际题目
        qs, _ = bank_query(
            syllabus_id=sid,
            category=task.get("category") or None,
            question_type=task.get("question_type"),
            limit=task.get("question_count", 5),
            random_order=True,
        )

        # 3. AI 生成学习讲解
        q_stems = []
        for q in qs[:min(len(qs), 5)]:
            content = q.get("content", {})
            if isinstance(content, str):
                try:
                    content = json.loads(content)
                except Exception:
                    content = {}
            stem = content.get("stem", "")[:150]
            kp = q.get("kp_name") or q.get("sub_category") or ""
            q_stems.append(f"- [{kp}] {stem}")

        prompt = f"""你是{_syllabi_by_id.get(sid, {}).get('name', '') if sid in _syllabi_by_id else ''}备考辅导老师。
为以下每日学习任务生成学习讲解内容：

任务：{task.get('title', '')}
知识点：{task.get('category', '')}
题型：{task.get('question_type', '')}
阶段：{task.get('phase', '')}

本任务题目预览：
{chr(10).join(q_stems) if q_stems else '（随机抽取）'}

请输出严格 JSON：
{{
  "summary": "本日学习目标概述（50字内）",
  "key_points": ["核心知识点1（含简短讲解）", "核心知识点2（含简短讲解）", "核心知识点3（含简短讲解）"],
  "methods": ["解题方法或技巧1", "解题方法或技巧2"],
  "common_mistakes": ["常见错误1", "常见错误2"]
}}"""

        from agents.llm_client import call_llm
        lc = None
        try:
            resp = call_llm([
                {"role": "system", "content": "你是备考辅导老师。只输出JSON，讲解通俗易懂。"},
                {"role": "user", "content": prompt}
            ], temperature=0.5)
            m = re.search(r'\{[\s\S]*\}', resp)
            if m:
                lc = json.loads(m.group())
        except Exception as e:
            logger.error(f"AI 生成学习讲解失败: {e}")

        if not lc:
            lc = {
                "summary": f"掌握{task.get('category', '')}相关知识点，完成{task.get('question_count', 5)}道{task.get('question_type', '')}练习",
                "key_points": ["理解题目考察的知识点", "注意审题和关键信息提取"],
                "methods": ["先复习相关知识点再做练习", "做完后对照解析总结错因"],
                "common_mistakes": ["粗心审题", "知识点混淆"],
            }

        # 4. 缓存到任务记录
        await client.patch(
            f"{settings.SUPABASE_URL}/rest/v1/plan_daily_tasks?id=eq.{task_id}",
            headers=headers,
            json={"learning_content": lc}
        )

        return {"task_id": task_id, "learning_content": lc, "cached": False}


@router.get("/plans/{plan_id}/done-ids")
async def get_done_question_ids(plan_id: str, user_id: str = Query(...), current_user: str = Depends(get_current_user)):
    """获取用户在该计划下已做过的所有题目 ID"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()
    url = f"{settings.SUPABASE_URL}/rest/v1/question_records?plan_id=eq.{plan_id}&user_id=eq.{user_id}&select=question_id&limit=5000"
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(url, headers=headers)
        records = res.json() if res.status_code == 200 else []
        ids = list({r["question_id"] for r in records})
        return {"ids": ids, "count": len(ids)}


@router.get("/plans/{plan_id}/question-states")
async def get_question_states(plan_id: str, user_id: str = Query(...), current_user: str = Depends(get_current_user)):
    """返回每道题的作答状态：总次数、正确次数、正确率"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()
    url = f"{settings.SUPABASE_URL}/rest/v1/question_records?plan_id=eq.{plan_id}&user_id=eq.{user_id}&select=question_id,is_correct&limit=5000"
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(url, headers=headers)
        records = res.json() if res.status_code == 200 else []
    states = {}
    for r in records:
        qid = r["question_id"]
        if qid not in states:
            states[qid] = {"total": 0, "correct": 0}
        states[qid]["total"] += 1
        if r.get("is_correct"):
            states[qid]["correct"] += 1
    # 计算掌握率
    result = {}
    for qid, s in states.items():
        rate = int(s["correct"] / s["total"] * 100) if s["total"] > 0 else 0
        # 分类：<40薄弱 40-60待巩固 >=60优势
        level = "weak" if rate < 40 else ("consolidating" if rate < 60 else "strong")
        result[qid] = {"total": s["total"], "correct": s["correct"], "rate": rate, "level": level}
    return {"states": result}


@router.get("/plans/{plan_id}/questions-count")
async def get_question_stats(plan_id: str, user_id: str = Query(...), current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()
    # 先取计划的 syllabus_id
    plan_url = f"{settings.SUPABASE_URL}/rest/v1/subject_plans?id=eq.{plan_id}&select=syllabus_id"
    total_q = 0
    async with httpx.AsyncClient(timeout=30.0) as client:
        plan_res = await client.get(plan_url, headers=headers)
        if plan_res.status_code == 200 and plan_res.json():
            sid = plan_res.json()[0].get("syllabus_id", "")
            total_q = bank_count(sid)

        url = f"{settings.SUPABASE_URL}/rest/v1/question_records?plan_id=eq.{plan_id}&user_id=eq.{user_id}&select=question_id,is_correct"
        res = await client.get(url, headers=headers)
        records = res.json() if res.status_code == 200 else []
        done = len(records)
        correct = sum(1 for r in records if r.get("is_correct"))
        return {"done": done, "correct": correct, "total": total_q,
                "accuracy": int(correct / done * 100) if done else 0}


# ====================================================================
# 8b. 按 ID 列表取题（做题页用）
# ====================================================================
@router.get("/questions/by-ids")
async def get_questions_by_ids(
    ids: str = Query(...),
    syllabus_id: str = Query(...),
    user_id: str = Query(""),
):
    """批量获取题目详情 — 题库本地存储，无需登录"""
    id_list = [i.strip() for i in ids.split(",") if i.strip()]
    questions = bank_get_by_ids(syllabus_id, id_list)
    return {"questions": questions}


# ====================================================================
# 9. 提交答案 → AI 批改 → 更新掌握度
# ====================================================================
@router.post("/plans/{plan_id}/submit")
async def submit_answer(plan_id: str, data: AnswerSubmit, current_user: str = Depends(get_current_user)):
    verify_user_match(data.user_id, current_user)
    headers = get_supabase_headers()
    now = datetime.now(timezone.utc).isoformat()

    # 先获取计划的 syllabus_id，再用精确 ID 查题
    plan = await _get_plan_by_id(plan_id, data.user_id)
    sid = plan.get("syllabus_id", "") if plan else ""

    q = None
    if sid:
        qs = bank_get_by_ids(sid, [data.question_id])
        q = qs[0] if qs else None

    is_correct = False
    ai_feedback = None

    if q:
        qtype = q.get("question_type", "")
        if qtype in AI_JUDGE_TYPES:
            # AI 批改题型：翻译/作文/简答/案例分析/编程等
            type_labels = {
                "translation": "翻译", "essay": "作文/论述", "short_answer": "简答",
                "case_analysis": "案例分析", "teaching_design": "教学设计",
                "programming": "编程", "calculation": "计算", "analysis": "论述分析"
            }
            type_label = type_labels.get(qtype, qtype)
            try:
                stem = (q.get("content", {}) or {}).get("stem", "")
                ref = q.get("answer", "")
                fb = call_llm([
                    {"role": "system", "content": f"你是{type_label}批改专家。严格打分，只输出 JSON。"},
                    {"role": "user", "content": f"""批改以下{type_label}题：
题目: {stem}
参考答案: {ref}
学生答案: {data.user_answer}

输出 JSON：
{{"score": 0-100, "is_pass": true/false, "feedback": "简短批改意见（50字内）", "highlights": ["亮点", "改进点"]}}
"""}
                ], temperature=0.3)
                m = re.search(r'\{[\s\S]*\}', fb)
                if m:
                    ai_feedback = json.loads(m.group())
                    is_correct = ai_feedback.get("is_pass", False)
            except Exception as e:
                logger.error(f"AI 批改失败 [{qtype}]: {e}")
                ai_feedback = {"score": 0, "is_pass": False, "feedback": "批改服务暂不可用"}
        else:
            is_correct = _check_answer(data.user_answer, q.get("answer"), qtype)

    # 写入答题记录
    record = {
        "id": str(uuid.uuid4()),
        "plan_id": plan_id,
        "user_id": data.user_id,
        "question_id": data.question_id,
        "user_answer": str(data.user_answer),
        "is_correct": is_correct,
        "source": data.source,
        "task_id": data.task_id,
        "time_spent": data.time_spent,
        "created_at": now,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        await client.post(f"{settings.SUPABASE_URL}/rest/v1/question_records", headers=headers, json=record)

    # 更新知识点掌握度（聚合：先查再 UPDATE / INSERT）
    if q:
        kp = q.get("kp_name") or q.get("sub_category", "")
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 查询是否已有该知识点的掌握度记录
                lookup_url = (
                    f"{settings.SUPABASE_URL}/rest/v1/user_kp_mastery"
                    f"?user_id=eq.{data.user_id}&plan_id=eq.{plan_id}&kp_name=eq.{kp}"
                    f"&limit=1"
                )
                lookup_res = await client.get(lookup_url, headers=headers)
                existing = (lookup_res.json() or []) if lookup_res.status_code == 200 else []

                if existing:
                    # 聚合更新
                    row = existing[0]
                    total_count = (row.get("total_count") or 0) + 1
                    correct_count = (row.get("correct_count") or 0) + (1 if is_correct else 0)
                    # mastery_score 用 EWMA：新分数 = 旧分数 * 0.7 + 本次结果 * 0.3
                    old_score = row.get("mastery_score") or 50
                    new_score = round(old_score * 0.7 + (100 if is_correct else 0) * 0.3, 1)
                    patch_url = (
                        f"{settings.SUPABASE_URL}/rest/v1/user_kp_mastery"
                        f"?id=eq.{row['id']}"
                    )
                    await client.patch(patch_url, headers=headers, json={
                        "total_count": total_count,
                        "correct_count": correct_count,
                        "mastery_score": new_score,
                        "last_practiced_at": now,
                        "updated_at": now,
                    })
                else:
                    # 首次插入
                    kp_row = {
                        "id": str(uuid.uuid4()),
                        "user_id": data.user_id,
                        "plan_id": plan_id,
                        "kp_name": kp,
                        "kp_id": q.get("kp_id") or kp,
                        "category": q.get("category"),
                        "sub_category": q.get("sub_category"),
                        "total_count": 1,
                        "correct_count": 1 if is_correct else 0,
                        "mastery_score": 70.0 if is_correct else 30.0,
                        "last_practiced_at": now,
                        "created_at": now,
                        "updated_at": now,
                    }
                    await client.post(
                        f"{settings.SUPABASE_URL}/rest/v1/user_kp_mastery",
                        headers=headers,
                        json=kp_row
                    )
        except Exception as e:
            logger.warning(f"更新掌握度失败: {e}")

    return {
        "is_correct": is_correct,
        "ai_feedback": ai_feedback,
        "correct_answer": q.get("answer") if q and q.get("question_type") not in ("translation", "essay") else None,
        "explanation": q.get("explanation") if q else None,
    }


# ====================================================================
# 10. 知识点掌握度
# ====================================================================
@router.get("/plans/{plan_id}/mastery")
async def get_mastery(plan_id: str, user_id: str = Query(...), current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()
    url = f"{settings.SUPABASE_URL}/rest/v1/user_kp_mastery?user_id=eq.{user_id}&plan_id=eq.{plan_id}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(url, headers=headers)
        return {"mastery": res.json() if res.status_code == 200 else []}


# ====================================================================
# 11-13. 错题本
# ====================================================================
@router.get("/plans/{plan_id}/mistakes")
async def get_mistakes(plan_id: str, user_id: str = Query(...),
                       limit: int = Query(50), offset: int = Query(0),
                       current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()

    # 先获取计划的 syllabus_id
    plan = await _get_plan_by_id(plan_id, user_id)
    sid = plan.get("syllabus_id", "") if plan else ""

    url = (
        f"{settings.SUPABASE_URL}/rest/v1/question_records"
        f"?plan_id=eq.{plan_id}&user_id=eq.{user_id}&is_correct=eq.false"
        f"&select=*&order=created_at.desc&limit={limit}&offset={offset}"
    )
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(url, headers=headers)
        records = res.json() if res.status_code == 200 else []

    # 按 ID 精确取题
    q_ids = list({r["question_id"] for r in records})
    questions = bank_get_by_ids(sid, q_ids) if sid else []
    q_map = {q["id"]: q for q in questions}
    result = []
    for r in records:
        q = q_map.get(r["question_id"])
        if q:
            result.append({**r, "question": q})
    return {"mistakes": result, "total": len(result)}


@router.get("/mistakes/overview")
async def get_mistakes_overview(user_id: str = Query(...), current_user: str = Depends(get_current_user)):
    """跨计划错题总览"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()
    url = (
        f"{settings.SUPABASE_URL}/rest/v1/question_records"
        f"?user_id=eq.{user_id}&is_correct=eq.false"
        f"&select=question_id,plan_id,created_at&order=created_at.desc&limit=200"
    )
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(url, headers=headers)
        records = res.json() if res.status_code == 200 else []
        from collections import Counter
        qid_counts = Counter(r["question_id"] for r in records)
        return {"total_mistakes": len(records), "unique_questions": len(qid_counts)}


@router.get("/mistakes/practice")
async def random_mistake_practice(user_id: str = Query(...), limit: int = Query(10),
                                  current_user: str = Depends(get_current_user)):
    """随机抽取错题练习 — 跨考纲"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()
    url = (
        f"{settings.SUPABASE_URL}/rest/v1/question_records"
        f"?user_id=eq.{user_id}&is_correct=eq.false"
        f"&select=question_id,plan_id&order=created_at.desc&limit=100"
    )
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(url, headers=headers)
        records = res.json() if res.status_code == 200 else []

    # 按 plan_id 分组 → 查每个考纲的题
    qids_by_plan = {}
    for r in records:
        pid = r.get("plan_id", "")
        if pid not in qids_by_plan:
            qids_by_plan[pid] = []
        qids_by_plan[pid].append(r["question_id"])

    # 收集所有唯一的 plan_id，批量获取 syllabus_id
    unique_pids = list({r.get("plan_id", "") for r in records})
    pid_to_sid = {}
    if unique_pids:
        # 批量查询所有 plan → syllabus_id 映射（单次请求）
        pid_filter = ",".join(f'"{p}"' for p in unique_pids)
        plans_url = (
            f"{settings.SUPABASE_URL}/rest/v1/subject_plans"
            f"?id=in.({pid_filter})&select=id,syllabus_id"
        )
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                plans_res = await client.get(plans_url, headers=headers)
                if plans_res.status_code == 200:
                    for p in (plans_res.json() or []):
                        pid_to_sid[p["id"]] = p.get("syllabus_id", "")
            except Exception:
                pass

    # 跨考纲查询题目（一次查所有）
    result = []
    for pid, qids in qids_by_plan.items():
        sid = pid_to_sid.get(pid, "")
        if sid:
            qs = bank_get_by_ids(sid, list(set(qids)))
            result.extend(qs)

    random.shuffle(result)
    return {"questions": result[:limit], "total": len(result[:limit])}


# ====================================================================
# 14. 代码提交 → 沙箱执行 → 测试点评分
# ====================================================================
@router.get("/code/languages")
async def get_languages():
    """返回可用语言列表（Python 始终可用）"""
    return {"languages": get_available_languages()}


class CodeRun(BaseModel):
    question_id: str = ""
    syllabus_id: str = ""
    language: str = "python"
    code: str
    input: str = ""


@router.post("/code/run")
async def run_code_endpoint(data: CodeRun):
    """运行代码（自定义输入）—— 沙箱执行，返回输出"""
    result = await run_code(data.language, data.code, data.input)
    return {
        "output": result.get("stdout", "") or result.get("stderr", ""),
        "exit_code": result.get("exit_code"),
        "timeout": result.get("timeout", False),
    }


class CodeSubmit(BaseModel):
    user_id: str = ""
    plan_id: str = ""
    question_id: str
    syllabus_id: str = ""
    language: str = "python"
    code: str
    source: str = "daily"
    task_id: Optional[str] = None


@router.post("/code/submit")
async def submit_code(data: CodeSubmit):
    """提交代码 → 沙箱执行 → 逐测试点评分，返回 AC/WA/TLE 等状态（无需登录）"""

    # 1. 查题目 — 直接用 syllabus_id 从本地题库查
    sid = data.syllabus_id
    q = None
    if sid:
        qs = bank_get_by_ids(sid, [data.question_id])
        q = qs[0] if qs else None
    if not q:
        raise HTTPException(status_code=404, detail="题目不存在")

    if q.get("question_type") != "programming":
        raise HTTPException(status_code=400, detail="该题目不是编程题")

    # 2. 获取测试用例 — 支持 JSON 和文本两种格式
    content = q.get("content", {})
    if isinstance(content, str):
        content_str = content
        try:
            content = json.loads(content)
        except Exception:
            content = {}
    else:
        content_str = json.dumps(content, ensure_ascii=False) if isinstance(content, dict) else str(content)

    test_cases = content.get("test_cases", []) if isinstance(content, dict) else []

    # 文本格式测试用例: ---TEST_CASES--- INPUT:... OUTPUT:... POINTS:... DESC:...
    if not test_cases and isinstance(content_str, str) and "---TEST_CASES---" in content_str:
        tc_section = content_str.split("---TEST_CASES---", 1)[1]
        tc_blocks = tc_section.strip().split("INPUT:")
        for block in tc_blocks:
            block = block.strip()
            if not block:
                continue
            tc = {"input": "", "expected_output": "", "points": 25, "description": ""}
            block = "INPUT:" + block
            for line in block.split("\n"):
                line = line.strip()
                if line.startswith("INPUT:"):
                    tc["input"] = line[6:].strip()
                elif line.startswith("OUTPUT:"):
                    tc["expected_output"] = line[7:].strip()
                elif line.startswith("POINTS:"):
                    try: tc["points"] = int(line[7:].strip())
                    except: pass
                elif line.startswith("DESC:"):
                    tc["description"] = line[5:].strip()
            if tc["input"]:
                test_cases.append(tc)

    # 如果没有测试用例，回退到 AI 批改
    if not test_cases:
        # 降级：用 AI 批改
        from agents.llm_client import call_llm
        ref = q.get("answer", "")
        stem = content.get("stem", "")
        try:
            fb = call_llm([
                {"role": "system", "content": "你是编程题批改专家。只输出 JSON。"},
                {"role": "user", "content": f"""批改以下编程题：
题目: {stem}
参考答案: {ref}
学生代码: {data.code}

输出 JSON：
{{"score": 0-100, "is_pass": true/false, "feedback": "简短意见（50字内）"}}
"""}
            ], temperature=0.3)
            m = re.search(r'\{[\s\S]*\}', fb)
            ai_feedback = json.loads(m.group()) if m else {"score": 0, "is_pass": False, "feedback": "批改失败"}
        except Exception:
            ai_feedback = {"score": 0, "is_pass": False, "feedback": "批改服务暂不可用"}

        is_correct = ai_feedback.get("is_pass", False)
        return {
            "is_correct": is_correct,
            "ai_feedback": ai_feedback,
            "has_test_cases": False,
            "language": data.language,
        }

    # 3. 逐测试点执行
    total_points = sum(tc.get("points", 10) for tc in test_cases)
    passed_points = 0
    test_results = []
    all_passed = True

    for i, tc in enumerate(test_cases):
        stdin = tc.get("input", "")
        expected = tc.get("expected_output", tc.get("expected", ""))
        points = tc.get("points", 10)
        desc = tc.get("description", f"测试点 {i + 1}")

        try:
            result = await run_code(
                lang=data.language,
                code=data.code,
                stdin=stdin,
                timeout_ms=tc.get("timeout_ms", 5000),
            )
        except Exception as e:
            result = {"stdout": "", "stderr": str(e), "exit_code": -1, "timeout": True}

        passed = False
        status = "WA"

        if result.get("timeout"):
            status = "TLE"
        elif result.get("exit_code", 0) != 0:
            status = "RE"
        elif judge_test_case(result.get("stdout", ""), expected):
            passed = True
            status = "AC"
            passed_points += points
        else:
            status = "WA"

        test_results.append({
            "index": i + 1,
            "description": desc,
            "status": status,
            "passed": passed,
            "points": points,
            "earned": points if passed else 0,
            "stdout": result.get("stdout", "")[:500],
            "stderr": result.get("stderr", "")[:500],
        })

        if not passed:
            all_passed = False

    score_pct = round(passed_points / total_points * 100) if total_points > 0 else 0
    is_correct = all_passed

    # 4. 记录答题
    headers = get_supabase_headers()
    now = datetime.now(timezone.utc).isoformat()
    record = {
        "id": str(uuid.uuid4()),
        "plan_id": data.plan_id,
        "user_id": data.user_id,
        "question_id": data.question_id,
        "user_answer": json.dumps({"language": data.language, "code": data.code[:2000]}, ensure_ascii=False),
        "is_correct": is_correct,
        "source": data.source,
        "task_id": data.task_id,
        "created_at": now,
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"{settings.SUPABASE_URL}/rest/v1/question_records",
                headers=headers, json=record
            )
    except Exception:
        pass

    return {
        "is_correct": is_correct,
        "score": score_pct,
        "passed_points": passed_points,
        "total_points": total_points,
        "test_results": test_results,
        "passed_count": sum(1 for t in test_results if t["passed"]),
        "total_count": len(test_results),
        "language": data.language,
        "has_test_cases": True,
        "supported_languages": content.get("languages", ["python"]),
    }
