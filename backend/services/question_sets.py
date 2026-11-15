"""题集创建（2026-11-13）

团队出题跑完后，把 `run.output.questions` 里已落库的题打包成题集。
放在 service 里，是因为有两个调用方：
  · `routers/questions.py` 的手动「从 run 建题集」接口；
  · `routers/agents._execute_run_body()` 在 run 收尾时自动建（页面关掉也不丢）。
"""
from __future__ import annotations

from typing import Optional

import httpx

from config import settings
from logging_config import logger


def _headers() -> dict:
    return {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


async def create_set(*, user_id: str, name: str, description: Optional[str],
                     question_ids: list[str], source: str = "generated",
                     set_type: str = "generated") -> Optional[dict]:
    """创建题集并写入 question_ids；失败返回 None，不抛给 run 收尾。"""
    ids = [str(q) for q in (question_ids or []) if q]
    if not ids:
        return None
    data = {
        "user_id": user_id,
        "name": name or f"团队出题 · {len(ids)} 道",
        "description": description or f"团队出题 · {len(ids)} 道",
        "set_type": set_type,
        "source": source,
        "question_ids": ids,
    }
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.post(
                f"{settings.SUPABASE_URL}/rest/v1/question_sets",
                headers=_headers(), json=data)
        if res.status_code not in (200, 201):
            logger.info(f"[question_sets] 创建题集失败 {res.status_code}: {res.text[:200]}")
            return None
        row = res.json()
        if isinstance(row, list):
            row = row[0] if row else None
        return row if isinstance(row, dict) else None
    except Exception as e:
        logger.info(f"[question_sets] 创建题集异常: {e}")
        return None
