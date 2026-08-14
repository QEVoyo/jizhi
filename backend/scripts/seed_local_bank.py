"""
本地题库种子脚本
1. 从 Supabase 导出已有题目
2. 用 AI 批量生成新题目
3. 写入本地 JSON 文件
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json, re, httpx, asyncio, uuid, requests, time, sys, io
from config import settings

# 修复 Windows GBK 编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HEADERS = {
    "apikey": settings.SUPABASE_KEY,
    "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_KEY}",
    "Content-Type": "application/json",
}

# ===== AI 调用 =====
def call_ai(messages: list, temp: float = 0.8) -> str:
    url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
    body = {
        "model": settings.VOLC_ROLE_ENDPOINT_ID,
        "messages": messages,
        "temperature": temp,
        "max_tokens": 8192,
        "stream": False
    }
    h = {"Content-Type": "application/json", "Authorization": f"Bearer {settings.ARK_API_KEY}"}
    for attempt in range(3):
        try:
            resp = requests.post(url, headers=h, json=body, timeout=120)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
            print(f"  API {resp.status_code}, retry {attempt+1}...")
            time.sleep(2)
        except Exception as e:
            print(f"  Error: {e}, retry {attempt+1}...")
            time.sleep(2)
    raise Exception("AI call failed after 3 attempts")


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
    if qt == "choice" or qt == "cloze":
        opts = q["content"].get("options", [])
        if not isinstance(opts, list) or len(opts) < 4: return False
        if not q.get("answer"): return False
    if qt == "fill":
        if not q.get("answer"): return False
    if qt == "translation":
        if not q.get("answer"): return False
    return True


# ===== 从 Supabase 导出 =====
async def export_from_supabase():
    url = f"{settings.SUPABASE_URL}/rest/v1/cet4_questions?select=*&limit=500"
    async with httpx.AsyncClient(timeout=30) as cl:
        r = await cl.get(url, headers=HEADERS)
        if r.status_code == 200:
            return r.json()
        print(f"导出失败: {r.status_code}")
        return []


# ===== 生成新题 =====
SUBCATS = {
    "vocabulary": ["高频核心词", "近义词辨析", "词义辨析", "固定搭配", "短语动词"],
    "grammar": ["时态语态", "虚拟语气", "从句", "非谓语动词", "倒装强调", "主谓一致", "情态动词"],
    "reading": ["快速阅读", "仔细阅读", "选词填空", "主旨理解", "细节推断"],
    "translation": ["社会文化类", "科技教育类", "经济发展类", "日常生活类", "传统文化类"],
}

GEN_PROMPT_TEMPLATE = """你是 CET-4 大学英语四级考试出题专家。请生成 __COUNT__ 道 CET-4 真题风格的题目。

题型: __QTYPE__
分类: __CATEGORY__ / __SUBCAT__
难度: 3-8

## 要求
- 严格贴合 CET-4 考试风格和难度
- 题干为完整英文句子（翻译题为中文句子）
- 选择题选项用 A/B/C/D 开头，4个选项长度相近，干扰项合理
- 填空题在句子中用 ____ 留空
- 翻译题为纯中译英，给出中文句子，答案为英文译文
- 每题提供详细中文解析（考点+为什么对+为什么错）

## 输出格式
严格的 JSON 数组，每个元素格式：
```json
[
  {
    "category": "__CATEGORY__",
    "sub_category": "__SUBCAT__",
    "question_type": "__QTYPE__",
    "difficulty": 5,
    "content": {
      "stem": "题干内容",
      "options": ["A. xx", "B. xx", "C. xx", "D. xx"]
    },
    "answer": "A",
    "explanation": "详细中文解析",
    "kp_name": "知识点名称"
  }
]
```
## 注意
- 翻译题 options 字段设为空数组 []
- 填空题 answer 为填入的单词/短语
- 每道题难度在 3-8 之间随机分布
- 禁止重复题目，确保每道题考查不同的知识点"""


def generate_batch(category: str, subcat: str, qtype: str, count: int = 5) -> list:
    """用 AI 生成一批题目"""
    prompt = GEN_PROMPT_TEMPLATE.replace("__COUNT__", str(count)) \
        .replace("__QTYPE__", qtype) \
        .replace("__CATEGORY__", category) \
        .replace("__SUBCAT__", subcat)
    messages = [
        {"role": "system", "content": "你是 CET-4 出题专家。只输出 JSON 数组，不做额外说明。"},
        {"role": "user", "content": prompt}
    ]
    raw = call_ai(messages)
    items = parse_json(raw)
    validated = []
    for item in items:
        if validate(item):
            item["id"] = str(uuid.uuid4())
            if not item.get("content"):
                item["content"] = {}
            if isinstance(item["content"], dict) and "options" not in item["content"]:
                item["content"]["options"] = []
            validated.append(item)
        else:
            print(f"  WARN 校验不通过: {item.get('content', {}).get('stem', 'N/A')[:40]}")
    return validated


async def main():
    print("=" * 60)
    print("本地题库种子脚本")
    print("=" * 60)

    # 1. 导出已有题目
    print("\n[1/3] 从 Supabase 导出已有题目...")
    existing = await export_from_supabase()
    print(f"  导出 {len(existing)} 题")

    # 2. 统计各分类数量
    from collections import Counter
    cat_count = Counter(q["category"] for q in existing)
    for cat, cnt in sorted(cat_count.items()):
        print(f"  {cat}: {cnt}")

    # 3. 生成新题目标
    targets = {
        "vocabulary": 180,
        "grammar": 180,
        "reading": 80,
        "translation": 80,
    }

    all_questions = list(existing)

    print(f"\n[2/3] 生成新题目（目标 ~520 题）...")

    for category, target_total in targets.items():
        current = cat_count.get(category, 0)
        needed = target_total - current
        if needed <= 0:
            print(f"\n  {category}: 已有 {current}，跳过")
            continue

        print(f"\n  {category}: 已有 {current}，需要 {needed}，目标 {target_total}")

        subcats = SUBCATS[category]
        qtype_map = {
            "vocabulary": ["choice", "fill"],
            "grammar": ["choice"],
            "reading": ["choice", "cloze"],
            "translation": ["translation"],
        }

        per_subcat = max(4, needed // len(subcats))
        generated = 0

        for subcat in subcats:
            qtypes = qtype_map[category]
            for qtype in qtypes:
                if generated >= needed:
                    break
                batch_size = min(6, needed - generated)
                if batch_size <= 0:
                    break
                print(f"    生成 {subcat}/{qtype} x{batch_size}...", end=" ", flush=True)
                try:
                    batch = generate_batch(category, subcat, qtype, batch_size)
                    all_questions.extend(batch)
                    generated += len(batch)
                    print(f"[OK] +{len(batch)} (累计 {generated}/{needed})")
                except Exception as e:
                    print(f"[FAIL] {e}")
                time.sleep(0.5)  # 避免频率限制

    print(f"\n[3/3] 保存题库: {len(all_questions)} 题")

    # 统计
    final_count = Counter(q["category"] for q in all_questions)
    for cat in ["vocabulary", "grammar", "reading", "translation"]:
        qtype_dist = Counter(q["question_type"] for q in all_questions if q["category"] == cat)
        print(f"  {cat}: {final_count.get(cat, 0)} ({dict(qtype_dist)})")

    # 写入
    output_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "cet4_questions.json"
    )
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_questions, f, ensure_ascii=False, indent=2)
    print(f"\n[DONE] 已保存到 {output_path}")
    print(f"   共 {len(all_questions)} 道题")


if __name__ == "__main__":
    asyncio.run(main())
