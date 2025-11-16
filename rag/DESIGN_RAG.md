# RAG 模块设计文档

## 1. 总体架构

本 RAG (Retrieval-Augmented Generation) 模块为 AIMemos 知识库系统提供智能检索和生成能力，主要包含以下核心组件：

```
┌─────────────────────────────────────────────────────────┐
│                   用户查询接口                            │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Query Processing Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Query Parser │  │  Embedder    │  │Query Rewriter│  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Retrieval Layer (Milvus)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │Vector Search │  │  Re-ranker   │  │Context Filter│  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│            Generation Layer (LLM)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │Prompt Builder│  │  LLM Client  │  │Response Parse│  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   响应返回用户                            │
└─────────────────────────────────────────────────────────┘
```

### 数据流程

1. **文档摄取流程**：文档 → 分块 → 嵌入 → 向量存储
2. **查询流程**：用户查询 → 嵌入 → 向量检索 → 重排序 → 上下文构建 → LLM 生成 → 结果返回

## 2. 组件清单

### 2.1 核心组件

| 组件名称 | 文件路径 | 功能描述 |
|---------|---------|---------|
| Embeddings | `rag/embeddings.py` | 基于 moka-ai/m3e-base 的向量嵌入服务 |
| Vector Store | `rag/vector_store.py` | Milvus Lite 向量数据库操作封装 |
| Ingest Pipeline | `rag/ingest.py` | 文档摄取与索引构建管道 |
| LLM Client | `rag/llm_client.py` | OpenAI 兼容的本地 LLM 客户端 |
| Workflow | `pocketflow/rag_workflow.yaml` | PocketFlow 工作流编排定义 |

### 2.2 依赖库

详见 `rag/requirements.txt`：
- **transformers**: Hugging Face 模型加载
- **torch**: 深度学习框架
- **pymilvus**: Milvus 向量数据库客户端
- **sentencepiece**: 分词器支持
- **requests**: HTTP 客户端
- **tqdm**: 进度条显示
- **python-dateutil**: 时间处理
- **ujson**: 高性能 JSON 解析

## 3. Milvus Schema 设计

### 3.1 Collection: kb_documents

```python
collection_name = "kb_documents"

schema = {
    "fields": [
        {
            "name": "pk",
            "type": "INT64",
            "is_primary": True,
            "auto_id": True,
            "description": "主键 ID"
        },
        {
            "name": "embedding",
            "type": "FLOAT_VECTOR",
            "dim": 768,  # m3e-base 向量维度
            "description": "文档块的向量表示"
        },
        {
            "name": "content",
            "type": "VARCHAR",
            "max_length": 65535,
            "description": "原始文本内容"
        },
        {
            "name": "source",
            "type": "VARCHAR",
            "max_length": 512,
            "description": "文档来源路径或标识"
        },
        {
            "name": "metadata",
            "type": "JSON",
            "description": "元数据（知识库ID、文档类型、标签等）"
        },
        {
            "name": "created_at",
            "type": "INT64",
            "description": "创建时间戳（毫秒）"
        }
    ]
}
```

### 3.2 索引配置

```python
index_params = {
    "metric_type": "L2",  # 欧氏距离
    "index_type": "IVF_FLAT",  # 倒排文件索引
    "params": {
        "nlist": 128  # 聚类中心数量
    }
}
```

### 3.3 搜索参数

```python
search_params = {
    "metric_type": "L2",
    "params": {
        "nprobe": 10  # 搜索的聚类数量
    }
}
```

## 4. Chunking 策略

### 4.1 Token-based Chunking

- **分块方法**：基于 tokenizer 的 token 数量分块
- **最大 tokens**：512 tokens/chunk
- **重叠 tokens**：128 tokens（25% 重叠）
- **分隔符优先级**：双换行 > 单换行 > 句号 > 逗号 > 空格

### 4.2 实现逻辑

```python
def chunk_text(text, tokenizer, max_tokens=512, overlap=128):
    """
    将文本按 token 数量分块
    
    参数:
        text: 原始文本
        tokenizer: 分词器
        max_tokens: 每块最大 token 数
        overlap: 块之间重叠的 token 数
    
    返回:
        List[str]: 文本块列表
    """
    # 1. 将文本编码为 tokens
    # 2. 按 max_tokens 切分
    # 3. 添加 overlap 确保上下文连续性
    # 4. 解码回文本
```

### 4.3 优势

- 保持语义完整性
- 避免截断关键信息
- 通过重叠确保上下文连贯
- 适配模型最大输入长度

## 5. 检索与 Rerank 策略

### 5.1 两阶段检索

#### 第一阶段：向量召回（Recall）

```python
# 从 Milvus 检索 top-k 候选
top_k = 20  # 召回数量
results = vector_store.search(
    query_embedding=query_vec,
    top_k=top_k,
    filter_expr='metadata["kb_id"] == "{kb_id}"'  # 可选的知识库过滤
)
```

#### 第二阶段：重排序（Rerank）

```python
# 基于以下因素重排序：
# 1. 语义相似度（向量距离）
# 2. 关键词匹配度（BM25 分数）
# 3. 时间新鲜度（可选）
# 4. 文档重要性（可选）

final_top_n = 5  # 最终返回数量
reranked_results = rerank(
    results,
    query=user_query,
    top_n=final_top_n,
    weights={
        "semantic": 0.7,
        "keyword": 0.2,
        "freshness": 0.1
    }
)
```

### 5.2 混合检索（Hybrid Search）

未来可扩展支持：
- 向量检索 + 全文检索
- 稠密向量 + 稀疏向量
- 多向量表示（文本 + 表格 + 图片）

## 6. Prompt 模板

### 6.1 基础 RAG Prompt

```python
RAG_PROMPT_TEMPLATE = """你是一个专业的知识库助手。基于以下提供的上下文信息，准确回答用户的问题。

## 上下文信息

{context}

## 用户问题

{question}

## 回答要求

1. 仅基于提供的上下文信息回答
2. 如果上下文中没有相关信息，请明确说明"根据当前知识库，我无法回答这个问题"
3. 回答要准确、简洁、专业
4. 如果可能，引用具体的来源信息

## 你的回答

"""
```

### 6.2 多轮对话 Prompt

```python
CONVERSATION_PROMPT_TEMPLATE = """你是一个专业的知识库助手。基于历史对话和上下文信息，回答用户的问题。

## 对话历史

{chat_history}

## 相关上下文

{context}

## 当前问题

{question}

## 回答

"""
```

### 6.3 自我反思 Prompt（高级）

```python
REFLECTION_PROMPT_TEMPLATE = """请评估以下回答的质量：

原始问题：{question}
上下文：{context}
生成回答：{answer}

评估维度：
1. 准确性（是否基于上下文）
2. 完整性（是否充分回答）
3. 相关性（是否切题）

评分（1-5）：
改进建议：
"""
```

## 7. 监控与安全建议

### 7.1 监控指标

#### 性能指标
- 查询响应时间（p50, p95, p99）
- 向量检索延迟
- LLM 生成延迟
- 吞吐量（QPS）

#### 质量指标
- 检索准确率（Top-K Accuracy）
- 答案相关性评分
- 用户满意度反馈
- 引用准确性

#### 资源指标
- CPU/GPU 使用率
- 内存占用
- 向量数据库大小
- 缓存命中率

### 7.2 安全建议

#### 输入验证
```python
# 1. 查询长度限制
MAX_QUERY_LENGTH = 1000

# 2. 防止注入攻击
def sanitize_query(query: str) -> str:
    # 移除特殊字符
    # 限制格式
    pass

# 3. 敏感词过滤
BLOCKED_KEYWORDS = [...]
```

#### 访问控制
```python
# 1. 用户权限验证
def check_kb_permission(user_id: str, kb_id: str) -> bool:
    # 检查用户是否有权访问该知识库
    pass

# 2. 内容过滤
# 确保检索结果仅来自用户有权访问的知识库
filter_expr = f'metadata["owner_id"] == "{user_id}"'
```

#### 数据隐私
- 向量数据库访问控制
- 日志脱敏（不记录敏感查询内容）
- 定期清理过期数据
- 加密存储（可选）

#### 速率限制
```python
# 防止滥用
@rate_limit(max_requests=100, window=60)  # 100 req/min
def query_rag(query: str, kb_id: str):
    pass
```

## 8. 最小可行开发步骤

### Phase 1: 基础设施（第1-2周）

**目标**：搭建基础环境和数据流程

1. **环境准备**
   - [ ] 安装依赖（`pip install -r rag/requirements.txt`）
   - [ ] 下载 m3e-base 模型（约 400MB）
   - [ ] 启动 Milvus Lite

2. **Embedding 服务**
   - [ ] 实现 `embeddings.py`
   - [ ] 测试向量生成（单文本、批量）
   - [ ] 验证向量维度和归一化

3. **向量存储**
   - [ ] 实现 `vector_store.py`
   - [ ] 创建 collection 和索引
   - [ ] 测试插入和检索功能

4. **文档摄取**
   - [ ] 实现 `ingest.py`
   - [ ] 测试文本分块逻辑
   - [ ] 批量索引测试数据

**验收标准**：
- 能够将文档目录索引到 Milvus
- 向量检索返回相关结果
- 端到端耗时 < 10秒（100个文档）

### Phase 2: LLM 集成（第3周）

**目标**：集成本地 LLM 生成能力

1. **LLM 客户端**
   - [ ] 实现 `llm_client.py`
   - [ ] 测试 chat_completion 接口
   - [ ] 处理流式输出（可选）

2. **Prompt 工程**
   - [ ] 设计基础 RAG prompt
   - [ ] 测试不同 prompt 模板效果
   - [ ] 优化上下文窗口利用率

3. **端到端集成**
   - [ ] 查询 → 检索 → 生成流程
   - [ ] 错误处理和重试机制
   - [ ] 性能优化（并发、缓存）

**验收标准**：
- 查询响应时间 < 5秒
- 答案基于检索到的上下文
- 引用来源清晰可追溯

### Phase 3: 工作流编排（第4周）

**目标**：使用 PocketFlow 编排完整流程

1. **PocketFlow 集成**
   - [ ] 编写 `rag_workflow.yaml`
   - [ ] 定义 ingest、reindex、query 任务
   - [ ] 配置任务依赖和参数

2. **批处理支持**
   - [ ] 批量文档索引任务
   - [ ] 定期重建索引任务
   - [ ] 增量更新支持

3. **监控和日志**
   - [ ] 添加关键节点日志
   - [ ] 性能指标收集
   - [ ] 错误报警机制

**验收标准**：
- 通过 PocketFlow 启动完整流程
- 任务状态可追踪
- 失败任务自动重试

### Phase 4: 优化与增强（第5-6周）

**目标**：性能优化和功能增强

1. **检索优化**
   - [ ] 实现 Rerank 机制
   - [ ] 混合检索（向量+关键词）
   - [ ] 缓存热门查询

2. **生成优化**
   - [ ] Prompt 模板优化
   - [ ] 上下文压缩策略
   - [ ] 多轮对话支持

3. **用户体验**
   - [ ] 流式输出支持
   - [ ] 引用高亮显示
   - [ ] 相关性评分展示

**验收标准**：
- 检索准确率提升 20%+
- 响应速度提升 30%+
- 用户满意度 > 4.0/5.0

## 9. 技术选型理由

### 9.1 为什么选择 m3e-base？

- **中文友好**：专门针对中文优化的嵌入模型
- **性能优秀**：在中文语义理解任务上表现出色
- **轻量级**：约 400MB，适合本地部署
- **开源免费**：可商用，无版权风险

### 9.2 为什么选择 Milvus Lite？

- **轻量部署**：单文件部署，无需复杂配置
- **高性能**：支持海量向量检索（百万级）
- **易于集成**：Python SDK 使用简单
- **可扩展**：未来可平滑迁移到 Milvus 集群版

### 9.3 为什么使用 PocketFlow？

- **项目统一**：与 AIMemos 现有技术栈一致
- **工作流编排**：支持复杂的任务依赖和调度
- **易于维护**：YAML 配置，清晰直观

## 10. 未来扩展方向

### 10.1 短期（1-3个月）

- 支持更多文档格式（PDF、Word、PPT）
- 图片和表格内容理解
- 多模态检索（文本+图片）

### 10.2 中期（3-6个月）

- 知识图谱构建
- 实体关系抽取
- 自动摘要和标签生成
- A/B 测试框架

### 10.3 长期（6-12个月）

- 多语言支持（英文、日文等）
- 联邦学习（隐私保护）
- 主动学习（持续优化）
- 垂直领域微调

## 11. 常见问题 FAQ

### Q1: 如何调整检索结果数量？

修改 `ingest.py` 或查询代码中的 `top_k` 参数。建议：
- 召回阶段：top_k = 10-20
- 重排序后：top_n = 3-5

### Q2: 如何处理长文档？

使用分块策略：
- 设置合理的 `max_tokens`（推荐 512）
- 增加 `overlap`（推荐 128）
- 分块时保持语义完整性

### Q3: 如何提升检索准确率？

1. 优化分块策略
2. 使用混合检索
3. 添加 Rerank 层
4. 优化 Prompt 设计
5. 收集用户反馈进行微调

### Q4: 如何降低成本？

1. 使用本地 LLM（无 API 费用）
2. 缓存常见查询
3. 批量处理降低调用次数
4. 按需加载模型

### Q5: 如何确保数据安全？

1. 用户权限验证
2. 知识库隔离
3. 敏感数据过滤
4. 访问日志审计
5. 定期备份

## 12. 参考资源

### 模型和工具
- [moka-ai/m3e-base](https://huggingface.co/moka-ai/m3e-base) - 中文 Embedding 模型
- [Milvus](https://milvus.io/) - 向量数据库
- [PocketFlow](https://github.com/pocketflow-ai/pocketflow) - 工作流框架

### 相关论文
- [RAG: Retrieval-Augmented Generation](https://arxiv.org/abs/2005.11401)
- [Dense Passage Retrieval](https://arxiv.org/abs/2004.04906)
- [Improving Language Models by Retrieving from Trillions of Tokens](https://arxiv.org/abs/2112.04426)

### 最佳实践
- [LangChain RAG Guide](https://python.langchain.com/docs/use_cases/question_answering/)
- [OpenAI Embeddings Best Practices](https://platform.openai.com/docs/guides/embeddings)

---

**文档版本**: v1.0  
**最后更新**: 2025-11-14  
**维护者**: AIMemos Team
