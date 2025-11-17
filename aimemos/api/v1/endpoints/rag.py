"""RAG 查询相关的 API 端点。"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Depends, status
from pydantic import BaseModel, Field

# Try to import RAG dependencies, but don't fail if not available
try:
    import sys
    import os
    # Add rag directory to path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'rag'))
    from rag.integration import create_rag_integration
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    create_rag_integration = None

from ....services.knowledge_base import get_knowledge_base_service
from ...dependencies import get_current_user

router = APIRouter()

# Global RAG integration instance
_rag_integration = None


def get_rag_integration():
    """获取 RAG 集成实例（单例模式）"""
    if not RAG_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="RAG功能未启用，请安装相关依赖"
        )
    global _rag_integration
    if _rag_integration is None:
        _rag_integration = create_rag_integration()
    return _rag_integration


class RAGIndexRequest(BaseModel):
    """RAG 索引请求模型"""
    
    kb_id: str = Field(..., description="知识库 ID")
    max_tokens: int = Field(512, ge=128, le=2048, description="每块最大 token 数")
    overlap_tokens: int = Field(128, ge=0, le=512, description="重叠 token 数")


class RAGIndexResponse(BaseModel):
    """RAG 索引响应模型"""
    
    kb_id: str = Field(..., description="知识库 ID")
    kb_name: str = Field(..., description="知识库名称")
    total_documents: int = Field(..., description="总文档数")
    indexed_documents: int = Field(..., description="已索引文档数")
    skipped_documents: int = Field(..., description="跳过文档数")
    total_chunks: int = Field(..., description="总块数")


class RAGSearchRequest(BaseModel):
    """RAG 搜索请求模型"""
    
    query: str = Field(..., min_length=1, max_length=1000, description="查询文本")
    kb_id: Optional[str] = Field(None, description="知识库 ID（可选，不提供则搜索所有知识库）")
    top_k: int = Field(5, ge=1, le=20, description="返回结果数量")


class RAGSearchResult(BaseModel):
    """RAG 搜索结果项"""
    
    content: str = Field(..., description="文本内容")
    source: str = Field(..., description="来源")
    score: float = Field(..., description="相关性分数")
    metadata: dict = Field(..., description="元数据")


class RAGSearchResponse(BaseModel):
    """RAG 搜索响应模型"""
    
    query: str = Field(..., description="查询文本")
    kb_id: Optional[str] = Field(None, description="知识库 ID")
    results: List[RAGSearchResult] = Field(..., description="搜索结果")
    total: int = Field(..., description="结果数量")


@router.post("/index", response_model=RAGIndexResponse, summary="批量索引知识库（后台异步）")
async def index_knowledge_base(
    request: RAGIndexRequest,
    current_user: str = Depends(get_current_user)
):
    """
    批量索引指定知识库的所有文档到向量数据库（异步执行）。
    
    将知识库中的所有文档提交到异步索引队列，每个文档都会创建对应的
    rag_index_task 记录来跟踪索引状态。
    
    此接口立即返回，索引在后台执行。可通过文档 API 查看每个文档的索引状态。
    
    需要认证。只能索引当前用户的知识库。
    """
    from ....services.rag_sync_hook import get_rag_sync_hook
    from ....services.document import get_document_service
    
    try:
        # 获取知识库下的所有文档
        doc_service = get_document_service()
        documents = doc_service.list_documents(current_user, kb_id=request.kb_id)
        
        if not documents:
            raise HTTPException(status_code=404, detail="知识库未找到或没有文档")
        
        # 获取知识库信息
        kb_service = get_knowledge_base_service()
        kb = kb_service.get_knowledge_base(current_user, request.kb_id)
        if not kb:
            raise HTTPException(status_code=404, detail="知识库未找到")
        
        # 提交每个文档到异步索引队列
        rag_hook = get_rag_sync_hook()
        indexed_count = 0
        skipped_count = 0
        
        for doc in documents:
            # 跳过文件夹
            if doc.doc_type == 'folder':
                skipped_count += 1
                continue
            
            # 触发异步索引
            rag_hook.on_document_created(current_user, doc)
            indexed_count += 1
        
        return RAGIndexResponse(
            kb_id=request.kb_id,
            kb_name=kb.name,
            total_documents=len(documents),
            indexed_documents=indexed_count,
            skipped_documents=skipped_count,
            total_chunks=0  # 异步执行，无法立即获得总块数
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提交索引任务失败: {str(e)}")


@router.post("/search", response_model=RAGSearchResponse, summary="RAG 语义搜索")
async def search_knowledge_base(
    request: RAGSearchRequest,
    current_user: str = Depends(get_current_user)
):
    """
    在知识库中进行语义搜索。
    
    使用向量相似度搜索找到与查询最相关的文档块。
    如果提供 kb_id，则只在该知识库中搜索；
    否则在用户所有知识库中搜索。
    
    需要认证。只能搜索当前用户的知识库。
    """
    rag = get_rag_integration()
    
    try:
        if request.kb_id:
            # 搜索指定知识库
            results = rag.search_in_knowledge_base(
                user_id=current_user,
                kb_id=request.kb_id,
                query=request.query,
                top_k=request.top_k
            )
        else:
            # 搜索所有知识库
            results = rag.search_all_knowledge_bases(
                user_id=current_user,
                query=request.query,
                top_k=request.top_k
            )
        
        # 转换结果格式
        search_results = [
            RAGSearchResult(
                content=r['content'],
                source=r['source'],
                score=r['score'],
                metadata=r['metadata']
            )
            for r in results
        ]
        
        return RAGSearchResponse(
            query=request.query,
            kb_id=request.kb_id,
            results=search_results,
            total=len(search_results)
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.delete("/index/{kb_id}", status_code=204, summary="删除知识库索引")
async def delete_knowledge_base_index(
    kb_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    删除指定知识库的向量索引。
    
    从向量数据库中删除该知识库的所有文档向量，并删除所有相关的 rag_index_task 记录。
    知识库本身和文档不会被删除，只是移除 RAG 索引。
    
    需要认证。只能删除当前用户的知识库索引。
    """
    from ....db.repositories.rag_index_task import RAGIndexTaskRepository
    
    rag = get_rag_integration()
    task_repo = RAGIndexTaskRepository()
    
    try:
        # 验证知识库权限
        kb_service = get_knowledge_base_service()
        kb = kb_service.get_knowledge_base(current_user, kb_id)
        if not kb:
            raise HTTPException(status_code=404, detail="知识库未找到")
        
        # 删除向量
        count = rag.delete_knowledge_base_vectors(
            user_id=current_user,
            kb_id=kb_id
        )
        
        # 删除该知识库下所有文档的索引任务记录
        task_repo.delete_by_knowledge_base_id(kb_id, current_user)
        
        return {"deleted": count}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.post("/reindex/document/{doc_id}", response_model=dict, summary="重新索引文档（后台异步）")
async def reindex_document(
    doc_id: str,
    max_tokens: int = Query(512, ge=128, le=2048, description="每块最大 token 数"),
    overlap_tokens: int = Query(128, ge=0, le=512, description="重叠 token 数"),
    current_user: str = Depends(get_current_user)
):
    """
    重新索引单个文档（异步执行）。
    
    删除文档的旧向量并重新生成新的向量索引。
    适用于文档内容更新后需要刷新 RAG 索引的情况。
    
    此接口立即返回，索引在后台执行。可通过文档 API 查看索引状态。
    
    需要认证。只能重新索引当前用户的文档。
    """
    from ....services.rag_sync_hook import get_rag_sync_hook
    from ....services.document import get_document_service
    
    try:
        # 获取文档
        doc_service = get_document_service()
        doc = doc_service.get_document(current_user, doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="文档未找到")
        
        # 触发异步重新索引
        rag_hook = get_rag_sync_hook()
        rag_hook.on_document_updated(current_user, doc)
        
        return {
            "doc_id": doc_id,
            "message": "重新索引任务已提交，正在后台执行",
            "status": "indexing"
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提交重新索引任务失败: {str(e)}")


@router.delete("/index/document/{doc_id}", status_code=204, summary="删除文档索引")
async def delete_document_index(
    doc_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    删除指定文档的向量索引。
    
    从向量数据库中删除该文档的所有向量，并删除相关的 rag_index_task 记录。
    文档本身不会被删除，只是移除 RAG 索引。
    
    需要认证。只能删除当前用户的文档索引。
    """
    from ....db.repositories.rag_index_task import RAGIndexTaskRepository
    
    rag = get_rag_integration()
    task_repo = RAGIndexTaskRepository()
    
    try:
        # 删除向量
        count = rag.delete_document_vectors(
            user_id=current_user,
            doc_id=doc_id
        )
        
        # 删除索引任务记录
        task_repo.delete_by_document_id(doc_id, current_user)
        
        return {"deleted": count}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")
