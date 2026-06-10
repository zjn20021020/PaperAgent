"""
示例脚本：演示如何使用 PaperAgent
"""
from main import run_paper_agent


def example_basic():
    """基础示例：使用默认配置"""
    print("\n=== 示例 1: 基础使用 ===\n")

    run_paper_agent(
        topic="Attention Mechanism for Natural Language Processing",
        target_conference="ACL"
    )


def example_custom_models():
    """示例：自定义模型"""
    print("\n=== 示例 2: 自定义模型 ===\n")

    run_paper_agent(
        topic="Graph Neural Networks for Molecular Property Prediction",
        target_conference="NeurIPS",
        model_name="gpt-4",
        review_model_name="claude-opus-4"
    )


def example_computer_vision():
    """示例：计算机视觉主题"""
    print("\n=== 示例 3: 计算机视觉 ===\n")

    run_paper_agent(
        topic="Self-Supervised Learning for Image Recognition",
        target_conference="CVPR",
        output_dir="output/cv_papers"
    )


def example_reinforcement_learning():
    """示例：强化学习主题"""
    print("\n=== 示例 4: 强化学习 ===\n")

    run_paper_agent(
        topic="Multi-Agent Reinforcement Learning with Communication",
        target_conference="ICML"
    )


if __name__ == "__main__":
    # 选择要运行的示例
    import sys

    examples = {
        "1": example_basic,
        "2": example_custom_models,
        "3": example_computer_vision,
        "4": example_reinforcement_learning
    }

    if len(sys.argv) > 1:
        example_num = sys.argv[1]
        if example_num in examples:
            examples[example_num]()
        else:
            print(f"未知示例: {example_num}")
            print(f"可用示例: {', '.join(examples.keys())}")
    else:
        print("请指定示例编号:")
        print("  python examples.py 1  # 基础使用")
        print("  python examples.py 2  # 自定义模型")
        print("  python examples.py 3  # 计算机视觉")
        print("  python examples.py 4  # 强化学习")
