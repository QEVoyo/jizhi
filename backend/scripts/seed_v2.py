"""
CET-4 题库高质量生成 — 改进版
- 每批 3-5 题，质量优先
- 翻译题纯中译英（无选项）
- 选题严格按四级真题风格
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json, re, httpx, asyncio, requests
from config import settings
from logging_config import logger

HEADERS = {
    "apikey": settings.SUPABASE_KEY,
    "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_KEY}",
    "Content-Type": "application/json",
}
TABLE_URL = f"{settings.SUPABASE_URL}/rest/v1/cet4_questions"


def call_ai(messages: list, temp: float = 0.7) -> str:
    url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
    body = {
        "model": settings.VOLC_ROLE_ENDPOINT_ID,
        "messages": messages,
        "temperature": temp,
        "max_tokens": 4096,
        "stream": False
    }
    h = {"Content-Type": "application/json", "Authorization": f"Bearer {settings.ARK_API_KEY}"}
    resp = requests.post(url, headers=h, json=body, timeout=90)
    if resp.status_code == 200:
        return resp.json()["choices"][0]["message"]["content"]
    raise Exception(f"API {resp.status_code}")


def parse_json(text: str) -> list:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:])
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
    m = re.search(r'\[[\s\S]*\]', text)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return []


def validate(q: dict) -> bool:
    if not isinstance(q, dict): return False
    if "content" not in q or not isinstance(q["content"], dict): return False
    if "stem" not in q["content"]: return False
    qt = q.get("question_type", "")
    if qt == "choice":
        opts = q["content"].get("options", [])
        if not isinstance(opts, list) or len(opts) < 4: return False
        if not q.get("answer") or len(str(q["answer"]).strip()) == 0: return False
    if qt == "fill":
        if not q.get("answer"): return False
    if qt == "translation":
        # 翻译题不需要 options
        if not q.get("answer"): return False
    return True


CHOICE_PROMPTS = {
    "vocabulary": """你是 CET-4 词汇题出题专家。生成 {count} 道词汇选择题(4选项A/B/C/D)。

分类: {sub}
难度: {diff_min}-{diff_max}
要求：
- 题目贴合"{sub}"知识点，CET-4 真题风格
- 题干为完整英文句子，一处划线/留空
- 4个选项长度相近，干扰项合理
- 每题提供详细中文解析（考点+为什么对+为什么错）

返回 JSON：
[{{"category":"{cat}","sub_category":"{sub}","kp_name":"知识点名称","question_type":"choice","difficulty":5,
   "content":{{"stem":"完整英文题干","options":["A. xxx","B. xxx","C. xxx","D. xxx"]}},
   "answer":"A","explanation":"解析：..."}}]
只返回 JSON 数组。""",

    "grammar": """你是 CET-4 语法题出题专家。生成 {count} 道语法选择题(4选项A/B/C/D)。

分类: {sub}
难度: {diff_min}-{diff_max}
要求：
- 题目贴合"{sub}"知识点
- 题干为完整英文句子，语法考点明确
- 每题提供详细中文解析（考点+为什么对+为什么错）

返回 JSON：
[{{"category":"{cat}","sub_category":"{sub}","kp_name":"知识点名称","question_type":"choice","difficulty":5,
   "content":{{"stem":"完整英文题干","options":["A. xxx","B. xxx","C. xxx","D. xxx"]}},
   "answer":"A","explanation":"解析：..."}}]
只返回 JSON 数组。""",

    "reading": """你是 CET-4 阅读题出题专家。生成 {count} 道阅读理解选择题。

分类: {sub}
难度: {diff_min}-{diff_max}
要求：
- 给出一段100-200词的英文短文
- 每段短文后跟1道选择题(4选项A/B/C/D)
- 题目考察{sub}能力
- 每题提供详细中文解析

返回 JSON：
[{{"category":"{cat}","sub_category":"{sub}","kp_name":"{sub}","question_type":"choice","difficulty":5,
   "content":{{"stem":"【短文】xxx\\n\\n问题：xxx","options":["A. xxx","B. xxx","C. xxx","D. xxx"]}},
   "answer":"A","explanation":"解析：..."}}]
只返回 JSON 数组。"""
}

FILL_PROMPTS = {
    "vocabulary": """你是 CET-4 词汇题出题专家。生成 {count} 道填空题。

分类: {sub} | 难度: {diff_min}-{diff_max}
要求：题干为英文句子，留一个空让学生填单词/短语。提供中文解析。

返回 JSON：
[{{"category":"{cat}","sub_category":"{sub}","kp_name":"知识点名称","question_type":"fill","difficulty":5,
   "content":{{"stem":"完整英文题干（用 ______ 标记填空位置）","options":[]}},
   "answer":"正确答案","explanation":"解析：..."}}]
只返回 JSON 数组。""",
}

CLOZE_PROMPTS = {
    "reading": """你是 CET-4 选词填空题出题专家。生成 {count} 道选词填空题。

分类: {sub} | 难度: {diff_min}-{diff_max}
要求：
- 一段100-150词英文短文，挖5个空
- 提供8-10个候选词（含干扰词）
- 用______(1)______, ______(2)______ 标记空格

返回 JSON：
[{{"category":"{cat}","sub_category":"{sub}","kp_name":"{sub}","question_type":"cloze","difficulty":5,
   "content":{{"stem":"完整短文（含______(N)______标记）","options":["candidate1","candidate2",...,"candidate10"]}},
   "answer":["word1","word2","word3","word4","word5"],
   "explanation":"解析：逐空说明"}}]
只返回 JSON 数组。""",
}

TRANSLATION_PROMPT = """你是 CET-4 翻译题(中译英)出题专家。生成 {count} 道翻译题。

分类: {sub} | 难度: {diff_min}-{diff_max}
要求：
- 给出一句地道的中文（15-30字）
- 学生需要翻译成英文
- 提供标准英文译文 + 考点解析
- 题目无选项！纯粹的翻译题

返回 JSON（注意：options 为空数组！answer 是参考译文！）：
[{{"category":"{cat}","sub_category":"{sub}","kp_name":"翻译-{sub}","question_type":"translation","difficulty":5,
   "content":{{"stem":"中文句子（要翻译的内容）","options":[]}},
   "answer":"标准英文译文",
   "explanation":"考点解析：核心词汇、句型结构、易错点"}}]
只返回 JSON 数组。"""


# ============ 生成计划 ============
GENERATE_PLAN = [
    # 词汇 - choice
    ("vocabulary", "高频核心词", "choice", 12, [2,5], "CHOICE"),
    ("vocabulary", "近义词辨析", "choice", 10, [3,6], "CHOICE"),
    ("vocabulary", "词义辨析",   "choice", 8,  [3,7], "CHOICE"),
    # 词汇 - fill
    ("vocabulary", "固定搭配",   "fill",   8,  [2,5], "FILL"),
    # 语法
    ("grammar", "时态语态",     "choice", 12, [2,6], "CHOICE"),
    ("grammar", "虚拟语气",     "choice", 8,  [3,7], "CHOICE"),
    ("grammar", "从句",         "choice", 10, [3,7], "CHOICE"),
    ("grammar", "非谓语动词",   "choice", 8,  [4,8], "CHOICE"),
    ("grammar", "倒装强调",     "choice", 6,  [3,7], "CHOICE"),
    # 阅读
    ("reading", "快速阅读",     "choice", 10, [3,6], "CHOICE"),
    ("reading", "仔细阅读",     "choice", 8,  [4,8], "CHOICE"),
    ("reading", "选词填空",     "cloze",  6,  [4,7], "CLOZE"),
    # 翻译（纯中译英，无选项）
    ("translation", "社会文化类", "translation", 6, [3,7], "TRANSLATION"),
    ("translation", "科技教育类", "translation", 6, [3,7], "TRANSLATION"),
    ("translation", "经济发展类", "translation", 5, [3,7], "TRANSLATION"),
]


async def insert(questions: list) -> int:
    count = 0
    async with httpx.AsyncClient(timeout=30.0) as client:
        for q in questions:
            ans = q.get("answer", "")
            if isinstance(ans, (dict, list)):
                ans = json.dumps(ans, ensure_ascii=False)
            content = q.get("content", {})
            if isinstance(content, str):
                try: content = json.loads(content)
                except: content = {"stem": content}

            record = {
                "category": q["category"],
                "sub_category": q.get("sub_category", ""),
                "kp_name": q.get("kp_name", q.get("sub_category", "")),
                "kp_id": q.get("kp_id", q.get("sub_category", "").lower().replace(" ", "-")),
                "question_type": q.get("question_type", "choice"),
                "difficulty": int(q.get("difficulty", 5)),
                "content": content,  # JSONB — 传 dict 即可，不要 dumps
                "answer": json.dumps(ans, ensure_ascii=False) if not isinstance(ans, str) else ans,
                "explanation": q.get("explanation", ""),
                "distractor_analysis": q.get("distractor_analysis", {}) or {},
            }
            try:
                res = await client.post(TABLE_URL, headers=HEADERS, json=record)
                if res.status_code in [200, 201]:
                    count += 1
                else:
                    logger.info(f"  insert fail: {res.status_code} {res.text[:80]}")
            except Exception as e:
                logger.info(f"  net err: {e}")
    return count


async def main():
    # 先删除旧数据
    print("清空旧题库...")
    async with httpx.AsyncClient(timeout=30.0) as c:
        # 分批删
        r = await c.get(f"{settings.SUPABASE_URL}/rest/v1/cet4_questions?select=id&limit=500", headers=HEADERS)
        ids = [q["id"] for q in (r.json() if r.status_code == 200 else [])]
        for i in range(0, len(ids), 50):
            batch = ids[i:i+50]
            ids_str = ",".join([f'"{bid}"' for bid in batch])
            await c.delete(f"{settings.SUPABASE_URL}/rest/v1/cet4_questions?id=in.({ids_str})", headers=HEADERS)
        print(f"  已删除 {len(ids)} 题")

    total_ok = 0
    total_plan = sum(p[3] for p in GENERATE_PLAN)

    print(f"\n{'='*60}")
    print(f"  开始 AI 生成 {total_plan} 题 | {len(GENERATE_PLAN)} 个分类")
    print(f"{'='*60}\n")

    for i, (cat, sub, qtype, count, diff, prompt_type) in enumerate(GENERATE_PLAN):
        print(f"[{i+1}/{len(GENERATE_PLAN)}] {cat}/{sub} ({qtype}) ×{count} ...", end=" ", flush=True)

        # 每批最多5题
        all_qs = []
        remaining = count
        while remaining > 0:
            batch = min(5, remaining)
            # 选 prompt
            if prompt_type == "TRANSLATION":
                prompt = TRANSLATION_PROMPT.format(cat=cat, sub=sub, count=batch, diff_min=diff[0], diff_max=diff[1])
            elif prompt_type == "CLOZE":
                prompt = CLOZE_PROMPTS["reading"].format(cat=cat, sub=sub, count=batch, diff_min=diff[0], diff_max=diff[1])
            elif prompt_type == "FILL":
                prompt = FILL_PROMPTS["vocabulary"].format(cat=cat, sub=sub, count=batch, diff_min=diff[0], diff_max=diff[1])
            else:
                base = CHOICE_PROMPTS.get(cat, CHOICE_PROMPTS["vocabulary"])
                prompt = base.format(cat=cat, sub=sub, count=batch, diff_min=diff[0], diff_max=diff[1])

            for attempt in range(3):
                try:
                    resp = call_ai([
                        {"role": "system", "content": "你是 CET-4 出题专家。只返回 JSON 数组，不要额外文字。不要 markdown 代码块。"},
                        {"role": "user", "content": prompt}
                    ], temp=0.8)
                    parsed = parse_json(resp)
                    valid = [q for q in parsed if validate(q)]
                    if valid:
                        all_qs.extend(valid[:batch])
                        remaining -= len(valid[:batch])
                        break
                    logger.info(f"  attempt {attempt+1}: {len(parsed)} parsed, {len(valid)} valid")
                except Exception as e:
                    logger.info(f"  attempt {attempt+1} err: {e}")
                    await asyncio.sleep(1)
            else:
                # 3次都失败，跳过剩余
                remaining = 0

        if all_qs:
            n = await insert(all_qs[:count])
            total_ok += n
            print(f"→ {n}/{count}")
        else:
            print("→ FAILED")

    print(f"\n{'='*60}")
    print(f"  完成: {total_ok}/{total_plan} 题入库")
    print(f"  API: {TABLE_URL}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    asyncio.run(main())
