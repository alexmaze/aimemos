# 聊天会话管理模块

## 概述

本模块为 AI Memos 提供了大模型聊天会话管理功能，支持：

1. **会话历史管理**：创建、查询、更新和删除聊天会话
2. **消息历史记录**：完整记录用户与AI的对话历史
3. **知识库关联**：支持指定关联知识库以实现RAG（检索增强生成）
4. **流式响应**：使用Server-Sent Events (SSE)实现流式聊天体验
5. **过程展示**：RAG检索的每个步骤都可以返回给前端展示

## 功能特性

### 1. 会话管理

- **创建会话**：可选择是否关联知识库
- **列出会话**：获取用户的所有聊天会话列表
- **获取会话详情**：查看单个会话的信息
- **更新会话**：修改会话标题或关联的知识库
- **删除会话**：删除会话及其所有消息

### 2. 消息管理

- **获取消息历史**：查看会话中的所有消息
- **发送消息**：向AI发送消息并接收流式响应
- **RAG上下文**：消息可以包含RAG检索的上下文信息
- **来源追踪**：记录RAG检索的文档来源

### 3. RAG集成

当会话关联知识库时，发送消息会自动触发RAG流程：

1. **向量搜索**：在关联的知识库中搜索相关文档
2. **上下文构建**：将检索到的文档内容组织成上下文
3. **LLM生成**：基于上下文和对话历史生成回复
4. **流式返回**：将生成的内容以流式方式返回

每个步骤都会通过SSE返回进度信息，便于前端展示处理过程。

## API端点

### 会话管理端点

#### 创建会话

```http
POST /api/v1/chats
Content-Type: application/json
Authorization: Bearer {token}

{
  "title": "我的聊天会话",
  "knowledge_base_id": "kb_id_optional"
}
```

**响应**：
```json
{
  "id": "session_id",
  "user_id": "user_id",
  "title": "我的聊天会话",
  "knowledge_base_id": "kb_id_optional",
  "created_at": "2025-11-17T08:00:00",
  "updated_at": "2025-11-17T08:00:00"
}
```

#### 列出会话

```http
GET /api/v1/chats?skip=0&limit=100
Authorization: Bearer {token}
```

#### 获取会话详情

```http
GET /api/v1/chats/{session_id}
Authorization: Bearer {token}
```

#### 更新会话

```http
PUT /api/v1/chats/{session_id}
Content-Type: application/json
Authorization: Bearer {token}

{
  "title": "新标题"
}
```

#### 删除会话

```http
DELETE /api/v1/chats/{session_id}
Authorization: Bearer {token}
```

### 消息管理端点

#### 获取消息历史

```http
GET /api/v1/chats/{session_id}/messages?skip=0&limit=100
Authorization: Bearer {token}
```

**响应**：
```json
[
  {
    "id": "message_id",
    "session_id": "session_id",
    "role": "user",
    "content": "你好",
    "rag_context": null,
    "rag_sources": null,
    "created_at": "2025-11-17T08:00:00"
  },
  {
    "id": "message_id_2",
    "session_id": "session_id",
    "role": "assistant",
    "content": "你好！有什么我可以帮助你的吗？",
    "rag_context": "...",
    "rag_sources": [...],
    "created_at": "2025-11-17T08:00:01"
  }
]
```

#### 发送消息（流式响应）

```http
POST /api/v1/chats/{session_id}/messages
Content-Type: application/json
Authorization: Bearer {token}

{
  "content": "请介绍一下XX技术"
}
```

**响应**（Server-Sent Events格式）：
```
data: {"type": "rag_step", "step": "search_start", "data": {"kb_id": "kb_id"}}

data: {"type": "rag_step", "step": "search_complete", "data": {"count": 5}}

data: {"type": "rag_step", "step": "context_build", "data": {}}

data: {"type": "rag_step", "step": "context_complete", "data": {"sources": 5}}

data: {"type": "rag_step", "step": "generate_start", "data": {}}

data: {"type": "message", "content": "XX技术"}

data: {"type": "message", "content": "是一种"}

data: {"type": "message", "content": "..."}

data: {"type": "done"}
```

## 数据模型

### ChatSession（聊天会话）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 会话ID（UUID） |
| user_id | string | 所属用户ID |
| title | string | 会话标题 |
| knowledge_base_id | string \| null | 关联的知识库ID |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### ChatMessage（聊天消息）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 消息ID（UUID） |
| session_id | string | 所属会话ID |
| role | string | 角色：user 或 assistant |
| content | string | 消息内容 |
| rag_context | string \| null | RAG检索的上下文 |
| rag_sources | string \| null | RAG来源信息（JSON） |
| created_at | datetime | 创建时间 |

## 使用示例

### 基本聊天会话

```bash
# 1. 创建会话
SESSION=$(curl -X POST "http://localhost:8000/api/v1/chats" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"技术咨询"}' | jq -r '.id')

# 2. 发送消息
curl -X POST "http://localhost:8000/api/v1/chats/$SESSION/messages" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"你好，请介绍一下FastAPI"}' \
  --no-buffer

# 3. 查看消息历史
curl "http://localhost:8000/api/v1/chats/$SESSION/messages" \
  -H "Authorization: Bearer $TOKEN"
```

### 使用RAG的聊天会话

```bash
# 1. 创建知识库（假设已有）
KB_ID="your_knowledge_base_id"

# 2. 创建关联知识库的会话
SESSION=$(curl -X POST "http://localhost:8000/api/v1/chats" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"技术文档咨询\",\"knowledge_base_id\":\"$KB_ID\"}" | jq -r '.id')

# 3. 发送消息（会自动使用RAG）
curl -X POST "http://localhost:8000/api/v1/chats/$SESSION/messages" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"根据我的文档，请介绍XX项目的架构"}' \
  --no-buffer
```

### JavaScript/TypeScript示例（前端）

```typescript
// 创建会话
async function createChatSession(title: string, kbId?: string) {
  const response = await fetch('/api/v1/chats', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      title,
      knowledge_base_id: kbId
    })
  });
  return await response.json();
}

// 发送消息（流式）
async function sendMessage(sessionId: string, content: string) {
  const response = await fetch(`/api/v1/chats/${sessionId}/messages`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ content })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        
        switch (data.type) {
          case 'rag_step':
            console.log(`RAG步骤: ${data.step}`, data.data);
            // 显示RAG处理进度
            break;
          case 'message':
            console.log('消息片段:', data.content);
            // 追加到聊天界面
            break;
          case 'done':
            console.log('响应完成');
            break;
          case 'error':
            console.error('错误:', data.content);
            break;
        }
      }
    }
  }
}

// 获取消息历史
async function getMessages(sessionId: string) {
  const response = await fetch(`/api/v1/chats/${sessionId}/messages`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  return await response.json();
}
```

## RAG流程说明

当会话关联了知识库时，发送消息会触发以下RAG流程：

1. **search_start**：开始在知识库中搜索相关文档
2. **search_complete**：搜索完成，返回找到的文档数量
3. **context_build**：开始构建上下文
4. **context_complete**：上下文构建完成，返回使用的来源数量
5. **generate_start**：开始生成AI回复
6. **message**（多个）：流式返回生成的内容片段
7. **done**：响应完成

如果某个步骤失败，会返回 `search_error` 等错误事件。

## 部署说明

### 基础部署（不含RAG）

基础功能不需要额外依赖，可以直接使用：

```bash
uv sync
uv run aimemos
```

### 完整部署（含RAG）

要启用RAG功能，需要安装额外依赖并配置LLM服务：

1. 安装RAG依赖：
```bash
uv sync --extra rag
```

2. 配置环境变量：
```bash
export OPENAI_BASE_URL='http://localhost:8000/v1'  # LLM服务地址
export OPENAI_API_KEY='your-api-key'  # API密钥（如需要）
```

3. 启动服务：
```bash
uv run aimemos
```

## 技术实现

### 流式响应

使用FastAPI的 `StreamingResponse` 配合 Server-Sent Events (SSE) 协议实现流式响应：

- 媒体类型：`text/event-stream`
- 数据格式：每行以 `data: ` 开头，后跟JSON数据
- 连接保持：客户端保持连接直到收到 `done` 事件

### RAG集成

- **嵌入模型**：使用 m3e-base 模型生成文本嵌入
- **向量数据库**：使用 Milvus Lite 存储和检索向量
- **LLM调用**：支持任何OpenAI兼容的API接口

### 数据库设计

- **chat_sessions** 表：存储会话基本信息
- **chat_messages** 表：存储消息内容，通过外键关联会话
- **索引优化**：在 user_id、session_id、created_at 上建立索引

## 注意事项

1. **RAG依赖**：RAG功能需要安装额外的依赖包（transformers, torch等），这些包比较大
2. **LLM服务**：需要单独部署兼容OpenAI API的LLM服务
3. **流式超时**：建议客户端设置合理的超时时间
4. **并发控制**：大量并发请求时注意LLM服务的性能
5. **数据隔离**：每个用户只能访问自己的会话和消息

## 扩展建议

1. **多模型支持**：支持选择不同的LLM模型
2. **对话摘要**：自动生成会话摘要
3. **导出功能**：导出对话历史为Markdown或PDF
4. **协作功能**：支持会话分享和多人协作
5. **语音输入**：集成语音转文字功能
6. **图片理解**：支持多模态输入（图片+文字）
