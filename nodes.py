"""
节点模块
实现 LangGraph 的各个节点功能
"""
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv

from state import PaperAgentState
from tools import PaperSearchTool, ExperimentSimulator
from prompts import (
    INSPIRATION_EXTRACTION_PROMPT,
    RESEARCH_PROPOSAL_PROMPT,
    EXPERIMENT_DESIGN_PROMPT,
    PAPER_ARCHITECTURE_PROMPT,
    PAPER_WRITING_PROMPT,
    PAPER_POLISH_PROMPT,
    REMOVE_AI_TONE_PROMPT,
    PAPER_REVIEW_PROMPT,
    EXPERIMENT_ANALYSIS_PROMPT,
    SECTION_SPEC_PROMPT,
    SECTION_WRITING_PROMPT,
    SECTION_VALIDATION_PROMPT,
    REVISE_BY_REVIEW_PROMPT
)

load_dotenv()


def fill_prompt(template: str, **kwargs) -> str:
    """
    安全地填充提示词模板。

    使用 {key} 占位符替换，而非 str.format()，
    因为提示词中包含大量 LaTeX 花括号（如 \\cite{}、\\paragraph{}），
    会被 str.format() 误判为占位符而报错。
    """
    result = template
    for key, value in kwargs.items():
        result = result.replace("{" + key + "}", str(value))
    return result


def extract_json(text: str):
    """
    从 LLM 响应中提取 JSON（对象或数组）。

    容忍模型在 JSON 前后输出多余文字或 ```json 代码块。
    解析失败时返回 None。
    """
    import json
    import re

    if not text:
        return None

    # 去掉 markdown 代码块标记
    cleaned = re.sub(r"```(?:json)?", "", text).strip()

    # 直接尝试
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # 截取第一个 { 或 [ 到最后一个 } 或 ] 的片段
    start_candidates = [i for i in (cleaned.find("{"), cleaned.find("[")) if i != -1]
    end_candidates = [i for i in (cleaned.rfind("}"), cleaned.rfind("]")) if i != -1]
    if start_candidates and end_candidates:
        start = min(start_candidates)
        end = max(end_candidates)
        try:
            return json.loads(cleaned[start:end + 1])
        except Exception:
            return None
    return None


def count_words(text: str) -> int:
    """统计英文单词数（粗略去除 LaTeX 命令后按空白切分）。"""
    import re
    if not text:
        return 0
    # 去掉 \command 和花括号内容标记，保留正文词
    stripped = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^}]*\})?", " ", text)
    stripped = re.sub(r"[{}$&%#_~^]", " ", stripped)
    words = re.findall(r"[A-Za-z][A-Za-z\-']*", stripped)
    return len(words)


class PaperAgentNodes:
    """科研 Agent 的节点实现"""

    def __init__(
        self,
        model_name: str = "gpt-4",
        review_model_name: str = None,
        temperature: float = 0.7
    ):
        """
        初始化节点

        Args:
            model_name: 主要使用的模型
            review_model_name: 审稿使用的模型（如果不同）
            temperature: 温度参数
        """
        # 初始化主模型
        self.llm = self._build_llm(model_name, temperature)

        # 初始化审稿模型（审稿用较低温度，输出更确定）
        if review_model_name and review_model_name != model_name:
            self.review_llm = self._build_llm(review_model_name, 0.3)
        else:
            self.review_llm = self.llm

        # 初始化工具
        self.paper_search = PaperSearchTool(max_results=10)
        self.experiment_simulator = ExperimentSimulator()

    @staticmethod
    def _build_llm(model_name: str, temperature: float):
        """
        根据模型名构建对应的 LLM 客户端。

        - Claude 系列走 Anthropic 接口。
        - 其它一律走 OpenAI 兼容接口（ChatOpenAI），
          支持通过 LLM_BASE_URL / OPENAI_BASE_URL 指定自定义服务
          （如 DeepSeek、Kimi、本地 vLLM 等 OpenAI 兼容 API）。
        """
        if model_name.startswith("claude"):
            return ChatAnthropic(
                model=model_name,
                temperature=temperature,
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )

        # OpenAI 兼容接口（含 OpenAI 官方、DeepSeek 等）
        api_key = (
            os.getenv("OPENAI_API_KEY")
            or os.getenv("LLM_API_KEY")
        )
        base_url = (
            os.getenv("OPENAI_BASE_URL")
            or os.getenv("LLM_BASE_URL")
        )

        kwargs = {
            "model": model_name,
            "temperature": temperature,
            "api_key": api_key,
        }
        if base_url:
            kwargs["base_url"] = base_url

        return ChatOpenAI(**kwargs)

    def retrieve_papers(self, state: PaperAgentState) -> Dict[str, Any]:
        """
        节点1: 检索相关论文

        Args:
            state: 当前状态

        Returns:
            更新的状态
        """
        print(f"\n{'='*60}")
        print(f"[Step 1/11] 检索相关论文...")
        print(f"{'='*60}")

        topic = state["topic"]
        print(f"研究主题: {topic}")

        # 检索论文
        papers = self.paper_search.search_papers(topic, max_results=10)
        print(f"找到 {len(papers)} 篇相关论文")

        # 格式化论文信息
        papers_summary = self.paper_search.format_papers_for_prompt(papers)

        return {
            "retrieved_papers": papers,
            "papers_summary": papers_summary,
            "messages": [f"检索到 {len(papers)} 篇论文"]
        }

    def extract_inspiration(self, state: PaperAgentState) -> Dict[str, Any]:
        """
        节点2: 提取灵感和研究方向

        Args:
            state: 当前状态

        Returns:
            更新的状态
        """
        print(f"\n{'='*60}")
        print(f"[Step 2/11] 分析论文并提取研究灵感...")
        print(f"{'='*60}")

        topic = state["topic"]
        papers_summary = state["papers_summary"]

        # 构造提示词
        prompt = fill_prompt(
            INSPIRATION_EXTRACTION_PROMPT,
            topic=topic,
            papers_info=papers_summary
        )

        # 调用 LLM
        messages = [HumanMessage(content=prompt)]
        response = self.llm.invoke(messages)
        content = response.content

        # 解析响应（简化处理）
        parts = content.split("Part 2")
        inspirations = parts[0] if len(parts) > 0 else content

        parts = content.split("Part 3")
        innovation_directions_text = parts[1] if len(parts) > 1 else ""

        parts = content.split("Part 4")
        selected_direction = parts[1] if len(parts) > 1 else innovation_directions_text

        print(f"✓ 提取了研究灵感和创新方向")

        return {
            "inspirations": inspirations,
            "innovation_directions": [innovation_directions_text],
            "selected_direction": selected_direction,
            "messages": ["提取了研究灵感"]
        }

    def design_research_proposal(self, state: PaperAgentState) -> Dict[str, Any]:
        """
        节点3: 设计课题方案

        Args:
            state: 当前状态

        Returns:
            更新的状态
        """
        print(f"\n{'='*60}")
        print(f"[Step 3/11] 设计研究方案...")
        print(f"{'='*60}")

        topic = state["topic"]
        selected_direction = state["selected_direction"]
        inspirations = state["inspirations"]

        # 构造提示词
        prompt = fill_prompt(
            RESEARCH_PROPOSAL_PROMPT,
            direction=selected_direction,
            inspiration=inspirations,
            topic=topic
        )

        # 调用 LLM
        messages = [HumanMessage(content=prompt)]
        response = self.llm.invoke(messages)
        content = response.content

        # 简化解析（实际应该更严格地解析各部分）
        problem_statement = "Problem defined based on research direction"
        proposed_method = content
        key_innovations = "Key innovations extracted from proposal"
        technical_details = "Technical details from proposal"

        print(f"✓ 完成研究方案设计")

        return {
            "problem_statement": problem_statement,
            "proposed_method": proposed_method,
            "key_innovations": key_innovations,
            "technical_details": technical_details,
            "messages": ["设计了研究方案"]
        }

    def design_experiments(self, state: PaperAgentState) -> Dict[str, Any]:
        """
        节点4: 设计实验方案

        Args:
            state: 当前状态

        Returns:
            更新的状态
        """
        print(f"\n{'='*60}")
        print(f"[Step 4/11] 设计实验方案...")
        print(f"{'='*60}")

        proposed_method = state["proposed_method"]

        # 构造提示词
        prompt = fill_prompt(EXPERIMENT_DESIGN_PROMPT, proposal=proposed_method)

        # 调用 LLM
        messages = [HumanMessage(content=prompt)]
        response = self.llm.invoke(messages)
        experiment_design = response.content

        # 模拟实验结果
        datasets = ["Dataset-A", "Dataset-B", "Dataset-C"]
        baselines = ["Baseline-1", "Baseline-2", "Baseline-3"]
        metrics = ["Accuracy", "F1-Score", "Precision"]

        experiment_results = self.experiment_simulator.generate_mock_results(
            baselines=baselines,
            datasets=datasets,
            metrics=metrics
        )

        print(f"✓ 完成实验设计和模拟结果生成")

        return {
            "experiment_design": experiment_design,
            "datasets": datasets,
            "baselines": baselines,
            "metrics": metrics,
            "experiment_results": experiment_results,
            "messages": ["设计了实验方案"]
        }

    def design_paper_architecture(self, state: PaperAgentState) -> Dict[str, Any]:
        """
        节点5: 设计论文架构

        Args:
            state: 当前状态

        Returns:
            更新的状态
        """
        print(f"\n{'='*60}")
        print(f"[Step 5/11] 设计论文架构...")
        print(f"{'='*60}")

        topic = state["topic"]
        key_innovations = state["key_innovations"]
        conference = state.get("target_conference", "NeurIPS")

        # 构造提示词
        prompt = fill_prompt(
            PAPER_ARCHITECTURE_PROMPT,
            topic=topic,
            innovation=key_innovations
        )

        # 调用 LLM
        messages = [HumanMessage(content=prompt)]
        response = self.llm.invoke(messages)
        architecture = response.content

        # 让设计模块进一步把架构拆解为逐章节规格（含字数要求）
        spec_prompt = fill_prompt(
            SECTION_SPEC_PROMPT,
            topic=topic,
            innovation=key_innovations,
            conference=conference,
            architecture=architecture
        )
        spec_response = self.llm.invoke([HumanMessage(content=spec_prompt)])
        section_specs = extract_json(spec_response.content)

        # 解析失败时回退到默认规格，保证流程可继续
        if not isinstance(section_specs, list) or not section_specs:
            print("  ⚠ 章节规格解析失败，使用默认规格")
            section_specs = self._default_section_specs()

        # 规范化字段，补齐缺失项
        normalized = []
        for spec in section_specs:
            if not isinstance(spec, dict) or not spec.get("section"):
                continue
            normalized.append({
                "section": str(spec.get("section")).strip(),
                "requirements": str(spec.get("requirements", "")).strip()
                or f"撰写 {spec.get('section')} 章节的标准内容。",
                "min_words": int(spec.get("min_words", 150) or 150),
                "max_words": int(spec.get("max_words", 1200) or 1200),
            })
        if not normalized:
            normalized = self._default_section_specs()

        # 同时保留旧的 section_outlines 以兼容其它逻辑
        section_outlines = {s["section"]: s["requirements"] for s in normalized}

        print(f"✓ 完成论文架构设计，共 {len(normalized)} 个章节:")
        for s in normalized:
            print(f"    - {s['section']} ({s['min_words']}-{s['max_words']} 词)")

        return {
            "paper_architecture": architecture,
            "section_specs": normalized,
            "section_outlines": section_outlines,
            "current_section_index": 0,
            "paper_sections": {},
            "messages": [f"设计了论文架构，拆解为 {len(normalized)} 个章节"]
        }

    @staticmethod
    def _default_section_specs():
        """默认章节规格（当 LLM 输出无法解析时的回退）。"""
        return [
            {"section": "Abstract", "requirements": "概括问题、方法与主要结果。",
             "min_words": 150, "max_words": 250},
            {"section": "Introduction", "requirements": "介绍问题背景、动机、现有方法局限与本文贡献。",
             "min_words": 600, "max_words": 1000},
            {"section": "Related Work", "requirements": "综述相关工作并指出与本文的区别。",
             "min_words": 500, "max_words": 900},
            {"section": "Methodology", "requirements": "详细描述所提方法，从整体到细节。",
             "min_words": 800, "max_words": 1500},
            {"section": "Experiments", "requirements": "给出实验设置、对比实验与消融实验结果分析。",
             "min_words": 700, "max_words": 1200},
            {"section": "Conclusion", "requirements": "总结贡献并展望未来工作。",
             "min_words": 200, "max_words": 400},
        ]

    def dispatch_section(self, state: PaperAgentState) -> Dict[str, Any]:
        """
        节点6a: 派发下一个待写章节（设计模块 → 写作模块）

        从 section_specs 中取出当前索引对应的章节，作为写作模块的输入。
        重置该章节的尝试计数与反馈。
        """
        specs = state["section_specs"]
        idx = state.get("current_section_index", 0)
        spec = specs[idx]

        print(f"\n{'='*60}")
        print(f"[Step 6/11] 派发章节 {idx + 1}/{len(specs)}: {spec['section']}")
        print(f"  字数要求: {spec['min_words']}-{spec['max_words']} 词")
        print(f"{'='*60}")

        return {
            "current_section_name": spec["section"],
            "current_section_requirements": spec["requirements"],
            "current_section_min_words": spec["min_words"],
            "current_section_max_words": spec["max_words"],
            "section_feedback": "",
            "section_attempts": 0,
            "section_passed": False,
            "messages": [f"派发章节: {spec['section']}"]
        }

    def write_section(self, state: PaperAgentState) -> Dict[str, Any]:
        """
        节点6b: 撰写当前章节（写作模块，只写一节，需满足字数要求）

        会参考上一轮校验反馈进行重写。
        """
        section = state["current_section_name"]
        requirements = state["current_section_requirements"]
        min_words = state["current_section_min_words"]
        max_words = state["current_section_max_words"]
        attempts = state.get("section_attempts", 0) + 1
        feedback = state.get("section_feedback", "")

        print(f"\n  [写作] {section} (第 {attempts} 次尝试)...")

        # 为不同章节提供相应上下文
        if section in ("Methodology", "Method"):
            content_context = state.get("proposed_method", "")
        elif section in ("Experiments", "Results", "Results and Analysis"):
            content_context = state.get("experiment_results", "")
        elif section in ("Related Work",):
            content_context = state.get("inspirations", "") or state.get("papers_summary", "")
        elif section == "Abstract":
            content_context = (
                f"研究主题: {state.get('topic', '')}\n"
                f"核心创新: {state.get('key_innovations', '')}\n"
                f"主要结果: {state.get('experiment_results', '')}"
            )
        else:
            content_context = (
                f"研究主题: {state.get('topic', '')}\n"
                f"核心创新: {state.get('key_innovations', '')}\n"
                f"研究方案: {state.get('proposed_method', '')}"
            )

        feedback_text = (
            f"上一轮校验未通过，请针对性修改：\n{feedback}"
            if feedback else "这是首次撰写，暂无修改反馈。"
        )

        prompt = fill_prompt(
            SECTION_WRITING_PROMPT,
            section=section,
            requirements=requirements,
            min_words=min_words,
            max_words=max_words,
            content=content_context,
            feedback=feedback_text
        )

        response = self.llm.invoke([HumanMessage(content=prompt)])
        draft = response.content.strip()
        wc = count_words(draft)

        print(f"    生成草稿，约 {wc} 词")

        return {
            "current_section_draft": draft,
            "current_section_word_count": wc,
            "section_attempts": attempts,
            "messages": [f"撰写 {section} 第 {attempts} 次，{wc} 词"]
        }

    def validate_section(self, state: PaperAgentState) -> Dict[str, Any]:
        """
        节点6c: 校验当前章节（校验模块，确认字数和内容是否达标）

        通过则把章节保存进 paper_sections 并推进到下一节；
        未通过则带反馈返回写作模块重写。
        达到最大尝试次数时强制放行（保留当前草稿），避免死循环。
        """
        section = state["current_section_name"]
        requirements = state["current_section_requirements"]
        min_words = state["current_section_min_words"]
        max_words = state["current_section_max_words"]
        draft = state["current_section_draft"]
        actual_words = state["current_section_word_count"]
        attempts = state.get("section_attempts", 1)

        max_attempts = int(os.getenv("MAX_SECTION_ATTEMPTS", "3"))

        print(f"  [校验] {section}...")

        # 先做客观字数检查
        word_count_ok = min_words <= actual_words <= max_words

        # 调用 LLM 做内容检查
        prompt = fill_prompt(
            SECTION_VALIDATION_PROMPT,
            section=section,
            requirements=requirements,
            min_words=min_words,
            max_words=max_words,
            actual_words=actual_words,
            draft=draft
        )
        response = self.llm.invoke([HumanMessage(content=prompt)])
        result = extract_json(response.content)

        if isinstance(result, dict):
            content_ok = bool(result.get("content_ok", False))
            llm_word_ok = bool(result.get("word_count_ok", word_count_ok))
            feedback = str(result.get("feedback", "")).strip()
            llm_passed = bool(result.get("passed", False))
        else:
            # 解析失败：以客观字数为准，内容默认需要再检查
            content_ok = True
            llm_word_ok = word_count_ok
            feedback = "校验输出解析失败，按字数检查结果处理。"
            llm_passed = word_count_ok

        # 以客观字数检查为准结合内容检查
        passed = word_count_ok and content_ok and llm_passed

        # 更新已保存章节
        paper_sections = dict(state.get("paper_sections", {}))
        idx = state.get("current_section_index", 0)

        if passed:
            print(f"    ✓ 通过 (字数 {actual_words}, 区间 {min_words}-{max_words})")
            paper_sections[section] = draft
            return {
                "section_passed": True,
                "paper_sections": paper_sections,
                "current_section_index": idx + 1,
                "section_feedback": "",
                "messages": [f"章节 {section} 通过校验并保存"]
            }

        # 未通过但已达最大尝试次数：强制放行，保留当前草稿
        if attempts >= max_attempts:
            print(f"    ⚠ 已达最大尝试次数 ({max_attempts})，强制保存当前草稿")
            paper_sections[section] = draft
            return {
                "section_passed": True,
                "paper_sections": paper_sections,
                "current_section_index": idx + 1,
                "section_feedback": "",
                "messages": [f"章节 {section} 达最大尝试次数，强制放行"]
            }

        # 未通过，返回反馈重写
        reason = []
        if not word_count_ok:
            if actual_words < min_words:
                reason.append(f"字数不足，当前 {actual_words} 词，需达到至少 {min_words} 词，请扩写。")
            else:
                reason.append(f"字数超标，当前 {actual_words} 词，需不超过 {max_words} 词，请精简。")
        if not content_ok:
            reason.append(feedback)
        combined_feedback = " ".join([r for r in reason if r]) or feedback

        print(f"    ✗ 未通过: {combined_feedback[:80]}")

        return {
            "section_passed": False,
            "section_feedback": combined_feedback,
            "messages": [f"章节 {section} 未通过，准备重写"]
        }

    def assemble_paper(self, state: PaperAgentState) -> Dict[str, Any]:
        """
        节点6d: 所有章节写完后，按规格顺序组装为完整论文。
        """
        specs = state["section_specs"]
        paper_sections = state.get("paper_sections", {})

        print(f"\n{'='*60}")
        print(f"[Step 6/11] 组装完整论文（{len(paper_sections)} 个章节）")
        print(f"{'='*60}")

        ordered = []
        for spec in specs:
            name = spec["section"]
            content = paper_sections.get(name, "")
            ordered.append(f"\\section{{{name}}}\n{content}")
        full_paper = "\n\n".join(ordered)

        print(f"✓ 完成论文组装")

        return {
            "full_paper": full_paper,
            "messages": ["完成了论文撰写与组装"]
        }

    def polish_paper(self, state: PaperAgentState) -> Dict[str, Any]:
        """
        节点7: 润色论文

        Args:
            state: 当前状态

        Returns:
            更新的状态
        """
        print(f"\n{'='*60}")
        print(f"[Step 7/11] 润色论文...")
        print(f"{'='*60}")

        full_paper = state.get("polished_paper") or state.get("full_paper")

        # 构造提示词
        prompt = fill_prompt(PAPER_POLISH_PROMPT, content=full_paper)

        # 调用 LLM
        messages = [HumanMessage(content=prompt)]
        response = self.llm.invoke(messages)
        polished_content = response.content

        # 提取 Part 1 (LaTeX 内容)
        if "Part 1" in polished_content:
            parts = polished_content.split("Part 2")
            polished_paper = parts[0].replace("Part 1 [LaTeX]:", "").strip()
        else:
            polished_paper = polished_content

        print(f"✓ 完成论文润色")

        return {
            "polished_paper": polished_paper,
            "messages": ["润色了论文"]
        }

    def remove_ai_tone(self, state: PaperAgentState) -> Dict[str, Any]:
        """
        节点8: 去除 AI 味

        Args:
            state: 当前状态

        Returns:
            更新的状态
        """
        print(f"\n{'='*60}")
        print(f"[Step 8/11] 去除 AI 味...")
        print(f"{'='*60}")

        polished_paper = state["polished_paper"]

        # 构造提示词
        prompt = fill_prompt(REMOVE_AI_TONE_PROMPT, content=polished_paper)

        # 调用 LLM
        messages = [HumanMessage(content=prompt)]
        response = self.llm.invoke(messages)
        deai_content = response.content

        # 提取 Part 1
        if "Part 1" in deai_content:
            parts = deai_content.split("Part 2")
            deai_paper = parts[0].replace("Part 1 [LaTeX]:", "").strip()
        else:
            deai_paper = deai_content

        print(f"✓ 完成去 AI 味")

        return {
            "deai_paper": deai_paper,
            "messages": ["去除了 AI 味"]
        }

    def review_paper(self, state: PaperAgentState) -> Dict[str, Any]:
        """
        节点9: 审稿论文

        Args:
            state: 当前状态

        Returns:
            更新的状态
        """
        iteration = state.get("review_iteration", 0) + 1

        print(f"\n{'='*60}")
        print(f"[Step 9/11] 审稿论文 (第 {iteration} 次)...")
        print(f"{'='*60}")

        deai_paper = state["deai_paper"]
        target_conference = state.get("target_conference", "NeurIPS")

        # 构造提示词
        prompt = fill_prompt(
            PAPER_REVIEW_PROMPT,
            conference=target_conference,
            paper_content=deai_paper
        )

        # 调用审稿模型
        messages = [HumanMessage(content=prompt)]
        response = self.review_llm.invoke(messages)
        review_report = response.content

        # 提取评分（简化处理）
        score = 7.5  # 默认分数
        if "Rating:" in review_report or "评分：" in review_report:
            # 尝试提取分数
            import re
            score_match = re.search(r'(\d+\.?\d*)\s*分', review_report)
            if score_match:
                score = float(score_match.group(1))
            else:
                score_match = re.search(r'Rating:\s*(\d+\.?\d*)', review_report)
                if score_match:
                    score = float(score_match.group(1))

        print(f"  审稿评分: {score}/10")

        # 判断是否需要修改
        min_score = float(os.getenv("MIN_REVIEW_SCORE", "8.0"))
        max_iterations = int(os.getenv("MAX_REVIEW_ITERATIONS", "3"))

        needs_revision = (score < min_score) and (iteration < max_iterations)

        if needs_revision:
            print(f"  需要继续改进 (当前分数 {score} < 目标分数 {min_score})")
        else:
            if score >= min_score:
                print(f"  ✓ 达到目标分数!")
            else:
                print(f"  已达到最大迭代次数 ({max_iterations}), 终止优化")

        # 追加到审稿历史
        review_history = list(state.get("review_history", []))
        review_history.append({
            "iteration": iteration,
            "score": score,
            "report": review_report
        })

        return {
            "review_report": review_report,
            "review_score": score,
            "review_iteration": iteration,
            "review_history": review_history,
            "needs_revision": needs_revision,
            "messages": [f"完成第 {iteration} 次审稿，评分 {score}"]
        }

    def revise_by_review(self, state: PaperAgentState) -> Dict[str, Any]:
        """
        节点9b: 根据审稿意见修改论文（改稿模块）

        仅在审稿未通过时进入。依据 review_report 对全文进行针对性修改，
        修改结果作为后续润色的输入（写回 polished_paper 供 polish_paper 处理）。
        """
        print(f"\n{'='*60}")
        print(f"[Step] 根据审稿意见修改论文...")
        print(f"{'='*60}")

        review_report = state["review_report"]
        # 以最近一版论文为修改基础：优先去AI味后的版本，回退到润色版/全文
        paper_content = (
            state.get("deai_paper")
            or state.get("polished_paper")
            or state.get("full_paper")
        )

        prompt = fill_prompt(
            REVISE_BY_REVIEW_PROMPT,
            review_report=review_report,
            paper_content=paper_content
        )

        response = self.llm.invoke([HumanMessage(content=prompt)])
        revised = response.content.strip()

        # 若模型误带 Part 标记，做一次清理
        if revised.startswith("Part 1"):
            revised = revised.split("\n", 1)[-1].strip()

        print(f"✓ 完成按审稿意见改稿")

        # 写回 polished_paper，使下一步 polish_paper 在改稿基础上继续润色
        return {
            "revised_paper": revised,
            "polished_paper": revised,
            "messages": ["根据审稿意见修改了论文"]
        }

    def finalize_paper(self, state: PaperAgentState) -> Dict[str, Any]:
        """
        节点10: 生成最终论文

        Args:
            state: 当前状态

        Returns:
            更新的状态
        """
        print(f"\n{'='*60}")
        print(f"[Step 10/11] 生成最终论文...")
        print(f"{'='*60}")

        final_paper = state["deai_paper"]

        print(f"✓ 最终论文已准备完成")

        return {
            "final_paper": final_paper,
            "messages": ["生成了最终论文"]
        }
