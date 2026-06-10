# PaperAgent 🤖📄

<div align="center">

**基于 LangGraph 的端到端学术论文自动生成系统**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/LangGraph-latest-green.svg)](https://github.com/langchain-ai/langgraph)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[English](#english) | [中文](#中文)

</div>

---

## 中文

### 📖 项目简介

PaperAgent 是一个**完全自动化的学术论文生成系统**，基于 LangGraph 构建的多智能体协作框架。它能够从零开始，完成从论文检索、灵感提取、方案设计、实验设计、论文撰写到多轮审稿优化的**完整科研流程**，最终生成符合顶会标准的 LaTeX 学术论文。

> **致谢**：本项目的 Prompt 设计参考了 [awesome-ai-research-writing](https://github.com/Leey21/awesome-ai-research-writing) 项目中的最佳实践。

### ✨ 核心特性

#### 🎯 **完整的端到端自动化工作流**
- **智能论文检索**：从 arXiv 自动检索相关研究，构建知识图谱
- **研究灵感提取**：分析现有工作的局限性，识别研究空白
- **方案自动设计**：生成完整的研究方案和技术路线
- **实验自动设计**：设计对比实验、消融实验等完整实验方案
- **逐章节撰写**：按架构设计逐节撰写，每节经过独立的写作-校验循环
- **智能迭代优化**：润色 → 去 AI 味 → 审稿 → 改稿的完整闭环

#### 🔄 **精细化的质量控制系统**

##### **章节流水线**（架构设计 → 逐节撰写）
每个章节独立经过「写作 → 校验 → 重写」循环，确保每节质量：
```
架构设计 (设计所有章节规格)
    ↓
派发章节 (取出一个待写章节)
    ↓
写作章节 (生成草稿)
    ↓
校验章节 (检查字数和内容)
    ├─ 未通过 → 返回「写作章节」(最多 3 次尝试)
    └─ 通过 → 保存章节
        ├─ 还有未写章节 → 返回「派发章节」
        └─ 所有章节完成 → 进入「组装论文」
```

##### **审稿迭代循环**（改稿 → 润色 → 审稿）
审稿未通过时，先根据审稿意见改稿，再进行润色和去 AI 味处理：
```
组装论文
    ↓
润色论文
    ↓
去 AI 味
    ↓
审稿评估
    ├─ 评分 < 目标 且 未达最大轮次
    │   ↓
    │   根据审稿意见改稿
    │   ↓
    │   返回「润色论文」(形成改稿-润色-审稿闭环)
    └─ 评分 ≥ 目标 或 达到最大轮次
        ↓
        最终输出
```

#### 🛠️ **技术亮点**

##### **1. LangGraph 状态机架构**
- **有向图工作流**：清晰的节点定义和状态转换
- **条件分支控制**：章节校验分支 + 审稿迭代分支
- **循环控制机制**：章节重写循环 + 审稿改进循环
- **状态持久化**：完整的状态追踪和历史记录

##### **2. 精细化模块设计**

**核心节点（11 个）**：
1. `retrieve_papers` - 论文检索
2. `extract_inspiration` - 灵感提取
3. `design_proposal` - 方案设计
4. `design_experiments` - 实验设计
5. `design_architecture` - 架构设计（生成章节规格）
6. `dispatch_section` - 派发待写章节
7. `write_section` - 撰写当前章节
8. `validate_section` - 校验章节质量
9. `assemble_paper` - 组装完整论文
10. `polish_paper` - 论文润色
11. `remove_ai_tone` - 去 AI 味
12. `review_paper` - 模拟审稿
13. `revise_by_review` - 根据审稿意见改稿
14. `finalize_paper` - 最终输出

**工具模块**：
- `PaperSearchTool` - arXiv 论文检索
- `ExperimentSimulator` - 实验结果模拟
- `DocumentGenerator` - LaTeX 文档生成

**提示词系统**：
- 从 `Prompt.md` 提取的专业模板
- 支持多会议格式（NeurIPS, ICML, ICLR, ACL, CVPR, AAAI）
- 精心设计的审稿人角色模拟

##### **3. 智能质量控制**

**章节级别控制**：
- 字数要求验证（最小/最大字数）
- 内容质量检查（逻辑完整性）
- 最多 3 次重写机会
- 达到上限后强制放行（避免死循环）

**论文级别控制**：
- 多维度评分系统
- 自动识别问题并生成改进建议
- 改稿后重新润色和去 AI 味
- 最多 3 轮审稿迭代（可配置）
- 目标分数可配置（默认 8.0/10）

##### **4. 完整的日志追踪**
- 每个节点的执行过程记录
- 所有审稿历史保存（每轮的评分和报告）
- 完整对话日志（便于调试和分析）

### 📊 系统架构

```
┌────────────────────────────────────────────────────────────────────────────┐
│                          PaperAgent Workflow                               │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  阶段 1: 知识获取                                                            │
│  ┌──────────────────────────────────────────────────────────────┐         │
│  │ 1. 检索相关论文 (arXiv Search)                                │         │
│  │      ↓                                                       │         │
│  │ 2. 提取研究灵感 (Inspiration Extraction)                      │         │
│  └──────────────────────────────────────────────────────────────┘         │
│                           ↓                                                │
│  阶段 2: 方案设计                                                            │
│  ┌──────────────────────────────────────────────────────────────┐         │
│  │ 3. 设计研究方案 (Proposal Design)                             │         │
│  │      ↓                                                       │         │
│  │ 4. 设计实验方案 (Experiment Design)                           │         │
│  └──────────────────────────────────────────────────────────────┘         │
│                           ↓                                                │
│  阶段 3: 论文撰写（章节流水线）                                               │
│  ┌──────────────────────────────────────────────────────────────┐         │
│  │ 5. 设计论文架构 (Architecture Design)                         │         │
│  │      ↓ (生成所有章节规格：名称、要求、字数范围)                  │         │
│  │  ┌────────────────────────────────────────────────────┐      │         │
│  │  │  逐章节循环 (Section Pipeline)                      │      │         │
│  │  │                                                    │      │         │
│  │  │  6. 派发章节 (Dispatch Section)                    │      │         │
│  │  │       ↓                                            │      │         │
│  │  │  7. 写作章节 (Write Section)                       │      │         │
│  │  │       ↓                                            │      │         │
│  │  │  8. 校验章节 (Validate Section)                    │      │         │
│  │  │       ↓                                            │      │         │
│  │  │  未通过？─Yes─→ 返回「写作章节」(带反馈，最多3次)       │      │         │
│  │  │       ↓ No                                         │      │         │
│  │  │  通过：保存章节                                      │      │         │
│  │  │       ↓                                            │      │         │
│  │  │  还有待写章节？─Yes─→ 返回「派发章节」              │      │         │
│  │  │       ↓ No                                         │      │         │
│  │  └────────────────────────────────────────────────────┘      │         │
│  │      ↓                                                       │         │
│  │ 9. 组装完整论文 (Assemble Paper)                             │         │
│  └──────────────────────────────────────────────────────────────┘         │
│                           ↓                                                │
│  阶段 4: 迭代优化（审稿闭环）                                                 │
│  ┌──────────────────────────────────────────────────────────────┐         │
│  │  ┌──────────────────────────────────────────────┐            │         │
│  │  │  审稿迭代循环 (最多 3 轮)                      │            │         │
│  │  │                                              │            │         │
│  │  │  10. 润色论文 (Polish Paper) ←─┐             │            │         │
│  │  │       ↓                       │             │            │         │
│  │  │  11. 去 AI 味 (Remove AI Tone) │             │            │         │
│  │  │       ↓                       │             │            │         │
│  │  │  12. 审稿评估 (Review Paper)   │             │            │         │
│  │  │       ↓                       │             │            │         │
│  │  │  评分 < 目标 且 未达最大轮次？    │             │            │         │
│  │  │       ↓ Yes                   │             │            │         │
│  │  │  13. 根据审稿意见改稿 ──────────┘             │            │         │
│  │  │       (Revise by Review)                   │            │         │
│  │  │                                              │            │         │
│  │  └──────────────────────────────────────────────┘            │         │
│  │       ↓ (评分达标 或 达到最大轮次)                             │         │
│  │  14. 最终输出 (Finalize Paper)                               │         │
│  └──────────────────────────────────────────────────────────────┘         │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### 🚀 快速开始

#### 1. 安装

```bash
# 克隆项目
git clone https://github.com/zjn20021020/PaperAgent.git
cd PaperAgent

# 安装依赖
pip install -r requirements.txt
```

#### 2. 配置 API Keys

复制环境变量模板：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# API Keys
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Model Configuration
DEFAULT_MODEL=gpt-4
REVIEW_MODEL=claude-opus-4

# Agent Configuration
MAX_REVIEW_ITERATIONS=3      # 最大审稿轮次
MIN_REVIEW_SCORE=8.0         # 目标评分
MAX_SECTION_ATTEMPTS=3       # 每章节最大重写次数
```

#### 3. 运行

基本用法：

```bash
python main.py --topic "Vision Transformer for Image Classification"
```

完整参数：

```bash
python main.py \
  --topic "Your Research Topic" \
  --conference NeurIPS \
  --model gpt-4 \
  --review-model claude-opus-4 \
  --output-dir output
```

### 📂 项目结构

```
PaperAgent/
├── main.py              # 主程序入口
├── graph.py             # LangGraph 工作流定义（状态图构建）
├── nodes.py             # 节点实现（14 个核心节点）
├── state.py             # 状态定义（TypedDict）
├── tools.py             # 工具模块（论文检索、文档生成等）
├── prompts.py           # 提示词模板库
├── requirements.txt     # Python 依赖
├── .env.example         # 环境变量模板
├── .gitignore           # Git 忽略配置
├── Prompt.md            # 详细提示词文档（参考自 awesome-ai-research-writing）
├── CONFIG.md            # 配置说明
├── output/              # 输出目录
│   ├── README.md        # 示例说明文档
│   └── *.tex            # 生成的论文文件
└── README.md            # 本文件
```

### 📝 输出内容

运行完成后，在 `output/` 目录生成以下文件：

| 文件 | 说明 |
|------|------|
| `{topic}_{timestamp}.tex` | 完整的 LaTeX 格式论文 |
| `{topic}_{timestamp}_review_history.txt` | 完整审稿历史（所有轮次的评分和报告） |
| `{topic}_{timestamp}_conversation_log.txt` | 完整工作流执行日志（所有节点的输出） |

### 📌 示例展示

查看 `output/` 目录中的示例论文 **"SliceDice: A Hybrid Sparse and Low-Rank Attention Framework"**。

> **⚠️ 重要说明**：该示例使用 **`deepseek-v4-flash`** 模型生成，这是一个经济型的快速模型。
> 
> **使用更高级的模型可获得显著更好的效果**：
> - **GPT-4** / **GPT-4 Turbo**：更强的推理能力和学术写作质量
> - **Claude Opus 4**：更严格的审稿标准和更自然的表达
> - **GPT-4o**：平衡性能与成本的最新模型

#### 示例亮点

✅ **完整的学术结构**
- Abstract, Introduction, Related Work, Methodology, Experiments, Conclusion
- 符合 NeurIPS 会议标准
- 使用专业的 LaTeX 排版

✅ **5 轮审稿迭代展示**
- 第 1 轮：7.50/10（初稿问题识别）
- 第 2 轮：3.00/10（发现致命问题：方法描述与实验脱节）
- 第 3 轮：7.50/10（问题修复）
- 第 4 轮：6.00/10（新问题：动机实验不充分）
- 第 5 轮：7.50/10（达到可接受水平）

✅ **真实的审稿反馈**
- 详细的优点和不足分析
- 具体的改进建议
- 问题根源剖析

查看 `output/README.md` 了解更多示例详情。

### 🎨 支持的会议模板

- **NeurIPS** - Neural Information Processing Systems
- **ICML** - International Conference on Machine Learning
- **ICLR** - International Conference on Learning Representations
- **ACL** - Association for Computational Linguistics
- **CVPR** - Computer Vision and Pattern Recognition
- **AAAI** - Association for the Advancement of Artificial Intelligence

### 💡 使用建议

#### 模型选择

| 用途 | 推荐模型 | 优势 |
|------|---------|------|
| **主模型（写作）** | `gpt-4` | 平衡性能与成本，学术写作质量高 |
| | `claude-opus-4` | 推理能力更强，适合复杂研究 |
| | `gpt-4-turbo` | 响应速度更快 |
| **审稿模型** | `claude-opus-4` | 审稿标准更严格，反馈更详细 |
| | `gpt-4` | 成本更低的选择 |
| **经济模式** | `deepseek-v4-flash` | 大幅降低成本，适合测试 |

#### 参数调优

在 `.env` 中调整关键参数：

```env
# 审稿控制
MAX_REVIEW_ITERATIONS=3      # 增加到 5 可获得更多优化机会
MIN_REVIEW_SCORE=8.5         # 提高目标分数要求更严格

# 章节控制
MAX_SECTION_ATTEMPTS=3       # 每章节最大重写次数
```

#### 自定义提示词

所有提示词在 `prompts.py` 中定义，可根据需要修改：

```python
# 示例：修改论文写作风格
SECTION_WRITING_PROMPT = """
# Role
你是顶级会议的资深作者...

# Task
撰写论文的 {section} 章节...

# Constraints
- 逻辑严谨，表达凝练
- 避免过度使用破折号和列表
- 去除 AI 味，保持自然流畅
...
"""
```

### 🔧 高级功能

#### 1. 可视化工作流

```python
from graph import create_paper_agent_graph, visualize_graph

app = create_paper_agent_graph()
visualize_graph(app)  # 需要安装 pygraphviz
```

#### 2. 支持自定义 LLM 后端

除了 OpenAI 和 Anthropic，还支持任何 OpenAI 兼容的 API：

```env
# DeepSeek API
LLM_API_KEY=your_deepseek_api_key
LLM_BASE_URL=https://api.deepseek.com/v1
DEFAULT_MODEL=deepseek-chat

# 本地 vLLM
LLM_API_KEY=dummy
LLM_BASE_URL=http://localhost:8000/v1
DEFAULT_MODEL=your-local-model
```

#### 3. 章节字数要求自动生成

系统会根据会议要求和章节类型自动分配字数：
- Abstract: 150-250 词
- Introduction: 600-1000 词
- Methodology: 800-1500 词
- Experiments: 700-1200 词
- Conclusion: 200-400 词

### ⚠️ 免责声明

1. **学术诚信**：本工具生成的论文**仅供参考和学习**，不应直接提交发表。请务必进行人工审核、验证实验结果和完善论证。

2. **数据隐私**：使用第三方 API 时，数据会发送到外部服务器，请注意敏感信息保护。

3. **成本控制**：完整运行一次可能消耗大量 API 调用（尤其是章节流水线和审稿迭代），建议先用小案例测试。

4. **实验结果**：当前版本使用**模拟实验结果**，实际使用需集成真实实验代码或手动替换实验数据。

### 🙏 致谢

- **Prompt 设计**：参考了 [awesome-ai-research-writing](https://github.com/Leey21/awesome-ai-research-writing) 项目的最佳实践
- **技术栈**：基于 [LangChain](https://github.com/langchain-ai/langchain) 和 [LangGraph](https://github.com/langchain-ai/langgraph) 构建

### 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 📄 许可证

MIT License

---

## English

### 📖 Overview

PaperAgent is a **fully automated academic paper generation system** built on LangGraph's multi-agent framework. It automates the entire research pipeline from paper retrieval to multi-round review optimization, generating publication-ready LaTeX papers that meet top-tier conference standards.

> **Acknowledgments**: The prompt design is inspired by best practices from the [awesome-ai-research-writing](https://github.com/Leey21/awesome-ai-research-writing) project.

### ✨ Key Features

#### 🎯 **End-to-End Automation**
- **Smart Paper Retrieval**: Automatically fetch and analyze relevant research from arXiv
- **Inspiration Extraction**: Identify limitations and research gaps
- **Proposal Generation**: Create complete research proposals and technical roadmaps
- **Experiment Design**: Design comprehensive experimental protocols
- **Section-by-Section Writing**: Each section goes through independent write-validate cycles
- **Iterative Optimization**: Complete loop of polish → detone → review → revise

#### 🔄 **Fine-Grained Quality Control**

##### **Section Pipeline** (Architecture Design → Section-by-Section Writing)
Each section independently goes through "write → validate → rewrite" cycles:
```
Architecture Design (generate all section specs)
    ↓
Dispatch Section (pick next section to write)
    ↓
Write Section (generate draft)
    ↓
Validate Section (check word count & content)
    ├─ Failed → Back to "Write Section" (max 3 attempts)
    └─ Passed → Save section
        ├─ More sections → Back to "Dispatch Section"
        └─ All done → "Assemble Paper"
```

##### **Review Iteration Loop** (Revise → Polish → Review)
When review fails, revise based on feedback first, then polish and detone:
```
Assemble Paper
    ↓
Polish Paper
    ↓
Remove AI Tone
    ↓
Review Paper
    ├─ Score < Target & Not Max Iterations
    │   ↓
    │   Revise by Review (based on feedback)
    │   ↓
    │   Back to "Polish Paper" (revise-polish-review loop)
    └─ Score ≥ Target or Max Iterations Reached
        ↓
        Finalize Paper
```

### 📌 Example Output

Check the example paper **"SliceDice: A Hybrid Sparse and Low-Rank Attention Framework"** in the `output/` directory.

> **⚠️ Important**: This example was generated using **`deepseek-v4-flash`**, an economical fast model.
> 
> **Use more advanced models for significantly better results**:
> - **GPT-4** / **GPT-4 Turbo**: Stronger reasoning and academic writing
> - **Claude Opus 4**: Stricter review standards and more natural expression
> - **GPT-4o**: Balanced performance and cost

The example demonstrates:
- ✅ Complete academic structure (Abstract, Introduction, Methodology, Experiments, Conclusion)
- ✅ 5 review iterations (scores: 7.50 → 3.00 → 7.50 → 6.00 → 7.50)
- ✅ Detailed improvement suggestions and problem analysis
- ✅ NeurIPS-compliant academic writing

### 🚀 Quick Start

#### 1. Installation

```bash
git clone https://github.com/zjn20021020/PaperAgent.git
cd PaperAgent
pip install -r requirements.txt
```

#### 2. Configure API Keys

```bash
cp .env.example .env
# Edit .env with your API keys
```

#### 3. Run

```bash
python main.py --topic "Vision Transformer for Image Classification"
```

### 💡 Model Selection

| Purpose | Recommended Model | Advantage |
|---------|------------------|-----------|
| **Main Model** | `gpt-4` | Balanced performance and cost |
| | `claude-opus-4` | Stronger reasoning for complex research |
| **Review Model** | `claude-opus-4` | Stricter standards, detailed feedback |
| **Budget Mode** | `deepseek-v4-flash` | Significantly lower cost |

### ⚠️ Disclaimer

1. **Academic Integrity**: Papers generated by this tool are **for reference and learning only**. Do not submit directly for publication. Manual review, experimental validation, and refinement are required.

2. **Privacy**: When using third-party APIs, data is sent to external servers. Be cautious with sensitive information.

3. **Cost**: A complete run may consume significant API calls. Test with small examples first.

4. **Experiments**: The current version uses **simulated experimental results**. Real experiments need to be integrated for actual use.

### 🙏 Acknowledgments

- **Prompt Design**: Inspired by [awesome-ai-research-writing](https://github.com/Leey21/awesome-ai-research-writing)
- **Tech Stack**: Built on [LangChain](https://github.com/langchain-ai/langchain) and [LangGraph](https://github.com/langchain-ai/langgraph)

### 📄 License

MIT License

---

<div align="center">

**Made with ❤️ for the research community**

If you find this project helpful, please give it a ⭐!

</div>
