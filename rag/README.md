# RAG 模块使用指南

本目录包含 AIMemos 项目的 RAG (Retrieval-Augmented Generation，检索增强生成) 模块实现。

## 📁 文件结构

```
rag/
├── DESIGN_RAG.md       # 详细设计文档（中文）
├── requirements.txt    # Python 依赖
├── embeddings.py       # m3e-base 嵌入模型封装
├── vector_store.py     # Milvus Lite 向量数据库操作
├── ingest.py          # 文档摄取与索引构建
├── llm_client.py      # OpenAI 兼容的 LLM 客户端
└── README.md          # 本文件

pocketflow/
└── rag_workflow.yaml  # PocketFlow 工作流定义
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装 RAG 模块依赖
pip install -r rag/requirements.txt

# 或者使用 uv（如果项目已集成）
uv pip install -r rag/requirements.txt
```

### 2. 准备数据

创建测试数据目录并添加一些文档：

```bash
mkdir -p data/kb
echo "人工智能是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。" > data/kb/ai_intro.txt
echo "机器学习是人工智能的一个子领域，使计算机系统能够从数据中学习和改进。" > data/kb/ml_intro.txt
echo "深度学习是机器学习的一种方法，使用多层神经网络来学习数据的表示。" > data/kb/dl_intro.txt
```

### 3. 测试嵌入模型

首次运行会自动下载 moka-ai/m3e-base 模型（约 400MB）：

```bash
cd rag
python embeddings.py
```

预期输出：
```
Loading tokenizer and model: moka-ai/m3e-base
Using device: cuda  # 或 cpu
Model loaded successfully. Embedding dimension: 768
...
```

### 4. 启动 Milvus Lite

Milvus Lite 是内嵌式向量数据库，无需单独安装服务。首次运行时会自动创建数据库文件。

### 5. 索引文档

运行文档摄取脚本，将 `data/kb` 目录中的文档索引到向量数据库：

```bash
cd rag
python ingest.py --data-dir ../data/kb --kb-id test_kb
```

参数说明：
- `--data-dir`: 文档目录（默认：./data/kb）
- `--kb-id`: 知识库 ID（默认：default）
- `--milvus-uri`: Milvus 数据库路径（默认：./milvus_demo.db）
- `--max-tokens`: 每块最大 token 数（默认：512）
- `--overlap-tokens`: 块重叠 token 数（默认：128）
- `--batch-size`: 嵌入批次大小（默认：32）
- `--recreate-index`: 重建索引（删除现有数据）

预期输出：
```
=== RAG Document Ingestion Pipeline ===

Initializing embedder...
Loading tokenizer and model: moka-ai/m3e-base
...
Loading documents...
Loaded 3 documents

Step 1: Chunking documents...
Total chunks created: 5

Step 2: Generating embeddings...
Generating embeddings: 100%|████████████| 1/1 [00:00<00:00, ...]
Generated 5 embeddings

Step 3: Inserting into vector store...
  Inserted batch 1: 5 chunks

=== Ingestion completed ===
Total chunks inserted: 5
```

### 6. 启动本地 LLM（可选）

为了测试完整的 RAG 流程，需要一个提供 OpenAI 兼容 API 的本地 LLM。

#### 选项 A: 使用 vLLM

```bash
# 安装 vLLM
pip install vllm

# 启动服务（示例：使用 Qwen 模型）
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen-7B-Chat \
    --host 0.0.0.0 \
    --port 8000
```

#### 选项 B: 使用 FastChat

```bash
# 安装 FastChat
pip install fschat

# 启动 OpenAI 兼容服务
python -m fastchat.serve.openai_api_server \
    --host 0.0.0.0 \
    --port 8000
```

#### 选项 C: 使用 Ollama

```bash
# 安装 Ollama (https://ollama.ai)
# 拉取模型
ollama pull qwen:7b

# Ollama 默认在 http://localhost:11434 提供 API
# 需要设置 base_url 为 http://localhost:11434/v1
```

### 7. 测试 LLM 客户端

设置环境变量并测试连接：

```bash
export OPENAI_BASE_URL='http://localhost:8000/v1'
export OPENAI_API_KEY='EMPTY'  # 如果不需要 API key

cd rag
python llm_client.py --prompt "你好，请介绍一下你自己"
```

预期输出：
```
=== LLM Client Test ===

Base URL: http://localhost:8000/v1
Testing connection...

Connection successful!

System: 你是一个专业的AI助手
User: 你好，请介绍一下你自己