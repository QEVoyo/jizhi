"""工作流模板（代码化编排）。

新增场景 = 加一个 Workflow；执行器、轨迹、校验、前端运行页都不用改。
P0 只把 `question_gen` 标成 ready；另外两条先展示为 planned，
等 runner 接好再改状态 —— 不拿「能点但跑不通」的模板糊弄人。
"""
from __future__ import annotations

from .models import Node, Workflow


QUESTION_GEN = Workflow(
    key="question_gen",
    name="团队出题",
    description="规划 → 检索 → 生成 → 结构校验 → 语义复核 → 修复复检 → 落库 → 汇总。"
                "只有通过校验的题才落库，未通过的如实丢弃。",
    nodes=(
        Node("plan", agent="planner", timeout_s=60),
        Node("retrieve", agent="retriever", deps=("plan",), timeout_s=20),
        Node("generate", agent="generator", deps=("plan", "retrieve"), timeout_s=180),
        Node("verify", agent="verifier", deps=("generate",), timeout_s=40),
        # LLM 语义复核（2026-11-12）：结构/规则之后，独立模型再看答案与解析是否自洽。
        # 只复核首轮通过的题；复核不可用/预算不足时保留结构校验结果。
        Node("verify_semantic", agent="verifier", deps=("verify",),
             when="has_passed", timeout_s=60, optional=True),
        # 校验-修复环（2026-11-12）：最多打回重出一轮。
        # 修复节点失败/预算不足时 optional 兜底，仍用第一轮通过的题落库。
        Node("repair", agent="generator", deps=("verify_semantic",),
             when="has_failures", timeout_s=120, optional=True),
        Node("verify_retry", agent="verifier", deps=("repair",),
             when="has_repair", timeout_s=40, optional=True),
        Node("persist", tool="bank.persist",
             deps=("verify_semantic", "verify_retry"), timeout_s=60),
        Node("aggregate", agent="conductor", deps=("persist",), timeout_s=20),
    ),
    final_key="aggregate",
)

# 快速模式（2026-11-12）：同一入口按 mode 路由到更短的 DAG。
# 不规划、不检索、不修复，只做「生成 → 校验 → 落库 → 汇总」，
# 用于低风险/低预算请求；完整团队模式仍走 question_gen。
QUICK_QUESTION_GEN = Workflow(
    key="question_gen_quick",
    name="快速出题",
    description="快速模式：跳过规划与检索，生成 → 校验 → 落库 → 汇总。",
    nodes=(
        Node("generate", agent="generator", timeout_s=150),
        Node("verify", agent="verifier", deps=("generate",), timeout_s=40),
        Node("persist", tool="bank.persist", deps=("verify",), timeout_s=60),
        Node("aggregate", agent="conductor", deps=("persist",), timeout_s=20),
    ),
    final_key="aggregate",
)

FILE_TO_QUESTIONS = Workflow(
    key="file_to_questions",
    name="上传文件生成题目",
    description="文档解析 → 可出题点抽象 → 用户确认 → 生成 → 命题保真校验 → 题集。",
    nodes=(
        Node("parse", tool="docs.parse", timeout_s=60),
        Node("plan", agent="planner", deps=("parse",), timeout_s=60),
        Node("generate", agent="generator", deps=("plan",), timeout_s=240),
        Node("verify", agent="verifier", deps=("generate",), timeout_s=40),
        Node("aggregate", agent="conductor", deps=("verify",), timeout_s=20),
    ),
    status="planned",
)

EVALUATE = Workflow(
    key="evaluate",
    name="团队评估",
    description="检索证据 → 评估 → 校验 → 汇总；与生成分离，避免自评自过。",
    nodes=(
        Node("retrieve", agent="retriever", timeout_s=20),
        Node("evaluate", agent="evaluator", deps=("retrieve",), timeout_s=90),
        Node("verify", agent="verifier", deps=("evaluate",), timeout_s=40),
        Node("aggregate", agent="conductor", deps=("verify",), timeout_s=20),
    ),
    status="planned",
)

# 调参圆桌（2026-11-11）：先取证，再由四个角色并行发言，最后主控裁决。
# 四个发言节点没有互相依赖，会同时启动；judge 等四票到齐。
TUNING_DEBATE = Workflow(
    key="tuning_debate",
    name="调参圆桌",
    description="证据 → 数据/规划/评估/小基四角色并行发言 → 主控裁决；"
                "裁决受参数空间与冷却期硬边界约束。",
    nodes=(
        Node("evidence", agent="debate_context", timeout_s=60),
        Node("data", agent="debate_data", deps=("evidence",), timeout_s=90,
             to_agent="debate_judge"),
        Node("plan", agent="debate_plan", deps=("evidence",), timeout_s=90,
             to_agent="debate_judge"),
        Node("evaluate", agent="debate_eval", deps=("evidence",), timeout_s=90,
             to_agent="debate_judge"),
        Node("xiaoji", agent="debate_xiaoji", deps=("evidence",), timeout_s=90,
             to_agent="debate_judge"),
        Node("judge", agent="debate_judge",
             deps=("data", "plan", "evaluate", "xiaoji"), timeout_s=90),
    ),
    final_key="judge",
)


# 交卷解析（2026-11-14）：交卷后真实创建 run，错题按批归因，
# 结构核对后写回答题记录，再由汇总节点给出分布与学习建议。
EXAM_ANALYSIS = Workflow(
    key="exam_analysis",
    name="交卷解析",
    description="错题收集 → 批量 AI 归因 → 结构核对 → 写回解析 → 汇总建议。",
    nodes=(
        Node("analyze", agent="exam_analyst", timeout_s=150),
        Node("verify", agent="exam_verifier", deps=("analyze",), timeout_s=20),
        Node("persist", tool="exam.persist", deps=("verify",), timeout_s=30),
        Node("aggregate", agent="exam_summary", deps=("persist",), timeout_s=20),
    ),
    final_key="aggregate",
)


# AI 出考卷（2026-11-15）：蓝图 → 题库取证 → 组卷 → 结构校验 → 落卷 → 汇总。
# 复用 planner/retriever/generator/verifier/conductor 五个角色，
# 不新增 Agent 契约；卷子落成 simulation 套卷，现有做题/交卷/解析链路直接可用。
EXAM_GEN = Workflow(
    key="exam_gen",
    name="AI 出考卷",
    description="卷面蓝图 → 题库取证 → 组卷 → 结构校验 → 落卷 → 汇总。",
    nodes=(
        Node("plan", agent="planner", timeout_s=60),
        Node("retrieve", agent="retriever", deps=("plan",), timeout_s=40),
        Node("compose", agent="generator", deps=("plan", "retrieve"), timeout_s=40),
        Node("verify", agent="verifier", deps=("compose",), timeout_s=20),
        Node("persist", tool="paper.persist", deps=("verify",), timeout_s=30),
        Node("aggregate", agent="conductor", deps=("persist",), timeout_s=20),
    ),
    final_key="aggregate",
)


# 考卷讲解视频（2026-11-15）：取卷面+本次作答 → 讲评大纲 → 口播脚本 →
# 内容校验 → TTS/上传/入库 → 汇总。脚本用播放器已有的 sections 结构。
EXAM_VIDEO = Workflow(
    key="exam_video",
    name="考卷讲解视频",
    description="卷面与作答取证 → 讲评大纲 → 口播脚本 → 内容校验 → 合成视频 → 汇总。",
    nodes=(
        Node("gather", tool="paper.context", timeout_s=30),
        Node("plan", agent="planner", deps=("gather",), timeout_s=60),
        Node("script", agent="generator", deps=("plan",), timeout_s=120),
        Node("verify", agent="verifier", deps=("script",), timeout_s=30),
        Node("synthesize", tool="video.synthesize", deps=("verify",), timeout_s=180),
        Node("aggregate", agent="conductor", deps=("synthesize",), timeout_s=20),
    ),
    final_key="aggregate",
)


WORKFLOWS: dict[str, Workflow] = {
    w.key: w for w in (QUESTION_GEN, QUICK_QUESTION_GEN,
                       FILE_TO_QUESTIONS, EVALUATE, TUNING_DEBATE,
                       EXAM_ANALYSIS, EXAM_GEN, EXAM_VIDEO)
}


def list_workflows(only_ready: bool = False) -> list[dict]:
    out = []
    for w in WORKFLOWS.values():
        if only_ready and w.status != "ready":
            continue
        out.append({
            "key": w.key,
            "name": w.name,
            "description": w.description,
            "status": w.status,
            "final_key": w.final_key,
            "nodes": [
                {"key": n.key, "agent": n.agent, "tool": n.tool,
                 "deps": list(n.deps), "when": n.when,
                 "optional": n.optional, "to_agent": n.to_agent}
                for n in w.nodes
            ],
        })
    return out
