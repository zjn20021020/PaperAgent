"""
状态定义模块
定义 LangGraph 的状态结构
"""
from typing import TypedDict, List, Optional, Annotated
from operator import add


class PaperAgentState(TypedDict):
    """科研 Agent 的状态"""

    # 输入
    topic: str  # 研究主题
    target_conference: str  # 目标会议（如 NeurIPS, ICML, ICLR）

    # 论文检索阶段
    retrieved_papers: List[dict]  # 检索到的论文列表
    papers_summary: str  # 论文摘要汇总

    # 灵感与方向阶段
    inspirations: str  # 提取的灵感
    research_gaps: str  # 研究空白
    innovation_directions: List[str]  # 创新方向列表
    selected_direction: str  # 选定的研究方向

    # 课题方案阶段
    problem_statement: str  # 问题陈述
    proposed_method: str  # 提出的方法
    key_innovations: str  # 核心创新点
    technical_details: str  # 技术细节

    # 实验设计阶段
    experiment_design: str  # 实验设计方案
    datasets: List[str]  # 数据集
    baselines: List[str]  # 对比方法
    metrics: List[str]  # 评估指标
    experiment_results: str  # 实验结果（模拟或真实）

    # 论文架构阶段
    paper_architecture: str  # 论文架构设计
    section_outlines: dict  # 各章节大纲
    section_specs: List[dict]  # 设计模块产出的逐章节规格（含字数要求）

    # 章节流水线（设计→写作→校验，逐节进行）
    current_section_index: int  # 当前正在处理的章节索引
    current_section_name: str  # 当前章节名
    current_section_requirements: str  # 当前章节的内容要求
    current_section_min_words: int  # 当前章节最少字数
    current_section_max_words: int  # 当前章节最多字数
    current_section_draft: str  # 当前章节的草稿
    current_section_word_count: int  # 当前草稿字数
    section_feedback: str  # 校验反馈（用于重写）
    section_attempts: int  # 当前章节已尝试次数
    section_passed: bool  # 当前章节是否通过校验（含放行）

    # 论文写作阶段
    paper_sections: dict  # 各章节内容（已通过校验并保存）
    full_paper: str  # 完整论文

    # 润色和审查阶段
    polished_paper: str  # 润色后的论文
    deai_paper: str  # 去 AI 味后的论文
    review_report: str  # 审稿报告（最新一次）
    review_score: float  # 审稿评分（最新一次）
    review_iteration: int  # 审查迭代次数
    revised_paper: str  # 根据审稿意见修改后的论文
    review_history: List[dict]  # 所有审稿历史（每项含 iteration, score, report）

    # 控制流程
    needs_revision: bool  # 是否需要修改
    final_paper: str  # 最终论文

    # 消息历史（用于调试和追踪）
    messages: Annotated[List[str], add]  # 过程消息
