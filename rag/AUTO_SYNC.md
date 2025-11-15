# RAG 自动同步功能

## 概述

RAG 模块现在支持**自动同步**功能。当文档发生变化时（创建、更新、删除），RAG 向量索引会自动更新，无需手动调用 API。

## 工作原理

### 事件钩子机制

系统在文档服务层实现了事件钩子机制，监听以下事件：

1. **文档创建** (`on_document_created`)
   - 触发时机：调用 `create_note()` 或 `upload_document()` 后
   - 自动操作：为新文档生成向量并索引到 Milvus

2. **文档更新** (`on_document_updated`)
   - 触发时机：调用 `update_document()` 后
   - 自动操作：删除旧向量，重新生成并索引新向量

3. **文档删除** (`on_document_deleted`)
   - 触发时机：调用 `delete_document()` 后
   - 自动操作：从 Milvus 中删除文档的所有向量

### 架构流程

```
┌─────────────────────────────────────────────────────────┐
│                API 请求 (FastAPI)                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│            Document Service                              │
│  ┌────────────────────────────────────────────────────┐ │
│  │ create_note() / upload_document()                  │ │
│  │    ↓                                               │ │
│  │ 1. 创建/上传文档到数据库                            │ │
│  │    ↓                                               │ │
│  │ 2. 调用 rag_sync_hook.on_document_created()       │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │ update_document()                                  │ │
│  │    ↓                                               │ │
│  │ 1. 更新文档数据库记录                              │ │
│  │    ↓                                               │ │
│  │ 2. 调用 rag_sync_hook.on_document_updated()       │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │ delete_document()                                  │ │
│  │    ↓                                               │ │
│  │ 1. 删除文档数据库记录                              │ │
│  │    ↓                                               │ │
│  │ 2. 调用 rag_sync_hook.on_document_deleted()       │ │
│  └────────────────────────────────────────────────────┘ │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              RAG Sync Hook                               │
│  ┌────────────────────────────────────────────────────┐ │
│  │ 延迟加载 RAG Integration                           │ │
│  │    ↓                                               │ │
│  │ 调用相应的 RAG 操作：                               │ │
│  │ - index_document()                                 │ │
│  │ - reindex_document()                               │ │
│  │ - delete_document_vectors()                        │ │
│  └────────────────────────────────────────────────────┘ │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│            RAG Integration → Milvus                      │
│  - 生成向量嵌入                                          │
│  - 更新向量索引                                          │
│  - 维护元数据关联                                        │
└─────────────────────────────────────────────────────────┘
```

## 使用示例

### 自动索引 - 无需额外操作

```python
# 1. 创建笔记 - 自动索引
response = requests.post(
    "http://localhost:8000/api/v1/documents?kb_id=kb123",
    headers={"Authorization": f"******"},
    json={
        "name": "机器学习笔记",
        "content": "机器学习是人工智能的一个分支..."
    }
)
# ✅ 文档创建后自动生成向量并索引

# 2. 上传文档 - 自动索引
files = {"file": open("ai_paper.pdf", "rb")}
data = {"kb_id": "kb123", "summary": "AI 论文"}
response = requests.post(
    "http://localhost:8000/api/v1/documents/upload",
    headers={"Authorization": f"******"},
    files=files,
    data=data
)
# ✅ 文件上传后自动提取文本、生成向量并索引

# 3. 更新文档 - 自动重新索引
response = requests.put(
    "http://localhost:8000/api/v1/documents/doc123",
    headers={"Authorization": f"******"},
    json={"content": "更新后的内容..."}
)
# ✅ 文档更新后自动删除旧向量、生成新向量并重新索引

# 4. 删除文档 - 自动删除向量
response = requests.delete(
    "http://localhost:8000/api/v1/documents/doc123",
    headers={"Authorization": f"******"}
)
# ✅ 文档删除后自动从向量数据库中删除相关向量

# 5. 语义搜索 - 直接使用最新索引
response = requests.post(
    "http://localhost:8000/api/v1/rag/search",
    headers={"Authorization": f"******"},
    json={
        "query": "什么是机器学习？",
        "kb_id": "kb123",
        "top_k": 5
    }
)
# ✅ 搜索结果自动反映最新的文档状态
```

## 日志和监控

自动同步操作会记录日志，便于监控和调试：

```python
# 成功日志示例
INFO - Auto-indexed document abc123 (机器学习笔记): 3 chunks
INFO - Auto-reindexed document abc123 (机器学习笔记): 4 chunks  
INFO - Auto-deleted 3 vectors for document abc123

# 错误日志示例
ERROR - Failed to auto-index document abc123: Connection timeout
ERROR - Failed to auto-reindex document abc123: Model not loaded
```

## 性能考虑

### 异步处理（未来改进）

当前实现是同步的，即文档操作会等待 RAG 索引完成。对于大文档或高并发场景，可能需要：

1. **后台任务队列**：使用 Celery 或类似工具异步处理
2. **批量延迟索引**：收集一段时间内的变更，批量处理
3. **增量更新优化**：只重新索引变更的部分

### 当前性能

- **小文档** (< 10KB)：索引耗时 < 1 秒
- **中等文档** (10-100KB)：索引耗时 1-5 秒
- **大文档** (> 100KB)：索引耗时 5-30 秒

## 配置选项

### 禁用自动同步

如果需要手动控制索引时机，可以禁用自动同步：

```python
from aimemos.services.rag_sync_hook import get_rag_sync_hook

# 禁用自动同步
hook = get_rag_sync_hook()
hook.disable()

# 执行文档操作（不会自动索引）
# ...

# 重新启用
hook.enable()
```

### 环境变量控制（未来）

计划添加环境变量控制：

```bash
# .env
RAG_AUTO_SYNC=true  # 启用自动同步（默认）
RAG_SYNC_ASYNC=false  # 同步模式（默认）
RAG_SYNC_BATCH_SIZE=10  # 批量处理大小
```

## 错误处理

自动同步采用**最佳努力**策略：

1. **索引失败不影响文档操作**
   - 文档成功创建/更新/删除
   - RAG 索引失败仅记录日志
   - 可以稍后手动重新索引

2. **失败重试**
   - 当前：记录错误，不重试
   - 未来：可配置自动重试策略

3. **状态一致性**
   - 文档状态始终以数据库为准
   - RAG 索引可通过手动 API 重建

## 手动索引 API（仍然可用）

即使启用了自动同步，仍然可以使用手动索引 API：

```bash
# 重新索引单个文档
POST /api/v1/rag/reindex/document/{doc_id}

# 索引整个知识库
POST /api/v1/rag/index
{
  "kb_id": "kb123"
}

# 删除文档索引
DELETE /api/v1/rag/index/document/{doc_id}
```

## 最佳实践

1. **批量导入**
   - 批量导入大量文档时，考虑暂时禁用自动同步
   - 导入完成后，使用 `/api/v1/rag/index` 一次性索引

2. **监控日志**
   - 定期检查错误日志
   - 对失败的索引进行手动重试

3. **性能优化**
   - 对于大文档，考虑分批上传
   - 避免频繁的小更新，合并为单次更新

4. **测试环境**
   - 测试环境可以禁用自动同步以加快测试速度
   - 生产环境建议启用自动同步

## 常见问题

### Q1: 自动同步会影响 API 响应速度吗？

**A**: 会有轻微影响。小文档（< 10KB）通常增加 < 1 秒延迟。未来版本将支持异步处理以完全消除影响。

### Q2: 如果自动索引失败怎么办？

**A**: 文档操作仍会成功完成，只是 RAG 索引未更新。可以通过手动 API 重新索引：
```bash
POST /api/v1/rag/reindex/document/{doc_id}
```

### Q3: 可以选择性地对某些文档禁用自动索引吗？

**A**: 当前版本不支持，但可以在代码中添加条件逻辑。未来版本将支持文档级别的配置。

### Q4: 文件夹类型会被索引吗？

**A**: 不会。系统自动跳过 `doc_type='folder'` 的文档，只索引笔记和上传文档。

### Q5: 如何查看某个文档的索引状态？

**A**: 当前版本通过日志查看。未来版本将添加 API 端点返回索引状态。

## 技术细节

### 延迟加载

RAG Integration 采用延迟加载机制：
- 首次文档操作时才初始化 RAG 组件
- 避免应用启动时的额外开销
- 如果 RAG 模块不可用，不影响文档服务

### 异常隔离

自动同步的错误不会影响主流程：
```python
try:
    rag.index_document(user_id, document)
except Exception as e:
    logger.error(f"Failed to auto-index: {e}")
    # 继续执行，不中断文档操作
```

### 资源管理

- RAG Integration 实例单例模式
- 避免重复加载嵌入模型
- 共享 Milvus 连接

## 未来改进

1. **异步任务队列**
   - 使用 Celery 异步处理索引
   - 支持失败重试和延迟队列

2. **批量优化**
   - 批量文档导入时自动检测并批量索引
   - 减少数据库往返次数

3. **智能更新**
   - 检测内容变化，只索引变更部分
   - 支持增量更新而非完全重建

4. **监控面板**
   - 索引状态仪表板
   - 实时同步进度显示
   - 错误统计和报警

## 参考文档

- [RAG 集成说明](INTEGRATION.md)
- [RAG 设计文档](DESIGN_RAG.md)
- [API 文档](http://localhost:8000/docs)
