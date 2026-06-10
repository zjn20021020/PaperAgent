# 配置指南

## API Keys 配置

### 1. OpenAI API Key

访问 [OpenAI Platform](https://platform.openai.com/api-keys) 获取 API Key。

```env
OPENAI_API_KEY=sk-...
```

### 2. Anthropic API Key

访问 [Anthropic Console](https://console.anthropic.com/) 获取 API Key。

```env
ANTHROPIC_API_KEY=sk-ant-...
```

## 模型配置

### 支持的模型

#### OpenAI 模型
- `gpt-4`: GPT-4 标准版本
- `gpt-4-turbo`: GPT-4 Turbo 版本（更快）
- `gpt-4o`: GPT-4 Omni（多模态）
- `gpt-3.5-turbo`: GPT-3.5（成本更低）

#### Anthropic 模型
- `claude-opus-4`: Claude Opus 4（最强推理能力）
- `claude-sonnet-4`: Claude Sonnet 4（平衡性能）
- `claude-haiku-4`: Claude Haiku 4（快速响应）

### 推荐配置

#### 方案 1: 成本优化
```env
DEFAULT_MODEL=gpt-4-turbo
REVIEW_MODEL=gpt-4-turbo
```

#### 方案 2: 质量优先
```env
DEFAULT_MODEL=claude-opus-4
REVIEW_MODEL=claude-opus-4
```

#### 方案 3: 混合方案（推荐）
```env
DEFAULT_MODEL=gpt-4
REVIEW_MODEL=claude-opus-4
```
- 主模型使用 GPT-4 完成大部分任务
- 审稿模型使用 Claude Opus 提供更严格的评估

## Agent 配置

### 审稿迭代控制

```env
# 最大审稿迭代次数
MAX_REVIEW_ITERATIONS=3

# 目标评分（1-10 分）
MIN_REVIEW_SCORE=8.0
```

#### 配置建议

- **快速模式**: `MAX_REVIEW_ITERATIONS=1`, `MIN_REVIEW_SCORE=7.0`
  - 适合初稿生成
  - 成本最低

- **标准模式**: `MAX_REVIEW_ITERATIONS=3`, `MIN_REVIEW_SCORE=8.0`
  - 适合正常使用
  - 平衡质量和成本

- **高质量模式**: `MAX_REVIEW_ITERATIONS=5`, `MIN_REVIEW_SCORE=8.5`
  - 适合重要论文
  - 成本较高

## 高级配置

### 温度参数

在代码中可以调整温度参数（0-1）：

```python
app = create_paper_agent_graph(
    model_name="gpt-4",
    temperature=0.7  # 默认 0.7
)
```

- `temperature=0.3`: 更保守，输出更确定
- `temperature=0.7`: 平衡创造性和准确性（推荐）
- `temperature=0.9`: 更有创造性，但可能偏离主题

### 论文检索数量

在 `tools.py` 中修改：

```python
class PaperSearchTool:
    def __init__(self, max_results: int = 10):  # 默认 10 篇
        self.max_results = max_results
```

建议范围：5-20 篇
- 太少：可能遗漏重要研究
- 太多：增加处理时间和成本

## 成本估算

### 单次完整运行大致成本（使用 GPT-4）

| 阶段 | Token 消耗 | 成本（USD） |
|------|-----------|------------|
| 论文检索与分析 | ~10K | $0.30 |
| 方案设计 | ~5K | $0.15 |
| 实验设计 | ~5K | $0.15 |
| 论文撰写 | ~20K | $0.60 |
| 润色与优化 | ~15K | $0.45 |
| 审稿（3次） | ~15K | $0.45 |
| **总计** | **~70K** | **~$2.10** |

*注：实际成本可能因论文复杂度而异*

### 成本优化建议

1. **使用 GPT-4-Turbo**: 成本约为 GPT-4 的 1/3
2. **减少审稿迭代**: 设置 `MAX_REVIEW_ITERATIONS=1`
3. **减少论文检索数量**: `max_results=5`
4. **使用 GPT-3.5**: 成本最低，但质量会下降

## 故障排查

### API Key 无效

```
Error: Incorrect API key provided
```

**解决方案**:
1. 检查 `.env` 文件是否存在
2. 确认 API Key 格式正确
3. 验证 API Key 是否有效且有余额

### 速率限制

```
Error: Rate limit exceeded
```

**解决方案**:
1. 等待几分钟后重试
2. 升级 API 账户以获得更高限额
3. 使用不同的 API Key

### 网络超时

```
Error: Request timeout
```

**解决方案**:
1. 检查网络连接
2. 增加超时时间（在代码中设置 `request_timeout`）
3. 使用 VPN（如果 API 在你的地区不可用）

### arXiv 检索失败

```
Error: Unable to fetch papers from arXiv
```

**解决方案**:
1. 检查网络连接到 arxiv.org
2. 减少 `max_results` 数量
3. 更改搜索关键词
4. 稍后重试（可能是临时限流）

## 环境变量完整示例

```env
# ======================
# API Keys
# ======================
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxx

# ======================
# Model Configuration
# ======================
# 主要模型：用于论文生成、分析等
DEFAULT_MODEL=gpt-4

# 审稿模型：用于论文审查
REVIEW_MODEL=claude-opus-4

# ======================
# Agent Configuration
# ======================
# 最大审稿迭代次数（1-10）
MAX_REVIEW_ITERATIONS=3

# 目标审稿分数（1.0-10.0）
MIN_REVIEW_SCORE=8.0

# ======================
# Optional: Advanced Settings
# ======================
# 论文检索最大结果数
# MAX_PAPERS=10

# LLM 温度参数
# TEMPERATURE=0.7

# 请求超时时间（秒）
# REQUEST_TIMEOUT=120
```

## 测试配置

使用以下命令测试你的配置：

```bash
# 测试 API Keys
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('OpenAI Key:', 'OK' if os.getenv('OPENAI_API_KEY') else 'Missing'); print('Anthropic Key:', 'OK' if os.getenv('ANTHROPIC_API_KEY') else 'Missing')"

# 快速测试运行（使用简单主题）
python main.py --topic "Machine Learning" --conference NeurIPS
```

## 参考链接

- [OpenAI API 文档](https://platform.openai.com/docs/api-reference)
- [Anthropic API 文档](https://docs.anthropic.com/claude/reference)
- [LangChain 文档](https://python.langchain.com/)
- [LangGraph 文档](https://python.langchain.com/docs/langgraph)
