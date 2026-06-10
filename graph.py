"""
LangGraph 工作流定义
构建完整的科研 Agent 工作流
"""
from langgraph.graph import StateGraph, END
from typing import Literal

from state import PaperAgentState
from nodes import PaperAgentNodes


def create_paper_agent_graph(
    model_name: str = "gpt-4",
    review_model_name: str = None,
    temperature: float = 0.7
):
    """
    创建科研 Agent 的 LangGraph 工作流

    Args:
        model_name: 主要使用的模型
        review_model_name: 审稿使用的模型
        temperature: 温度参数

    Returns:
        编译后的 LangGraph
    """

    # 初始化节点
    nodes = PaperAgentNodes(
        model_name=model_name,
        review_model_name=review_model_name,
        temperature=temperature
    )

    # 创建状态图
    workflow = StateGraph(PaperAgentState)

    # 添加节点
    workflow.add_node("retrieve_papers", nodes.retrieve_papers)
    workflow.add_node("extract_inspiration", nodes.extract_inspiration)
    workflow.add_node("design_proposal", nodes.design_research_proposal)
    workflow.add_node("design_experiments", nodes.design_experiments)
    workflow.add_node("design_architecture", nodes.design_paper_architecture)
    # 章节流水线：派发 → 写作 → 校验 → 组装
    workflow.add_node("dispatch_section", nodes.dispatch_section)
    workflow.add_node("write_section", nodes.write_section)
    workflow.add_node("validate_section", nodes.validate_section)
    workflow.add_node("assemble_paper", nodes.assemble_paper)
    workflow.add_node("polish_paper", nodes.polish_paper)
    workflow.add_node("remove_ai_tone", nodes.remove_ai_tone)
    workflow.add_node("review_paper", nodes.review_paper)
    workflow.add_node("revise_by_review", nodes.revise_by_review)
    workflow.add_node("finalize_paper", nodes.finalize_paper)

    # 定义边（工作流）
    # 设置入口点
    workflow.set_entry_point("retrieve_papers")

    # 线性流程
    workflow.add_edge("retrieve_papers", "extract_inspiration")
    workflow.add_edge("extract_inspiration", "design_proposal")
    workflow.add_edge("design_proposal", "design_experiments")
    workflow.add_edge("design_experiments", "design_architecture")

    # 架构设计完成后进入章节流水线
    workflow.add_edge("design_architecture", "dispatch_section")
    # 派发的章节交给写作模块
    workflow.add_edge("dispatch_section", "write_section")
    # 写作完成后交给校验模块
    workflow.add_edge("write_section", "validate_section")

    # 校验后：未通过则重写当前节；通过则判断是否还有下一节
    def after_validation(
        state: PaperAgentState
    ) -> Literal["write_section", "dispatch_section", "assemble_paper"]:
        if not state.get("section_passed", False):
            # 未通过，带反馈重写当前章节
            return "write_section"
        # 通过：检查是否还有未写的章节
        idx = state.get("current_section_index", 0)
        total = len(state.get("section_specs", []))
        if idx < total:
            return "dispatch_section"
        return "assemble_paper"

    workflow.add_conditional_edges(
        "validate_section",
        after_validation,
        {
            "write_section": "write_section",
            "dispatch_section": "dispatch_section",
            "assemble_paper": "assemble_paper"
        }
    )

    # 组装完成后进入润色阶段
    workflow.add_edge("assemble_paper", "polish_paper")
    workflow.add_edge("polish_paper", "remove_ai_tone")
    workflow.add_edge("remove_ai_tone", "review_paper")

    # 条件边：根据审稿结果决定是否继续迭代
    # 未通过 → 先按审稿意见改稿，再润色；通过 → 直接输出
    def should_revise(state: PaperAgentState) -> Literal["revise_by_review", "finalize_paper"]:
        """决定是否需要继续修改"""
        if state.get("needs_revision", False):
            return "revise_by_review"
        else:
            return "finalize_paper"

    workflow.add_conditional_edges(
        "review_paper",
        should_revise,
        {
            "revise_by_review": "revise_by_review",
            "finalize_paper": "finalize_paper"
        }
    )

    # 改稿后回到润色 → 去AI味 → 再次审稿，形成迭代闭环
    workflow.add_edge("revise_by_review", "polish_paper")

    # 最终节点
    workflow.add_edge("finalize_paper", END)

    # 编译图
    app = workflow.compile()

    return app


def visualize_graph(app):
    """
    可视化工作流图（需要安装 pygraphviz）

    Args:
        app: 编译后的 LangGraph
    """
    try:
        from IPython.display import Image, display
        display(Image(app.get_graph().draw_mermaid_png()))
    except Exception as e:
        print(f"无法可视化图: {e}")
        print("提示: 安装 pygraphviz 和 IPython 以支持图可视化")
