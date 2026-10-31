"""多智能体编排运行时（2026-10-30）

设计见 project1/AGENT_ORCHESTRATION_DESIGN.md 第二、三节。

这里刻意不引入 LangChain 等重框架：
  · 需要的只有「DAG 执行 + A2A 消息 + 轨迹持久化 + 预算/取消」；
  · 学习场景的工作流是有限的、可枚举的，代码化模板比通用引擎更可控；
  · 依赖越少，部署越稳（这个项目已经在「可选依赖缺失」上吃过亏）。
"""

from .models import Node, RunBudget, RunContext, Workflow  # noqa: F401
