"""
CET-4 题库种子脚本 — 用 AI 批量生成分类真题并写入 Supabase
运行: cd backend && python scripts/seed_cet4_questions.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import uuid
import httpx
from config import settings
from utils.volc_client import VolcClient
from logging_config import logger

# Supabase 配置
HEADERS = {
    "apikey": settings.SUPABASE_KEY,
    "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_KEY}",
    "Content-Type": "application/json",
}
SUPABASE_URL = settings.SUPABASE_URL
TABLE_URL = f"{SUPABASE_URL}/rest/v1/cet4_questions"

# ============================================================
# 题库生成计划：分类 + 数量 + 题型
# ============================================================
QUESTION_PLAN = [
    # === 词汇 (vocabulary) ===
    {"category": "vocabulary", "sub_category": "高频核心词", "question_type": "choice", "count": 12, "difficulty_range": [2, 5]},
    {"category": "vocabulary", "sub_category": "近义词辨析", "question_type": "choice", "count": 10, "difficulty_range": [3, 6]},
    {"category": "vocabulary", "sub_category": "固定搭配", "question_type": "fill", "count": 8, "difficulty_range": [2, 5]},
    {"category": "vocabulary", "sub_category": "词义辨析", "question_type": "choice", "count": 8, "difficulty_range": [3, 7]},

    # === 语法 (grammar) ===
    {"category": "grammar", "sub_category": "时态语态", "question_type": "choice", "count": 12, "difficulty_range": [2, 6]},
    {"category": "grammar", "sub_category": "虚拟语气", "question_type": "choice", "count": 8, "difficulty_range": [3, 7]},
    {"category": "grammar", "sub_category": "从句", "question_type": "choice", "count": 10, "difficulty_range": [3, 7]},
    {"category": "grammar", "sub_category": "非谓语动词", "question_type": "choice", "count": 8, "difficulty_range": [4, 8]},
    {"category": "grammar", "sub_category": "倒装强调", "question_type": "choice", "count": 6, "difficulty_range": [3, 7]},

    # === 阅读 (reading) ===
    {"category": "reading", "sub_category": "快速阅读", "question_type": "choice", "count": 10, "difficulty_range": [3, 6]},
    {"category": "reading", "sub_category": "仔细阅读", "question_type": "choice", "count": 8, "difficulty_range": [4, 8]},
    {"category": "reading", "sub_category": "选词填空", "question_type": "cloze", "count": 6, "difficulty_range": [4, 7]},

    # === 翻译 (translation) ===
    {"category": "translation", "sub_category": "社会文化类", "question_type": "translation", "count": 6, "difficulty_range": [3, 7]},
    {"category": "translation", "sub_category": "科技教育类", "question_type": "translation", "count": 6, "difficulty_range": [3, 7]},
    {"category": "translation", "sub_category": "经济发展类", "question_type": "translation", "count": 5, "difficulty_range": [3, 7]},
]

TOTAL = sum(p["count"] for p in QUESTION_PLAN)


def build_prompt(plan: dict, batch_size: int) -> str:
    """根据分类构建生成 prompt"""
    cat_name = {
        "vocabulary": "词汇与语法", "grammar": "语法结构",
        "reading": "阅读理解", "translation": "翻译"
    }.get(plan["category"], plan["category"])

    type_desc = {
        "choice": "选择题（4个选项A/B/C/D，只有一个正确答案）",
        "fill": "填空题（留空让学生填单词或短语）",
        "cloze": "选词填空题（给一篇短文，挖掉几个词，提供候选词列表让学生选择填入。格式：content.stem 为短文全文，用 ______(数字) 标记空格位置，content.options 为候选词列表）",
        "translation": "翻译题（给一句中文，让学生翻译成英文）"
    }.get(plan["question_type"], plan["question_type"])

    diff_min, diff_max = plan["difficulty_range"]

    return f"""你是大学英语四级(CET-4)真题出题专家。请生成 {batch_size} 道 CET-4 {cat_name} 真题。

要求：
- 题型：{type_desc}
- 子分类：{plan['sub_category']}
- 难度：{diff_min}-{diff_max}（满分10，CET-4 真题难度在 2-7 之间）
- 题目必须是 CET-4 真实考试风格，贴合 {plan['sub_category']} 知识点
- 每道题必须提供详细的答案解析（中文）

返回 JSON 数组格式：
[
  {{
    "category": "{plan['category']}",
    "sub_category": "{plan['sub_category']}",
    "kp_name": "具体知识点名称（如'定语从句关系代词'）",
    "kp_id": "英文知识ID（如'relative-pronoun'）",
    "question_type": "{plan['question_type']}",
    "difficulty": 4,
    "content": {{
      "stem": "题目文本...",
      "options": ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"]
    }},
    "answer": "A",
    "explanation": "详细解析：为什么选A，为什么不选其他选项。考点是...",
    "tags": ["CET-4", "{plan['category']}", "{plan['sub_category']}"]
  }},
  ...
]

注意：
- 选择题 content.options 必须是 4 个选项的数组
- 填空题 content.options 为空数组 []
- 翻译题 content.options 为空数组，answer 为参考译文
- 选词填空 content.options 为候选词列表，content.stem 中用 ______1、______2 标记空格
- 只返回 JSON 数组，不要额外文字。"""


def parse_ai_response(text: str) -> list:
    """从 AI 返回文本中提取 JSON 数组"""
    text = text.strip()
    # 去掉 markdown 代码块
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:]) if lines[0].startswith("```") else text
        if text.endswith("```"):
            text = text[:-3]
    # 找到 JSON 数组
    import re
    match = re.search(r'\[[\s\S]*\]', text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return []


def validate_question(q: dict) -> bool:
    """校验题目格式"""
    required = ["category", "sub_category", "question_type", "difficulty", "content", "answer"]
    for field in required:
        if field not in q:
            logger.info(f"  缺少字段: {field}")
            return False
    if not isinstance(q.get("content"), dict):
        logger.info(f"  content 不是 dict")
        return False
    if "stem" not in q["content"]:
        logger.info(f"  content 缺 stem")
        return False
    if q.get("question_type") == "choice" and not isinstance(q["content"].get("options"), list):
        logger.info(f"  选择题缺 options")
        return False
    if not q.get("explanation"):
        q["explanation"] = ""  # 允许空解析
    if not q.get("kp_name"):
        q["kp_name"] = q.get("sub_category", "")
    if not q.get("kp_id"):
        q["kp_id"] = q.get("sub_category", "").lower().replace(" ", "-")
    if not q.get("tags"):
        q["tags"] = ["CET-4", q.get("category", ""), q.get("sub_category", "")]
    return True


async def insert_questions(questions: list) -> int:
    """批量写入 Supabase，每条单独插入"""
    count = 0
    async with httpx.AsyncClient(timeout=30.0) as client:
        for q in questions:
            # 清理字段
            record = {
                "category": q["category"],
                "sub_category": q["sub_category"],
                "kp_name": q.get("kp_name", q["sub_category"]),
                "kp_id": q.get("kp_id", q["sub_category"].lower().replace(" ", "-")),
                "question_type": q["question_type"],
                "difficulty": int(q.get("difficulty", 5)),
                "content": json.dumps(q["content"], ensure_ascii=False),
                "answer": json.dumps(q.get("answer", ""), ensure_ascii=False) if isinstance(q.get("answer"), (dict, list)) else json.dumps(str(q.get("answer", ""))),
                "explanation": q.get("explanation", ""),
            }
            # 处理 answer：choice 存纯字符串，其他保持原样
            if isinstance(record["answer"], str) and record["question_type"] != "choice":
                record["answer"] = record["answer"]
            elif not isinstance(record["answer"], str):
                record["answer"] = json.dumps(record["answer"], ensure_ascii=False)

            try:
                res = await client.post(TABLE_URL, headers=HEADERS, json=record)
                if res.status_code in [200, 201]:
                    count += 1
                else:
                    logger.info(f"  插入失败 [{res.status_code}]: {res.text[:100]}")
            except Exception as e:
                logger.info(f"  网络错误: {e}")
    return count


async def main():
    client = VolcClient()
    total_inserted = 0
    total_planned = sum(p["count"] for p in QUESTION_PLAN)

    print(f"\n{'='*60}")
    print(f"  CET-4 题库种子脚本")
    print(f"  计划生成: {total_planned} 题 | {len(QUESTION_PLAN)} 个分类")
    print(f"{'='*60}\n")

    for i, plan in enumerate(QUESTION_PLAN):
        cat = plan["category"]
        sub = plan["sub_category"]
        qtype = plan["question_type"]
        count = plan["count"]

        print(f"[{i+1}/{len(QUESTION_PLAN)}] {cat}/{sub} ({qtype}) × {count} ...", end=" ", flush=True)

        # 分批次调用 AI（每批最多8题，保证质量）
        batch_size = min(count, 8)
        batches_needed = (count + batch_size - 1) // batch_size
        all_questions = []

        for batch_idx in range(batches_needed):
            remaining = count - len(all_questions)
            current_batch = min(batch_size, remaining)

            prompt = build_prompt(plan, current_batch)
            try:
                response = client.chat([
                    {"role": "system", "content": "你是 CET-4 真题出题专家。只返回 JSON 数组，不要额外文字。"},
                    {"role": "user", "content": prompt}
                ], temperature=0.8)

                parsed = parse_ai_response(response)
                valid = [q for q in parsed if validate_question(q)]
                all_questions.extend(valid[:current_batch])

                if len(valid) < len(parsed):
                    print(f"[{len(valid)}/{len(parsed)} valid]", end=" ", flush=True)
            except Exception as e:
                print(f"[AI错误: {e}]", end=" ", flush=True)

        # 写入数据库
        if all_questions:
            inserted = await insert_questions(all_questions)
            total_inserted += inserted
            print(f"→ 生成 {len(all_questions)} / 写入 {inserted}")
        else:
            print("→ 生成失败（0题）")

    print(f"\n{'='*60}")
    print(f"  完成！共写入 {total_inserted} / {total_planned} 题")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
