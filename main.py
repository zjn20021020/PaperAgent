"""
主程序入口
运行科研 Agent
"""
import os
import sys
import argparse
from dotenv import load_dotenv

# 解决 Windows 控制台中文乱码问题
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from graph import create_paper_agent_graph
from tools import DocumentGenerator
from state import PaperAgentState

# 加载环境变量
load_dotenv()


def run_paper_agent(
    topic: str,
    target_conference: str = "NeurIPS",
    model_name: str = None,
    review_model_name: str = None,
    output_dir: str = "output"
):
    """
    运行科研 Agent

    Args:
        topic: 研究主题
        target_conference: 目标会议
        model_name: 使用的模型
        review_model_name: 审稿模型
        output_dir: 输出目录
    """

    # 使用环境变量或默认值
    if model_name is None:
        model_name = os.getenv("DEFAULT_MODEL", "gpt-4")

    if review_model_name is None:
        review_model_name = os.getenv("REVIEW_MODEL", model_name)

    print(f"\n{'='*80}")
    print(f"科研 Agent 启动")
    print(f"{'='*80}")
    print(f"研究主题: {topic}")
    print(f"目标会议: {target_conference}")
    print(f"主模型: {model_name}")
    print(f"审稿模型: {review_model_name}")
    print(f"{'='*80}\n")

    # 创建工作流
    app = create_paper_agent_graph(
        model_name=model_name,
        review_model_name=review_model_name,
        temperature=0.7
    )

    # 初始化状态
    initial_state: PaperAgentState = {
        "topic": topic,
        "target_conference": target_conference,
        "retrieved_papers": [],
        "papers_summary": "",
        "inspirations": "",
        "research_gaps": "",
        "innovation_directions": [],
        "selected_direction": "",
        "problem_statement": "",
        "proposed_method": "",
        "key_innovations": "",
        "technical_details": "",
        "experiment_design": "",
        "datasets": [],
        "baselines": [],
        "metrics": [],
        "experiment_results": "",
        "paper_architecture": "",
        "section_outlines": {},
        "section_specs": [],
        "current_section_index": 0,
        "current_section_name": "",
        "current_section_requirements": "",
        "current_section_min_words": 0,
        "current_section_max_words": 0,
        "current_section_draft": "",
        "current_section_word_count": 0,
        "section_feedback": "",
        "section_attempts": 0,
        "section_passed": False,
        "paper_sections": {},
        "full_paper": "",
        "polished_paper": "",
        "deai_paper": "",
        "review_report": "",
        "review_score": 0.0,
        "review_iteration": 0,
        "revised_paper": "",
        "review_history": [],
        "needs_revision": False,
        "final_paper": "",
        "messages": []
    }

    # 运行工作流
    try:
        # 章节流水线会产生较多步骤，提高递归上限
        final_state = app.invoke(initial_state, {"recursion_limit": 100})

        print(f"\n{'='*80}")
        print(f"工作流执行完成!")
        print(f"{'='*80}\n")

        # 保存最终论文
        doc_gen = DocumentGenerator()

        # 保存 LaTeX 源文件
        latex_content = doc_gen.create_latex_template(
            title="Research Paper Title",  # 可以从论文内容中提取
            authors="Author Names",
            abstract="Abstract content",
            sections=final_state.get("paper_sections", {}),
            conference=target_conference
        )

        # 使用最终论文内容（如果有的话）
        if final_state.get("final_paper"):
            latex_content = final_state["final_paper"]

        filename = topic.replace(" ", "_")[:50]  # 限制文件名长度
        filepath = doc_gen.save_paper(latex_content, filename, output_dir)

        print(f"✓ 论文已保存到: {filepath}")

        # 保存审稿报告（最新一次）
        if final_state.get("review_report"):
            review_filepath = filepath.replace(".tex", "_review.txt")
            with open(review_filepath, 'w', encoding='utf-8') as f:
                f.write(final_state["review_report"])
            print(f"✓ 审稿报告（最新）已保存到: {review_filepath}")

        # 保存完整审稿历史（所有轮次）
        review_history = final_state.get("review_history", [])
        if review_history:
            history_filepath = filepath.replace(".tex", "_review_history.txt")
            with open(history_filepath, 'w', encoding='utf-8') as f:
                f.write(f"审稿历史记录（共 {len(review_history)} 轮）\n")
                f.write("=" * 80 + "\n\n")
                for record in review_history:
                    f.write(f"第 {record['iteration']} 轮审稿\n")
                    f.write(f"评分: {record['score']:.2f}/10\n")
                    f.write("-" * 80 + "\n")
                    f.write(record['report'])
                    f.write("\n\n" + "=" * 80 + "\n\n")
            print(f"✓ 审稿历史（{len(review_history)} 轮）已保存到: {history_filepath}")

        # 保存完整对话日志
        messages = final_state.get("messages", [])
        if messages:
            log_filepath = filepath.replace(".tex", "_conversation_log.txt")
            with open(log_filepath, 'w', encoding='utf-8') as f:
                f.write(f"工作流对话日志\n")
                f.write(f"研究主题: {topic}\n")
                f.write(f"目标会议: {target_conference}\n")
                f.write("=" * 80 + "\n\n")
                for i, msg in enumerate(messages, 1):
                    f.write(f"[{i}] {msg}\n")
            print(f"✓ 对话日志（{len(messages)} 条）已保存到: {log_filepath}")

        # 打印统计信息
        print(f"\n{'='*80}")
        print(f"统计信息")
        print(f"{'='*80}")
        print(f"检索论文数: {len(final_state.get('retrieved_papers', []))}")
        print(f"审稿迭代次数: {final_state.get('review_iteration', 0)}")
        print(f"最终评分: {final_state.get('review_score', 0):.2f}/10")
        print(f"{'='*80}\n")

        return final_state

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="科研 Agent - 自动论文生成系统")

    parser.add_argument(
        "--topic",
        type=str,
        required=True,
        help="研究主题"
    )

    parser.add_argument(
        "--conference",
        type=str,
        default="NeurIPS",
        choices=["NeurIPS", "ICML", "ICLR", "ACL", "CVPR", "AAAI"],
        help="目标会议"
    )

    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="使用的模型 (如 gpt-4, claude-opus-4)"
    )

    parser.add_argument(
        "--review-model",
        type=str,
        default=None,
        help="审稿使用的模型"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="输出目录"
    )

    args = parser.parse_args()

    # 运行 Agent
    run_paper_agent(
        topic=args.topic,
        target_conference=args.conference,
        model_name=args.model,
        review_model_name=args.review_model,
        output_dir=args.output_dir
    )


if __name__ == "__main__":
    main()
