"""
本地题库 — 支持多考纲多题库文件
启动时根据 syllabi.json 的 question_bank 字段加载对应 JSON 到内存
"""
import json
import random
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).parent / "data"

# syllabus_id → {questions: [...], index: {id: q}}
_banks: dict[str, dict] = {}
_loaded: bool = False


def load():
    """从 JSON 文件加载所有考纲题库到内存"""
    global _banks, _loaded
    syllabi_file = DATA_DIR / "syllabi.json"
    if not syllabi_file.exists():
        print("[题库] syllabi.json 不存在，无法加载题库")
        return

    with open(syllabi_file, "r", encoding="utf-8") as f:
        syllabi = json.load(f)

    for s in syllabi:
        bank_file = s.get("question_bank")
        if not bank_file:
            continue
        file_path = DATA_DIR / bank_file
        if not file_path.exists():
            print(f"[题库] {s['id']}: ⚠ 题库文件不存在 → {bank_file}")
            continue
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                questions = json.load(f)
            _banks[s["id"]] = {
                "questions": questions,
                "index": {q["id"]: q for q in questions},
            }
            print(f"[题库] {s['id']} ({s['name']}): OK 已加载 {len(questions)} 题")
        except Exception as e:
            print(f"[题库] {s['id']}: FAIL 加载失败 - {e}")

    _loaded = True
    total = sum(len(b["questions"]) for b in _banks.values())
    print(f"[题库] 总计 {len(_banks)} 个考纲题库，{total} 道题目")


def reload():
    """重新加载全部题库（管理员上传新题后调用）"""
    global _banks, _loaded
    _banks = {}
    _loaded = False
    load()


def get_bank(syllabus_id: str) -> Optional[dict]:
    """获取某个考纲的题库"""
    return _banks.get(syllabus_id)


def has_bank(syllabus_id: str) -> bool:
    return syllabus_id in _banks


def count(syllabus_id: Optional[str] = None) -> int:
    """题目总数。传入 syllabus_id 则只统计该考纲"""
    if syllabus_id:
        bank = _banks.get(syllabus_id)
        return len(bank["questions"]) if bank else 0
    return sum(len(b["questions"]) for b in _banks.values())


def _get_stem(q: dict) -> str:
    c = q.get("content", {})
    if isinstance(c, str):
        try:
            c = json.loads(c)
        except Exception:
            c = {}
    return (c.get("stem") or "").lower()


def query(
    syllabus_id: str,
    category: str = None,
    sub_category: str = None,
    question_type: str = None,
    difficulty: int = None,
    search: str = None,
    limit: int = 20,
    offset: int = 0,
    random_order: bool = False,
    exclude_ids: set = None,
) -> tuple[list[dict], int]:
    """
    按考纲 + 条件筛选题目。返回 (结果列表, 总数)
    所有筛选在 Python 内存完成，零延迟。
    """
    bank = _banks.get(syllabus_id)
    if not bank:
        return [], 0

    results = bank["questions"]

    if category:
        results = [q for q in results if q.get("category") == category]
    if sub_category:
        results = [q for q in results if q.get("sub_category") == sub_category]
    if question_type:
        results = [q for q in results if q.get("question_type") == question_type]
    if difficulty is not None:
        results = [q for q in results if q.get("difficulty") == difficulty]
    if exclude_ids:
        results = [q for q in results if q.get("id") not in exclude_ids]
    if search:
        kw = search.lower()
        results = [
            q for q in results
            if kw in _get_stem(q)
            or kw in (q.get("kp_name") or "").lower()
        ]

    total = len(results)

    if random_order and results:
        random.shuffle(results)

    return results[offset: offset + limit], total


def get_by_ids(syllabus_id: str, ids: list[str]) -> list[dict]:
    """按 ID 列表精确取题"""
    bank = _banks.get(syllabus_id)
    if not bank:
        return []
    return [bank["index"][i] for i in ids if i in bank["index"]]


# ---- 全局跨考纲查询（管理员用） ----
def find_question_global(question_id: str) -> tuple[Optional[str], Optional[dict]]:
    """在所有题库中查找题目，返回 (syllabus_id, question) 或 (None, None)"""
    for sid, bank in _banks.items():
        q = bank["index"].get(question_id)
        if q:
            return sid, q
    return None, None


def query_global(
    category: str = None,
    sub_category: str = None,
    question_type: str = None,
    search: str = None,
    syllabus_id: str = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """跨考纲聚合查询，可选按 syllabus_id 过滤"""
    if syllabus_id:
        bank = _banks.get(syllabus_id)
        if not bank:
            return [], 0
        pool = bank["questions"]
    else:
        pool = []
        for b in _banks.values():
            pool.extend(b["questions"])

    results = pool
    if category:
        results = [q for q in results if q.get("category") == category]
    if sub_category:
        results = [q for q in results if q.get("sub_category") == sub_category]
    if question_type:
        results = [q for q in results if q.get("question_type") == question_type]
    if search:
        kw = search.lower()
        results = [q for q in results
                   if kw in _get_stem(q) or kw in (q.get("kp_name") or "").lower()]
    total = len(results)
    return results[offset: offset + limit], total


def all_category_stats() -> dict:
    """返回所有题库的分类/题型/子分类统计"""
    by_category = {}
    by_type = {}
    by_sub_category = {}
    by_syllabus = {}
    for sid, bank in _banks.items():
        for q in bank["questions"]:
            cat = q.get("category") or "未分类"
            by_category[cat] = by_category.get(cat, 0) + 1
            qt = q.get("question_type") or "未知"
            by_type[qt] = by_type.get(qt, 0) + 1
            sc = q.get("sub_category") or "未分类"
            by_sub_category[sc] = by_sub_category.get(sc, 0) + 1
            by_syllabus[sid] = by_syllabus.get(sid, 0) + 1
    return {
        "by_category": by_category,
        "by_type": by_type,
        "by_sub_category": by_sub_category,
        "by_syllabus": by_syllabus,
    }


def delete_question_global(question_id: str) -> tuple[bool, Optional[str]]:
    """跨考纲删除题目，返回 (是否成功, syllabus_id)"""
    for sid, bank in _banks.items():
        q = bank["index"].get(question_id)
        if q:
            bank["questions"] = [qq for qq in bank["questions"] if qq.get("id") != question_id]
            del bank["index"][question_id]
            # 持久化
            save_bank_to_file(sid)
            return True, sid
    return False, None


def save_bank_to_file(syllabus_id: str):
    """持久化指定考纲的题库到文件"""
    bank = _banks.get(syllabus_id)
    if not bank:
        return
    syllabi_file = DATA_DIR / "syllabi.json"
    if not syllabi_file.exists():
        return
    with open(syllabi_file, "r", encoding="utf-8") as f:
        syllabi = json.load(f)
    for s in syllabi:
        if s["id"] == syllabus_id and s.get("question_bank"):
            file_path = DATA_DIR / s["question_bank"]
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(bank["questions"], f, ensure_ascii=False, indent=2)
            return


def get_random(
    syllabus_id: str,
    n: int,
    exclude_ids: set = None,
    category: str = None,
    question_type: str = None,
) -> list[dict]:
    """随机取 N 道题，支持排除和筛选"""
    bank = _banks.get(syllabus_id)
    if not bank:
        return []
    pool = bank["questions"]
    if category:
        pool = [q for q in pool if q.get("category") == category]
    if question_type:
        pool = [q for q in pool if q.get("question_type") == question_type]
    if exclude_ids:
        pool = [q for q in pool if q.get("id") not in exclude_ids]
    if len(pool) <= n:
        return pool[:]
    return random.sample(pool, n)


def add_questions(syllabus_id: str, new_questions: list[dict]):
    """向已有题库追加题目并持久化"""
    bank = _banks.get(syllabus_id)
    if not bank:
        # 创建新题库
        _banks[syllabus_id] = {"questions": [], "index": {}}
        bank = _banks[syllabus_id]

    for q in new_questions:
        bank["questions"].append(q)
        bank["index"][q["id"]] = q

    # 持久化 — 找到对应的文件名
    syllabi_file = DATA_DIR / "syllabi.json"
    if syllabi_file.exists():
        with open(syllabi_file, "r", encoding="utf-8") as f:
            syllabi = json.load(f)
        for s in syllabi:
            if s["id"] == syllabus_id and s.get("question_bank"):
                file_path = DATA_DIR / s["question_bank"]
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(bank["questions"], f, ensure_ascii=False, indent=2)
                print(f"[题库] {syllabus_id}: 已持久化 {len(bank['questions'])} 题 → {s['question_bank']}")
                break


def save_bank(syllabus_id: str, questions: list[dict], filename: str):
    """保存整个题库到文件并加载到内存"""
    file_path = DATA_DIR / filename
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    _banks[syllabus_id] = {
        "questions": questions,
        "index": {q["id"]: q for q in questions},
    }
    print(f"[题库] {syllabus_id}: 已保存 {len(questions)} 题 → {filename}")


# ============================================================
# 向后兼容 — 无 syllabus_id 时默认查 CET-4
# ============================================================
def _resolve_sid(syllabus_id: str = None) -> str:
    if syllabus_id and syllabus_id in _banks:
        return syllabus_id
    if syllabus_id:
        return syllabus_id  # 即使没加载也返回，让调用方处理
    # 默认 CET-4
    if "cet4" in _banks:
        return "cet4"
    if _banks:
        return next(iter(_banks.keys()))
    return ""


# 启动时自动加载
load()
