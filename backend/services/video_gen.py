"""视频库生成引擎（2026-09-04 定稿）

知识点级模板生成视频：
  LLM 脚本（qwen-turbo，DashScope）→ 讯飞 TTS → Supabase Storage 音轨。

省钱原则（定稿）：
  1. 视频单元 = 知识点，与题目无关：一个新知识点只生成一次，其下所有题复用
  2. 按格生产：(subject, knowledge_key, angle) 唯一约束 + generating 占位幂等，并发等复用
  3. 热度分级铺格：use_count 驱动扩产，钱花在高频知识点上
  4. 脚本与音轨解耦：换音色/重录只需重跑 TTS（script_text 已落库可复用）
  5. 进程内 asyncio 队列（挂 lifespan），默认单 worker 串行压低 API 并发

差异化四轴（随机组合，观感 2000+）：
  讲解角度 12 × 叙事风格 6 × 画面模板 6 × 音色池 3
"""
import asyncio
import hashlib
import json
import random
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from config import settings
from services.supabase import db
from agents.qwen_client import call_qwen
from utils.qwen_tts_client import get_tts_audio as qwen_tts
from logging_config import logger

# ==================== 差异化四轴 ====================

# 讲解角度：(key, 名称, 给 LLM 的讲解定位)
ANGLE_POOL: List[tuple] = [
    ("concept", "概念精讲", "把知识点的核心概念讲透，为什么存在、解决什么问题"),
    ("method", "方法论框架", "给出通用步骤框架，学生套着步骤就能做一类题"),
    ("pitfall", "易错排雷", "盘点最常见错误做法，逐条拆解坑在哪里"),
    ("shortcut", "秒杀技巧", "给出快速路径和判断窍门，一眼定位切入点"),
    ("contrast", "对比辨析", "把易混概念/结构并排对比，一条条抠差别"),
    ("origin", "根源推导", "从原理推导公式结论，让学生理解来龙去脉"),
    ("mnemonic", "口诀记忆", "编朗朗上口的口诀或记忆锚点，快速记牢"),
    ("exam", "考试视角", "站在出题人角度讲考什么、常怎么考、怎么拿分"),
    ("notes", "学霸笔记", "结构化干货总结，像学霸整理好的笔记页"),
    ("story", "情境故事", "把知识点放进贴近生活的场景故事里讲"),
    ("visual", "图解演示", "用图示化的空间想象来讲，能画的一定画出来"),
    ("demo", "拆题示范", "挑一道最经典的例题完整示范解题全过程"),
]

# 叙事风格：给 LLM 的语气要求（画面模板与音色在前端播放器/TTS 侧落实）
STYLE_POOL: List[tuple] = [
    ("tutor", "严谨耐心的一线老师，用词规范、节奏稳"),
    ("coach", "训练营教练，短句推进、充满鼓劲"),
    ("friend", "成绩好的同桌，口语自然、像聊天一样"),
    ("story", "讲故事的人，有场景有悬念"),
    ("professor", "大学教授研讨腔，重视原理与推演"),
    ("punchy", "短视频快节奏，金句密集、直接给结论"),
]

# 画面模板 key（前端播放器按 key 渲染不同视觉壳；后端只落库）
# 画面模板池（2026-09-05 用户拍板扩到 10 套，参考短视频形式；播放器按 template_key 换美术皮肤）
TEMPLATE_POOL = [
    "chalkboard",   # 黑板听讲：木质框黑板 + 粉笔字
    "paper",        # 手写笔记：纸纹 + 楷体 + 荧光笔
    "whiteboard",   # 白板手绘：马克笔粗线 + 涂鸦箭头
    "chat",         # 聊天流：气泡对话，学生问老师答
    "qa",           # 问答反转：大卡片揭晓答案
    "fun",          # 弹幕贴纸：贴纸吐槽 + 活泼弹跳
    "neon",         # 赛博霓虹：黑底发光描边 + 网格扫描线
    "mindmap",      # 思维导图：中心词 + 分支节点
    "glass",        # 玻璃流光：毛玻璃卡片 + 光晕（全站品牌一致）
    "compare",      # 左右擂台：错 vs 对分屏对决
]

# 音色池（2026-09-04 用户定调：小基同款千问声色——温柔/清新/开朗/知心四档）
VOICE_POOL = ["longanqian", "longanlingxi", "longanlufeng", "longanlingxin"]

# ==================== 脚本提示词 ====================

# 氛围四态（2026-09-04 用户定调：一个视频内按内容切换气质——严谨/轻松/强调/示范）
MOODS = ("lecture", "story", "highlight", "demo")


def _infer_mood(heading: str) -> str:
    h = heading or ""
    if any(k in h for k in ("例", "示范", "题")): return "demo"
    if any(k in h for k in ("口诀", "记住", "重点", "必背", "强调")): return "highlight"
    if any(k in h for k in ("比喻", "故事", "身边", "生活", "打比方")): return "story"
    return "lecture"


# ===== 演示构件学科纪律（2026-09-05 用户拍板：四级视频里出现算法例题不行）=====
# array 数值演示只属于数学/算法/编程类科目；其余科目一律禁用——
# 例题必须写本学科真实题型语境，严禁任何数理/编程概念与类比（默认禁用，宁可少用）
ARRAY_ALLOWED_SUBJECTS = {"algorithm-ds", "acm-icpc", "grad-math", "ncre2-python", "ncre2-c"}


def _moves_narration_consistent(script) -> bool:
    """镜内一致性质检（2026-09-05 用户抓包「口播说左指针右移，画面只有右指针动」）：
    口播明确声称的指针移动方向，moves 里必须真实发生一步；未声称的方向不管。"""
    scenes = script.get("scenes") if isinstance(script, dict) else None
    if not isinstance(scenes, list):
        return True
    for sc in scenes:
        if not isinstance(sc, dict) or sc.get("widget") != "array":
            continue
        narr = str(sc.get("narration") or "")
        moves = sc.get("moves")
        if not isinstance(moves, list) or len(moves) < 2:
            continue
        try:
            l_up = any(isinstance(moves[i].get("l"), int) and isinstance(moves[i + 1].get("l"), int)
                       and moves[i + 1]["l"] > moves[i]["l"] for i in range(len(moves) - 1))
            r_down = any(isinstance(moves[i].get("r"), int) and isinstance(moves[i + 1].get("r"), int)
                         and moves[i + 1]["r"] < moves[i]["r"] for i in range(len(moves) - 1))
        except Exception:
            continue
        # 正反两种语序都要认：「左指针右移」和「右移左指针」都算声称左指针右移
        if re.search(r"左指针.{0,4}(右移|往右|向右)|(右移|往右|向右).{0,4}左指针", narr) and not l_up:
            return False
        if re.search(r"右指针.{0,4}(左移|往左|向左)|(左移|往左|向左).{0,4}右指针", narr) and not r_down:
            return False
    return True


def _array_notes_arithmetic_ok(script) -> bool:
    """确定性数字质检（2026-09-05 用户连环抓包 note 算错和/长度）：
    array 镜 note 里的「和N」必须是窗和（values[l..r] 之和）或双指针和（values[l]+values[r]）之一，
    「长度N」必须等于 r-l+1。数字不符即判不合格。"""
    scenes = script.get("scenes") if isinstance(script, dict) else None
    if not isinstance(scenes, list):
        return True
    for sc in scenes:
        if not isinstance(sc, dict) or sc.get("widget") != "array":
            continue
        params = sc.get("params") if isinstance(sc.get("params"), dict) else {}
        values = params.get("values")
        moves = params.get("moves")   # 2026-09-05 修：moves 在 params 里，之前读 sc.moves 一直为空转
        if not isinstance(values, list) or not isinstance(moves, list):
            continue
        nums = []
        for v in values:
            try:
                nums.append(float(v))
            except (TypeError, ValueError):
                nums = None
                break
        if nums is None or len(nums) < 2:
            continue
        for m in moves:
            if not isinstance(m, dict):
                continue
            try:
                l, r = int(m.get("l")), int(m.get("r"))
            except (TypeError, ValueError):
                continue
            if l < 0 or r < l or r >= len(nums):
                continue
            note = str(m.get("note") or "")
            wsum = sum(nums[l:r + 1])
            psum = nums[l] + nums[r]
            ms = re.search(r"和(?:为|=|是|等于)?\s*([0-9]+(?:\.[0-9]+)?)", note)
            if ms:
                n = float(ms.group(1))
                # 「窗口和」只认真正的窗和；普通「和」允许指针和或窗和之一
                if "窗口" in note:
                    if abs(n - wsum) > 1e-6:
                        return False
                elif abs(n - wsum) > 1e-6 and abs(n - psum) > 1e-6:
                    return False
            mlen = re.search(r"长度\s*([0-9]+)", note)
            if mlen and int(mlen.group(1)) != (r - l + 1):
                return False
    return True


def _demo_discipline(subject: str) -> tuple:
    """返回 (demo_min 构件提示, 学科纪律段落, 理科例题正确性纪律)。
    语言/文科类禁 array；数理类放宽但例题仍限本学科；算法类强制「正统无歧义 + 前提原理讲透」。"""
    subject = subject or "通用"
    if subject in ARRAY_ALLOWED_SUBJECTS:
        return (
            "array/balance/example",
            "本学科允许 array 构件做数值演示，但例题仍必须是本学科题型原文语境，不得把例题写成别的学科（如数学例题不得写成代码题）。",
            "算法/编程类例题纪律（最高优先）：双指针例题**默认讲「滑动窗口」经典题**——长度最小的子数组"
            "（[2,3,1,2,4,3]，求和 ≥7。array 演示**用无 target 走路模式（target 留空)**，note 标注窗口和。标准走查：窗口依次 2、5、6、8(len4 记录)→移 l 后 6→加 4 后 10→移 l 后 7(len3 记录)→移 l 后 6→加 3 后 9→移 l 后 7(len2，即 [4,3])→**答案 2**。每个和值必须自己重新相加核对，一步不许错，moves 要走到出现答案那一步为止）；"
            "或讲无重复字符的最长子串。**不要再用「两数之和」当主打例题**——只有完整讲清「数组有序前提＋单调性原理"
            "（l 右移和只增、r 左移和只减，才能双向收缩）」时才允许；任何算法题的前提、步骤、结论必须数学上完全正确，一步不能错、含糊的别讲。",
        )
    return (
        "balance/example",
        "本学科不是数理/编程类，**严禁使用 array 构件**；全片严禁出现「数组、数列、两数之和、指针、算法、代码、变量、遍历、二分」等任何数理/编程概念或比喻。"
        "图形演示只用 balance(易错对比) 和 example(例题演算)；例题必须是本学科真实题型的原样语境"
        "（英语阅读给英文短文主旨/细节题，语法给英文例句判断，政治给真实选择题题干，司法给案例题题干，教资试讲给课堂情景）。",
        "",
    )


# 脚本 JSON 骨架：生成提示词与质检修补提示词共用，字段只维护这一处
_SCRIPT_SCHEMA = """{
  "title": "≤14字标题",
  "hook": "开场悬念问题，≤16字",
  "scenes": [
    {"mood": "lecture|story|highlight|demo", "widget": "point|array|balance|example|phrase", "params": {...}, "narration": "该镜头口播句"}
  ],
  "narration": "各镜口播连成的完整口播稿(360~520字)"
}"""


_SCRIPT_PROMPT = """你是资深教研老师 + 分镜师。给一个知识点做 60~90 秒学习短视频，画面由「演示构件」表演，禁止满屏文字。

知识点：{knowledge_name}
学科：{subject}
讲解角度：{angle_name}——{angle_desc}
讲述风格：{style_desc}

【结构】（顺序不可乱）
1. 开场 2.2 秒是「钩子」（hook 字段）：一个与主题强相关的悬念问题，不是标题
2. 主体推进：概念讲透 → 易错对比 → 图形演示 → 经典例题 → 口诀收束
3. 结尾一句话收束，让人记得住

【构件】（每个镜头用一件构件表演；画面主体是图形，文字只做批注）
- point：纯文字批注，text≤14字，全片最多 2 个
- balance：易错对比，left/right 各 {{"title":"≤8字","lines":["每条≤12字"]}}，讲「错做法 vs 对做法」
- example：例题演算台，stem≤40字，work=演算步骤 3~5 条每条≤16字，answer≤12字（可空）
- array：数值演示，values=数字列表，target=目标值(可空)，moves=步骤：每步 {{"l":左指针下标,"r":右指针下标(可空),"note":"≤12字批注"}}，3~6 步；两数之和模式靠单调性收缩、滑动窗口模式 target 留空并逐窗算和
- phrase：金句/口诀，text≤16字

【硬性要求】（违反任何一条即重写）
1. scenes 6~9 个；每镜 narration 是该镜 1~3 句完整口播、45~70 字——把「为什么这么做、关键动作、哪里易错」讲透，绝不一句话带过
2. 各镜 narration 连起来即完整口播稿，总 360~520 字；句子短、口语化；禁 markdown、emoji；写完自查字数，不足就扩写或加镜
3. 至少 1 个 {demo_min} 构件和 1 个 phrase 收束
4. 例题要经典：选「当前知识点」流传最广、最出圈的教材/真题原型，数字小而具体，步骤一步步走完且与答案完全一致；不编题号出处；知识点内容拿不准的宁可省略
5. mood 每镜一个：lecture 严谨 / story 轻松比喻 / highlight 重点强调 / demo 例题示范；全片至少 2 种
6. 学科纪律（最高优先）：{demo_rule}
7. 演示与口播严格一致（array 专属）：口播声称的指针移动方向必须真实发生在 moves 里——声称哪种方向，就选数值把那种方向真实演一遍。严禁口播一套、moves 一套
8. {example_hint}
9. 数字零误差（最高优先）：note 优先写状态词（太大/太小/找到/缩小窗口/记录），**能不用具体数字就不用**；一旦写了数字（画面、note、口播），就必须等于用 values 重算的结果——「和N」=窗口和或双指针和、「长度N」=r-l+1，拿不准就换成状态词

严格只输出 JSON：
{schema}"""


def _extract_json(text: str) -> Optional[dict]:
    """从 LLM 回复里抠 JSON（容忍 ```json 围栏与前后杂文）"""
    if not text:
        return None
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*", "", t)
    t = re.sub(r"\s*```$", "", t)
    try:
        return json.loads(t)
    except Exception:
        pass
    lo, hi = t.find("{"), t.rfind("}")
    if lo != -1 and hi > lo:
        try:
            return json.loads(t[lo:hi + 1])
        except Exception:
            return None
    return None


def make_knowledge_key(subject: str, kp_id: str) -> str:
    """稳定、url-safe 的知识点键：学科 + kp_id 短哈希（展示用 knowledge_name 另存）"""
    h = hashlib.sha1(str(kp_id).strip().encode("utf-8")).hexdigest()[:12]
    return f"{subject}:{h}"


def question_fingerprint(stem: str, options: Any = None, answer: Any = None) -> str:
    """题干归一化指纹（去空白/标点/全半角）→ sha1 前 16 位"""
    norm = str(stem or "")
    norm = norm.lower().replace("（", "(").replace("）", ")").replace("，", ",").replace("。", ".")
    norm = re.sub(r"[^\w一-鿿]+", "", norm)
    return hashlib.sha1(norm.encode("utf-8")).hexdigest()[:16]


# ==================== 队列与工作循环 ====================

# 队列元素：{subject, knowledge_key, angle}（生成时按唯一格回查行，行是唯一事实源）
_queue: asyncio.Queue = asyncio.Queue()
_pending: set = set()   # (subject, knowledge_key, angle) 已排队未完成，防重复入队


def start_video_worker() -> asyncio.Task:
    """启动后台生成 worker（main.py lifespan 挂载，进程内、不依赖外部队列）"""
    tasks = [
        asyncio.create_task(_worker_loop(i))
        for i in range(max(1, settings.VIDEO_WORKERS))
    ]
    return asyncio.ensure_future(asyncio.gather(*tasks))


def requeue_spec(subject: str, knowledge_key: str, angle: str) -> None:
    """把某格重新排进队列（复活重试/用户生成用），_pending 去重幂等"""
    gkey = (subject, knowledge_key, angle)
    if gkey in _pending:
        return
    _pending.add(gkey)
    _queue.put_nowait({"subject": subject, "knowledge_key": knowledge_key, "angle": angle})


async def _worker_loop(idx: int):
    logger.info(f"🎬 视频生成 worker[{idx}] 启动")
    while True:
        spec = await _queue.get()
        gkey = (spec["subject"], spec["knowledge_key"], spec["angle"])
        retrying = False
        try:
            retrying = await _generate_one(spec)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.info(f"❌ worker[{idx}] 未捕获异常: {e}")
        finally:
            _queue.task_done()
            if not retrying:
                _pending.discard(gkey)


async def _get_row(subject: str, knowledge_key: str, angle: str) -> Optional[dict]:
    """按唯一格回查生成行（生成时刻的最新事实：attempts/音色/风格都以库里为准）"""
    resp = await db.select("video_library", select="*", eq={
        "subject": subject, "knowledge_key": knowledge_key, "angle": angle,
    }, use_service_role=True)
    rows = resp.json() if resp.status_code < 300 else []
    return rows[0] if rows else None


def _angle_info(key: str) -> tuple:
    return dict((a[0], a) for a in ANGLE_POOL).get(key, ANGLE_POOL[0])


def _style_info(key: str) -> tuple:
    return dict((s[0], s) for s in STYLE_POOL).get(key, STYLE_POOL[0])


async def _generate_one(spec: dict) -> bool:
    """生成单条：脚本(LLM) → 口播(TTS) → 上传(storage) → 状态 ready。
    返回 True = 稍后自动重试（占位保留），False = 本格工作收尾。"""
    row = await _get_row(spec["subject"], spec["knowledge_key"], spec["angle"])
    if not row:
        logger.info(f"⚠️ 生成行不存在（可能被删）: {spec}")
        return False

    vid = row["id"]
    try:
        # 1. 脚本
        angle = _angle_info(row.get("angle"))
        style = _style_info(row.get("style"))
        subject = row["subject"] or "通用"
        demo_min, demo_rule, example_hint = _demo_discipline(subject)
        prompt = _SCRIPT_PROMPT.format(
            schema=_SCRIPT_SCHEMA,
            knowledge_name=row["knowledge_name"],
            subject=subject,
            angle_name=angle[1],
            angle_desc=angle[2],
            style_desc=style[1],
            demo_min=demo_min,
            demo_rule=demo_rule,
            example_hint=example_hint or "",
        )

        def _discipline_ok(s) -> bool:
            """学科纪律质检：非数理学科出现 array 构件 = 不合格（2026-09-05）"""
            if subject in ARRAY_ALLOWED_SUBJECTS:
                return True
            return not any(sc.get("widget") == "array" for sc in (s.get("scenes") or []))

        def _structure_ok(s) -> bool:
            """结构质检（2026-09-05）：分镜脚本必须 6~9 镜；旧 sections 脚本另算"""
            scenes = s.get("scenes")
            if isinstance(scenes, list) and scenes:
                return 6 <= len(scenes) <= 9
            return isinstance(s.get("sections"), list) and bool(s.get("sections"))

        def _reasons_of(scr, nar) -> list:
            """把不过关的具体原因列出来（进错误信息与修补提示，方便排障）"""
            if not scr:
                return ["JSON失败"]
            out = []
            if not scr.get("narration"):
                out.append("无narration")
            elif len(nar or "") < 240:
                out.append(f"口播{len(nar)}字<240")
            if not _structure_ok(scr):
                out.append("镜数非6~9")
            if not _discipline_ok(scr):
                out.append("学科违规")
            if not _moves_narration_consistent(scr):
                out.append("口播方向与moves不一致")
            if not _array_notes_arithmetic_ok(scr):
                out.append("note算术错误")
            return out

        raw = await asyncio.to_thread(
            call_qwen, [{"role": "user", "content": prompt}],
            temperature=0.75, model=settings.QWEN_VIDEO_MODEL,
        )
        script = _extract_json(raw)
        narration = str(script.get("narration", "")).strip() if script else ""
        scenes = script.get("scenes") if script else None
        # 兜底拼接：模型偶把完整口播散在各镜 narration 而顶格 summary 写短——
        # 与提示词「各镜 narration 连起来即口播稿」同语义，达标即采纳（省一次修补 LLM 调用）
        if script and len(narration) < 240 and isinstance(scenes, list):
            joined = "".join(str(sc.get("narration") or "") for sc in scenes).strip()
            if len(joined) >= 240:
                narration = joined
                script["narration"] = joined
        script_ok = bool(script and script.get("narration") and len(narration) >= 240
                         and _structure_ok(script)
                         and _discipline_ok(script)
                         and _moves_narration_consistent(script)
                         and _array_notes_arithmetic_ok(script))
        if not script_ok:
            # 一次修补重写（turbo 偶发输出短稿/半截 JSON/学科违规/演示口播不一致）：明确问题让它重来
            disc_hint = ("；另外：本学科严禁 array 构件（改用 balance/example），"
                         "严禁任何算法/数列/代码类概念或比喻，例题必须是本学科题型语境") \
                if subject not in ARRAY_ALLOWED_SUBJECTS else ""
            move_hint = ("；array 镜：口播里声称的指针移动方向必须在 moves 里真实发生——"
                         "讲「左指针右移」就让某一步 l 变大、讲「右指针左移」就让某一步 r 变小，"
                         "并选用能让这些方向都演示到的数字") \
                if not _moves_narration_consistent(script) else ""
            arith_hint = ("；array 镜某步 note 的数字算错了：note 里的「和N」必须是该步窗口所有数字之和"
                          "（或双指针两数之和）、「长度N」必须等于右指针-左指针+1——"
                          "把每一步的数字用 values 重新加一遍，零误差再输出") \
                if not _array_notes_arithmetic_ok(script) else ""
            struct_hint = ("；scenes 必须是 6~9 个镜头（当前不够/超了，增删镜头补齐）") \
                if script and not _structure_ok(script) else ""
            repair = ("你刚才的脚本输出没有通过质检（JSON 不完整、镜数不合规、口播字数不足或内容违规）。"
                      "请重新完整输出，仍然只输出 JSON：" + _SCRIPT_SCHEMA +
                      "（口播总字数不足就逐镜扩写：补做法原因、易错点、动作细节）"
                      + disc_hint + move_hint + arith_hint + struct_hint)
            raw2 = await asyncio.to_thread(
                call_qwen,
                [{"role": "user", "content": prompt},
                 {"role": "assistant", "content": (raw or "")[:3000]},
                 {"role": "user", "content": repair}],
                temperature=0.7, model=settings.QWEN_VIDEO_MODEL,
            )
            script2 = _extract_json(raw2)
            narration2 = str(script2.get("narration", "")).strip() if script2 else ""
            scenes2 = script2.get("scenes") if script2 else None
            if script2 and len(narration2) < 240 and isinstance(scenes2, list):
                joined2 = "".join(str(sc.get("narration") or "") for sc in scenes2).strip()
                if len(joined2) >= 240:
                    narration2 = joined2
                    script2["narration"] = joined2
            if script2 and script2.get("narration") and len(narration2) >= 240 \
                    and _structure_ok(script2) \
                    and _discipline_ok(script2) \
                    and _moves_narration_consistent(script2) \
                    and _array_notes_arithmetic_ok(script2):
                script = script2
                narration = narration2
            else:
                r1 = "; ".join(_reasons_of(script, narration)) or "通过"
                r2 = "; ".join(_reasons_of(script2, narration2)) or "通过"
                raise ValueError(f"脚本两次质检不通过：初稿[{r1}] / 修补稿[{r2}]")
        narration = str(script["narration"]).strip()

        # 分镜规范化：widget 白名单（未知构件降级为 point）；mood 白名单 + 标题线索推断兜底
        WIDGETS = {"point", "array", "balance", "example", "phrase"}
        for sc in (script.get("scenes") or []):
            if sc.get("widget") not in WIDGETS:
                p = sc.get("params")
                if not isinstance(p, dict):
                    p = {}
                sc["widget"] = "point"
                sc["params"] = {"text": str(p.get("text", "")) or "讲解要点"}
            m = sc.get("mood")
            if m not in MOODS:
                sc["mood"] = _infer_mood(str(sc.get("narration") or "")[:30])
        # 兼容旧版 sections 脚本：mood 归一化
        for sec in (script.get("sections") or []):
            m = sec.get("mood")
            if m not in MOODS:
                sec["mood"] = _infer_mood(str(sec.get("heading") or ""))

        # 2. TTS（2026-09-04 用户定调：只用阿里云千问，便于统一管理；失败走行级重试）
        voice = row.get("voice_key") if row.get("voice_key") in VOICE_POOL else VOICE_POOL[0]
        audio = await asyncio.to_thread(qwen_tts, narration, voice=voice, speed=settings.VIDEO_TTS_SPEED)
        if not audio:
            raise RuntimeError("千问 TTS 返回空音频")
        tts_engine = "qwen"

        # 3. 上传 storage（公共读桶；新视频是新对象，anon 直插即可）
        resp = await db.storage_upload("video-lib", f"{vid}/audio.mp3", audio, content_type="audio/mpeg")
        if resp.status_code >= 300:
            raise RuntimeError(f"storage 上传失败 {resp.status_code}: {resp.text[:120]}")

        # 4. 落库 ready
        audio_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/video-lib/{vid}/audio.mp3"
        # 时长估算按语速档换算：6 档 ≈ 6.2 字/秒，档位越低越慢越长（与脚本时间轴同一口径；
        # 播放器实际用 <audio> 元数据实时校准，此处仅供列表展示）
        _rate6 = 0.5 + 5 / 8 * 1.5
        _rate = 0.5 + (max(1, min(9, int(settings.VIDEO_TTS_SPEED))) - 1) / 8 * 1.5
        _cps = 6.2 * (_rate / _rate6)
        await db.update("video_library", eq={"id": vid}, data={
            "status": "ready",
            "title": str(script.get("title", ""))[:40],
            "script": script,
            "script_text": narration,
            "audio_url": audio_url,
            "audio_duration": round(len(narration) / _cps, 1),
            "error": None,
            "model": settings.QWEN_VIDEO_MODEL,
            "tts_engine": tts_engine,
            "updated_at": datetime.utcnow().isoformat(),
        }, use_service_role=True)
        logger.info(f"✅ 视频就绪: {spec['knowledge_key']} [{spec['angle']}] {vid}")
        return False

    except Exception as e:
        attempts = int(row.get("attempts") or 0) + 1
        await db.update("video_library", eq={"id": vid}, data={
            "status": "failed" if attempts >= 2 else "generating",
            "attempts": attempts,
            "error": str(e)[:500],
            "updated_at": datetime.utcnow().isoformat(),
        }, use_service_role=True)
        logger.info(f"⚠️ 视频生成失败({attempts}): {spec['knowledge_key']} {spec['angle']} - {e}")
        if attempts < 2:
            await asyncio.sleep(5)
            _queue.put_nowait(spec)
            return True   # 稍后重试：占位保留，_pending 不清理
        return False


# ==================== 对外接口 ====================

async def _fetch_videos(knowledge_key: str, subject: str = "", statuses: Optional[List[str]] = None) -> List[dict]:
    """查询某知识点的视频行（默认全部状态）；subject/statuses 在内存过滤（表量小，简单可靠）"""
    resp = await db.select("video_library", select="*",
                           eq={"knowledge_key": knowledge_key}, use_service_role=True)
    rows = resp.json() if resp.status_code < 300 else []
    if subject:
        rows = [r for r in rows if r.get("subject") == subject]
    if statuses:
        rows = [r for r in rows if r.get("status") in statuses]
    return rows


async def _revive_row(row_id: str, subject: str, knowledge_key: str, angle: str) -> bool:
    """复活失败行：重置随机搭配 → generating → 入队（_pending 去重）"""
    await db.update("video_library", eq={"id": row_id}, data={
        "status": "generating",
        "style": random.choice(STYLE_POOL)[0],
        "template_key": random.choice(TEMPLATE_POOL),
        "voice_key": random.choice(VOICE_POOL),
        "model": settings.QWEN_VIDEO_MODEL,
        "error": None,
        "updated_at": datetime.utcnow().isoformat(),
    }, use_service_role=True)
    gkey = (subject, knowledge_key, angle)
    if gkey in _pending:
        return False
    _pending.add(gkey)
    _queue.put_nowait({"subject": subject, "knowledge_key": knowledge_key, "angle": angle})
    return True


async def ensure_videos(
    knowledge_key: str,
    knowledge_name: str,
    subject: str = "",
    stage: str = "",
    goal: int = 1,
    author_name: str = "官方基智",
    author_avatar: str = "/logo.png",
) -> Dict[str, Any]:
    """确保知识点至少有 goal 条视频（ready/generating 都算），缺口排产。
    顺序：先复活 failed 旧行（按住原格，防重复），不够再用未占角度新插。
    返回 {videos, triggered} —— 前端据此直接展示或显示「生成中」。"""
    goal = max(1, min(int(goal), 6))
    rows = await _fetch_videos(knowledge_key, subject, ["ready", "generating"])
    need = goal - len(rows)
    triggered = 0

    if need > 0:
        # ① 先复活失败行（谁失败谁复活——角度格子不动，杜绝同知识点重复行）
        failed_rows = await _fetch_videos(knowledge_key, subject, ["failed"])
        for fr in failed_rows[:need]:
            try:
                if await _revive_row(fr["id"], subject or "", knowledge_key, fr.get("angle")):
                    triggered += 1
            except Exception:
                continue
        need = goal - len(await _fetch_videos(knowledge_key, subject, ["ready", "generating"]))

        # ② 还不够 → 用未被占用的角度新插（含 failed 行已占的角度，防止重复）
        if need > 0:
            active = await _fetch_videos(knowledge_key, subject, ["ready", "generating", "failed"])
            used_angles = {r.get("angle") for r in active}
            used_tpls = {r.get("template_key") for r in active}
            for _ in range(need):
                cands = [a for a in ANGLE_POOL if a[0] not in used_angles]
                if not cands:
                    break
                angle = random.choice(cands)[0]
                gkey = (subject, knowledge_key, angle)
                if gkey in _pending:
                    used_angles.add(angle)
                    continue
                # 同知识点多条视频不撞同一个模板（2026-09-05 用户定调）：先选没用过的
                tpl_cands = [t for t in TEMPLATE_POOL if t not in used_tpls] or list(TEMPLATE_POOL)
                tpl = random.choice(tpl_cands)
                used_tpls.add(tpl)
                row = {
                    "subject": subject or "",
                    "knowledge_key": knowledge_key,
                    "knowledge_name": knowledge_name,
                    "stage": stage or "",
                    "author_name": author_name,
                    "author_avatar": author_avatar,
                    "angle": angle,
                    "style": random.choice(STYLE_POOL)[0],
                    "template_key": tpl,
                    "voice_key": random.choice(VOICE_POOL),
                    "status": "generating",
                    "goal": goal,
                    "tts_engine": "qwen",
                    "prompt_version": 1,
                    "model": settings.QWEN_VIDEO_MODEL,
                }
                resp = await db.insert("video_library", row, use_service_role=True)
                if resp.status_code >= 300:
                    if resp.status_code != 409:
                        logger.info(f"⚠️ 视频占位失败 {resp.status_code}: {resp.text[:150]}")
                    used_angles.add(angle)
                    continue
                _pending.add(gkey)
                _queue.put_nowait({"subject": subject or "", "knowledge_key": knowledge_key, "angle": angle})
                triggered += 1
                used_angles.add(angle)

    # 重新查一遍，把本次占位行也带上（前端显示「生成中」）
    if triggered:
        rows = await _fetch_videos(knowledge_key, subject, ["ready", "generating"])
    return {"videos": rows, "triggered": triggered}


async def related_videos(
    knowledge_key: str,
    subject: str = "",
    question_fingerprint: str = "",
    limit: int = 8,
) -> Dict[str, Any]:
    """检索排行（零 LLM）：
      100 = 本知识点 ready 视频；70 = 同学科其他（按 use_count）；
      55 = 无同科时兜底的全局热门。可选把结果快照进 question_video_links。"""
    primary = await _fetch_videos(knowledge_key, subject, ["ready"])
    primary.sort(key=lambda r: -(r.get("use_count") or 0))
    items = [dict(r, match_score=100) for r in primary]

    if len(items) < limit:
        resp = await db.select("video_library", select="*", use_service_role=True)
        pool = [r for r in (resp.json() if resp.status_code < 300 else []) if r.get("status") == "ready"]
        if subject:
            reserve = sorted(
                (r for r in pool if r.get("subject") == subject and r.get("knowledge_key") != knowledge_key),
                key=lambda r: -(r.get("use_count") or 0),
            )
            fallback_score = 70
        else:
            reserve = sorted(
                (r for r in pool if r.get("knowledge_key") != knowledge_key),
                key=lambda r: -(r.get("use_count") or 0),
            )
            fallback_score = 55
        for r in reserve:
            if len(items) >= limit:
                break
            items.append(dict(r, match_score=fallback_score))

    # 快照题↔视频绑定（先删后插，简单幂等；失败不阻塞检索返回）
    if question_fingerprint and items:
        try:
            await db.delete("question_video_links", eq={"question_fingerprint": question_fingerprint},
                            use_service_role=True)
            for it in items[:limit]:
                await db.insert("question_video_links", {
                    "question_fingerprint": question_fingerprint,
                    "video_id": it["id"],
                    "match_score": it["match_score"],
                }, use_service_role=True)
        except Exception as e:
            logger.info(f"⚠️ 绑定快照写入失败（不影响检索）: {e}")

    return {"items": items, "exact": len(primary)}


async def warm_batch(items: List[dict], goal: int = 1) -> Dict[str, Any]:
    """批量暖库：items = [{subject, stage, knowledge_key, knowledge_name}]，逐条 ensure。
    高频在前（调用方排好序），直接顺序排产。"""
    enqueued = 0
    skipped = 0
    for it in items:
        try:
            res = await ensure_videos(
                it.get("knowledge_key"),
                it.get("knowledge_name") or it.get("knowledge_key"),
                subject=it.get("subject") or "",
                stage=it.get("stage") or "",
                goal=it.get("goal") or goal,
                author_name=it.get("author_name") or "官方基智",
                author_avatar=it.get("author_avatar") or "/logo.png",
            )
            enqueued += res["triggered"]
            if res["triggered"] == 0:
                skipped += 1
        except Exception as e:
            logger.info(f"⚠️ 暖库单条异常 {it.get('knowledge_key')}: {e}")
            skipped += 1
    return {"enqueued": enqueued, "skipped": skipped, "total": len(items)}


def collect_syllabus_knowledge(syllabus_ids: Optional[List[str]] = None, per: int = 0, max_n: int = 0,
                               top_n: int = 0) -> List[dict]:
    """枚举学科计划题库知识点（供暖库脚本/后台批量生成共用）：
    按题数热度倒序；per>0 时每考纲各取前 per；返回 warm 条目清单"""
    from pathlib import Path
    data_dir = Path(__file__).resolve().parent.parent / "data"
    syllabi = json.load(open(data_dir / "syllabi.json", encoding="utf-8"))
    if syllabus_ids:
        syllabi = [s for s in syllabi if s["id"] in set(syllabus_ids)]
    kps = {}
    for s in syllabi:
        bank_file = s.get("question_bank")
        if not bank_file or not (data_dir / bank_file).exists():
            continue
        try:
            bank = json.load(open(data_dir / bank_file, encoding="utf-8"))
        except Exception:
            continue
        for q in bank:
            kp_id = q.get("kp_id") or q.get("sub_category")
            if not kp_id:
                continue
            entry = kps.setdefault(kp_id, {
                "kp_id": kp_id, "name": q.get("kp_name") or kp_id, "count": 0, "syllabus_id": s["id"],
            })
            entry["count"] += 1
    items = sorted(kps.values(), key=lambda x: -x["count"])
    if per > 0:
        by = {}
        for it in items:
            by.setdefault(it["syllabus_id"], []).append(it)
        items = [x for lst in by.values() for x in lst[:per]]
    if max_n > 0:
        items = items[:max_n]
    return [{
        "subject": it["syllabus_id"],
        "knowledge_name": it["name"],
        "knowledge_key": make_knowledge_key(it["syllabus_id"], it["kp_id"]),
        "stage": "",
        "goal": 1,
        "author_name": "官方基智",
        "author_avatar": "/logo.png",
        "heat": it["count"],
    } for it in items]


def queue_stats() -> Dict[str, Any]:
    return {"queue_size": _queue.qsize(), "pending": len(_pending)}