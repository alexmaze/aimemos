"""
RAG 查询示例脚本

此脚本演示如何使用 RAG 模块进行端到端的查询：
1. 从向量数据库检索相关文档
2. 使用 LLM 生成基于上下文的回答

使用前提:
- 已运行 ingest.py 索引文档
- 已启动本地 LLM 服务
"""

import argparse
from typing import List, Dict, Any

from embeddings import create_embedder
from vector_store import create_vector_store
from llm_client import create_llm_client


# RAG Prompt 模板
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


def format_context(results: List[Dict[str, Any]]) -> str:
    """
    格式化检索结果为上下文文本
    
    Args:
        results: 检索结果列表
        
    Returns:
        格式化的上下文字符串
    """
    context_parts = []
    
    for i, result in enumerate(results):
        source = result.get('source', 'Unknown')
        content = result.get('content', '')
        score = result.get('score', 0.0)
        
        context_parts.append(
            f"[文档 {i+1}] (来源: {source}, 相关性: {score:.2f})\n{content}"
        )
    
    return "\n\n".join(context_parts)


def query_rag(
    query: str,
    embedder,
    vector_store,
    llm_client,
    top_k: int = 5,
    kb_id: str = None,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    执行 RAG 查询
    
    Args:
        query: 用户查询
        embedder: 嵌入模型实例
        vector_store: 向量数据库实例
        llm_client: LLM 客户端实例
        top_k: 检索的文档数量
        kb_id: 知识库 ID（用于过滤）
        verbose: 是否打印详细信息
        
    Returns:
        包含答案和元数据的字典
    """
    if verbose:
        print(f"\n{'='*60}")
        print(f"查询: {query}")
        print(f"{'='*60}\n")
    
    # Step 1: 生成查询的嵌入向量
    if verbose:
        print("Step 1: 生成查询嵌入向量...")
    
    query_embedding = embedder.embed_text(query)
    
    # Step 2: 从向量数据库检索相关文档
    if verbose:
        print(f"Step 2: 检索 top-{top_k} 相关文档...")
    
    filter_expr = None
    if kb_id:
        filter_expr = f'metadata["kb_id"] == "{kb_id}"'
    
    search_results = vector_store.search(
        query_embeddings=[query_embedding.tolist()],
        top_k=top_k,
        filter_expr=filter_expr
    )
    
    results = search_results[0]  # 取第一个查询的结果
    
    if verbose:
        print(f"找到 {len(results)} 个相关文档:\n")
        for i, result in enumerate(results):
            print(f"  {i+1}. {result['source']} (相关性: {result['score']:.4f})")
            print(f"     内容片段: {result['content'][:100]}...")
            print()
    
    # Step 3: 构建 Prompt
    if verbose:
        print("Step 3: 构建 Prompt...")
    
    context = format_context(results)
    prompt = RAG_PROMPT_TEMPLATE.format(
        context=context,
        question=query
    )
    
    if verbose:
        print(f"Prompt 长度: {len(prompt)} 字符\n")
    
    # Step 4: 调用 LLM 生成答案
    if verbose:
        print("Step 4: 生成答案...")
    
    response = llm_client.simple_generate(
        prompt=query,
        system_message=f"你是一个专业的知识库助手。请基于以下上下文回答问题。\n\n上下文:\n{context}"
    )
    
    if verbose:
        print(f"\n{'='*60}")
        print("答案:")
        print(f"{'='*60}\n")
        print(response)
        print()
    
    return {
        'query': query,
        'answer': response,
        'context': results,
        'num_results': len(results)
    }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='RAG 查询示例'
    )
    parser.add_argument(
        '--query',
        type=str,
        default='什么是人工智能？',
        help='查询问题 (default: "什么是人工智能？")'
    )
    parser.add_argument(
        '--kb-id',
        type=str,
        help='知识库 ID（用于过滤查询结果）'
    )
    parser.add_argument(
        '--top-k',
        type=int,
        default=3,
        help='检索的文档数量 (default: 3)'
    )
    parser.add_argument(
        '--milvus-uri',
        type=str,
        default='./milvus_demo.db',
        help='Milvus 数据库路径 (default: ./milvus_demo.db)'
    )
    parser.add_argument(
        '--collection-name',
        type=str,
        default='kb_documents',
        help='Collection 名称 (default: kb_documents)'
    )
    parser.add_argument(
        '--model-name',
        type=str,
        default='moka-ai/m3e-base',
        help='嵌入模型名称 (default: moka-ai/m3e-base)'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("RAG 查询示例")
    print("=" * 60)
    print()
    print(f"配置:")
    print(f"  查询: {args.query}")
    print(f"  Top-K: {args.top_k}")
    print(f"  KB ID: {args.kb_id or 'All'}")
    print(f"  Milvus URI: {args.milvus_uri}")
    print(f"  Collection: {args.collection_name}")
    print()
    
    # 初始化组件
    print("初始化组件...")
    
    try:
        # 1. 初始化嵌入模型
        print("  1. 加载嵌入模型...")
        embedder = create_embedder(model_name=args.model_name)
        
        # 2. 连接向量数据库
        print("  2. 连接向量数据库...")
        vector_store = create_vector_store(
            collection_name=args.collection_name,
            embedding_dim=embedder.get_embedding_dim(),
            uri=args.milvus_uri
        )
        
        # 3. 初始化 LLM 客户端
        print("  3. 初始化 LLM 客户端...")
        llm_client = create_llm_client()
        
        # 测试 LLM 连接
        if not llm_client.test_connection():
            print("\n错误: 无法连接到 LLM 服务")
            print("请确保:")
            print("  1. LLM 服务正在运行")
            print("  2. 设置了正确的 OPENAI_BASE_URL 环境变量")
            print("  3. API key 正确（如果需要）")
            return 1
        
        print("\n所有组件初始化成功！\n")
        
        # 执行查询
        result = query_rag(
            query=args.query,
            embedder=embedder,
            vector_store=vector_store,
            llm_client=llm_client,
            top_k=args.top_k,
            kb_id=args.kb_id,
            verbose=True
        )
        
        print("=" * 60)
        print("查询完成！")
        print("=" * 60)
        
        # 清理
        vector_store.disconnect()
        
        return 0
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
