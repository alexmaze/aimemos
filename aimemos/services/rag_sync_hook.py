"""
RAG 自动同步钩子

此模块提供文档事件的自动同步机制，
当文档创建、更新或删除时自动更新 RAG 索引。
"""

import logging
from typing import Optional
from datetime import datetime
from ..models.document import Document
from ..db import get_document_repository

logger = logging.getLogger(__name__)


class RAGSyncHook:
    """
    RAG 自动同步钩子
    
    监听文档事件并自动更新 RAG 索引
    """
    
    def __init__(self):
        """初始化同步钩子"""
        self._rag_integration = None
        self._enabled = True
    
    def _get_rag_integration(self):
        """延迟加载 RAG 集成实例（避免循环导入）"""
        if self._rag_integration is None:
            try:
                import sys
                import os
                # Add rag directory to path
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'rag'))
                from rag.integration import create_rag_integration
                self._rag_integration = create_rag_integration()
                logger.info("RAG integration initialized for auto-sync")
            except Exception as e:
                logger.warning(f"Failed to initialize RAG integration: {e}")
                self._enabled = False
        return self._rag_integration
    
    def on_document_created(self, user_id: str, document: Document) -> None:
        """
        文档创建后的钩子
        
        Args:
            user_id: 用户 ID
            document: 创建的文档
        """
        if not self._enabled:
            return
        
        # 跳过文件夹类型
        if document.doc_type == 'folder':
            return
        
        # 获取 repository 用于更新状态
        doc_repo = get_document_repository()
        
        try:
            # 更新状态为 indexing
            started_at = datetime.utcnow()
            doc_repo.update_rag_index_status(
                user_id=user_id,
                doc_id=document.id,
                status='indexing',
                started_at=started_at
            )
            
            rag = self._get_rag_integration()
            if rag:
                chunks_count = rag.index_document(user_id, document)
                
                # 更新状态为 completed
                completed_at = datetime.utcnow()
                doc_repo.update_rag_index_status(
                    user_id=user_id,
                    doc_id=document.id,
                    status='completed',
                    started_at=started_at,
                    completed_at=completed_at
                )
                
                if chunks_count > 0:
                    logger.info(
                        f"Auto-indexed document {document.id} "
                        f"({document.name}): {chunks_count} chunks"
                    )
        except Exception as e:
            # 更新状态为 failed
            doc_repo.update_rag_index_status(
                user_id=user_id,
                doc_id=document.id,
                status='failed',
                error=str(e)
            )
            logger.error(f"Failed to auto-index document {document.id}: {e}")
    
    def on_document_updated(self, user_id: str, document: Document) -> None:
        """
        文档更新后的钩子
        
        Args:
            user_id: 用户 ID
            document: 更新后的文档
        """
        if not self._enabled:
            return
        
        # 跳过文件夹类型
        if document.doc_type == 'folder':
            return
        
        # 获取 repository 用于更新状态
        doc_repo = get_document_repository()
        
        try:
            # 更新状态为 indexing
            started_at = datetime.utcnow()
            doc_repo.update_rag_index_status(
                user_id=user_id,
                doc_id=document.id,
                status='indexing',
                started_at=started_at
            )
            
            rag = self._get_rag_integration()
            if rag:
                chunks_count = rag.reindex_document(user_id, document.id)
                
                # 更新状态为 completed
                completed_at = datetime.utcnow()
                doc_repo.update_rag_index_status(
                    user_id=user_id,
                    doc_id=document.id,
                    status='completed',
                    started_at=started_at,
                    completed_at=completed_at
                )
                
                if chunks_count > 0:
                    logger.info(
                        f"Auto-reindexed document {document.id} "
                        f"({document.name}): {chunks_count} chunks"
                    )
        except Exception as e:
            # 更新状态为 failed
            doc_repo.update_rag_index_status(
                user_id=user_id,
                doc_id=document.id,
                status='failed',
                error=str(e)
            )
            logger.error(f"Failed to auto-reindex document {document.id}: {e}")
    
    def on_document_deleted(self, user_id: str, doc_id: str) -> None:
        """
        文档删除后的钩子
        
        Args:
            user_id: 用户 ID
            doc_id: 删除的文档 ID
        """
        if not self._enabled:
            return
        
        try:
            rag = self._get_rag_integration()
            if rag:
                count = rag.delete_document_vectors(user_id, doc_id)
                if count > 0:
                    logger.info(
                        f"Auto-deleted {count} vectors for document {doc_id}"
                    )
        except Exception as e:
            logger.error(f"Failed to auto-delete vectors for document {doc_id}: {e}")
    
    def disable(self):
        """禁用自动同步"""
        self._enabled = False
        logger.info("RAG auto-sync disabled")
    
    def enable(self):
        """启用自动同步"""
        self._enabled = True
        logger.info("RAG auto-sync enabled")


# 全局钩子实例
_rag_sync_hook = RAGSyncHook()


def get_rag_sync_hook() -> RAGSyncHook:
    """获取 RAG 同步钩子实例"""
    return _rag_sync_hook
