"""
词条系统路由 — 词条生成/查询、抓取记录、熟练度、词条本、薄弱词定向出题
============================================================
词条本体全局共享：AI 生成一次，全员复用（vocab_entries.word 唯一）
记录与熟练度按用户隔离（vocab_lookups / word_mastery）
"""
import json
import re

import httpx
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel

from agents.llm_client import call_llm
from config import settings
from utils.auth_middleware import get_current_user, verify_user_match

router = APIRouter()


def _headers():
    return {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",  # POST 后返回完整行（否则 201 空 body）
    }


def _entry_prompt(word: str) -> list:
    return [
        {"role": "system", "content": "你是英语词典编辑。只输出 JSON，不要任何其他文字。"},
        {"role": "user", "content": (
            f'为单词 "{word}" 生成词典条目，JSON 格式：'
            '{{"word": "...", "phonetic": "英式音标", "meaning": "简洁中文释义（词性+含义，多个义项用分号）", "example": "一个地道英文例句"}}'
        )},
    ]


def _extract_entry_json(text: str) -> dict:
    """容错提取 AI 返回的 JSON"""
    try:
        return json.loads(text)
    except Exception:
        pass
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    return {}


async def _get_entry(word: str) -> dict:
    """查词条；没有就 AI 生成并缓存（全局共享）"""
    async with httpx.AsyncClient(timeout=20.0) as client:
        res = await client.get(
            f"{settings.SUPABASE_URL}/rest/v1/vocab_entries",
            headers=_headers(), params={"word": f"eq.{word}", "limit": "1"})
        rows = res.json() if res.status_code == 200 and isinstance(res.json(), list) else []
        if rows:
            return rows[0]
        # 不存在 → AI 生成
        try:
            data = _extract_entry_json(call_llm(_entry_prompt(word), temperature=0.4, use_cache=False))
        except Exception:
            data = {}
        entry = {
            "word": (data.get("word") or word).lower(),
            "phonetic": data.get("phonetic") or "",
            "meaning": data.get("meaning") or "（释义生成失败，请稍后重试）",
            "example": data.get("example") or "",
            "source": "ai",
        }
        try:
            ins = await client.post(
                f"{settings.SUPABASE_URL}/rest/v1/vocab_entries",
                headers=_headers(), json=entry)
            if ins.status_code in (200, 201) and isinstance(ins.json(), list):
                return ins.json()[0]
        except Exception:
            pass
        return entry  # 插入失败也返回内存条目（下次再缓存）


# ============================================================
# 词条查询与记录
# ============================================================

@router.get("/vocab/entries/{word}")
async def get_entry(word: str, current_user: str = Depends(get_current_user)):
    """获取词条（不存在则 AI 生成并缓存）"""
    return await _get_entry(word.lower().strip()[:64])


class LookupBody(BaseModel):
    user_id: str
    words: list = []
    touchpoint: str = "chat_ask"  # chat_ask / xiaoji_vision


@router.post("/vocab/lookups")
async def post_lookups(body: LookupBody, current_user: str = Depends(get_current_user)):
    """记录词条抓取/讲解触点"""
    verify_user_match(body.user_id, current_user)
    words = list({str(w).lower().strip() for w in body.words if str(w).strip()})[:20]
    if not words:
        return {"success": True, "recorded": 0}
    async with httpx.AsyncClient(timeout=20.0) as client:
        for w in words:
            await client.post(
                f"{settings.SUPABASE_URL}/rest/v1/vocab_lookups",
                headers=_headers(),
                json={"user_id": body.user_id, "word": w, "touchpoint": body.touchpoint})
    return {"success": True, "recorded": len(words)}


# ============================================================
# 熟练度（EWMA 平滑，与知识点掌握度同构）
# ============================================================

class MasteryBody(BaseModel):
    user_id: str
    word: str
    known: bool = True


@router.post("/vocab/mastery")
async def post_mastery(body: MasteryBody, current_user: str = Depends(get_current_user)):
    """词条卡「认识/不认识」打分"""
    verify_user_match(body.user_id, current_user)
    word = body.word.lower().strip()[:64]
    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.get(
            f"{settings.SUPABASE_URL}/rest/v1/word_mastery",
            headers=_headers(),
            params={"user_id": f"eq.{body.user_id}", "word": f"eq.{word}", "limit": "1"})
        rows = res.json() if res.status_code == 200 and isinstance(res.json(), list) else []
        target = 100.0 if body.known else 20.0
        if rows:
            row = rows[0]
            old = float(row.get("mastery_score") or 0)
            new_score = round(old * 0.7 + target * 0.3, 1)
            payload = {
                "mastery_score": new_score,
                "correct_count": int(row.get("correct_count") or 0) + (1 if body.known else 0),
                "total_count": int(row.get("total_count") or 0) + 1,
                "last_practiced_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            }
            await client.patch(
                f"{settings.SUPABASE_URL}/rest/v1/word_mastery?id=eq.{row['id']}",
                headers=_headers(), json=payload)
            return {"success": True, "mastery_score": new_score, "total_count": payload["total_count"]}
        new_score = round(target, 1)
        await client.post(
            f"{settings.SUPABASE_URL}/rest/v1/word_mastery",
            headers=_headers(),
            json={"user_id": body.user_id, "word": word, "mastery_score": new_score,
                  "correct_count": 1 if body.known else 0, "total_count": 1})
        return {"success": True, "mastery_score": new_score, "total_count": 1}


# ============================================================
# 词条本
# ============================================================

@router.get("/vocab/stats")
async def vocab_stats(user_id: str = Query(...), current_user: str = Depends(get_current_user)):
    """词条本统计：总数 / 已掌握 / 薄弱"""
    verify_user_match(user_id, current_user)
    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.get(
            f"{settings.SUPABASE_URL}/rest/v1/word_mastery",
            headers=_headers(),
            params={"user_id": f"eq.{user_id}", "select": "word,mastery_score", "limit": "5000"})
        rows = res.json() if res.status_code == 200 and isinstance(res.json(), list) else []
    mastered = sum(1 for r in rows if (r.get("mastery_score") or 0) >= 80)
    weak = sum(1 for r in rows if (r.get("mastery_score") or 0) < 60)
    return {"total": len(rows), "mastered": mastered, "weak": weak,
            "avg": round(sum(r.get("mastery_score") or 0 for r in rows) / len(rows), 1) if rows else None}


@router.get("/vocab/wordbook")
async def wordbook(user_id: str = Query(...), filter: str = Query("all", pattern="^(all|weak|mastered)$"),
                   current_user: str = Depends(get_current_user)):
    """词条本列表（按熟练度升序，薄弱在前）"""
    verify_user_match(user_id, current_user)
    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.get(
            f"{settings.SUPABASE_URL}/rest/v1/word_mastery",
            headers=_headers(),
            params={"user_id": f"eq.{user_id}",
                    "select": "word,mastery_score,correct_count,total_count,last_practiced_at",
                    "order": "mastery_score.asc", "limit": "1000"})
        rows = res.json() if res.status_code == 200 and isinstance(res.json(), list) else []
    if filter == "weak":
        rows = [r for r in rows if (r.get("mastery_score") or 0) < 60]
    elif filter == "mastered":
        rows = [r for r in rows if (r.get("mastery_score") or 0) >= 80]
    # 词条释义批量补全（只取前 100 条的词条信息，避免过多请求）
    words = [r["word"] for r in rows[:100]]
    entries = {}
    if words:
        async with httpx.AsyncClient(timeout=15.0) as client:
            er = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/vocab_entries",
                headers=_headers(),
                params={"word": f"in.({','.join(words)})", "select": "word,phonetic,meaning,example", "limit": "100"})
            e_rows = er.json() if er.status_code == 200 and isinstance(er.json(), list) else []
            entries = {e["word"]: e for e in e_rows}
    return [{"word": r["word"], "mastery_score": r.get("mastery_score"),
             "correct_count": r.get("correct_count"), "total_count": r.get("total_count"),
             "last_practiced_at": r.get("last_practiced_at"),
             "entry": entries.get(r["word"])} for r in rows]


# ============================================================
# 薄弱词定向出题
# ============================================================

class PracticeBody(BaseModel):
    user_id: str
    words: list = []


@router.post("/vocab/practice-set")
async def vocab_practice_set(body: PracticeBody, current_user: str = Depends(get_current_user)):
    """用薄弱词生成一组练习题（选择题，写入 questions + generation_history）"""
    verify_user_match(body.user_id, current_user)
    words = [str(w).lower().strip() for w in body.words if str(w).strip()][:10]
    if not words:
        raise HTTPException(status_code=400, detail="请先选择薄弱词")
    prompt = (
        f"为以下英语单词各出一道单选题（题干用该词，考词义，4 个选项，附中文解析）：{', '.join(words)}。"
        '只输出 JSON 数组：[{"title": "题干", "options": {"A": "..","B":"..","C":"..","D":".."}, '
        '"answer": "正确选项字母", "explanation": "中文解析", "word": "对应单词"}]'
    )
    try:
        raw = call_llm([
            {"role": "system", "content": "你是英语出题老师。只输出 JSON 数组，不要任何其他文字。"},
            {"role": "user", "content": prompt},
        ], temperature=0.8, use_cache=False)
        m = re.search(r"\[[\s\S]*\]", raw)
        items = json.loads(m.group(0)) if m else []
    except Exception:
        items = []
    if not items:
        raise HTTPException(status_code=502, detail="出题失败，请稍后重试")

    created = []
    async with httpx.AsyncClient(timeout=20.0) as client:
        for it in items:
            q_data = {
                "user_id": body.user_id, "title": it.get("title", ""),
                "question_type": "choice", "difficulty_score": 5.0,
                "category": "vocabulary", "topic": it.get("word", ""),
                "options": it.get("options", {}), "answer": it.get("answer", ""),
                "explanation": it.get("explanation", ""),
                "source": "generated", "parent_id": None,
            }
            res = await client.post(
                f"{settings.SUPABASE_URL}/rest/v1/questions",
                headers=_headers(), json=q_data)
            if res.status_code in (200, 201) and isinstance(res.json(), list):
                q = res.json()[0]
                created.append({"id": q["id"], "title": q["title"], "word": it.get("word", "")})
                await client.post(
                    f"{settings.SUPABASE_URL}/rest/v1/generation_history",
                    headers=_headers(),
                    json={"user_id": body.user_id, "question_id": q["id"], "title": q["title"],
                          "question_type": "choice", "category": "vocabulary",
                          "topic": it.get("word", ""), "status": "pending"})
    return {"success": True, "created": created}
