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
    description="规划 → 检索 → 生成 → 校验 → 汇总。校验不过的题丢弃并如实报告。",
    nodes=(
        Node("plan", agent="planner", timeout_s=60),
        Node("retrieve", agent="retriever", deps=("plan",), timeout_s=20),
        Node("generate", agent="generator", deps=("plan", "retrieve"), timeout_s=180),
        Node("verify", agent="verifier", deps=("generate",), timeout_s=40),
        Node("aggregate", agent="conductor", deps=("verify",), timeout_s=20),
    ),
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


WORKFLOWS: dict[str, Workflow] = {
    w.key: w for w in (QUESTION_GEN, FILE_TO_QUESTIONS, EVALUATE)
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
            "nodes": [
                {"key": n.key, "agent": n.agent, "tool": n.tool,
                 "deps": list(n.deps), "when": n.when,
                 "optional": n.optional}
                for n in w.nodes
            ],
        })
    return out
