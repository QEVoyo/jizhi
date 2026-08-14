"""CET-4 题库批量生成 — 调用 LLM 按知识点×题型×难度生成题目"""
from config import settings
from agents.llm_client import call_llm
import json
import httpx
from logging_config import logger

# ============================================================
# 知识点配置：CET-4 五维度 × 知识组
# ============================================================
CET4_KNOWLEDGE_POINTS = {
    "vocabulary": {
        "name": "词汇",
        "subs": [
            {"name": "高频核心词", "kps": [
                {"id": "voc-hf-abandon", "name": "abandon"},
                {"id": "voc-hf-absorb", "name": "absorb"},
                {"id": "voc-hf-abstract", "name": "abstract"},
                {"id": "voc-hf-abuse", "name": "abuse"},
                {"id": "voc-hf-accommodate", "name": "accommodate"},
            ]},
            {"name": "近义词辨析", "kps": [
                {"id": "voc-syn-affect-effect", "name": "affect vs effect"},
                {"id": "voc-syn-ensure-assure", "name": "ensure vs assure vs insure"},
                {"id": "voc-syn-rise-raise", "name": "rise vs raise vs arise"},
            ]},
            {"name": "固定搭配", "kps": [
                {"id": "voc-coll-take", "name": "take 短语搭配"},
                {"id": "voc-coll-make", "name": "make 短语搭配"},
            ]},
        ],
    },
    "grammar": {
        "name": "语法",
        "subs": [
            {"name": "时态语态", "kps": [
                {"id": "gra-tense-present-perfect", "name": "现在完成时"},
                {"id": "gra-tense-past-perfect", "name": "过去完成时"},
                {"id": "gra-tense-passive", "name": "被动语态"},
            ]},
            {"name": "虚拟语气", "kps": [
                {"id": "gra-subj-present", "name": "与现在事实相反"},
                {"id": "gra-subj-past", "name": "与过去事实相反"},
                {"id": "gra-subj-suggest", "name": "suggest类动词虚拟"},
            ]},
            {"name": "从句", "kps": [
                {"id": "gra-clause-attributive", "name": "定语从句"},
                {"id": "gra-clause-noun", "name": "名词性从句"},
            ]},
        ],
    },
    "reading": {
        "name": "阅读",
        "subs": [
            {"name": "快速阅读", "kps": [
                {"id": "read-skim-main-idea", "name": "主旨大意题"},
                {"id": "read-skim-detail", "name": "细节定位题"},
            ]},
            {"name": "选词填空", "kps": [
                {"id": "read-cloze-context", "name": "上下文线索"},
                {"id": "read-cloze-collocation", "name": "固定搭配判断"},
            ]},
        ],
    },
    "translation": {
        "name": "翻译",
        "subs": [
            {"name": "社会文化类", "kps": [
                {"id": "trans-social-festival", "name": "节日文化"},
                {"id": "trans-social-education", "name": "教育话题"},
            ]},
            {"name": "科技经济类", "kps": [
                {"id": "trans-tech-internet", "name": "互联网发展"},
                {"id": "trans-tech-env", "name": "环境保护"},
            ]},
        ],
    },
}

# 题型配置
QUESTION_TYPES = {
    "choice": "选择题（4个选项，1个正确答案）",
    "fill": "填空题（一句话中挖一个空，填写单词或短语）",
    "cloze": "选词填空（一篇短文×10个空，从15个备选词中选）",
    "translation": "汉译英（给出中文句子，翻译为英文）",
}

# 难度描述
DIFFICULTY_LEVELS = {
    1: "基础入门，考察最直接的知识点识别",
    2: "常规四级难度，需要理解后作答",
    3: "较难，需要综合分析或排除混淆项",
    4: "拔高难度，考察知识点的灵活运用和深层理解",
}


def generate_question(category: str, sub_name: str, kp: dict, question_type: str, difficulty: int) -> dict | None:
    """生成单道题目"""

    cat_name = CET4_KNOWLEDGE_POINTS[category]["name"]
    type_desc = QUESTION_TYPES[question_type]
    diff_desc = DIFFICULTY_LEVELS[difficulty]

    prompt = f"""你是一位英语四六级考试命题专家。请为英语四级考试（CET-4）生成一道题目。

【题目参数】
- 考察维度：{cat_name}（{sub_name}）
- 知识点：{kp['name']}
- 题型：{type_desc}
- 难度：{diff_desc}

【出题要求】
1. 题目内容必须贴近四级考试真题风格
2. 题干和选项必须语法正确，无中式英语
3. 如果是选择题，4个选项长度和信息量要相似，混淆项要有一定的合理性
4. 如果是选词填空，短文长度80-120词，备选词15个
5. 解析要详细：不仅要说明正确答案为什么对，还要说明每个错误选项为什么错

【输出格式】
严格按以下JSON格式输出，不要输出其他文字：
{{
  "stem": "题干的完整文字",
  "options": ["A. xxx", "B. xxx", "C. xxx", "D. xxx"],
  "answer": "正确答案（选择题写选项字母如B，填空题写单词，翻译题写英文句子，选词填空写对应编号）",
  "explanation": "详细解析（100-200字）：正确选项的原因 + 各错误选项的排除理由",
  "distractor_analysis": {{"A": "为什么这个选项有迷惑性但不对", "B": "...", "C": "...", "D": "..."}}
}}

注意：
- 选择题必须在options中包含答案
- 填空题的answer是填入的单词/短语
- 翻译题的stem是中文，answer是英文译文
- 选词填空的options包含15个备选词，answer是每个空对应的词编号
"""

    for attempt in range(3):
        try:
            resp = call_llm([{"role": "user", "content": prompt}], temperature=0.8)
            # 提取 JSON
            resp = resp.strip()
            if resp.startswith("```"):
                parts = resp.split("```")
                resp = parts[1] if len(parts) > 1 else resp
                if resp.startswith("json"):
                    resp = resp[4:]
            content = json.loads(resp)
            return content
        except Exception as e:
            logger.info(f"生成题目失败 (attempt {attempt+1}): {e}")
            continue

    return None


async def batch_generate_and_save(target_count: int = 500):
    """
    批量生成题目并存入 Supabase。
    每个知识点 × 每种题型 × 2个难度 ≈ 大量题目
    """
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }

    total_generated = 0
    errors = 0

    for category, cat_data in CET4_KNOWLEDGE_POINTS.items():
        for sub in cat_data["subs"]:
            for kp in sub["kps"]:
                for q_type, q_desc in QUESTION_TYPES.items():
                    # 部分知识点不适合某些题型
                    if category == "reading" and q_type == "translation":
                        continue
                    if category == "translation" and q_type == "choice":
                        continue
                    if category == "vocabulary" and q_type == "cloze":
                        continue

                    for difficulty in [1, 2]:
                        if total_generated >= target_count:
                            logger.info(f"已达到目标题量 {target_count}，停止生成")
                            return total_generated

                        logger.info(
                            f"生成: {cat_data['name']}/{sub['name']}/{kp['name']} "
                            f"题型={q_type} 难度={difficulty}"
                        )

                        content = generate_question(category, sub["name"], kp, q_type, difficulty)

                        if content:
                            q_data = {
                                "category": category,
                                "sub_category": sub["name"],
                                "kp_id": kp["id"],
                                "kp_name": kp["name"],
                                "question_type": q_type,
                                "difficulty": difficulty,
                                "content": content,
                                "answer": content.get("answer", ""),
                                "explanation": content.get("explanation", ""),
                                "distractor_analysis": content.get("distractor_analysis"),
                            }

                            async with httpx.AsyncClient(timeout=30.0) as client:
                                res = await client.post(
                                    f"{settings.SUPABASE_URL}/rest/v1/cet4_questions",
                                    headers=headers, json=q_data
                                )
                                if res.status_code in [200, 201]:
                                    total_generated += 1
                                    logger.info(f"[OK] [{total_generated}/{target_count}]")
                                else:
                                    errors += 1
                                    logger.info(f"[FAIL] save error: {res.status_code} {res.text[:100]}")

    logger.info(f"Generation done! Success: {total_generated}, Failed: {errors}")
    return total_generated


# ============================================================
# 快捷入口：在 Python shell 中运行
# import asyncio
# from services.cet4_generator import batch_generate_and_save
# asyncio.run(batch_generate_and_save(target_count=500))
# ============================================================
