# RAG 异步索引功能文档

## 概述

RAG 模块支持异步索引，通过线程池管理索引任务，提供高效的并发控制和完善的任务管理机制。采用**简洁优雅**的 UUID 验证 + Milvus 删除-重建机制，确保数据一致性。

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

### 3. 防止数据污染 - 简洁优雅的方案

**核心机制**：UUID 验证 + Milvus 删除-重建

- **UUID 验证**：只有最新任务能更新文档状态
- **删除-重建**：每次索引前先删除旧向量，确保数据幂等
- **无需锁**：允许多个任务并发执行，最终结果仍然正确

**工作原理**：
```python
def _index_document_async(task_uuid, user_id, document):
    # 1. 验证是否是最新任务
    doc = doc_repo.get_by_id(user_id, document.id)
    if doc.rag_index_task_uuid != task_uuid:
        return  # 不是最新任务，退出
    
    # 2. 删除该文档的所有旧向量（幂等操作）
    rag.delete_document_vectors(user_id, document.id)
    
    # 3. 生成新向量并插入
    chunks = chunk_document(document)
    vectors = embed_chunks(chunks)
    rag.insert_vectors(vectors)
    
    # 4. 再次验证，只有最新任务才更新状态
    doc = doc_repo.get_by_id(user_id, document.id)
    if doc.rag_index_task_uuid != task_uuid:
        return  # 已被更新的任务替代
    
    # 5. 更新为完成状态
    update_status('completed')
```

**为什么简单却安全**：
- ✅ 即使两个线程并发执行，都会先删除再插入，最终只有一份向量数据
- ✅ UUID 验证确保只有最新任务更新状态
- ✅ 没有锁竞争，代码更简洁
- ✅ Milvus 的 delete 和 insert 本身是原子操作
- ✅ 资源浪费最小化（旧任务通过 UUID 验证快速退出）

**场景示例**：
```
场景 1：快速连续更新
T1: 创建文档 → 任务A提交（uuid=A）→ 线程1开始执行
T2: 更新文档 → 任务B提交（uuid=B）→ 线程2开始执行
T3: 线程1检查uuid → A≠B → 退出（不浪费资源）
T4: 线程2删除旧向量 → 生成新向量 → 插入 → 完成

结果：✅ 最终向量数据对应最新版本B，状态正确

场景 2：并发创建不同文档
T1: 创建doc1 → 线程1执行
T2: 创建doc2 → 线程2执行
T3: 创建doc3 → 线程3执行

结果：✅ 三个文档并发索引，充分利用线程池
```

### 4. 超时控制

- 默认超时时间：300 秒（5 分钟）
- 在文档列表/详情查询时自动检查超时任务
- 超时任务自动标记为 `timeout` 状态

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
4. 生成 task_uuid
   ↓
5. 更新数据库：status='indexing', task_uuid=xxx, started_at=now
   ↓
6. 提交任务到线程池
   ↓
7. 立即返回响应给用户（不等待索引完成）⚡
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

## 并发安全性保证

### 简洁优雅的防数据污染机制

系统使用 **UUID 验证 + Milvus 删除-重建**机制确保数据一致性，无需复杂的锁机制。

#### 核心原理

**UUID 验证**：
- 每次更新文档时生成新的 `task_uuid`
- 旧任务在执行过程中检查 UUID，发现不匹配则快速退出
- 只有最新任务能更新文档状态

**删除-重建**：
- 每次索引前先删除该文档的所有旧向量
- 即使多个任务并发执行删除+插入，最终也只有一份向量数据
- Milvus 的 delete 和 insert 本身是原子操作

#### 为什么安全

```python
场景：用户快速连续两次更新文档

T1: 更新1 → 生成uuid_A → 任务A提交 → 线程1开始
T2: 更新2 → 生成uuid_B → 任务B提交 → 线程2开始

线程1:
  1. 检查uuid → 文档uuid=uuid_B, 任务uuid=uuid_A → 不匹配 → 退出

线程2:
  1. 检查uuid → 文档uuid=uuid_B, 任务uuid=uuid_B → 匹配 ✅
  2. 删除旧向量（幂等，安全）
  3. 生成新向量并插入
  4. 再次检查uuid → 仍然匹配 ✅
  5. 更新状态为completed

最终结果：
- ✅ 向量数据对应最新版本（更新2）
- ✅ 文档状态正确（completed）
- ✅ 无资源浪费（旧任务快速退出）
```

#### 优势

- ✅ **简洁**：无需维护锁字典和锁逻辑
- ✅ **高效**：不同文档完全并发，无阻塞
- ✅ **安全**：UUID验证 + 原子操作保证数据正确性
- ✅ **优雅**：利用 Milvus 的特性，而非绕过它
- ✅ 同一文档的索引操作串行化（防止资源竞争）
- ✅ 即使 `future.cancel()` 失败，新任务也会等待旧任务完成

#### 2. UUID 验证（Task Validation）

**目的**：防止过期任务污染数据

**实现**：
```python
# 任务开始前验证
doc = doc_repo.get_by_id(user_id, document.id)
if doc.rag_index_task_uuid != task_uuid:
    return  # 任务已被取消，退出

# 执行索引...

# 任务完成前再次验证
doc = doc_repo.get_by_id(user_id, document.id)
if doc.rag_index_task_uuid != task_uuid:
    return  # 不更新状态，避免覆盖新任务的数据
```

**保证**：
- ✅ 过期任务不会更新数据库状态
- ✅ 防止旧任务覆盖新任务的结果
- ✅ 解决线程 ID 复用问题

### 完整的并发场景分析

#### 场景 1：快速连续更新文档

```
时间轴：
T1: 用户创建文档 doc1
    → 任务A提交（uuid=A）
    → 线程1启动，获得doc1的锁
    → 状态: indexing, uuid=A

T2: 用户更新文档 doc1（任务A仍在执行）
    → 尝试取消任务A（失败，已在运行）
    → 任务B提交（uuid=B）
    → 状态更新: indexing, uuid=B
    → 线程2启动，等待doc1的锁

T3: 线程1完成索引
    → 验证UUID：doc.uuid=B != task.uuid=A
    → ✅ 不更新状态（避免覆盖）
    → 释放锁

T4: 线程2获得锁
    → 验证UUID：doc.uuid=B == task.uuid=B ✓
    → 执行索引
    → 完成后更新: completed, uuid=B
```

**结果**：
- ✅ 没有重复的索引操作执行
- ✅ 最终状态反映的是最新任务（B）
- ✅ 用户数据正确

#### 场景 2：任务提交但未执行时被取消

```
T1: 创建文档 → 任务A提交到线程池队列
T2: 更新文档 → future.cancel() 成功 → 任务B提交
T3: 线程执行任务B（任务A已被取消）
```

**结果**：
- ✅ 任务A未执行，资源节省
- ✅ 只有任务B执行

#### 场景 3：并发创建多个不同文档

```
T1: 创建 doc1 → 任务A提交 → 线程1执行（获得doc1锁）
T2: 创建 doc2 → 任务B提交 → 线程2执行（获得doc2锁）
T3: 创建 doc3 → 任务C提交 → 线程3执行（获得doc3锁）
```

**结果**：
- ✅ 三个任务并发执行（不同文档的锁独立）
- ✅ 充分利用线程池资源

### 为什么能保证不会有两个线程同时处理同一文档？

**答案**：文档级锁 (`threading.Lock`) 的互斥特性保证了这一点。

Python 的 `threading.Lock` 是**可重入锁的基础版本**，具有以下特性：

1. **互斥性**：同一时刻只有一个线程能获得锁
2. **阻塞等待**：其他线程会在 `with lock:` 处阻塞，直到锁被释放
3. **FIFO 保证**：等待的线程按顺序获得锁（避免饥饿）

**代码验证**：
```python
# 线程1执行中
with doc_lock:  # 已获得锁
    # 执行索引...（耗时30秒）
    
# 线程2尝试执行（在线程1完成前）
with doc_lock:  # ← 在此阻塞等待，直到线程1释放锁
    # 只有在线程1完成后才会执行到这里
```

**总结**：
- ✅ **绝对保证**：同一文档同时只有一个线程执行索引
- ✅ **资源节省**：过期任务通过UUID验证快速退出
- ✅ **数据一致性**：最终状态反映最新任务的结果

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
