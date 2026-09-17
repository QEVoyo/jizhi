import sys
import asyncio
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from config import settings
import httpx
from datetime import datetime, timezone
import json
import re
from utils.sensitive_words import check_content_safety
from utils.auth_middleware import get_current_user, verify_user_match
from services import video_gen
from logging_config import logger

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
        logger.info(f"JSON 解析失败: {e}")
        logger.info(f"问题字符串: {json_str[:500]}")
        raise ValueError(f"JSON 解析失败: {str(e)}")


# ========== 题目 CRUD ==========
@router.post("/create")
async def create_question(user_id: str, data: QuestionCreate, current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
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
async def list_questions(user_id: str, limit: int = 50, current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
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
async def create_question_set(user_id: str, data: QuestionSetCreate, current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
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
async def list_question_sets(user_id: str, current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
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


# ========== 出题提示词：题型轴 × 学科轴（2026-09-11 重构）==========
# 旧版用一套 JSON 模板套所有题型，实测后果：
#   判断题 / 计算题的 answer 被污染成选项字母 "A"（共用模板硬塞了 options）
#   编程题缺 starter_code / test_cases —— 模板里根本没有这两个字段，落库也不写
# 现在：题型决定「输出字段表 + 答案写法」，学科决定「语境纪律」，两轴组合。

TYPE_MAP = {
    "选择题": "choice",
    "填空题": "fill",
    "判断题": "judge",
    "简答题": "essay",
    "计算题": "calculation",
    "论述题": "essay",
    "编程题": "programming",   # 与题库同名，才能落进代码编辑器 + 沙箱判分链路
}

# 学科中性角度池；只有计算机/编程类知识点才用代码向角度
ANGLES_COMMON = [
    "概念理解", "易错点辨析", "实际应用场景", "与其他概念的对比",
    "典型例题", "边界与特例", "常见变形", "综合运用",
]
ANGLES_CS = [
    "概念理解", "代码示例", "易错点辨析", "实际应用场景",
    "底层原理", "最佳实践", "常见面试题变形", "边界情况考察", "性能分析",
]

QTYPE_SPECS = {
    "选择题": {
        "task": "出一道单选题：题干 + 4 个选项（A/B/C/D），有且只有一个正确答案，干扰项要有迷惑性",
        "answer_rule": "answer 只写选项字母（A/B/C/D 之一），不要写选项内容",
        "fields": '''    "options": {"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"},
    "answer": "B",''',
        "forbid": ["缺少 options", "选项少于 4 个", "answer 写成选项内容"],
    },
    "填空题": {
        "task": "出一道填空题：题干中用 ____ 标出空缺（可多处），每个空缺的答案必须唯一确定",
        "answer_rule": "answer 写填空处的答案本身（简短，不带任何说明文字）；多个空缺按顺序用 | 分隔",
        "fields": '''    "answer": "填空答案",''',
        "forbid": ["输出 options 字段", "answer 里重复题干"],
    },
    "判断题": {
        "task": "出一道判断题：题干是一个可明确判定对错的陈述句",
        "answer_rule": "answer 只能原样写「正确」或「错误」两个词之一",
        "fields": '''    "answer": "正确",''',
        "forbid": ["输出 options 字段", "answer 写成 A/B、True/False、√/×"],
    },
    "简答题": {
        "task": "出一道简答题：提问指向明确，能按要点作答",
        "answer_rule": "answer 写参考答案，分点陈述（用 1. 2. 3. 分行），覆盖全部得分点",
        "fields": '''    "answer": "1. 要点一\\n2. 要点二\\n3. 要点三",''',
        "forbid": ["输出 options 字段"],
    },
    "计算题": {
        "task": "出一道计算题：给出具体的数值/表达式条件，要求算出结果",
        "answer_rule": "answer 写完整计算过程（分步）+ 最终结果，不要只写一个字母或一个光秃秃的数",
        "fields": '''    "answer": "解：\\n第一步 …\\n第二步 …\\n所以答案是 …",''',
        "forbid": ["输出 options 字段", "answer 写成选项字母"],
    },
    "论述题": {
        "task": "出一道论述题：给出可展开论述的命题或材料",
        "answer_rule": "answer 写分点论述要点（用 1. 2. 3. 分行），体现论证层次",
        "fields": '''    "answer": "1. 论点一 …\\n2. 论点二 …",''',
        "forbid": ["输出 options 字段"],
    },
}

# 学科纪律：约束用词、例子与禁止项（编程概念只在计算机学科出现）
SUBJECT_DISCIPLINE = {
    "通用": "用该知识点所属学科的规范语言出题；例子必须来自本学科语境。",
    "数学": "数学语境：公式与符号用 LaTeX（$...$），给具体数值或表达式；严禁出现代码、编程、算法复杂度等计算机概念。",
    "语文": "语文语境：用文段、字词、文言、文学常识；严禁出现公式推导与代码。",
    "英语": "英语语境：题干可用英文，考语法/词汇/句式/语篇；严禁出现公式与代码。",
    "物理": "物理语境：给具体物理情境与已知量，单位规范；严禁出现代码。",
    "化学": "化学语境：用化学式、反应、实验现象；方程式配平要正确；严禁出现代码。",
    "生物": "生物语境：用生命现象、结构功能、遗传与生态；严禁出现代码。",
    "历史": "历史语境：用史实、年代、史料，题干可给材料；严禁出现公式与代码。",
    "政治": "政治语境：用原理、概念、时事材料，答案按原理+材料分析组织；严禁出现代码。",
    "地理": "地理语境：用区域、图表描述、成因分析；严禁出现代码。",
    "计算机": "计算机语境：允许代码、算法、复杂度、数据结构等概念，术语使用准确。",
}

COMMON_JSON_TEMPLATE = '''{{
    "title": "题目内容",
    "type": "{q_type}",
{type_fields}
    "explanation": "详细解析",
    "hint": "解题提示（20字以内）",
    "difficulty_score": 在 {diff_min}-{diff_max} 之间的数值,
    "category": "{category}",
    "topic": "{topic}",
    "normalized_topic": "归一化后的标准知识点名称"
}}'''

# 编程题：与 data/*_questions.json 种子题库同构，含 content 结构化字段与 test_cases，
# answer 必须是可直接运行的完整程序（函数 + 读入 + print），送来就能出结果
PROGRAMMING_JSON_TEMPLATE = '''{{
    "title": "完整题干：题目描述 + 输入格式 + 输出格式 + 数据范围（分行写全，学生直接读这段）",
    "type": "programming",
    "content": {{
        "stem": "纯题目描述（不含输入输出格式说明，不含解题思路）",
        "input_description": "输入格式说明",
        "output_description": "输出格式说明",
        "constraints": "数据范围（如 1 ≤ n ≤ 10^5）",
        "test_cases": [
            {{"input": "样例输入1", "output": "样例输出1", "description": "说明"}},
            {{"input": "样例输入2", "output": "样例输出2", "description": "说明"}},
            {{"input": "样例输入3", "output": "样例输出3", "description": "边界或较大规模用例"}}
        ]
    }},
    "starter_code": "初始代码模板：只含函数签名与读入框架 + TODO 注释，不含解题逻辑",
    "answer": "完整可运行的 Python3 参考程序：函数实现 + input() 读入 + print() 输出，直接运行就能得到正确答案",
    "explanation": "解题思路 + 时间复杂度分析",
    "hint": "解题提示（20字以内）",
    "difficulty_score": 在 {diff_min}-{diff_max} 之间的数值,
    "category": "{category}",
    "topic": "{topic}",
    "normalized_topic": "归一化后的标准知识点名称"
}}'''


PROGRAMMING_REPAIR_PROMPT = '''你上一次出的编程题，参考答案与测试用例对不上（下面是**真实运行**的结果，不是猜测）：

{details}

参考答案代码：
{code}

请修正后重新输出**完整**的题目 JSON：
- 若是代码错了就改正代码；若是期望输出算错了就改正期望输出
- 改完必须自洽：把参考答案在每个用例的输入上跑一遍，输出要与期望输出逐字符一致
- 大数取模、边界值（0、1、最大值）请逐步核对，不要心算

必须严格按下列 JSON 格式输出，字段名一字不差（test_cases 的键必须是 input/output/description）：

{schema}'''


QTYPE_LABELS = {
    "choice": "选择题", "fill": "填空题", "judge": "判断题",
    "essay": "简答题/论述题", "calculation": "计算题",
    "coding": "编程题", "programming": "编程题",
}

# 评估提示词：按题型给「批改重点 + 专属结构化字段」（2026-09-11 重构）
# 旧版所有题型共用一段 detailed_analysis 自由文本：选择题的逐项对错、计算题的分步得分
# 全被压平成一句话，前端拿不到结构，无法分块渲染；编程题的 is_correct 由 AI 拍脑袋定，
# 而有测试用例时本该由沙箱判定（该走 /subject-plan/code/submit）。
EVAL_SPECS = {
    "choice": {
        "focus": "先判定用户所选选项对错，再逐一分析 A/B/C/D 每个选项为什么对、为什么错",
        "extra": '    "option_analysis": {"A": "对/错 + 原因", "B": "对/错 + 原因", "C": "对/错 + 原因", "D": "对/错 + 原因"},\n',
    },
    "judge": {
        "focus": "判断用户答的「正确/错误」是否与标准答案一致，再说明这个陈述为什么对/错、常见误解在哪",
        "extra": "",
    },
    "fill": {
        "focus": "比对用户填写内容与标准答案；表述不同但语义等价应判对，并说明为什么等价",
        "extra": "",
    },
    "essay": {
        "focus": "按得分点逐条核对，明确指出用户答到了哪些、漏了哪些",
        "extra": '    "key_points": [{"point": "得分点内容", "hit": true}],\n',
    },
    "calculation": {
        "focus": "逐步核对解题过程，指出从哪一步开始出错（若出错）；公式与数值分别评价",
        "extra": '    "steps": [{"step": "这一步在做什么", "correct": true}],\n',
    },
    "programming": {
        "focus": "评价算法思路、正确性、边界处理与时间复杂度；有测试用例的编程题已由沙箱逐点判分，此处只做思路点评，不要推翻判分结果",
        "extra": "",
    },
}
EVAL_SPECS["coding"] = EVAL_SPECS["programming"]


def _normalize_test_cases(tcs) -> list:
    """测试用例键名归一：模型时常写成 expected/sample_output/stdin 等变体，
    不归一的话自检会把 'None' 当成期望输出，误判成永久不一致。"""
    out = []
    if not isinstance(tcs, list):
        return out
    for tc in tcs:
        if not isinstance(tc, dict):
            continue
        inp = tc.get("input", tc.get("stdin", tc.get("sample_input", "")))
        exp = tc.get("output", tc.get("expected", tc.get("expected_output", tc.get("sample_output", ""))))
        out.append({"input": inp, "output": exp,
                    "description": tc.get("description", tc.get("desc", ""))})
    return out


async def _verify_programming_question(result: dict, max_cases: int = 5):
    """编程题质检闸：用真沙箱把参考答案跑一遍它自带的测试用例。

    模型自算的期望值经常错（实测 17 条用例 4 条对不上，通过率 76%），
    光看 JSON 结构看不出来，必须真跑。返回 (是否全过, 不一致明细)。
    """
    from utils.code_runner import _run_python_local, judge_test_case

    code = (result.get("answer") or "").strip()
    content = result.get("content") if isinstance(result.get("content"), dict) else {}
    tcs = _normalize_test_cases(result.get("test_cases") or content.get("test_cases") or [])
    if not code or not tcs:
        return False, [{"case": 0, "reason": "缺 answer 或 test_cases"}]

    mismatches = []
    for i, tc in enumerate(tcs[:max_cases], 1):
        if not isinstance(tc, dict):
            continue
        stdin = str(tc.get("input", ""))
        expected = str(tc.get("output", "")).strip()
        # 本地 Python 执行是阻塞的 → 丢线程池，别卡事件循环
        run = await asyncio.to_thread(_run_python_local, code, stdin, 5)
        got = (run.get("stdout") or "").strip()
        if run.get("timeout"):
            mismatches.append({"case": i, "input": stdin, "expected": expected, "got": got, "reason": "运行超时"})
        elif run.get("exit_code") not in (0, None) and not got:
            mismatches.append({"case": i, "input": stdin, "expected": expected,
                               "got": (run.get("stderr") or "")[:200], "reason": "参考答案运行报错"})
        elif not judge_test_case(got, expected):
            mismatches.append({"case": i, "input": stdin, "expected": expected, "got": got})
    return (not mismatches), mismatches


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

    user_id = data.get("user_id")
    category = data.get("category", "通用")
    topic = data.get("topic", "")
    question_type = data.get("question_type", "选择题")
    difficulty = data.get("difficulty", "中等")
    extra = data.get("extra", "")

    return await generate_question_core(user_id, category, topic, question_type, difficulty, extra)


async def generate_question_core(user_id, category, topic, question_type, difficulty, extra):
    """生成 1 道题并落库（/questions/generate 端点与队友「出题卡」共用）。
    返回题目 dict（落库成功含 id）。"""
    from agents.llm_client import call_llm
    import random

    q_type = TYPE_MAP.get(question_type, "choice")
    spec = QTYPE_SPECS.get(question_type) or QTYPE_SPECS["选择题"]

    # 三档难度 → difficulty_score 区间（2026-08-30 用户定稿：按档生成区间内难度，而非固定值）
    difficulty_map = {
        "简单": (1.0, 3.0),
        "中等": (4.0, 6.0),
        "困难": (7.0, 10.0)
    }
    diff_min, diff_max = difficulty_map.get(difficulty, (4.0, 6.0))
    diff_mid = round((diff_min + diff_max) / 2, 1)

    # 学科轴：先用给定学科，未指定则由模型判定（判定结果写回 category）
    subject_known = bool(category) and category not in ("通用", "未分类", "通用学科")
    subject_discipline = SUBJECT_DISCIPLINE.get(category, "") if subject_known else ""
    if not subject_known:
        subject_discipline = """【学科自定·最高优先】学科未指定，你必须先判定该知识点属于哪门学科（数学/英语/语文/物理/化学/生物/历史/政治/地理/计算机），再严格在该学科语境下出题，并把判定结果写进 category 字段：
- 除非知识点本身明确属于编程（如"装饰器""列表推导式""递归函数""时间复杂度"），否则严禁出现 Python/代码/算法/复杂度等计算机概念
- "函数"按数学函数出题，"定语从句"按英语语法出题，"集合"按数学集合出题，不要默认编程
- 学科决定用词与例子：数学用公式与数值，英语用句子与语境，语文用文段，史政地用材料与史实"""

    # 角度池：计算机/编程类才用得上代码向角度，其余学科用学科中性角度（取代旧版「编程角度再转译」的补丁）
    is_cs = (category == "计算机") or any(k in topic for k in ("代码", "编程", "算法", "复杂度", "递归", "指针", "函数式"))
    angle = random.choice(ANGLES_CS if is_cs else ANGLES_COMMON)
    seed = random.randint(1, 10000)

    # 编程题：沿用题库既有 schema（content 结构化 + test_cases + 完整可跑 answer），
    # 使生成题与种子题库同构，能被代码编辑器与沙箱判分链路消费
    if q_type == "programming":
        json_template = PROGRAMMING_JSON_TEMPLATE.format(
            diff_min=diff_min, diff_max=diff_max, category=category, topic=topic
        )
    else:
        json_template = COMMON_JSON_TEMPLATE.format(
            type_fields=spec["fields"], q_type=q_type,
            diff_min=diff_min, diff_max=diff_max, category=category, topic=topic
        )

    prompt = f"""请生成 1 道 {difficulty} 难度的 {question_type} 题。

学科/领域：{category}
具体知识点：{topic}
出题角度：{angle}
随机种子：{seed}
{f"补充说明：{extra}" if extra else ""}

【题型要求·{question_type}】
{spec["task"]}
- 答案写法：{spec["answer_rule"]}
- 禁止：{"；".join(spec["forbid"])}

【学科纪律】
{subject_discipline or SUBJECT_DISCIPLINE["通用"]}

【通用要求】
1. 从「{angle}」这个角度出题，不要和之前的题目重复
2. 题目清晰、准确，不出现"本题考察""难度等级"这类元描述
3. 难度等级为 {difficulty}：根据所出题目的实际难易，在 {diff_min}–{diff_max} 区间内给出 difficulty_score（该等级里偏简单取区间下限附近，偏难取区间上限附近），不得超出区间
4. 将用户输入的知识点 "{topic}" 归一化为简洁的标准知识点名称：
   - 禁止直接复制用户输入；提取核心关键词，去掉无关修饰词；不要包含学科前缀
   - 示例："二次函数最值怎么求" → "二次函数最值"；"Python集合" → "集合"
   - 最终名称必须在 2-12 个字之间

请只输出以下 JSON 格式，不要添加任何其他文字：

{json_template}"""

    try:
        response = call_llm(
            [{"role": "user", "content": prompt}],
            temperature=0.9,
            use_cache=False
        )
        logger.info(f"=== AI 原始返回 ===\n{response}\n=== 结束 ===")

        try:
            result = extract_json_from_response(response)
        except ValueError as e:
            logger.info(f"解析失败: {e}")
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
        # 难度系数钳制：缺字段/非数值 → 档位中值；数值越界 → 收回到档位区间内（防 LLM 走样落库）
        try:
            score = float(result.get("difficulty_score"))
        except (TypeError, ValueError):
            score = None
        if score is None:
            result["difficulty_score"] = diff_mid
        elif score < diff_min or score > diff_max:
            result["difficulty_score"] = max(diff_min, min(diff_max, score))
        if "options" not in result:
            result["options"] = {}
        # 只有选择题该带 options——旧版共用模板给每道题都塞选项，把判断题/计算题的答案
        # 污染成了选项字母 "A"；这里按题型清一次，防止模型惯性输出
        if q_type != "choice":
            result["options"] = None
        if "normalized_topic" not in result:
            result["normalized_topic"] = topic

        # 编程题质检闸（2026-09-11）：模型自算的期望输出经常错，光校验 JSON 结构看不出来。
        # 真跑参考答案 → 不一致就带着实跑证据让模型修一次 → 仍不过如实报错，不把坏题落库。
        if q_type == "programming":
            ok, mismatches = await _verify_programming_question(result)
            repair_round = 0
            while not ok and repair_round < 2:
                repair_round += 1
                logger.info(f"编程题质检未过（第 {repair_round} 次修复）：{mismatches}")
                repair_prompt = PROGRAMMING_REPAIR_PROMPT.format(
                    details=json.dumps(mismatches, ensure_ascii=False, indent=1),
                    code=(result.get("answer") or "")[:1500],
                    schema=PROGRAMMING_JSON_TEMPLATE,
                )
                try:
                    fixed = extract_json_from_response(
                        call_llm([{"role": "user", "content": repair_prompt}], temperature=0.3, use_cache=False)
                    )
                except ValueError:
                    continue
                # 容错取字段：模型可能用 reference_solution/code 代替 answer 等
                answer_fix = fixed.get("answer") or fixed.get("reference_solution") or fixed.get("code")
                if answer_fix:
                    result["answer"] = answer_fix
                for k in ("title", "explanation", "hint", "starter_code"):
                    if fixed.get(k):
                        result[k] = fixed[k]
                fixed_tcs = _normalize_test_cases(fixed.get("test_cases"))
                if not fixed_tcs:
                    fixed_tcs = _normalize_test_cases((fixed.get("content") or {}).get("test_cases")
                                                      if isinstance(fixed.get("content"), dict) else None)
                if fixed_tcs:
                    result["test_cases"] = fixed_tcs
                    if isinstance(result.get("content"), dict):
                        result["content"]["test_cases"] = fixed_tcs
                result["type"] = "programming"
                result["question_type"] = "programming"
                ok, mismatches = await _verify_programming_question(result)
            if not ok:
                logger.info(f"编程题质检最终未过：{mismatches}")
                raise HTTPException(
                    status_code=502,
                    detail="编程题质检未通过：测试用例与参考答案不符，请重新生成",
                )

        if user_id:
            logger.info(f"=== 开始保存题目，user_id: {user_id} ===")
            headers = {
                "apikey": settings.SUPABASE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_KEY}",
                "Content-Type": "application/json"
            }
            # 编程题补全：题干取完整 title，test_cases 优先取 content 内的结构化数组
            q_content = result.get("content") if isinstance(result.get("content"), dict) else None
            q_test_cases = _normalize_test_cases(result.get("test_cases")) or \
                _normalize_test_cases(q_content.get("test_cases") if q_content else None) or None

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
                # 编程题字段（旧版落库时被整体丢弃 → 代码编辑器无模板、沙箱无判分用例）
                "starter_code": result.get("starter_code"),
                "test_cases": q_test_cases,
                "source": "generated"
            }
            logger.info(f"=== 要保存的数据: {question_data} ===")

            headers["Prefer"] = "return=representation"

            async with httpx.AsyncClient() as client:
                url = f"{settings.SUPABASE_URL}/rest/v1/questions"
                res = await client.post(url, headers=headers, json=question_data)
                logger.info(f"=== 保存响应状态码: {res.status_code} ===")
                logger.info(f"=== 保存响应内容: {res.text} ===")
                if res.status_code in [200, 201]:
                    try:
                        saved = res.json()
                        if isinstance(saved, list) and len(saved) > 0:
                            result["id"] = saved[0].get("id")
                        elif isinstance(saved, dict):
                            result["id"] = saved.get("id")
                        logger.info(f"=== 保存成功，id: {result.get('id')} ===")
                    except Exception as e:
                        logger.info(f"=== 解析响应失败: {e} ===")
                        if user_id and result.get("title"):
                            query_url = f"{settings.SUPABASE_URL}/rest/v1/questions?user_id=eq.{user_id}&title=eq.{result.get('title')}&order=created_at.desc&limit=1"
                            query_res = await client.get(query_url, headers=headers)
                            if query_res.status_code == 200 and query_res.json():
                                result["id"] = query_res.json()[0].get("id")
                                logger.info(f"=== 查询到的 id: {result['id']} ===")
                else:
                    logger.info(f"保存题目失败: {res.text}")
                    raise HTTPException(status_code=400, detail=f"保存题目失败: {res.text}")

        # 题入库即排视频（2026-09-04 定稿）：知识点级懒生成。
        # fire-and-forget：命中库直接复用零消耗；缺口后台排产，不阻塞出题返回
        try:
            subject = result.get("category") or "通用"
            kp_name = result.get("normalized_topic") or topic or ""
            if kp_name:
                nk = video_gen.make_knowledge_key(subject, kp_name)
                asyncio.create_task(video_gen.ensure_videos(nk, kp_name, subject=subject))
        except Exception as e:
            logger.info(f"视频排产失败（不影响出题）: {e}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.info(f"生成题目失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


# ========== AI 评估 ==========
@router.post("/evaluate")
async def evaluate_answer(data: dict):
    """评估用户答案"""
    logger.info("=== evaluate_answer 被调用了 ===")  # 👈 加这行
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

    spec = EVAL_SPECS.get(q_type, EVAL_SPECS["choice"])
    prompt = f"""请评估用户的答题情况，并提供详细的题目解析。

【题目】
{title}

【题型】{QTYPE_LABELS.get(q_type, q_type)}

【批改重点】{spec["focus"]}

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
    "detailed_analysis": "围绕上面的批改重点展开的详细解析",
{spec["extra"]}    "knowledge_points": ["知识点1", "知识点2"]
}}"""

    try:
        response = call_llm([{"role": "user", "content": prompt}], temperature=0.5)
        logger.info(f"=== AI 原始返回: {response} ===")  # 👈 加这行
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
                logger.info(f"✅ 已更新掌握度: {mastery_score}%, 错题状态: {update_data.get('mistake_status')}")
        logger.info(f"=== 评估结果完整返回: {result} ===")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.info(f"评估失败: {e}")
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
async def get_generation_history(user_id: str, limit: int = 50, current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
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
async def get_mastery_data(user_id: str, current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
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
async def get_mistakes(user_id: str, current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
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