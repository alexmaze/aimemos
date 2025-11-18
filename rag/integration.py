"""
RAG 与现有知识库系统的集成模块

此模块提供了 RAG 功能与 AIMemos 现有知识库系统的集成，
包括文档索引、查询和管理功能。
"""

from typing import List, Dict, Any, Optional
import sys
import os

# Add parent directory to path to import aimemos modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from aimemos.models.knowledge_base import KnowledgeBase
from aimemos.models.document import Document
from aimemos.services.knowledge_base import get_knowledge_base_service
from aimemos.services.document import get_document_service

# Import RAG modules
from rag.embeddings import create_embedder, M3EEmbeddings
from rag.vector_store import create_vector_store, MilvusVectorStore
from rag.ingest import chunk_text_by_tokens


class RAGIntegration:
    """
    RAG 与知识库系统集成类
    
    提供文档索引、查询和管理功能，连接 RAG 向量搜索与现有知识库系统。
    
    Attributes:
        embedder: 嵌入模型实例
        vector_store: 向量数据库实例
        kb_service: 知识库服务
        doc_service: 文档服务
    """
    
    def __init__(
        self,
        embedder: Optional[M3EEmbeddings] = None,
        vector_store: Optional[MilvusVectorStore] = None,
        milvus_uri: str = "./milvus_aimemos.db",
        collection_name: str = "kb_documents"
    ):
        """
        初始化 RAG 集成
        
        Args:
            embedder: 嵌入模型实例（如果为 None 则创建新实例）
            vector_store: 向量数据库实例（如果为 None 则创建新实例）
            milvus_uri: Milvus 数据库路径
            collection_name: Collection 名称
        """
        # 初始化嵌入模型
        if embedder is None:
            self.embedder = create_embedder()
        else:
            self.embedder = embedder
        
        # 初始化向量数据库
        if vector_store is None:
            self.vector_store = create_vector_store(
                collection_name=collection_name,
                embedding_dim=self.embedder.get_embedding_dim(),
                uri=milvus_uri
            )
        else:
            self.vector_store = vector_store
        
        # 初始化服务
        self.kb_service = get_knowledge_base_service()
        self.doc_service = get_document_service()
    
    def index_document(
        self,
        user_id: str,
        document: Document,
        max_tokens: int = 512,
        overlap_tokens: int = 128
    ) -> int:
        """
        索引单个文档到向量数据库
        
        Args:
            user_id: 用户 ID
            document: 文档对象
            max_tokens: 每块最大 token 数
            overlap_tokens: 重叠 token 数
            
        Returns:
            插入的块数量
        """
        # 跳过文件夹类型
        if document.doc_type == 'folder':
            return 0
        
        # 获取文档内容
        content = document.content
        if not content or not content.strip():
            return 0
        
        # 分块
        chunks = chunk_text_by_tokens(
            content,
            self.embedder.tokenizer,
            max_tokens=max_tokens,
            overlap_tokens=overlap_tokens
        )
        
        if not chunks:
            return 0
        
        # 生成嵌入
        embeddings = self.embedder.embed_texts(chunks, show_progress=False)
        
        # 准备元数据
        sources = [document.name] * len(chunks)
        metadatas = [{
            'kb_id': document.knowledge_base_id,
            'doc_id': document.id,
            'doc_type': document.doc_type,
            'doc_name': document.name,
            'user_id': user_id,
            'chunk_index': i
        } for i in range(len(chunks))]
        
        # 插入向量数据库
        self.vector_store.insert(
            embeddings=embeddings.tolist(),
            contents=chunks,
            sources=sources,
            metadatas=metadatas
        )
        
        return len(chunks)
    

    def search_in_knowledge_base(
        self,
        user_id: str,
        kb_id: str,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        在指定知识库中搜索
        
        Args:
            user_id: 用户 ID
            kb_id: 知识库 ID
            query: 查询文本
            top_k: 返回结果数量
            
        Returns:
            搜索结果列表
        """
        # 验证知识库权限
        kb = self.kb_service.get_knowledge_base(user_id, kb_id)
        if not kb:
            raise ValueError(f"知识库 {kb_id} 不存在或无权访问")
        
        # 生成查询嵌入
        query_embedding = self.embedder.embed_text(query)
        
        # 搜索（过滤用户和知识库）
        filter_expr = f'metadata["kb_id"] == "{kb_id}" && metadata["user_id"] == "{user_id}"'
        
        results = self.vector_store.search(
            query_embeddings=[query_embedding.tolist()],
            top_k=top_k,
            filter_expr=filter_expr
        )
        
        return results[0] if results else []
    
    def search_all_knowledge_bases(
        self,
        user_id: str,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        在用户所有知识库中搜索
        
        Args:
            user_id: 用户 ID
            query: 查询文本
            top_k: 返回结果数量
            
        Returns:
            搜索结果列表
        """
        # 生成查询嵌入
        query_embedding = self.embedder.embed_text(query)
        
        # 搜索（仅过滤用户）
        filter_expr = f'metadata["user_id"] == "{user_id}"'
        
        results = self.vector_store.search(
            query_embeddings=[query_embedding.tolist()],
            top_k=top_k,
            filter_expr=filter_expr
        )
        
        return results[0] if results else []
    
    def delete_document_vectors(
        self,
        user_id: str,
        doc_id: str
    ) -> int:
        """
        删除文档的向量数据
        
        Args:
            user_id: 用户 ID
            doc_id: 文档 ID
            
        Returns:
            删除的向量数量
        """
        filter_expr = f'metadata["doc_id"] == "{doc_id}" && metadata["user_id"] == "{user_id}"'
        return self.vector_store.delete(filter_expr)
    
    def delete_knowledge_base_vectors(
        self,
        user_id: str,
        kb_id: str
    ) -> int:
        """
        删除知识库的所有向量数据
        
        Args:
            user_id: 用户 ID
            kb_id: 知识库 ID
            
        Returns:
            删除的向量数量
        """
        filter_expr = f'metadata["kb_id"] == "{kb_id}" && metadata["user_id"] == "{user_id}"'
        return self.vector_store.delete(filter_expr)
    
    def reindex_document(
        self,
        user_id: str,
        doc_id: str,
        max_tokens: int = 512,
        overlap_tokens: int = 128
    ) -> int:
        """
        重新索引文档（先删除再索引）
        
        Args:
            user_id: 用户 ID
            doc_id: 文档 ID
            max_tokens: 每块最大 token 数
            overlap_tokens: 重叠 token 数
            
        Returns:
            插入的块数量
        """
        # 获取文档
        doc = self.doc_service.get_document(user_id, doc_id)
        if not doc:
            raise ValueError(f"文档 {doc_id} 不存在或无权访问")
        
        # 删除旧的向量
        self.delete_document_vectors(user_id, doc_id)
        
        # 重新索引
        return self.index_document(
            user_id,
            doc,
            max_tokens=max_tokens,
            overlap_tokens=overlap_tokens
        )
    
    def get_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取统计信息
        
        Args:
            user_id: 用户 ID（可选，如果提供则只统计该用户的数据）
            
        Returns:
            统计信息字典
        """
        stats = self.vector_store.get_stats()
        
        # TODO: 添加用户特定的统计
        # 目前 Milvus 没有直接的统计接口，可以通过查询实现
        
        return stats
    
    def close(self):
        """关闭连接"""
        if self.vector_store:
            self.vector_store.disconnect()


def create_rag_integration(
    milvus_uri: str = "./milvus_aimemos.db",
    collection_name: str = "kb_documents"
) -> RAGIntegration:
    """
    工厂函数创建 RAG 集成实例
    
    Args:
        milvus_uri: Milvus 数据库路径
        collection_name: Collection 名称
        
    Returns:
        RAGIntegration 实例
    """
    return RAGIntegration(
        milvus_uri=milvus_uri,
        collection_name=collection_name
    )


if __name__ == "__main__":
    """
    示例用法
    
    需要先启动 AIMemos 应用并创建用户、知识库和文档
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='RAG 知识库集成示例'
    )
    parser.add_argument(
        '--user-id',
        type=str,
        required=True,
        help='用户 ID'
    )
    parser.add_argument(
        '--kb-id',
        type=str,
        required=True,
        help='知识库 ID'
    )
    parser.add_argument(
        '--action',
        type=str,
        choices=['search', 'delete'],
        default='search',
        help='操作类型'
    )
    parser.add_argument(
        '--query',
        type=str,
        help='搜索查询（当 action=search 时需要）'
    )
    parser.add_argument(
        '--top-k',
        type=int,
        default=5,
        help='搜索返回结果数量'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("RAG 知识库集成示例")
    print("=" * 60)
    print()
    
    # 创建集成实例
    rag = create_rag_integration()
    
    try:
        if args.action == 'search':
            if not args.query:
                print("错误: search 操作需要 --query 参数")
                exit(1)
            
            print(f"在知识库 {args.kb_id} 中搜索: {args.query}")
            print()
            
            results = rag.search_in_knowledge_base(
                user_id=args.user_id,
                kb_id=args.kb_id,
                query=args.query,
                top_k=args.top_k
            )
            
            print(f"找到 {len(results)} 个结果:")
            print()
            
            for i, result in enumerate(results):
                print(f"{i+1}. {result['source']} (相关性: {result['score']:.4f})")
                print(f"   文档ID: {result['metadata'].get('doc_id', 'N/A')}")
                print(f"   内容: {result['content'][:100]}...")
                print()
            
        elif args.action == 'delete':
            print(f"删除知识库 {args.kb_id} 的向量数据")
            
            count = rag.delete_knowledge_base_vectors(
                user_id=args.user_id,
                kb_id=args.kb_id
            )
            
            print(f"删除了 {count} 个向量")
    
    finally:
        rag.close()
    
    print()
    print("=" * 60)
