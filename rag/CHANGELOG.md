# RAG 模块更新日志

## [1.0.0] - 2025-11-14

### 新增功能

#### RAG 核心模块

在 `rag/` 目录下新增完整的 RAG（检索增强生成）模块：

1. **设计文档**
   - `DESIGN_RAG.md` - 9,869 字节的完整中文设计文档
     - 总体架构和数据流程
     - 组件清单和技术选型
     - Milvus schema 设计（6 个字段）
     - Chunking 策略（token-based, 512 tokens, 128 overlap）
     - 检索与 rerank 策略（两阶段检索）
     - Prompt 模板（基础 RAG、多轮对话、自我反思）
     - 监控与安全建议
     - 最小可行开发步骤（4 个阶段）
     - FAQ 和参考资源

2. **依赖管理**
   - `requirements.txt` - RAG 模块专用依赖
     - transformers (Hugging Face 模型)
     - torch (深度学习框架)
     - pymilvus (Milvus 客户端)
     - sentencepiece (分词器)
     - requests, tqdm, python-dateutil, ujson (工具库)

3. **嵌入模块** (`embeddings.py` - 8,644 字节)
   - `M3EEmbeddings` 类 - 封装 moka-ai/m3e-base 模型
   - 自动检测 CPU/GPU 设备
   - 支持单文本和批量嵌入
   - Mean pooling 和 L2 归一化
   - 自动获取向量维度（768）
   - 包含独立测试代码

4. **向量存储** (`vector_store.py` - 13,846 字节)
   - `MilvusVectorStore` 类 - Milvus Lite 操作封装
   - Collection 管理（创建、删除、统计）
   - Schema 定义（pk, embedding, content, source, metadata, created_at）
   - 索引管理（IVF_FLAT, L2 距离）
   - 数据操作（插入、搜索、删除）
   - 支持元数据过滤
   - 包含完整示例代码

5. **文档摄取** (`ingest.py` - 11,062 字节)
   - Token-based 文本分块（可配置 max_tokens 和 overlap）
   - 目录遍历和文件加载（支持 .txt, .md）
   - 批量嵌入生成
   - 批量向量插入
   - 命令行接口（argparse）
   - 进度显示（tqdm）
   - 完整的统计信息

6. **LLM 客户端** (`llm_client.py` - 10,592 字节)
   - `LLMClient` 类 - OpenAI 兼容 API 封装
   - 支持环境变量配置（OPENAI_BASE_URL, OPENAI_API_KEY）
   - chat_completion 方法
   - 流式输出支持
   - 连接测试功能
   - 简化的生成接口
   - 命令行测试工具

7. **Python 包** (`__init__.py` - 805 字节)
   - 包初始化和版本管理
   - 导出核心类和工厂函数
   - 文档字符串

8. **使用文档** (`README.md` - 2,992 字节)
   - 快速上手指南（中文）
   - 安装步骤
   - 7 步验证流程
   - LLM 服务配置（vLLM, FastChat, Ollama）
   - 常见问题解答

#### 验证和示例工具

9. **自动验证脚本** (`verify.py` - 5,782 字节)
   - 7 项自动检查
     1. 依赖库安装检查
     2. RAG 模块导入检查
     3. Embeddings 模块结构检查
     4. Vector Store 模块结构检查
     5. LLM Client 模块结构检查
     6. Ingest 模块结构检查
     7. PocketFlow 工作流文件检查
   - 测试总结和后续步骤指导
   - 可执行脚本（chmod +x）

10. **RAG 查询示例** (`query_example.py` - 6,057 字节)
    - 完整的端到端 RAG 查询演示
    - 4 步流程：嵌入生成 → 向量检索 → Prompt 构建 → LLM 生成
    - 命令行接口（支持自定义查询、top-k、KB 过滤）
    - 详细的进度输出和调试信息
    - RAG Prompt 模板示例
    - 可执行脚本（chmod +x）

#### PocketFlow 工作流

11. **工作流定义** (`pocketflow/rag_workflow.yaml` - 6,619 字节)
    - 全局配置（Milvus, Embedding, Chunking, LLM）
    - 6 个任务定义
      1. `ingest_documents` - 文档摄取
      2. `rebuild_index` - 重建索引
      3. `test_embeddings` - 测试嵌入
      4. `test_llm` - 测试 LLM
      5. `serve_query` - 查询服务（占位）
      6. `batch_query` - 批量查询（占位）
    - 调度配置（cron 表达式）
    - 3 个工作流管道
      - `full_setup` - 完整设置
      - `incremental_update` - 增量更新
      - `test_all` - 测试所有组件
    - 监控和日志配置
    - 资源限制和错误处理
    - 详细的使用说明

#### 测试数据目录

12. **测试数据结构** (`data/kb/`)
    - `.gitkeep` - 保持目录结构
    - `README.md` - 测试数据说明文档
    - 示例文档创建方法
    - 注意事项和最佳实践

#### 配置更新

13. **.gitignore 更新**
    - 排除 Milvus 数据库文件（milvus_demo.db*）
    - 排除 ML 模型缓存（.cache/, huggingface/, transformers_cache/）
    - 排除测试数据文件（data/kb/*）
    - 保留文档文件（!data/kb/README.md, !data/kb/.gitkeep）

### 技术特性

- ✅ Python 3.9+ 兼容
- ✅ 完整的中文文档和注释
- ✅ 所有模块包含独立测试代码
- ✅ 批量处理和进度显示
- ✅ 环境变量配置支持
- ✅ 错误处理和日志记录
- ✅ PocketFlow 工作流集成
- ✅ CodeQL 安全扫描通过（0 个警告）

### 文件统计

- 总文件数：14 个
- 代码行数：约 2,471 行（不含空行和注释）
- 文档大小：约 73 KB
- 支持的文档格式：txt, md
- 向量维度：768 (m3e-base)
- 默认分块大小：512 tokens，128 overlap

### 依赖项

#### 新增依赖（rag/requirements.txt）
```
transformers>=4.35.0
torch>=2.0.0
sentencepiece>=0.1.99
pymilvus>=2.3.0
requests>=2.31.0
tqdm>=4.66.0
python-dateutil>=2.8.2
ujson>=5.8.0
```

### 使用示例

#### 快速验证
```bash
cd rag
python verify.py
```

#### 文档索引
```bash
cd rag
python ingest.py --data-dir ../data/kb --kb-id test_kb
```

#### RAG 查询
```bash
export OPENAI_BASE_URL='http://localhost:8000/v1'
cd rag
python query_example.py --query "什么是人工智能？" --top-k 3
```

### 安全性

- 所有 Python 代码通过 CodeQL 安全扫描
- 输入验证和错误处理
- 路径遍历保护
- 环境变量隔离
- 无硬编码凭证

### 下一步建议

1. 集成到现有 FastAPI 端点
2. 添加文档索引 API
3. 实现查询历史和反馈
4. 添加 rerank 机制
5. 支持更多文档格式（PDF、Word）
6. 实现多模态检索
7. 添加知识图谱支持

### 贡献者

- AIMemos Team

### 参考文档

- `rag/README.md` - 快速上手指南
- `rag/DESIGN_RAG.md` - 完整设计文档
- `data/kb/README.md` - 测试数据说明
- `pocketflow/rag_workflow.yaml` - 工作流配置

---

**版本**: 1.0.0  
**发布日期**: 2025-11-14  
**分支**: copilot/add-rag-module-with-design-docs
