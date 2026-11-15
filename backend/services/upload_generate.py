"""上传题目生成与留存（2026-10-30）。

输入：已确认的 upload_jobs + upload_seeds。
输出：
  · questions（origin=upload，带 source_file_id / source_seed_id / source_ref）
  · question_sets（source=upload，一批一行）
  · generation_history（source=upload，每题一行，status=pending）
  · 通知 learning.upload_ready

原则：**先出题 → 校验 → 只把通过的题落库**。
没通过的题不写 questions，只在 upload_jobs.profile 里留原因，结果卡如实报告。
"""
from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from config import settings
from logging_config import logger
from services import upload_jobs, upload_runs

QWEN_MODEL = getattr(settings, "QWEN_REASON_MODEL", "qwen-plus")
MAX_PER_RUN = 20
CONCURRENCY = 3

# 跨任务的总闸门：多个上传任务同时生成时，所有单题调用共用这一个信号量。
# 单任务的 CONCURRENCY=3 只管本任务；没有总闸门，4 个任务就是 12 路并发。
_GLOBAL_LLM_SEM: Optional[asyncio.Semaphore] = None


def _global_llm_sem() -> asyncio.Semaphore:
    global _GLOBAL_LLM_SEM
    if _GLOBAL_LLM_SEM is None:
        _GLOBAL_LLM_SEM = asyncio.Semaphore(
            int(getattr(settings, "UPLOAD_LLM_CONCURRENCY", 6)))
    return _GLOBAL_LLM_SEM


def _headers(prefer: str = "") -> dict:
    h = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json",
    }
    if prefer:
        h["Prefer"] = prefer
    return h


def _base(table: str) -> str:
    return f"{settings.SUPABASE_URL}/rest/v1/{table}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


_STOP = {"的", "了", "和", "与", "在", "是", "有", "为", "对", "从", "到", "中", "上", "下",
         "这个", "一个", "可以", "能够", "表示", "称为", "叫做", "是指", "等于"}


def _tokens(s: str) -> set[str]:
    s = re.sub(r"[^一-龥A-Za-z0-9]+", " ", s or "")
    out = set()
    for w in s.split():
        if 2 <= len(w) <= 8 and w not in _STOP:
            out.add(w.lower())
    # 中文没有空格：按 2 字滑窗补一层
    for m in re.findall(r"[一-龥]{2,}", s or ""):
        for i in range(0, len(m) - 1):
            out.add(m[i:i + 2])
    return out


def _seed_fidelity(seed: dict, q: dict) -> bool:
    """题目是否真的在考这条命题：命题关键词至少要出现在题干/解析里。"""
    prop_tokens = _tokens(seed.get("proposition") or "")
    q_tokens = _tokens((q.get("title") or "") + " " + (q.get("explanation") or ""))
    if not prop_tokens:
        return True
    hit = len(prop_tokens & q_tokens)
    return hit >= 1


def _verify(q: dict, seed: dict) -> list[str]:
    reasons = []
    qtype = (q.get("question_type") or q.get("type") or "").lower()
    if not (q.get("title") or "").strip():
        reasons.append("题干为空")
    if not (q.get("answer") or "").strip():
        reasons.append("答案为空")
    if qtype in ("choice", "选择题"):
        opts = q.get("options")
        if not isinstance(opts, dict) or len(opts) < 4:
            reasons.append("选择题选项不足 4 个")
        elif str(q.get("answer")) not in opts:
            reasons.append("选择题答案不在选项里")
        elif len(set(str(v) for v in opts.values())) != len(opts):
            reasons.append("选择题选项重复")
    elif qtype in ("judge", "判断题"):
        if str(q.get("answer")).strip() not in ("正确", "错误"):
            reasons.append("判断题答案必须是正确/错误")
    elif qtype in ("fill", "填空题"):
        if not str(q.get("answer")).strip():
            reasons.append("填空题答案为空")
    if not (q.get("explanation") or "").strip():
        reasons.append("解析为空")
    if not _seed_fidelity(seed, q):
        reasons.append("题目与可出题点不对应（关键词不匹配）")
    return reasons


_TYPE_FIELDS = {
    "choice": '    "options": {"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"},\n    "answer": "B",\n',
    "judge": '    "answer": "正确",\n',
    "fill": '    "answer": "填空答案",\n',
    "calculation": '    "answer": "解：\\n第一步 …\\n所以答案是 …",\n',
    "essay": '    "answer": "1. 要点一\\n2. 要点二\\n3. 要点三",\n',
}

_TYPE_LABEL = {
    "choice": "单选题", "judge": "判断题", "fill": "填空题",
    "calculation": "计算题", "essay": "简答题/论述题",
}


def _prompt(seed: dict, qtype: str, difficulty: str, profile: dict) -> str:
    fields = _TYPE_FIELDS.get(qtype, _TYPE_FIELDS["choice"])
    return f"""你是出题老师。**只根据下面这条可出题点和原文证据**出 1 道题，不得引入文件外的事实。

【可出题点】
- 概念：{seed.get('concept')}
- 命题：{seed.get('proposition')}
- 适合题型：{', '.join(seed.get('question_forms') or [])}
- 干扰项角度：{'；'.join(seed.get('distractor_angles') or []) or '无'}
- 原文证据：{((seed.get('evidence') or {}).get('quote') or '')}

【本次要求】
- 题型：{_TYPE_LABEL.get(qtype, qtype)}
- 难度：{difficulty}
- 学科：{profile.get('domain') or '通用'}
- 文档类型：{profile.get('doc_type') or 'unknown'}

【硬规则】
1. 题干自包含；如果是理解题/材料题，题干必须写「根据材料」。
2. 选择题必须有 4 个唯一选项、有且只有一个正确；干扰项要来自常见误解。
3. 答案必须能被原文证据支持；解析里说明依据，不得编造。
4. 不要出「文件叫什么/作者是谁/某年某月」这种低价值题。
5. 不要照抄原文整段当题干；要抽象成具体问题。

只输出 JSON：
{{
    "title": "题干",
    "question_type": "{qtype}",
{fields}    "explanation": "解析（说明为什么，以及依据原文哪一点）",
    "hint": "20字内提示",
    "difficulty_score": 5.0,
    "category": "学科",
    "topic": "知识点",
    "normalized_topic": "归一化知识点"
}}"""


async def _call_one(seed: dict, qtype: str, difficulty: str, profile: dict) -> Optional[dict]:
    from agents.qwen_client import call_qwen
    from utils.ai_json import extract_object
    prompt = _prompt(seed, qtype, difficulty, profile)
    for attempt in range(2):
        try:
            out = await asyncio.to_thread(
                call_qwen, [{"role": "user", "content": prompt}],
                0.6 if attempt == 0 else 0.3, QWEN_MODEL, "upload_question_gen")
            data = extract_object(out)
            if not isinstance(data, dict) or not data.get("title"):
                raise ValueError("模型未返回题目 JSON")
            # 统一字段
            data.setdefault("question_type", qtype)
            if qtype == "choice" and not isinstance(data.get("options"), dict):
                raise ValueError("选择题缺 options")
            reasons = _verify(data, seed)
            if not reasons:
                return data
            logger.info(f"[upload] 第 {attempt+1} 次校验未过: {reasons}")
            # 带反馈重试一次
            prompt = prompt + f"\n\n上一次没通过校验：{'；'.join(reasons)}。请修正后重新输出完整 JSON。"
        except Exception as e:
            logger.info(f"[upload] 生成失败（第 {attempt+1} 次）: {e}")
    return None


_CROSS_PROMPT = """你是独立校验员，不负责出题。请逐题判断下面这批题目：
1. 题干是否真的在考「可出题点」的命题？（而不是跑题/泛泛而谈）
2. 答案是否正确、能否被原文证据支持？
3. 解析是否与答案一致？
4. 选择题是否只有一个正确选项？

题目如下：
{items}

只输出 JSON：
{{"results": [{{"index": 0, "ok": true, "reasons": []}}]}}

规则：
- 拿不准就判 ok=false，并写清原因；宁可错杀，不要让坏题进库。
- index 对应上面的编号。
"""


async def _crosscheck_batch(pairs: list[tuple[dict, dict]]) -> dict:
    """批量独立复核（一次 LLM 调用，不是逐题）。

    返回 {index: (ok, [reasons])}。调用失败返回 {} —— 不因复核服务挂了就整批失败。
    """
    if not pairs:
        return {}
    import asyncio as _asyncio
    from agents.qwen_client import call_qwen
    from utils.ai_json import extract_object

    out_map: dict = {}
    for start in range(0, len(pairs), 10):
        chunk = pairs[start:start + 10]
        blocks = []
        for i, (seed, q) in enumerate(chunk):
            opts = q.get("options") if isinstance(q.get("options"), dict) else {}
            blocks.append(
                f"[{i}] 命题：{seed.get('proposition')}\n"
                f"原文证据：{((seed.get('evidence') or {}).get('quote') or '')}\n"
                f"题目：{q.get('title')}\n"
                f"选项：{json.dumps(opts, ensure_ascii=False) if opts else '无'}\n"
                f"答案：{q.get('answer')}\n"
                f"解析：{q.get('explanation')}")
        prompt = _CROSS_PROMPT.format(items="\n\n".join(blocks))
        try:
            raw = await _asyncio.to_thread(
                call_qwen, [{"role": "user", "content": prompt}],
                0.1, QWEN_MODEL, "upload_crosscheck")
            data = extract_object(raw)
            for r in (data.get("results") or []):
                try:
                    idx = int(r.get("index")) + start
                except (TypeError, ValueError):
                    continue
                out_map[idx] = (bool(r.get("ok")), r.get("reasons") or [])
        except Exception as e:
            logger.info(f"[upload] 批量复核失败（跳过，不阻断落库）: {e}")
    return out_map


async def _insert_question(user_id: str, job: dict, seed: dict,
                           q: dict) -> Optional[dict]:
    payload = {
        "user_id": user_id,
        "title": q.get("title"),
        "question_type": q.get("question_type") or q.get("type") or "choice",
        "difficulty_score": q.get("difficulty_score", 5.0),
        "category": q.get("category") or (job.get("profile") or {}).get("domain") or "通用",
        "topic": q.get("topic") or seed.get("concept"),
        "normalized_topic": q.get("normalized_topic") or seed.get("concept"),
        "options": q.get("options"),
        "answer": q.get("answer"),
        "explanation": q.get("explanation"),
        "hint": q.get("hint"),
        "source": "generated",
        "origin": "upload",
        "source_file_id": job.get("id"),
        "source_seed_id": seed.get("id"),
        "source_ref": seed.get("source_ref") or {},
        "verification": {"passed": True, "seed_key": seed.get("seed_key")},
    }
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.post(f"{_base('questions')}?select=id",
                                    headers=_headers("return=representation"),
                                    json=payload)
        if res.status_code in (200, 201):
            rows = res.json()
            if isinstance(rows, list) and rows:
                return {**payload, "id": rows[0].get("id")}
            if isinstance(rows, dict):
                return {**payload, "id": rows.get("id")}
        logger.error(f"[upload] 写题目失败 {res.status_code}: {res.text[:160]}")
    except Exception as e:
        logger.error(f"[upload] 写题目异常: {e}")
    return None


async def _create_set(user_id: str, job: dict, question_ids: list[str],
                      passed: int, dropped: int) -> Optional[str]:
    name = f"《{job.get('filename') or '上传文件'}》 · {datetime.now().strftime('%m-%d')} 生成"
    payload = {
        "user_id": user_id, "name": name[:120],
        "description": f"来自上传文件 · {passed} 道题"
                       + (f" · {dropped} 道未通过质检" if dropped else ""),
        "set_type": "upload", "source": "upload",
        "source_file_id": job.get("id"), "upload_job_id": job.get("id"),
        "question_ids": question_ids,
    }
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.post(f"{_base('question_sets')}?select=id",
                                    headers=_headers("return=representation"),
                                    json=payload)
        if res.status_code in (200, 201):
            rows = res.json()
            if isinstance(rows, list) and rows:
                return rows[0].get("id")
            if isinstance(rows, dict):
                return rows.get("id")
        logger.error(f"[upload] 建题集失败 {res.status_code}: {res.text[:160]}")
    except Exception as e:
        logger.error(f"[upload] 建题集异常: {e}")
    return None


async def _insert_history(user_id: str, job: dict, set_id: str,
                          q: dict) -> None:
    payload = {
        "user_id": user_id, "question_id": q.get("id"),
        "title": q.get("title"), "question_type": q.get("question_type"),
        "category": q.get("category"), "topic": q.get("topic"),
        "status": "pending", "source": "upload",
        "set_id": set_id, "file_name": job.get("filename"),
        "upload_job_id": job.get("id"),
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(f"{_base('generation_history')}",
                                    headers=_headers("return=minimal"), json=payload)
        if res.status_code >= 300:
            logger.error(f"[upload] 写生成历史失败 {res.status_code}: {res.text[:160]}")
    except Exception as e:
        logger.error(f"[upload] 写生成历史异常: {e}")


async def _notify(user_id: str, filename: str, set_id: str,
                  passed: int, dropped: int) -> None:
    try:
        from utils.notification import notify, NotifyError
        await notify(
            user_id, "learning.upload_ready",
            source_id=set_id, title="上传题目已生成",
            content=f"《{filename}》生成了 {passed} 道题"
                    + (f"，{dropped} 道未通过质检已丢弃。" if dropped else "。"),
            link=f"/set-detail?id={set_id}",
            payload={"set_id": set_id, "passed": passed, "dropped": dropped},
        )
    except Exception as e:                                  # noqa: BLE001
        logger.error(f"[upload] 生成完成通知未送达: {e}")


# ==================== 生成单元检查点（2026-11-02） ====================
# 暂停/继续的前提不是「改个状态」，而是每道题都有地方落盘：
#   · 每个「种子 × 题型」在 upload_job_units 里一行；
#   · 生成完一道就写回，恢复时跳过已完成单元；
#   · worker 只在题目边界停，不假装能打断正在跑的 LLM 调用。

_UNIT_FIELDS = ("id,job_id,run_id,idx,seed_id,qtype,status,question,error")


async def _list_units(job_id: str) -> list:
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.get(_base("upload_job_units"), headers=_headers(), params={
                "job_id": f"eq.{job_id}", "select": _UNIT_FIELDS,
                "order": "idx.asc", "limit": "100",
            })
        return res.json() if res.status_code == 200 and isinstance(res.json(), list) else []
    except Exception as e:
        logger.info(f"[upload] 读生成单元失败: {e}")
        return []


async def _insert_units(job_id: str, run_id: Optional[str],
                        items: list[tuple[int, dict]]) -> bool:
    if not items:
        return True
    payload = []
    for idx, item in items:
        payload.append({
            "job_id": job_id, "run_id": run_id or None, "idx": idx,
            "seed_id": item.get("seed_id") or None,
            "qtype": item.get("qtype") or "",
            "status": "pending",
            "created_at": _now(), "updated_at": _now(),
        })
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(
                f"{_base('upload_job_units')}",
                headers=_headers("return=minimal"), json=payload)
        if res.status_code < 300:
            return True
        # 并发恢复时可能撞唯一键；重新读一遍即可
        logger.info(f"[upload] 写生成单元失败 {res.status_code}: {res.text[:160]}")
    except Exception as e:
        logger.info(f"[upload] 写生成单元异常: {e}")
    return False


async def _update_unit(unit_id: str, **fields: Any) -> bool:
    if not unit_id or not fields:
        return False
    fields.setdefault("updated_at", _now())
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.patch(
                f"{_base('upload_job_units')}?id=eq.{unit_id}",
                headers=_headers("return=minimal"), json=fields)
        return res.status_code < 300
    except Exception as e:
        logger.info(f"[upload] 更新生成单元失败: {e}")
        return False


def _build_plan(seeds: list[dict], count: int, types: list[str]) -> list[dict]:
    type_map = {"选择题": "choice", "判断题": "judge", "填空题": "fill",
                "计算题": "calculation", "简答题": "essay", "论述题": "essay"}
    plan: list[dict] = []
    if not seeds:
        return plan
    for i in range(count):
        seed = seeds[i % len(seeds)]
        qtype = types[i % len(types)]
        forms = seed.get("question_forms") or []
        if qtype not in forms and forms:
            qtype = type_map.get(forms[0], "choice")
        plan.append({"seed_id": seed.get("id"), "qtype": qtype})
    return plan


async def _stop_state(job_id: str, user_id: str) -> str:
    """返回 '' / paused / cancelled。每个题目边界查一次。"""
    if await upload_runs.is_cancelled(job_id, user_id):
        return "cancelled"
    job = await upload_jobs.get_job(job_id, user_id)
    if not job:
        return "cancelled"
    if job.get("pause_requested") or job.get("status") == "paused":
        return "paused"
    return ""


async def _generate_units(job_id: str, user_id: str, run_id: Optional[str],
                          seeds_by_id: dict, plan: list[dict], profile: dict,
                          difficulty: str) -> str:
    """按单元生成题目。返回 done / paused / cancelled。"""
    existing = await _list_units(job_id)
    have = {int(u.get("idx") or 0) for u in existing}
    missing = [(i, item) for i, item in enumerate(plan) if i not in have]
    if missing:
        await _insert_units(job_id, run_id, missing)
        existing = await _list_units(job_id)
    if not existing:
        raise RuntimeError(
            "生成单元表不可用（upload_job_units）；请先执行 "
            "backend/sql/agent_orchestration.sql")

    # 上次 worker 崩在「正在生成」的单元，恢复时重新排队；
    # 失败单元也允许再试一次（LLM 抖动不该让整批永久失败）。
    reset = False
    for u in existing:
        if u.get("status") == "generating":
            await _update_unit(u["id"], status="pending")
            reset = True
        elif u.get("status") == "failed":
            await _update_unit(u["id"], status="pending", error=None)
            reset = True
    if reset:
        existing = await _list_units(job_id)

    total = max(1, len(existing))
    completed = len([u for u in existing
                     if u.get("status") in ("done", "failed", "skipped")])
    done = len([u for u in existing if u.get("status") == "done"])
    pending = [u for u in existing if u.get("status") == "pending"]

    progress_lock = asyncio.Lock()
    counts = {"completed": completed, "done": done}

    async def report():
        pct = 5 + int(75 * counts["completed"] / total)
        rpct = 25 + int(60 * counts["completed"] / total)
        await upload_runs.set_progress(
            job_id, run_id, pct, "generating",
            run_progress=rpct, generated_count=counts["done"])

    # 恢复时先把真实进度写回去，别让界面从 5% 重新爬
    await report()

    if not pending:
        return "done"

    q: asyncio.Queue = asyncio.Queue()
    for u in pending:
        q.put_nowait(u)
    stop = asyncio.Event()

    async def one_unit():
        while not stop.is_set():
            try:
                unit = q.get_nowait()
            except asyncio.QueueEmpty:
                return
            state = await _stop_state(job_id, user_id)
            if state:
                stop.set()
                return
            seed = seeds_by_id.get(str(unit.get("seed_id") or "").lower())
            if not seed:
                await _update_unit(unit["id"], status="skipped",
                                   error="可出题点已删除")
                async with progress_lock:
                    counts["completed"] += 1
                    await report()
                continue

            await _update_unit(unit["id"], status="generating", error=None)
            err = ""
            qobj = None
            try:
                async with _global_llm_sem():
                    qobj = await _call_one(
                        seed, unit.get("qtype") or "choice", difficulty, profile)
            except Exception as e:                          # noqa: BLE001
                err = str(e)[:300]
                logger.info(f"[upload] 单元 {unit.get('idx')} 生成失败: {err}")
            if qobj:
                await _update_unit(unit["id"], status="done",
                                   question=qobj, error=None)
            else:
                await _update_unit(unit["id"], status="failed",
                                   error=err or "未通过结构/命题校验")

            async with progress_lock:
                counts["completed"] += 1
                if qobj:
                    counts["done"] += 1
                await report()

            if await _stop_state(job_id, user_id):
                stop.set()
                return

    workers = [asyncio.create_task(one_unit())
               for _ in range(max(1, min(CONCURRENCY, len(pending))))]
    await asyncio.gather(*workers, return_exceptions=True)

    state = await _stop_state(job_id, user_id)
    if state:
        return state
    return "done"


async def _mark_paused_from_units(job_id: str, user_id: str, run_id: Optional[str],
                                  stage: str = "paused") -> None:
    units = await _list_units(job_id)
    total = max(1, len(units))
    completed = len([u for u in units
                     if u.get("status") in ("done", "failed", "skipped")])
    await upload_jobs.mark_paused(
        job_id, user_id, run_id,
        progress=5 + int(75 * completed / total),
        run_progress=25 + int(60 * completed / total),
        stage=stage)


async def generate_for_job(job_id: str, user_id: str,
                           run_id: Optional[str] = None) -> dict:
    job = await upload_jobs.get_job(job_id, user_id)
    if not job:
        return {"ok": False, "error": "上传任务不存在"}
    run_id = run_id or job.get("run_id")
    if job.get("status") == "cancelled" or job.get("cancel_requested"):
        await upload_runs.mark_cancelled(job_id, user_id, run_id)
        return {"ok": False, "cancelled": True}
    if job.get("status") not in ("confirmed", "queued", "generating", "paused"):
        return {"ok": False, "error": f"当前状态不能生成：{job.get('status')}"}

    _profile = job.get("profile") or {}
    if isinstance(_profile, str):
        try:
            _profile = json.loads(_profile)
        except (ValueError, TypeError):
            _profile = {}
    profile = dict(_profile)
    phase = str(profile.get("generate_phase") or "")

    # 暂停状态被误投递（例如队列里还留着旧 job）：直接确认暂停，不干活
    if job.get("status") == "paused" or job.get("pause_requested"):
        if phase in ("", "generating", "verifying"):
            await _mark_paused_from_units(job_id, user_id, run_id)
            return {"ok": True, "paused": True}
        return {"ok": False, "error": "任务已暂停"}

    if phase == "done" or job.get("status") == "ready":
        return {"ok": True, "already": True}
    if phase == "saving":
        # 落库阶段中断：题目可能已经写了一半，自动重跑会重复
        await upload_runs.mark_failed(
            job_id, user_id, run_id,
            "上次在保存阶段中断，可能有部分题目已写入；为避免重复，请重新上传",
            job.get("filename") or "上传文件")
        return {"ok": False, "error": "保存阶段中断，已停止自动重试"}

    # 老库/老任务没有 phase：保留原来的「有产出就不自动重跑」保护
    if not phase and job.get("status") == "generating" \
            and int(job.get("generated_count") or 0) > 0:
        await upload_runs.mark_failed(
            job_id, user_id, run_id,
            "上次生成中途中断，已停止自动重试以免重复出题；请重新上传或联系管理员",
            job.get("filename") or "上传文件")
        return {"ok": False, "error": "生成中途中断，已停止重试"}

    seeds = await upload_jobs.get_selected_seeds(job_id, user_id)
    if not seeds:
        return {"ok": False, "error": "没有选中的可出题点"}
    seeds_by_id = {str(s.get("id") or "").lower(): s for s in seeds}

    confirm = profile.get("confirm") or {}
    count = max(1, min(MAX_PER_RUN, int(confirm.get("count") or 8)))
    type_map = {"选择题": "choice", "判断题": "judge", "填空题": "fill",
                "计算题": "calculation", "简答题": "essay", "论述题": "essay"}
    types = [type_map.get(str(t), str(t) if str(t) in
                          ("choice", "judge", "fill", "calculation", "essay")
                          else "choice")
             for t in (confirm.get("types") or ["选择题"])][:4] or ["choice"]
    difficulty = str(confirm.get("difficulty") or "中等")

    plan = profile.get("generate_plan") or []
    if phase != "verifying" and not plan:
        plan = _build_plan(seeds, count, types)
    profile["generate_plan"] = plan
    if not phase:
        phase = "generating"
        profile["generate_phase"] = "generating"
    await upload_jobs.update_job(job_id, profile=profile)

    started = _now()
    if phase == "generating":
        await upload_runs.set_progress(
            job_id, run_id, 5, "generating", run_progress=25,
            status="generating", started_at=job.get("started_at") or started,
            generated_count=int(job.get("generated_count") or 0),
            passed_count=int(job.get("passed_count") or 0), error=None)
        await upload_runs.set_run(
            run_id, status="running", started_at=job.get("started_at") or started)
        plan_step = await upload_runs.add_step(
            run_id, "plan", status="running")
        await upload_runs.finish_step(
            plan_step, output={"count": len(plan), "types": types,
                               "difficulty": difficulty, "seeds": len(seeds)})
        gen_step = await upload_runs.add_step(
            run_id, "generate", status="running",
            input_data={"count": len(plan)})
        state = await _generate_units(
            job_id, user_id, run_id, seeds_by_id, plan, profile, difficulty)
        if state == "cancelled":
            await upload_runs.finish_step(gen_step, status="cancelled")
            await upload_runs.mark_cancelled(job_id, user_id, run_id)
            return {"ok": False, "cancelled": True}
        if state == "paused":
            await upload_runs.finish_step(gen_step, status="skipped")
            await _mark_paused_from_units(job_id, user_id, run_id)
            return {"ok": True, "paused": True}

        profile["generate_phase"] = "verifying"
        await upload_jobs.update_job(job_id, profile=profile)
        units = await _list_units(job_id)
        await upload_runs.finish_step(
            gen_step, output={"generated": len(units),
                              "done": len([u for u in units
                                           if u.get("status") == "done"])})
    elif phase == "verifying":
        # 从「复核前」的暂停恢复：生成已全部完成，不再重跑单元
        await upload_runs.set_progress(
            job_id, run_id, 82, "crosschecking", run_progress=88,
            status="generating", error=None)
        await upload_runs.set_run(
            run_id, status="running", started_at=job.get("started_at") or started)
    else:
        return {"ok": False, "error": f"未知生成阶段：{phase}"}

    # ---------- 独立复核 + 落库 ----------
    state = await _stop_state(job_id, user_id)
    if state == "cancelled":
        await upload_runs.mark_cancelled(job_id, user_id, run_id)
        return {"ok": False, "cancelled": True}
    if state == "paused":
        await _mark_paused_from_units(job_id, user_id, run_id)
        return {"ok": True, "paused": True}

    units = await _list_units(job_id)
    if not units:
        await upload_runs.mark_failed(
            job_id, user_id, run_id,
            "生成单元丢失，无法继续复核；请重新上传",
            job.get("filename") or "上传文件")
        return {"ok": False, "error": "生成单元丢失"}
    candidates: list[tuple[dict, dict]] = []
    dropped: list[dict] = []
    for u in units:
        status = u.get("status")
        seed = seeds_by_id.get(str(u.get("seed_id") or "").lower())
        if status == "done" and u.get("question") and seed:
            candidates.append((seed, u["question"]))
        elif status == "failed":
            dropped.append({"reason": (u.get("error") or "生成失败")[:200],
                            "seed": u.get("seed_id")})
        elif status == "skipped":
            dropped.append({"reason": "可出题点已删除", "seed": u.get("seed_id")})
        elif status == "pending":
            # 理论上不会发生（暂停会提前返回）；保守起见不把没生成的题算通过
            dropped.append({"reason": "未生成（任务中断）", "seed": u.get("seed_id")})

    verify_step = await upload_runs.add_step(run_id, "verify", status="running")
    await upload_runs.set_progress(
        job_id, run_id, 82, "crosschecking", run_progress=88)
    cross = await _crosscheck_batch(candidates)

    passed_items: list[dict] = []
    for i, (seed, q) in enumerate(candidates):
        verdict = cross.get(i)
        if verdict and not verdict[0]:
            dropped.append({
                "reason": "独立复核未通过：" + "；".join(
                    str(x)[:80] for x in verdict[1][:3]),
                "seed": seed.get("seed_key"),
                "title": (q.get("title") or "")[:60],
            })
            continue
        saved = await _insert_question(user_id, job, seed, q)
        if saved:
            passed_items.append(saved)
        else:
            dropped.append({"reason": "题目落库失败", "seed": seed.get("seed_key")})
    await upload_runs.finish_step(
        verify_step, output={"passed": len(passed_items),
                             "dropped": len(dropped)})

    state = await _stop_state(job_id, user_id)
    if state == "cancelled":
        await upload_runs.mark_cancelled(job_id, user_id, run_id)
        return {"ok": False, "cancelled": True}
    if state == "paused":
        # 复核已经跑完，但还没开始写题集；恢复时重新复核即可，不会重复写题
        await _mark_paused_from_units(job_id, user_id, run_id)
        return {"ok": True, "paused": True}

    # 从这里开始写 questions / question_sets / generation_history。
    # 落库阶段不再接受暂停：中途停下会产生半套数据，恢复时可能重复写。
    profile["generate_phase"] = "saving"
    await upload_jobs.update_job(job_id, profile=profile)

    aggregate_step = await upload_runs.add_step(
        run_id, "aggregate", status="running")
    await upload_runs.set_progress(
        job_id, run_id, 90, "saving", run_progress=92)

    generated = len(units)
    if not passed_items:
        await upload_runs.finish_step(
            aggregate_step, output={"generated": generated, "passed": 0})
        profile["generate_phase"] = "done"
        await upload_jobs.update_job(
            job_id, profile={**profile, "generate_result": {
                "generated": generated, "passed": 0, "dropped": dropped[:20]}})
        await upload_runs.set_run(
            run_id, title=f"已完成：{job.get('filename') or '上传文件'}"[:200])
        await upload_runs.mark_ready(
            job_id, user_id, run_id, None, 0, len(dropped),
            generated=generated)
        return {"ok": True, "set_id": None, "passed": 0,
                "dropped": dropped, "message": "这批题都没通过质检，我没有把坏题塞给你。"}

    set_id = await _create_set(user_id, job, [q["id"] for q in passed_items],
                               len(passed_items), len(dropped))
    if not set_id:
        await upload_runs.finish_step(
            aggregate_step, status="failed", error="题集创建失败")
        await upload_runs.mark_failed(
            job_id, user_id, run_id,
            "题目已生成，但题集创建失败（question_sets.source 列未建？）",
            job.get("filename") or "上传文件")
        return {"ok": False, "error": "题集创建失败"}

    for q in passed_items:
        await _insert_history(user_id, job, set_id, q)

    profile["generate_phase"] = "done"
    await upload_jobs.update_job(
        job_id, profile={**profile, "generate_result": {
            "generated": generated, "passed": len(passed_items),
            "dropped": dropped[:20]}})
    await upload_runs.finish_step(
        aggregate_step, output={"set_id": set_id,
                                "passed": len(passed_items),
                                "dropped": len(dropped)})
    await upload_runs.set_run(
        run_id, title=f"已完成：{job.get('filename') or '上传文件'}"[:200])
    await upload_runs.mark_ready(
        job_id, user_id, run_id, set_id, len(passed_items), len(dropped),
        generated=generated)

    await _notify(user_id, job.get("filename") or "上传文件", set_id,
                  len(passed_items), len(dropped))
    return {"ok": True, "set_id": set_id, "passed": len(passed_items),
            "dropped": dropped, "questions": passed_items}
