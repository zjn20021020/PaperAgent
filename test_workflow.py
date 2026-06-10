"""
离线测试：使用 Mock LLM 验证完整工作流
无需 API Key 即可运行，用于验证流程逻辑是否正确
"""
import sys
import os

# Windows 控制台 UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 设置假 key 以通过初始化
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")
os.environ.setdefault("MAX_SECTION_ATTEMPTS", "3")

from langchain_core.messages import AIMessage
from state import PaperAgentState


class MockLLM:
    """模拟 LLM，根据提示词内容返回合理的假响应"""

    def __init__(self, role="main"):
        self.role = role
        self.call_count = 0
        # 用于测试章节校验循环：记录每个章节的写作次数
        self._write_counts = {}

    def invoke(self, messages):
        self.call_count += 1
        prompt = messages[0].content if messages else ""

        # 章节规格设计：返回 JSON 数组（2 个短章节便于测试）
        if "逐章节写作规格" in prompt or "逐章节的写作规格" in prompt:
            return AIMessage(content="""[
  {"section": "Abstract", "requirements": "概括问题、方法与结果。", "min_words": 5, "max_words": 100},
  {"section": "Introduction", "requirements": "介绍背景、动机与贡献。", "min_words": 5, "max_words": 100}
]""")

        # 章节校验：返回 JSON 对象
        if "章节质量检查员" in prompt or '"passed"' in prompt and "word_count_ok" in prompt:
            # 提取章节名以模拟"第一次不通过、第二次通过"
            import re
            m = re.search(r"章节名：(\w+)", prompt)
            section = m.group(1) if m else "unknown"
            self._write_counts[section] = self._write_counts.get(section, 0) + 1
            # Introduction 第一次故意不通过，测试重写循环
            if section == "Introduction" and self._write_counts[section] == 1:
                return AIMessage(content="""{
  "passed": false, "word_count_ok": false, "content_ok": true,
  "feedback": "字数不足，请扩写。"
}""")
            return AIMessage(content="""{
  "passed": true, "word_count_ok": true, "content_ok": true, "feedback": "通过"
}""")

        # 单章节写作：返回一段约 20 词的英文
        if "撰写论文的" in prompt or "请开始撰写" in prompt:
            return AIMessage(content=(
                "This section presents the proposed method and its motivation "
                "in a clear and concise manner for the target venue evaluation here."
            ))

        # 改稿模块：根据审稿意见修改论文
        if "根据审稿人的意见" in prompt or "rebuttal" in prompt or "审稿报告" in prompt and "论文全文" in prompt:
            return AIMessage(content=(
                "\\section{Abstract}\nRevised abstract addressing reviewer comments.\n\n"
                "\\section{Introduction}\nRevised introduction with added clarifications."
            ))

        # 审稿：第一次不通过触发改稿循环，之后通过
        if "审稿人" in prompt or "Review" in prompt:
            self._review_count = getattr(self, "_review_count", 0) + 1
            score = 6.0 if self._review_count == 1 else 8.5
            return AIMessage(content=f"""
Part 1 [Review Report]
Summary: 本文提出了一种新方法。
Weaknesses: 实验对比不够充分。
Rating: {score:.1f} 分。
Part 2 [Improvement Suggestions]
建议补充消融实验。
""")

        # 其他节点的通用结构化假内容
        return AIMessage(content="""
Part 1 [Generated Content]
Mock content for workflow testing.
Part 3 [Directions]
Direction A.
Part 4 [Recommended]
Recommended direction: improve efficiency.
""")


def run_offline_test():
    print("=" * 70)
    print("离线工作流测试 (Mock LLM, 真实 arXiv 检索)")
    print("=" * 70)

    mock_main = MockLLM("main")
    mock_review = MockLLM("review")

    from nodes import PaperAgentNodes
    n = PaperAgentNodes(model_name="gpt-4")
    n.llm = mock_main
    n.review_llm = mock_review

    from langgraph.graph import StateGraph, END
    from typing import Literal

    workflow = StateGraph(PaperAgentState)
    workflow.add_node("retrieve_papers", n.retrieve_papers)
    workflow.add_node("extract_inspiration", n.extract_inspiration)
    workflow.add_node("design_proposal", n.design_research_proposal)
    workflow.add_node("design_experiments", n.design_experiments)
    workflow.add_node("design_architecture", n.design_paper_architecture)
    workflow.add_node("dispatch_section", n.dispatch_section)
    workflow.add_node("write_section", n.write_section)
    workflow.add_node("validate_section", n.validate_section)
    workflow.add_node("assemble_paper", n.assemble_paper)
    workflow.add_node("polish_paper", n.polish_paper)
    workflow.add_node("remove_ai_tone", n.remove_ai_tone)
    workflow.add_node("review_paper", n.review_paper)
    workflow.add_node("revise_by_review", n.revise_by_review)
    workflow.add_node("finalize_paper", n.finalize_paper)

    workflow.set_entry_point("retrieve_papers")
    workflow.add_edge("retrieve_papers", "extract_inspiration")
    workflow.add_edge("extract_inspiration", "design_proposal")
    workflow.add_edge("design_proposal", "design_experiments")
    workflow.add_edge("design_experiments", "design_architecture")
    workflow.add_edge("design_architecture", "dispatch_section")
    workflow.add_edge("dispatch_section", "write_section")
    workflow.add_edge("write_section", "validate_section")

    def after_validation(state) -> Literal["write_section", "dispatch_section", "assemble_paper"]:
        if not state.get("section_passed", False):
            return "write_section"
        idx = state.get("current_section_index", 0)
        total = len(state.get("section_specs", []))
        return "dispatch_section" if idx < total else "assemble_paper"

    workflow.add_conditional_edges(
        "validate_section", after_validation,
        {"write_section": "write_section", "dispatch_section": "dispatch_section",
         "assemble_paper": "assemble_paper"}
    )
    workflow.add_edge("assemble_paper", "polish_paper")
    workflow.add_edge("polish_paper", "remove_ai_tone")
    workflow.add_edge("remove_ai_tone", "review_paper")

    def should_revise(state) -> Literal["revise_by_review", "finalize_paper"]:
        return "revise_by_review" if state.get("needs_revision", False) else "finalize_paper"

    workflow.add_conditional_edges(
        "review_paper", should_revise,
        {"revise_by_review": "revise_by_review", "finalize_paper": "finalize_paper"}
    )
    workflow.add_edge("revise_by_review", "polish_paper")
    workflow.add_edge("finalize_paper", END)
    test_app = workflow.compile()

    initial_state = {
        "topic": "Efficient Attention Mechanisms",
        "target_conference": "NeurIPS",
        "retrieved_papers": [], "papers_summary": "",
        "inspirations": "", "research_gaps": "", "innovation_directions": [],
        "selected_direction": "", "problem_statement": "", "proposed_method": "",
        "key_innovations": "", "technical_details": "", "experiment_design": "",
        "datasets": [], "baselines": [], "metrics": [], "experiment_results": "",
        "paper_architecture": "", "section_outlines": {}, "section_specs": [],
        "current_section_index": 0, "current_section_name": "",
        "current_section_requirements": "", "current_section_min_words": 0,
        "current_section_max_words": 0, "current_section_draft": "",
        "current_section_word_count": 0, "section_feedback": "",
        "section_attempts": 0, "section_passed": False,
        "paper_sections": {}, "full_paper": "", "polished_paper": "", "deai_paper": "",
        "review_report": "", "review_score": 0.0, "review_iteration": 0,
        "revised_paper": "", "review_history": [],
        "needs_revision": False, "final_paper": "", "messages": []
    }

    final = test_app.invoke(initial_state, {"recursion_limit": 100})

    print("\n" + "=" * 70)
    print("测试结果验证")
    print("=" * 70)
    checks = [
        ("检索论文", len(final.get("retrieved_papers", [])) > 0),
        ("提取灵感", bool(final.get("inspirations"))),
        ("研究方案", bool(final.get("proposed_method"))),
        ("实验设计", bool(final.get("experiment_design"))),
        ("章节规格", len(final.get("section_specs", [])) > 0),
        ("逐节写作并保存", len(final.get("paper_sections", {})) == len(final.get("section_specs", []))),
        ("论文组装", bool(final.get("full_paper"))),
        ("润色完成", bool(final.get("polished_paper"))),
        ("去AI味完成", bool(final.get("deai_paper"))),
        ("审稿报告", bool(final.get("review_report"))),
        ("最终论文", bool(final.get("final_paper"))),
        ("Introduction 触发了重写", mock_main._write_counts.get("Introduction", 0) >= 2),
        ("审稿触发了改稿(revised_paper)", bool(final.get("revised_paper"))),
        ("经过多轮审稿", final.get("review_iteration", 0) >= 2),
    ]
    all_pass = True
    for name, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
        all_pass = all_pass and ok

    print(f"\n已保存章节: {list(final.get('paper_sections', {}).keys())}")
    print(f"各章节写作次数: {mock_main._write_counts}")
    print(f"审稿迭代次数: {final.get('review_iteration')}")
    print(f"最终评分: {final.get('review_score')}")
    print("\n" + ("=" * 70))
    print("全部通过 ✓" if all_pass else "存在失败项 ✗")
    print("=" * 70)
    return all_pass


if __name__ == "__main__":
    run_offline_test()
