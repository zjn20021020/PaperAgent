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

PaperAgent 是一个创新的 AI 研究助手，能够**自动完成从论文检索、灵感提取、方案设计到论文撰写的全流程**。基于 LangGraph 构建的多智能体系统，结合 LLM 的强大能力，实现了科研论文生成的完全自动化。

### ✨ 核心特性

#### 🎯 **端到端自动化工作流**
- **智能论文检索**：自动从 arXiv 检索相关研究，提取关键信息
- **研究灵感提取**：分析现有工作的局限性，发现创新机会
- **方案自动设计**：生成完整的研究方案和技术路线
- **实验设计**：自动设计对比实验、消融实验等完整实验方案
- **论文撰写**：生成符合顶会标准的完整 LaTeX 论文

#### 🔄 **智能迭代优化系统**
- **多轮润色**：自动优化学术表达和论文结构
- **AI 去味处理**：消除机械化表达，使文本更自然流畅
- **模拟审稿机制**：以 Reviewer 视角评估论文质量
- **自适应迭代**：根据评分自动决定是否继续优化（最多 3 轮）

#### 🛠️ **技术亮点**

1. **LangGraph 状态机架构**
   - 基于有向图的工作流管理
   - 清晰的状态转换逻辑
   - 支持条件分支和循环控制
   - 易于扩展和维护

2. **模块化设计**
   - 解耦的节点实现（10+ 核心节点）
   - 可插拔的工具模块
   - 灵活的提示词模板系统
   - 支持多种 LLM 后端（OpenAI、Anthropic）

3. **智能评估系统**
   - 多维度论文质量评估
   - 自动识别论文问题并提出改进建议
   - 迭代终止条件自动判断

4. **完整的日志追踪**
   - 记录每个节点的执行过程
   - 保存所有审稿历史
   - 便于调试和优化

### 📊 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    PaperAgent Workflow                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 论文检索 (arXiv Search)                                 │
│           ↓                                                 │
│  2. 灵感提取 (Inspiration Extraction)                       │
│           ↓                                                 │
│  3. 方案设计 (Proposal Design)                              │
│           ↓                                                 │
│  4. 实验设计 (Experiment Design)                            │
│           ↓                                                 │
│  5. 架构设计 (Architecture Design)                          │
│           ↓                                                 │
│  6. 论文撰写 (Paper Writing)                                │
│           ↓                                                 │
│  ┌────────────────────────────────┐                        │
│  │   迭代优化循环 (最多 3 轮)       │                        │
│  │                                │                        │
│  │  7. 论文润色 (Polishing)       │                        │
│  │       ↓                        │                        │
│  │  8. 去 AI 味 (Detoning)        │                        │
│  │       ↓                        │                        │
│  │  9. 审稿评估 (Review)          │                        │
│  │       ↓                        │                        │
│  │  评分 < 目标？ ────Yes──→ 返回 7  │                        │
│  │       ↓ No                    │                        │
│  └────────────────────────────────┘                        │
│           ↓                                                 │
│  10. 最终输出 (Finalization)                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 🚀 快速开始

#### 1. 环境配置

```bash
# 克隆项目
git clone https://github.com/your-username/PaperAgent.git
cd PaperAgent

# 安装依赖
pip install -r requirements.txt
```

#### 2. 配置 API Keys

复制环境变量模板并填入你的 API Keys：

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
MAX_REVIEW_ITERATIONS=3
MIN_REVIEW_SCORE=8.0
```

#### 3. 运行 Agent

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
├── main.py                # 主程序入口
├── graph.py               # LangGraph 工作流定义
├── nodes.py               # 各节点功能实现
├── state.py               # 状态定义
├── tools.py               # 工具函数
├── prompts.py             # 提示词模板库
├── requirements.txt       # 依赖包列表
├── .env.example           # 环境变量示例
├── Prompt.md              # 详细提示词文档
├── CONFIG.md              # 配置说明文档
├── output/                # 输出目录
│   └── example/           # 示例输出
└── README.md              # 本文件
```

### 📝 输出内容

运行完成后，在 `output/` 目录生成：

| 文件 | 说明 |
|------|------|
| `{topic}_{timestamp}.tex` | 完整的 LaTeX 格式论文 |
| `{topic}_{timestamp}_review_history.txt` | 完整的审稿历史（所有轮次） |
| `{topic}_{timestamp}_conversation_log.txt` | 完整的工作流执行日志 |

### 📌 示例展示

查看 `output/` 目录中的示例论文 **"SliceDice: A Hybrid Sparse and Low-Rank Attention Framework"**。

> **注意**：该示例使用 `deepseek-v4-flash` 模型生成。使用更高级的模型（如 GPT-4、Claude Opus）可获得更好的效果。

该示例展示了：
- ✅ 完整的论文结构（摘要、引言、方法论、实验、结论）
- ✅ 5 轮审稿迭代过程（评分从 7.50 → 3.00 → 7.50 → 6.00 → 7.50）
- ✅ 详细的改进建议和问题分析
- ✅ 符合 NeurIPS 会议标准的学术写作

### 🎨 支持的会议模板

- **NeurIPS** (Neural Information Processing Systems)
- **ICML** (International Conference on Machine Learning)
- **ICLR** (International Conference on Learning Representations)
- **ACL** (Association for Computational Linguistics)
- **CVPR** (Computer Vision and Pattern Recognition)
- **AAAI** (Association for the Advancement of Artificial Intelligence)

### 💡 使用建议

#### 模型选择

| 场景 | 推荐模型 | 说明 |
|------|---------|------|
| **主模型** | `gpt-4` / `claude-opus-4` | 平衡性能与成本 |
| **审稿模型** | `claude-opus-4` | 更严格的审稿标准 |
| **经济模式** | `gpt-4-turbo` / `deepseek-v4-flash` | 降低成本 |

#### 自定义提示词

所有提示词在 `prompts.py` 中定义，支持自定义修改：

```python
# 修改论文写作风格
PAPER_WRITING_PROMPT = """
# Role
你是一位顶级会议的资深作者...

# Task
撰写符合 {conference} 标准的论文...

# Constraints
- 使用学术化但清晰的语言
- 避免过度复杂的句式
...
"""
```

### 🔧 高级功能

#### 可视化工作流

```python
from graph import create_paper_agent_graph, visualize_graph

app = create_paper_agent_graph()
visualize_graph(app)
```

#### 自定义迭代参数

在 `.env` 中配置：

```env
MAX_REVIEW_ITERATIONS=5    # 最大迭代次数
MIN_REVIEW_SCORE=8.5       # 目标评分
```

### ⚠️ 免责声明

1. **学术诚信**：本工具生成的论文仅供参考和学习，不应直接提交发表。请务必进行人工审核、验证和完善。

2. **数据隐私**：使用第三方 API 时，数据会发送到外部服务器，请注意敏感信息保护。

3. **成本控制**：完整运行一次可能消耗较多 API 调用，建议先用小案例测试。

4. **实验结果**：当前版本使用模拟实验结果，实际使用需集成真实实验代码。

### 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 📄 许可证

MIT License

---

## English

### 📖 Overview

PaperAgent is an innovative AI research assistant that **automates the entire pipeline from paper retrieval to paper writing**. Built on LangGraph with multi-agent architecture, it leverages the power of LLMs to achieve end-to-end academic paper generation.

### ✨ Key Features

#### 🎯 **End-to-End Automation**
- **Smart Paper Retrieval**: Automatically fetch and analyze relevant research from arXiv
- **Inspiration Extraction**: Identify limitations in existing work and discover innovation opportunities
- **Proposal Generation**: Create complete research proposals and technical roadmaps
- **Experiment Design**: Design comprehensive experimental protocols including ablation studies
- **Paper Writing**: Generate publication-ready LaTeX papers meeting top-tier conference standards

#### 🔄 **Intelligent Iterative Optimization**
- **Multi-round Polishing**: Automatically refine academic expression and paper structure
- **AI Tone Removal**: Eliminate mechanical expressions for natural, fluent writing
- **Simulated Review**: Evaluate paper quality from a reviewer's perspective
- **Adaptive Iteration**: Automatically decide whether to continue optimization based on scores (max 3 rounds)

#### 🛠️ **Technical Highlights**

1. **LangGraph State Machine Architecture**
   - Graph-based workflow management
   - Clear state transition logic
   - Support for conditional branching and loops
   - Easy to extend and maintain

2. **Modular Design**
   - Decoupled node implementations (10+ core nodes)
   - Pluggable tool modules
   - Flexible prompt template system
   - Support for multiple LLM backends (OpenAI, Anthropic)

3. **Intelligent Evaluation System**
   - Multi-dimensional paper quality assessment
   - Automatic problem identification and improvement suggestions
   - Smart termination condition detection

4. **Complete Logging**
   - Track execution of each node
   - Preserve all review history
   - Facilitate debugging and optimization

### 🚀 Quick Start

#### 1. Installation

```bash
git clone https://github.com/your-username/PaperAgent.git
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

### 📌 Example Output

Check the example paper **"SliceDice: A Hybrid Sparse and Low-Rank Attention Framework"** in the `output/` directory.

> **Note**: This example was generated using `deepseek-v4-flash`. Better results can be achieved with more advanced models (e.g., GPT-4, Claude Opus).

The example demonstrates:
- ✅ Complete paper structure (Abstract, Introduction, Methodology, Experiments, Conclusion)
- ✅ 5 review iterations (scores: 7.50 → 3.00 → 7.50 → 6.00 → 7.50)
- ✅ Detailed improvement suggestions and analysis
- ✅ Academic writing meeting NeurIPS standards

### ⚠️ Disclaimer

1. **Academic Integrity**: Papers generated by this tool are for reference and learning only. Do not submit directly for publication. Manual review and refinement are required.

2. **Privacy**: When using third-party APIs, data is sent to external servers. Be cautious with sensitive information.

3. **Cost**: A complete run may consume significant API calls. Test with small examples first.

4. **Experiments**: The current version uses simulated experimental results. Real experiments need to be integrated for actual use.

### 📄 License

MIT License

---

<div align="center">

**Made with ❤️ for the research community**

If you find this project helpful, please give it a ⭐!

</div>
