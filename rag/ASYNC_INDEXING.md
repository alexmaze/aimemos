# RAG 异步索引功能文档

## 概述

RAG 模块支持异步索引，通过线程池管理索引任务，提供高效的并发控制和完善的任务管理机制。

## 核心特性

### 1. 异步执行

- 索引任务在独立的工作线程中执行，不阻塞文档创建/更新操作
- 使用 `ThreadPoolExecutor` 管理线程池
- 默认最大并发数：4 个索引任务

### 2. 任务追踪

每个索引任务都有唯一标识符（UUID）和线程 ID：

```python
{
    "rag_index_task_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "rag_index_thread_id": 140735268359424,
    "rag_index_status": "indexing",
    "rag_index_started_at": "2025-11-15T06:30:00Z"
}
```

### 3. 防止重复执行

- 每个文档同一时间只能有一个活跃的索引任务
- 新任务提交时自动取消该文档的旧任务
- 通过 `task_uuid` 验证任务有效性，防止过期任务污染数据

### 4. 超时控制

- 默认超时时间：300 秒（5 分钟）
- 在文档列表/详情查询时自动检查超时任务
- 超时任务自动标记为 `timeout` 状态

### 5. 安全的任务终止

**问题**：线程 ID 可能被复用，直接根据线程 ID 终止可能误杀其他任务

**解决方案**：使用 `task_uuid` 进行任务验证

```python
# 在任务执行的关键节点验证 task_uuid
def _index_document_async(task_uuid, user_id, document):
    # 1. 开始前验证
    doc = doc_repo.get_by_id(user_id, document.id)
    if doc.rag_index_task_uuid != task_uuid:
        return  # 任务已被取消，退出
    
    # 2. 执行索引...
    
    # 3. 完成前再次验证
    doc = doc_repo.get_by_id(user_id, document.id)
    if doc.rag_index_task_uuid != task_uuid:
        return  # 避免更新过期状态
    
    # 4. 更新为完成状态
    update_status('completed')
```

## 数据库字段

### 新增字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `rag_index_task_uuid` | TEXT | 任务唯一标识符（UUID），用于验证任务有效性 |
| `rag_index_thread_id` | INTEGER | 执行索引的线程 ID（仅供参考） |
| `rag_index_status` | TEXT | 状态：pending, indexing, completed, failed, timeout |
| `rag_index_started_at` | TEXT | 索引开始时间（ISO 8601 格式） |
| `rag_index_completed_at` | TEXT | 索引完成时间（ISO 8601 格式） |
| `rag_index_error` | TEXT | 错误信息（失败时） |

## 工作流程

### 文档创建时

```
1. 用户调用 POST /api/v1/documents
   ↓
2. DocumentService.create_note() 创建文档记录
   ↓
3. 触发 RAGSyncHook.on_document_created()
   ↓
4. 取消该文档的现有任务（如果有）
   ↓
5. 生成 task_uuid
   ↓
6. 更新数据库：status='indexing', task_uuid=xxx, started_at=now
   ↓
7. 提交任务到线程池
   ↓
8. 立即返回响应给用户（不等待索引完成）
   ↓
9. 后台线程执行索引
   ↓
10. 索引完成后更新：status='completed', completed_at=now
```

### 文档更新时

```
1. 用户调用 PUT /api/v1/documents/{id}
   ↓
2. DocumentService.update_document() 更新文档
   ↓
3. 触发 RAGSyncHook.on_document_updated()
   ↓
4. 取消该文档的现有索引任务
   ↓
5. 生成新的 task_uuid
   ↓
6. 更新数据库：status='indexing', task_uuid=new_uuid, started_at=now
   ↓
7. 提交重新索引任务到线程池
   ↓
8. 后台线程删除旧向量并生成新向量
```

### 超时检查

```
1. 用户调用 GET /api/v1/documents 或 GET /api/v1/documents/{id}
   ↓
2. DocumentService.list_documents/get_document()
   ↓
3. RAGSyncHook.check_timeout_tasks()
   ↓
4. 查询所有 status='indexing' 且 started_at 超过阈值的任务
   ↓
5. 更新为：status='timeout', completed_at=now, error='Task exceeded timeout limit'
   ↓
6. 返回文档数据（包含最新的超时状态）
```

## API 响应示例

### 索引中的文档

```json
{
  "id": "doc123",
  "name": "AI笔记",
  "content": "人工智能是计算机科学的分支...",
  "rag_index_status": "indexing",
  "rag_index_task_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "rag_index_thread_id": 140735268359424,
  "rag_index_started_at": "2025-11-15T06:30:00Z",
  "rag_index_completed_at": null,
  "rag_index_error": null,
  ...
}
```

### 索引完成的文档

```json
{
  "id": "doc123",
  "name": "AI笔记",
  "content": "人工智能是计算机科学的分支...",
  "rag_index_status": "completed",
  "rag_index_task_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "rag_index_thread_id": 140735268359424,
  "rag_index_started_at": "2025-11-15T06:30:00Z",
  "rag_index_completed_at": "2025-11-15T06:30:05Z",
  "rag_index_error": null,
  ...
}
```

### 索引失败的文档

```json
{
  "id": "doc456",
  "name": "错误文档",
  "content": "...",
  "rag_index_status": "failed",
  "rag_index_task_uuid": "660e8400-e29b-41d4-a716-446655440111",
  "rag_index_thread_id": 140735268359425,
  "rag_index_started_at": "2025-11-15T06:31:00Z",
  "rag_index_completed_at": null,
  "rag_index_error": "Failed to connect to Milvus: connection timeout",
  ...
}
```

### 索引超时的文档

```json
{
  "id": "doc789",
  "name": "大文档",
  "content": "...",
  "rag_index_status": "timeout",
  "rag_index_task_uuid": "770e8400-e29b-41d4-a716-446655440222",
  "rag_index_thread_id": 140735268359426,
  "rag_index_started_at": "2025-11-15T06:25:00Z",
  "rag_index_completed_at": "2025-11-15T06:32:00Z",
  "rag_index_error": "Task exceeded timeout limit",
  ...
}
```

## 配置参数

### 环境变量（可选）

可以通过环境变量配置线程池和超时参数：

```bash
# 最大并发索引任务数（默认 4）
export RAG_MAX_WORKERS=8

# 索引任务超时时间（秒，默认 300）
export RAG_TIMEOUT_SECONDS=600
```

### 代码配置

在 `aimemos/services/rag_sync_hook.py` 中：

```python
class RAGSyncHook:
    DEFAULT_MAX_WORKERS = 4        # 默认最大并发数
    DEFAULT_TIMEOUT_SECONDS = 300  # 默认超时时间（5分钟）
    
    def __init__(
        self,
        max_workers: int = DEFAULT_MAX_WORKERS,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    ):
        # ...
```

## 性能优化建议

### 1. 调整并发数

根据服务器资源调整 `max_workers`：

- CPU 密集型（嵌入模型）：`max_workers = CPU 核心数`
- IO 密集型（网络请求）：`max_workers = CPU 核心数 * 2-4`

### 2. 调整超时时间

根据文档大小和索引速度：

- 小文档（< 10KB）：180 秒（3 分钟）
- 中等文档（10KB - 100KB）：300 秒（5 分钟）
- 大文档（> 100KB）：600 秒（10 分钟）

### 3. 监控指标

定期检查以下指标：

```python
# 获取当前活跃任务数
active_count = rag_sync_hook.get_active_tasks_count()

# 检查超时任务数
timeout_count = rag_sync_hook.check_timeout_tasks()
```

## 故障排查

### 问题 1：任务一直卡在 "indexing" 状态

**原因**：
- 索引任务可能崩溃但未更新状态
- 超时检查未被触发

**解决**：
- 查询文档列表触发超时检查
- 手动调用 `check_timeout_tasks()`

### 问题 2：索引失败频繁

**原因**：
- Milvus 连接问题
- 嵌入模型加载失败
- 内存不足

**解决**：
- 检查 `rag_index_error` 字段查看具体错误
- 检查 Milvus 服务状态
- 检查嵌入模型是否正确安装

### 问题 3：更新文档后搜索结果未变化

**原因**：
- 索引任务可能仍在执行中或失败

**解决**：
- 检查文档的 `rag_index_status`
- 等待索引完成后再搜索
- 如果失败，查看 `rag_index_error` 并重试

## 安全性

### 1. 任务隔离

- 每个任务使用唯一的 `task_uuid`
- 任务执行过程中多次验证 UUID 有效性
- 防止过期任务更新数据

### 2. 资源限制

- 线程池限制最大并发数
- 超时机制防止任务长期占用资源
- 失败任务不会重试（避免无限循环）

### 3. 错误处理

- 索引失败不影响文档操作
- 错误信息记录到数据库供诊断
- 用户可查看详细的失败原因

## 最佳实践

### 1. 批量导入时

```python
# 方式 A：逐个创建（推荐）- 自动异步索引
for doc_data in doc_list:
    service.create_note(user_id, kb_id, doc_data)
    # 索引任务自动在后台执行，不阻塞

# 方式 B：先创建文档，再批量索引
# 1. 禁用自动索引
rag_sync_hook.disable()

# 2. 批量创建文档
for doc_data in doc_list:
    service.create_note(user_id, kb_id, doc_data)

# 3. 启用自动索引
rag_sync_hook.enable()

# 4. 手动调用批量索引 API
POST /api/v1/rag/index
{
  "kb_id": "kb123",
  "max_tokens": 512
}
```

### 2. 监控索引状态

```python
# 定期检查索引状态
GET /api/v1/documents?kb_id=kb123

# 响应中包含每个文档的索引状态
{
  "items": [
    {
      "id": "doc1",
      "rag_index_status": "completed",
      ...
    },
    {
      "id": "doc2",
      "rag_index_status": "indexing",
      ...
    }
  ]
}
```

### 3. 处理索引失败

```python
# 1. 查询失败的文档
GET /api/v1/documents?kb_id=kb123

# 2. 查看失败原因
{
  "id": "doc123",
  "rag_index_status": "failed",
  "rag_index_error": "Milvus connection timeout"
}

# 3. 解决问题后重新索引
POST /api/v1/rag/reindex/document/doc123
```

## 总结

异步索引功能通过以下机制确保高效和安全：

1. **任务 UUID** - 唯一标识任务，防止误操作
2. **线程池** - 控制并发，防止资源耗尽
3. **超时检测** - 自动清理卡住的任务
4. **状态追踪** - 完整记录索引过程
5. **错误隔离** - 索引失败不影响文档操作

用户无需关心底层细节，只需：
- 正常创建/更新文档
- 查看文档时自动获得索引状态
- 出现问题时查看错误信息并重试
