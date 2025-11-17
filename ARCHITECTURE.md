# 聊天会话管理模块 - 架构图

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                          前端客户端                               │
│  - 会话列表界面                                                   │
│  - 聊天对话界面                                                   │
│  - SSE流式响应处理                                                │
│  - RAG过程展示                                                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTPS/REST API
                           │ Server-Sent Events
┌──────────────────────────▼──────────────────────────────────────┐
│                      FastAPI 应用层                              │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │         API 端点 (/api/v1/chats)                           │ │
│  │  - create_session    - list_sessions                      │ │
│  │  - get_session       - update_session                     │ │
│  │  - delete_session    - get_messages                       │ │
│  │  - send_message (SSE流式)                                 │ │
│  └───────────────────────┬────────────────────────────────────┘ │
│                          │                                       │
│  ┌───────────────────────▼────────────────────────────────────┐ │
│  │              服务层 (ChatService)                          │ │
│  │  - 会话管理逻辑                                            │ │
│  │  - 消息处理                                                │ │
│  │  - RAG流程编排 ◄───────┐                                  │ │
│  │  - 流式响应生成         │                                  │ │
│  └───────────────────────┬────────────────┬──────────────────┘ │
│                          │                │                     │
└──────────────────────────┼────────────────┼─────────────────────┘
                           │                │
        ┌──────────────────▼──────┐    ┌───▼───────────────────┐
        │   数据仓储层             │    │   RAG 集成模块        │
        │                         │    │                       │
        │ ┌────────────────────┐ │    │ ┌──────────────────┐ │
        │ │ ChatSessionRepo    │ │    │ │  向量搜索        │ │
        │ │ - 会话CRUD         │ │    │ │  (Milvus)       │ │
        │ └────────────────────┘ │    │ └──────────────────┘ │
        │                         │    │ ┌──────────────────┐ │
        │ ┌────────────────────┐ │    │ │  嵌入模型        │ │
        │ │ ChatMessageRepo    │ │    │ │  (M3E)          │ │
        │ │ - 消息CRUD         │ │    │ └──────────────────┘ │
        │ └────────────────────┘ │    │ ┌──────────────────┐ │
        │                         │    │ │  LLM客户端       │ │
        │ SQLite 数据库          │    │ │  (OpenAI API)   │ │
        │ - chat_sessions       │    │ └──────────────────┘ │
        │ - chat_messages       │    └───────────────────────┘
        └─────────────────────────┘

## 数据流程

### 1. 创建会话

User → API → ChatService → ChatSessionRepo → Database
                                                  ↓
                                            创建会话记录
                                                  ↓
                                            返回会话信息

### 2. 发送消息（不使用RAG）

User → API → ChatService
                 ↓
         保存用户消息 → MessageRepo → Database
                 ↓
         调用LLM生成
                 ↓
         流式返回内容 ──────────────┐
                 ↓                  │
         保存助手消息                │
                 ↓                  │
         更新会话时间戳              │
                                    ▼
                              SSE Stream → User

### 3. 发送消息（使用RAG）

User → API → ChatService
                 ↓
         保存用户消息
                 ↓
         ┌───────▼────────┐
         │  RAG 流程开始   │
         └────────────────┘
                 ↓
         发送: search_start
                 ↓
         向量搜索知识库 ──→ Milvus
                 ↓
         发送: search_complete (文档数)
                 ↓
         发送: context_build
                 ↓
         组织检索内容为上下文
                 ↓
         发送: context_complete (来源数)
                 ↓
         发送: generate_start
                 ↓
         构建LLM提示词（含上下文+历史）
                 ↓
         调用LLM流式生成
                 ↓
         发送: message (逐块) ────────┐
                 ↓                    │
         保存完整响应+RAG信息          │
                 ↓                    │
         发送: done                   │
                                      ▼
                                SSE Stream → User

## 数据模型

```
ChatSession
├── id (UUID)
├── user_id
├── title
├── knowledge_base_id (可选)
├── created_at
└── updated_at

ChatMessage
├── id (UUID)
├── session_id (FK → ChatSession)
├── role (user/assistant)
├── content
├── rag_context (可选)
├── rag_sources (可选，JSON)
└── created_at
```

## SSE 事件流

### RAG启用时

```
data: {"type": "rag_step", "step": "search_start", "data": {...}}
data: {"type": "rag_step", "step": "search_complete", "data": {"count": 5}}
data: {"type": "rag_step", "step": "context_build", "data": {}}
data: {"type": "rag_step", "step": "context_complete", "data": {"sources": 5}}
data: {"type": "rag_step", "step": "generate_start", "data": {}}
data: {"type": "message", "content": "根据"}
data: {"type": "message", "content": "您的"}
data: {"type": "message", "content": "文档..."}
...
data: {"type": "done"}
```

### RAG未启用时

```
data: {"type": "error", "content": "RAG功能未启用，请安装相关依赖"}
```

## 安全机制

1. **认证**：所有端点需要JWT Bearer Token
2. **授权**：用户只能访问自己的会话和消息
3. **数据隔离**：数据库层面通过user_id过滤
4. **SQL注入防护**：使用参数化查询
5. **输入验证**：Pydantic模型验证所有输入

## 扩展点

1. **自定义RAG处理器**：可以替换或扩展RAG流程
2. **多模型支持**：可以添加模型选择参数
3. **消息插件**：可以添加消息预处理/后处理钩子
4. **会话分享**：可以添加会话分享功能
5. **导出功能**：可以添加对话导出为不同格式
