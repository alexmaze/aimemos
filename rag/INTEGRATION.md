# RAG 与知识库系统集成说明

本文档说明如何使用 RAG 模块与 AIMemos 现有知识库系统的集成功能。

## 概述

RAG 集成提供了以下功能：

1. **自动索引**：将知识库中的文档自动索引到向量数据库
2. **语义搜索**：基于向量相似度的智能搜索
3. **增量更新**：支持单个文档的重新索引
4. **权限控制**：集成现有的用户权限系统

## 架构

```
┌─────────────────────────────────────────────────────────┐
│              AIMemos FastAPI Application                 │
├─────────────────────────────────────────────────────────┤
│  API Endpoints (/api/v1/rag)                            │
│  ├── POST /index          - 索引知识库                   │
│  ├── POST /search         - 语义搜索                     │
│  ├── DELETE /index/{kb_id}- 删除知识库索引              │
│  ├── POST /reindex/document/{doc_id} - 重新索引文档     │
│  └── DELETE /index/document/{doc_id} - 删除文档索引     │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│           RAG Integration Layer (integration.py)        │
│  - 连接知识库服务和文档服务                               │
│  - 管理向量索引生命周期                                   │
│  - 实现搜索和过滤逻辑                                     │
└─────────────────────────────────────────────────────────┘
            │                              │
            ▼                              ▼
┌──────────────────────┐      ┌──────────────────────────┐
│  Knowledge Base      │      │  RAG Core Modules        │
│  Services            │      │  - embeddings.py         │
│  - KnowledgeBase     │      │  - vector_store.py       │
│  - Document          │      │  - ingest.py             │
└──────────────────────┘      └──────────────────────────┘
            │                              │
            ▼                              ▼
┌──────────────────────┐      ┌──────────────────────────┐
│  SQLite Database     │      │  Milvus Lite Vector DB   │
│  (aimemos.db)        │      │  (milvus_aimemos.db)     │
└──────────────────────┘      └──────────────────────────┘
```

## 集成组件

### 1. RAG Integration (`rag/integration.py`)

核心集成模块，提供以下功能：

- `index_document()` - 索引单个文档
- `index_knowledge_base()` - 索引整个知识库
- `search_in_knowledge_base()` - 在指定知识库中搜索
- `search_all_knowledge_bases()` - 在所有知识库中搜索
- `delete_document_vectors()` - 删除文档向量
- `delete_knowledge_base_vectors()` - 删除知识库向量
- `reindex_document()` - 重新索引文档

### 2. API Endpoints (`aimemos/api/v1/endpoints/rag.py`)

提供 RESTful API 接口：

- `POST /api/v1/rag/index` - 索引知识库
- `POST /api/v1/rag/search` - 语义搜索
- `DELETE /api/v1/rag/index/{kb_id}` - 删除知识库索引
- `POST /api/v1/rag/reindex/document/{doc_id}` - 重新索引文档
- `DELETE /api/v1/rag/index/document/{doc_id}` - 删除文档索引

## 使用示例

### 1. 启动 AIMemos 应用

```bash
uv run aimemos
```

应用将在 `http://localhost:8000` 启动。

### 2. 创建用户和知识库

使用现有的 API 创建用户、知识库和文档：

```bash
# 注册用户
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "testuser",
    "password": "testpass"
  }'

# 登录获取 token
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"testuser","password":"testpass"}' | \
  python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# 创建知识库
KB_ID=$(curl -s -X POST "http://localhost:8000/api/v1/knowledge-bases" \
  -H "Content-Type: application/json" \
  -H "Authorization: ******" \
  -d '{
    "name": "AI 知识库",
    "description": "人工智能相关知识"
  }' | python -c "import sys, json; print(json.load(sys.stdin)['id'])")

# 创建文档
curl -X POST "http://localhost:8000/api/v1/documents?kb_id=$KB_ID" \
  -H "Content-Type: application/json" \
  -H "Authorization: ******" \
  -d '{
    "name": "人工智能简介",
    "content": "人工智能（Artificial Intelligence，简称AI）是计算机科学的一个分支...",
    "summary": "介绍人工智能的基本概念"
  }'
```

### 3. 索引知识库

```bash
# 索引整个知识库
curl -X POST "http://localhost:8000/api/v1/rag/index" \
  -H "Content-Type: application/json" \
  -H "Authorization: ******" \
  -d '{
    "kb_id": "'$KB_ID'",
    "max_tokens": 512,
    "overlap_tokens": 128
  }'
```

响应示例：
```json
{
  "kb_id": "kb_xxx",
  "kb_name": "AI 知识库",
  "total_documents": 5,
  "indexed_documents": 5,
  "skipped_documents": 0,
  "total_chunks": 12
}
```

### 4. 语义搜索

```bash
# 在指定知识库中搜索
curl -X POST "http://localhost:8000/api/v1/rag/search" \
  -H "Content-Type: application/json" \
  -H "Authorization: ******" \
  -d '{
    "query": "什么是机器学习？",
    "kb_id": "'$KB_ID'",
    "top_k": 5
  }'

# 在所有知识库中搜索（不指定 kb_id）
curl -X POST "http://localhost:8000/api/v1/rag/search" \
  -H "Content-Type: application/json" \
  -H "Authorization: ******" \
  -d '{
    "query": "深度学习的应用",
    "top_k": 10
  }'
```

响应示例：
```json
{
  "query": "什么是机器学习？",
  "kb_id": "kb_xxx",
  "results": [
    {
      "content": "机器学习是人工智能的一个子领域...",
      "source": "机器学习基础",
      "score": 0.8765,
      "metadata": {
        "kb_id": "kb_xxx",
        "doc_id": "doc_yyy",
        "doc_type": "note",
        "doc_name": "机器学习基础",
        "user_id": "testuser",
        "chunk_index": 0
      }
    }
  ],
  "total": 5
}
```

### 5. 文档更新后重新索引

```bash
# 更新文档内容
curl -X PUT "http://localhost:8000/api/v1/documents/$DOC_ID" \
  -H "Content-Type: application/json" \
  -H "Authorization: ******" \
  -d '{
    "content": "更新后的文档内容..."
  }'

# 重新索引文档
curl -X POST "http://localhost:8000/api/v1/rag/reindex/document/$DOC_ID" \
  -H "Authorization: ******"
```

### 6. 删除索引

```bash
# 删除文档索引
curl -X DELETE "http://localhost:8000/api/v1/rag/index/document/$DOC_ID" \
  -H "Authorization: ******"

# 删除整个知识库的索引
curl -X DELETE "http://localhost:8000/api/v1/rag/index/$KB_ID" \
  -H "Authorization: ******"
```

## Python 编程接口

也可以直接使用 Python 代码调用集成模块：

```python
from rag.integration import create_rag_integration

# 创建集成实例
rag = create_rag_integration()

# 索引知识库
stats = rag.index_knowledge_base(
    user_id="testuser",
    kb_id="kb_xxx",
    show_progress=True
)
print(f"索引了 {stats['indexed_documents']} 个文档")

# 搜索
results = rag.search_in_knowledge_base(
    user_id="testuser",
    kb_id="kb_xxx",
    query="什么是人工智能？",
    top_k=5
)

for result in results:
    print(f"- {result['source']}: {result['content'][:100]}...")

# 关闭连接
rag.close()
```

## 数据模型

### 向量数据库 Schema

```python
{
    "pk": int,                    # 主键（自动生成）
    "embedding": List[float],     # 768维向量（m3e-base）
    "content": str,               # 文本块内容
    "source": str,                # 文档名称
    "metadata": {                 # 元数据
        "kb_id": str,            # 知识库 ID
        "doc_id": str,           # 文档 ID
        "doc_type": str,         # 文档类型（note/uploaded）
        "doc_name": str,         # 文档名称
        "user_id": str,          # 用户 ID
        "chunk_index": int       # 块索引
    },
    "created_at": int             # 创建时间戳
}
```

## 权限控制

集成模块完全遵循 AIMemos 的权限模型：

1. **用户隔离**：每个用户只能访问自己的知识库和文档
2. **知识库权限**：通过 `kb_service.get_knowledge_base()` 验证权限
3. **文档权限**：通过 `doc_service.get_document()` 验证权限
4. **向量过滤**：搜索时自动添加 `user_id` 过滤条件

## 最佳实践

### 1. 索引时机

- **新建知识库**：创建知识库并添加文档后立即索引
- **批量导入**：批量导入文档后统一索引
- **文档更新**：更新文档内容后调用重新索引

### 2. 搜索优化

- **指定知识库**：如果明确知道搜索范围，指定 `kb_id` 可提高性能
- **合理的 top_k**：通常 5-10 个结果足够，避免过大的 top_k
- **结合传统搜索**：向量搜索与关键词搜索结合使用效果更好

### 3. 索引管理

- **定期清理**：删除知识库或文档时，同步删除向量索引
- **增量索引**：只对新增或修改的文档重新索引
- **批量操作**：避免频繁的小批量索引，尽量批量处理

## 性能考虑

1. **首次索引**：首次索引会下载 m3e-base 模型（约 400MB），需要一定时间
2. **索引速度**：取决于文档数量和内容长度，通常 100 个文档需要 1-2 分钟
3. **搜索延迟**：单次查询延迟通常 < 100ms（不含 LLM 生成时间）
4. **内存占用**：模型加载需要约 1-2GB 内存

## 故障排查

### 问题：索引失败

检查：
1. 文档内容是否为空
2. Milvus 数据库文件是否有写权限
3. 内存是否充足（至少 2GB 可用）

### 问题：搜索无结果

检查：
1. 知识库是否已索引
2. 用户权限是否正确
3. 查询文本是否过短或过于特殊

### 问题：性能慢

优化：
1. 使用 GPU 加速（如果可用）
2. 减小 `top_k` 值
3. 使用更小的 `max_tokens`
4. 批量索引而非逐个索引

## 下一步

1. **集成 LLM**：添加基于检索结果的问答生成
2. **自动触发**：文档创建/更新时自动触发索引
3. **批处理**：添加后台任务队列处理大批量索引
4. **多模态**：支持图片、表格等多模态内容
5. **Rerank**：添加重排序机制提升搜索质量

## 参考文档

- [RAG 设计文档](DESIGN_RAG.md)
- [RAG 使用指南](README.md)
- [AIMemos API 文档](http://localhost:8000/docs)
