"""
工具模块
包含论文检索、文档处理等工具函数
"""
import arxiv
import os
from typing import List, Dict
from datetime import datetime


class PaperSearchTool:
    """论文检索工具"""

    def __init__(self, max_results: int = 10):
        self.max_results = max_results
        self.client = arxiv.Client()

    def search_papers(
        self,
        query: str,
        max_results: int = None,
        sort_by: str = "relevance"
    ) -> List[Dict]:
        """
        从 arXiv 检索论文

        Args:
            query: 检索关键词
            max_results: 最大返回结果数
            sort_by: 排序方式，"relevance"（相关性，默认）或 "date"（最新）

        Returns:
            论文信息列表
        """
        if max_results is None:
            max_results = self.max_results

        if sort_by == "date":
            criterion = arxiv.SortCriterion.SubmittedDate
        else:
            criterion = arxiv.SortCriterion.Relevance

        try:
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=criterion,
                sort_order=arxiv.SortOrder.Descending
            )

            papers = []
            for result in self.client.results(search):
                paper_info = {
                    'title': result.title,
                    'authors': [author.name for author in result.authors],
                    'summary': result.summary,
                    'published': result.published.strftime('%Y-%m-%d'),
                    'pdf_url': result.pdf_url,
                    'categories': result.categories,
                    'primary_category': result.primary_category
                }
                papers.append(paper_info)

            return papers

        except Exception as e:
            print(f"Error searching papers: {e}")
            return []

    def format_papers_for_prompt(self, papers: List[Dict]) -> str:
        """
        将论文信息格式化为适合提示词的文本

        Args:
            papers: 论文信息列表

        Returns:
            格式化的文本
        """
        formatted = []
        for i, paper in enumerate(papers, 1):
            text = f"""
## Paper {i}: {paper['title']}

**Authors:** {', '.join(paper['authors'][:5])}{'...' if len(paper['authors']) > 5 else ''}

**Published:** {paper['published']}

**Categories:** {', '.join(paper['categories'])}

**Abstract:**
{paper['summary']}

**PDF URL:** {paper['pdf_url']}
"""
            formatted.append(text)

        return '\n\n'.join(formatted)


class DocumentGenerator:
    """文档生成工具"""

    @staticmethod
    def save_paper(content: str, filename: str, output_dir: str = "output") -> str:
        """
        保存论文到文件

        Args:
            content: 论文内容
            filename: 文件名
            output_dir: 输出目录

        Returns:
            保存的文件路径
        """
        os.makedirs(output_dir, exist_ok=True)

        # 添加时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_with_timestamp = f"{filename}_{timestamp}.tex"

        filepath = os.path.join(output_dir, filename_with_timestamp)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        return filepath

    @staticmethod
    def create_latex_template(
        title: str,
        authors: str,
        abstract: str,
        sections: Dict[str, str],
        conference: str = "NeurIPS"
    ) -> str:
        """
        创建 LaTeX 论文模板

        Args:
            title: 论文标题
            authors: 作者信息
            abstract: 摘要
            sections: 各章节内容字典
            conference: 目标会议

        Returns:
            LaTeX 文档内容
        """

        # 根据会议选择文档类
        if conference.upper() in ['NEURIPS', 'NIPS']:
            documentclass = 'neurips_2024'
        elif conference.upper() == 'ICML':
            documentclass = 'icml2024'
        elif conference.upper() == 'ICLR':
            documentclass = 'iclr2024_conference'
        else:
            documentclass = 'article'

        latex_content = f"""\\documentclass{{{documentclass}}}

\\usepackage{{amsmath}}
\\usepackage{{amssymb}}
\\usepackage{{graphicx}}
\\usepackage{{booktabs}}
\\usepackage{{hyperref}}
\\usepackage{{algorithm}}
\\usepackage{{algorithmic}}

\\title{{{title}}}

\\author{{{authors}}}

\\begin{{document}}

\\maketitle

\\begin{{abstract}}
{abstract}
\\end{{abstract}}

"""

        # 添加各个章节
        section_order = [
            'Introduction',
            'Related Work',
            'Methodology',
            'Method',
            'Experiments',
            'Results',
            'Results and Analysis',
            'Discussion',
            'Conclusion',
            'Limitations',
            'Broader Impact'
        ]

        for section_name in section_order:
            if section_name in sections:
                latex_content += f"""
\\section{{{section_name}}}
{sections[section_name]}

"""

        # 添加其他未在标准顺序中的章节
        for section_name, content in sections.items():
            if section_name not in section_order:
                latex_content += f"""
\\section{{{section_name}}}
{content}

"""

        # 添加参考文献
        latex_content += """
\\bibliographystyle{plain}
\\bibliography{references}

\\end{document}
"""

        return latex_content


class ExperimentSimulator:
    """实验模拟工具（用于生成模拟实验结果）"""

    @staticmethod
    def generate_mock_results(
        baselines: List[str],
        datasets: List[str],
        metrics: List[str],
        proposed_method: str = "Proposed Method"
    ) -> str:
        """
        生成模拟实验结果

        Args:
            baselines: 对比方法列表
            datasets: 数据集列表
            metrics: 评估指标列表
            proposed_method: 提出方法的名称

        Returns:
            格式化的实验结果文本
        """
        import random

        results = "# Experimental Results\n\n"

        for dataset in datasets:
            results += f"## Results on {dataset}\n\n"
            results += "| Method | " + " | ".join(metrics) + " |\n"
            results += "|--------|" + "|".join(["--------"] * len(metrics)) + "|\n"

            # 生成基线结果
            baseline_scores = {}
            for baseline in baselines:
                scores = [f"{random.uniform(0.70, 0.85):.3f}" for _ in metrics]
                baseline_scores[baseline] = scores
                results += f"| {baseline} | " + " | ".join(scores) + " |\n"

            # 生成提出方法的结果（略好于最佳基线）
            proposed_scores = []
            for i, metric in enumerate(metrics):
                best_baseline = max([float(baseline_scores[b][i]) for b in baselines])
                improvement = random.uniform(0.02, 0.05)
                proposed_scores.append(f"{best_baseline + improvement:.3f}")

            results += f"| **{proposed_method}** | " + " | ".join(proposed_scores) + " |\n\n"

        return results
