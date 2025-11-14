#!/usr/bin/env python
"""
RAG 模块验证脚本

此脚本用于验证 RAG 模块的各个组件是否正常工作。
运行此脚本可以快速检查安装是否成功。
"""

import sys
import os

# Add rag directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_imports():
    """测试是否能够导入所有模块"""
    print("=" * 60)
    print("测试 1: 检查依赖库是否安装")
    print("=" * 60)
    
    required_modules = [
        ('transformers', 'Hugging Face Transformers'),
        ('torch', 'PyTorch'),
        ('pymilvus', 'Milvus Python SDK'),
        ('sentencepiece', 'SentencePiece'),
        ('requests', 'Requests'),
        ('tqdm', 'tqdm'),
        ('dateutil', 'python-dateutil'),
        ('ujson', 'ujson')
    ]
    
    missing = []
    for module_name, display_name in required_modules:
        try:
            __import__(module_name)
            print(f"✓ {display_name:30s} - 已安装")
        except ImportError:
            print(f"✗ {display_name:30s} - 未安装")
            missing.append(module_name)
    
    if missing:
        print(f"\n缺少以下依赖: {', '.join(missing)}")
        print("请运行: pip install -r rag/requirements.txt")
        return False
    
    print("\n所有依赖已安装！\n")
    return True


def test_rag_modules():
    """测试 RAG 模块是否能够正常导入"""
    print("=" * 60)
    print("测试 2: 检查 RAG 模块")
    print("=" * 60)
    
    try:
        from rag import M3EEmbeddings, MilvusVectorStore, LLMClient
        print("✓ RAG 模块导入成功")
        print(f"  - M3EEmbeddings: {M3EEmbeddings}")
        print(f"  - MilvusVectorStore: {MilvusVectorStore}")
        print(f"  - LLMClient: {LLMClient}")
        return True
    except Exception as e:
        print(f"✗ RAG 模块导入失败: {e}")
        return False


def test_embeddings():
    """测试嵌入模型（简化版，不实际下载模型）"""
    print("\n" + "=" * 60)
    print("测试 3: 检查 Embeddings 模块结构")
    print("=" * 60)
    
    try:
        from rag.embeddings import M3EEmbeddings, create_embedder
        print("✓ Embeddings 模块结构正确")
        print("  提示: 首次运行会下载 moka-ai/m3e-base 模型（约 400MB）")
        return True
    except Exception as e:
        print(f"✗ Embeddings 模块检查失败: {e}")
        return False


def test_vector_store():
    """测试向量数据库模块"""
    print("\n" + "=" * 60)
    print("测试 4: 检查 Vector Store 模块结构")
    print("=" * 60)
    
    try:
        from rag.vector_store import MilvusVectorStore, create_vector_store
        print("✓ Vector Store 模块结构正确")
        print("  提示: 首次运行时会自动创建 Milvus Lite 数据库文件")
        return True
    except Exception as e:
        print(f"✗ Vector Store 模块检查失败: {e}")
        return False


def test_llm_client():
    """测试 LLM 客户端模块"""
    print("\n" + "=" * 60)
    print("测试 5: 检查 LLM Client 模块结构")
    print("=" * 60)
    
    try:
        from rag.llm_client import LLMClient, create_llm_client
        print("✓ LLM Client 模块结构正确")
        print("  提示: 需要启动本地 LLM 服务才能实际使用")
        print("  设置环境变量: export OPENAI_BASE_URL='http://localhost:8000/v1'")
        return True
    except Exception as e:
        print(f"✗ LLM Client 模块检查失败: {e}")
        return False


def test_ingest():
    """测试文档摄取模块"""
    print("\n" + "=" * 60)
    print("测试 6: 检查 Ingest 模块结构")
    print("=" * 60)
    
    try:
        from rag.ingest import (
            read_text_file,
            chunk_text_by_tokens,
            load_documents_from_directory,
            ingest_documents
        )
        print("✓ Ingest 模块结构正确")
        return True
    except Exception as e:
        print(f"✗ Ingest 模块检查失败: {e}")
        return False


def test_workflow():
    """测试工作流文件"""
    print("\n" + "=" * 60)
    print("测试 7: 检查 PocketFlow 工作流文件")
    print("=" * 60)
    
    workflow_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'pocketflow',
        'rag_workflow.yaml'
    )
    
    if not os.path.exists(workflow_path):
        print(f"✗ 工作流文件不存在: {workflow_path}")
        return False
    
    try:
        import yaml
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = yaml.safe_load(f)
        
        print(f"✓ 工作流文件存在且格式正确")
        print(f"  - 工作流名称: {workflow.get('name', 'N/A')}")
        print(f"  - 任务数量: {len(workflow.get('tasks', {}))}")
        return True
    except Exception as e:
        print(f"✗ 工作流文件解析失败: {e}")
        return False


def print_next_steps():
    """打印后续步骤"""
    print("\n" + "=" * 60)
    print("后续步骤")
    print("=" * 60)
    print("""
1. 准备测试数据:
   mkdir -p data/kb
   echo "测试文档内容" > data/kb/test.txt

2. 测试嵌入模型（首次运行会下载模型）:
   cd rag
   python embeddings.py

3. 索引文档:
   cd rag
   python ingest.py --data-dir ../data/kb --kb-id test_kb

4. （可选）启动本地 LLM 并测试:
   export OPENAI_BASE_URL='http://localhost:8000/v1'
   cd rag
   python llm_client.py

详细说明请参考:
- rag/README.md - 快速上手指南
- rag/DESIGN_RAG.md - 完整设计文档
""")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("RAG 模块验证脚本")
    print("=" * 60)
    print()
    
    results = []
    
    # 运行所有测试
    results.append(("依赖检查", test_imports()))
    results.append(("模块导入", test_rag_modules()))
    results.append(("Embeddings", test_embeddings()))
    results.append(("Vector Store", test_vector_store()))
    results.append(("LLM Client", test_llm_client()))
    results.append(("Ingest", test_ingest()))
    results.append(("Workflow", test_workflow()))
    
    # 打印总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name:20s} - {status}")
    
    print(f"\n通过: {passed}/{total}")
    
    if passed == total:
        print("\n✓ 所有测试通过！RAG 模块安装成功。")
        print_next_steps()
        return 0
    else:
        print("\n✗ 部分测试失败，请检查错误信息。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
