"""
RAG 自动同步钩子

此模块提供文档事件的自动同步机制，
当文档创建、更新或删除时自动更新 RAG 索引。

使用线程池异步执行索引任务，支持超时控制和任务管理。
"""

import logging
import threading
import uuid
from typing import Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, Future
from ..models.document import Document
from ..db import get_document_repository
from ..db.repositories.rag_index_task import RAGIndexTaskRepository

logger = logging.getLogger(__name__)


class RAGSyncHook:
    """
    RAG 自动同步钩子
    
    监听文档事件并自动更新 RAG 索引。
    使用线程池异步执行索引任务，支持并发控制和超时检测。
    """
    
    # 默认配置
    DEFAULT_MAX_WORKERS = 4  # 最大并发索引任务数
    DEFAULT_TIMEOUT_SECONDS = 300  # 默认超时时间：5分钟
    
    def __init__(self, max_workers: int = DEFAULT_MAX_WORKERS, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS):
        """初始化同步钩子
        
        Args:
            max_workers: 线程池最大工作线程数
            timeout_seconds: 索引任务超时时间（秒）
        """
        self._rag_integration = None
        self._enabled = True
        self._max_workers = max_workers
        self._timeout_seconds = timeout_seconds
        
        # 线程池
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="RAGIndexer-"
        )
        
        # RAG 索引任务仓储
        self._task_repo = RAGIndexTaskRepository()
        
        # 活跃任务追踪：{task_uuid: (Future, doc_id, user_id)}
        self._active_tasks = {}
        self._tasks_lock = threading.Lock()
    
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
    

    
    def _index_document_async(
        self,
        task_uuid: str,
        user_id: str,
        document: Document,
        is_reindex: bool = False
    ) -> None:
        """异步索引文档（在工作线程中执行）
        
        使用 UUID 验证 + Milvus 删除-重建机制确保数据一致性。
        即使多个任务并发执行，最终也只有最新任务的结果会被保留。
        
        Args:
            task_uuid: 任务唯一标识符
            user_id: 用户 ID
            document: 文档对象
            is_reindex: 是否是重新索引
        """
        doc_repo = get_document_repository()
        thread_id = threading.get_ident()
        
        try:
            # 1. 验证任务是否仍然有效（通过 task_uuid 比对）
            task = self._task_repo.get_by_document_id(document.id, user_id)
            if not task or task.task_uuid != task_uuid:
                logger.info(f"Task {task_uuid} for document {document.id} is stale, skipping")
                return
            
            rag = self._get_rag_integration()
            if not rag:
                raise Exception("RAG integration not available")
            
            # 2. 删除该文档的所有旧向量（幂等操作）
            # 即使多个任务并发执行，删除操作也是安全的
            rag.delete_document_vectors(user_id, document.id)
            
            # 3. 生成新向量并插入
            # 获取最新文档内容
            doc = doc_repo.get_by_id(user_id, document.id)
            task = self._task_repo.get_by_document_id(document.id, user_id)
            if not task or task.task_uuid != task_uuid:
                logger.info(f"Task {task_uuid} for document {document.id} was cancelled before indexing")
                return
            
            chunks_count = rag.index_document(user_id, doc)
            
            # 4. 再次验证任务仍然有效，只有最新任务才更新状态
            task = self._task_repo.get_by_document_id(document.id, user_id)
            if not task or task.task_uuid != task_uuid:
                logger.info(f"Task {task_uuid} for document {document.id} was superseded, not updating status")
                return
            
            # 5. 更新状态为 completed
            completed_at = datetime.now()
            self._task_repo.update(
                task_id=task.id,
                status='completed',
                completed_at=completed_at
            )
            
            if chunks_count > 0:
                action = "reindexed" if is_reindex else "indexed"
                logger.info(
                    f"Auto-{action} document {document.id} "
                    f"({document.name}): {chunks_count} chunks"
                )
        
        except Exception as e:
            # 验证任务仍然有效
            task = self._task_repo.get_by_document_id(document.id, user_id)
            if not task or task.task_uuid != task_uuid:
                logger.info(f"Task {task_uuid} for document {document.id} was cancelled, not updating error status")
                return
            
            # 更新状态为 failed
            self._task_repo.update(
                task_id=task.id,
                status='failed',
                error=str(e)
            )
            action = "reindex" if is_reindex else "index"
            logger.error(f"Failed to auto-{action} document {document.id}: {e}")
        
        finally:
            # 从活跃任务中移除
            with self._tasks_lock:
                if task_uuid in self._active_tasks:
                    del self._active_tasks[task_uuid]
    
    def _submit_indexing_task(
        self,
        user_id: str,
        document: Document,
        is_reindex: bool = False
    ) -> None:
        """提交异步索引任务
        
        Args:
            user_id: 用户 ID
            document: 文档对象
            is_reindex: 是否是重新索引
        """
        if not self._enabled:
            return
        
        # 跳过文件夹类型
        if document.doc_type == 'folder':
            return
        
        # 生成任务 UUID
        task_uuid = str(uuid.uuid4())
        
        # 创建或更新 RAG 索引任务记录
        # 新的 task_uuid 会自动使旧任务失效
        started_at = datetime.now()
        task = self._task_repo.upsert(
            document_id=document.id,
            user_id=user_id,
            knowledge_base_id=document.knowledge_base_id,
            task_uuid=task_uuid,
            status='indexing'
        )
        
        # 更新开始时间
        self._task_repo.update(
            task_id=task.id,
            started_at=started_at,
            thread_id=None  # 线程ID在任务开始后才知道
        )
        
        # 提交任务到线程池
        future = self._executor.submit(
            self._index_document_async,
            task_uuid,
            user_id,
            document,
            is_reindex
        )
        
        # 记录活跃任务
        with self._tasks_lock:
            self._active_tasks[task_uuid] = (future, document.id, user_id)
    
    def on_document_created(self, user_id: str, document: Document) -> None:
        """
        文档创建后的钩子（异步执行索引）
        
        Args:
            user_id: 用户 ID
            document: 创建的文档
        """
        self._submit_indexing_task(user_id, document, is_reindex=False)
    
    def on_document_updated(self, user_id: str, document: Document) -> None:
        """
        文档更新后的钩子（异步执行重新索引）
        
        Args:
            user_id: 用户 ID
            document: 更新后的文档
        """
        self._submit_indexing_task(user_id, document, is_reindex=True)
    
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
            # 删除 RAG 索引任务记录
            self._task_repo.delete_by_document_id(doc_id, user_id)
            
            # 删除向量
            rag = self._get_rag_integration()
            if rag:
                count = rag.delete_document_vectors(user_id, doc_id)
                if count > 0:
                    logger.info(
                        f"Auto-deleted {count} vectors for document {doc_id}"
                    )
        except Exception as e:
            logger.error(f"Failed to auto-delete vectors for document {doc_id}: {e}")
    
    def check_timeout_tasks(self) -> int:
        """检查并标记超时的索引任务
        
        Returns:
            标记为超时的任务数量
        """
        # TODO: Implement batch timeout checking
        # For now, timeout checking happens when querying individual documents
        return 0
    
    def get_active_tasks_count(self) -> int:
        """获取当前活跃任务数量
        
        Returns:
            活跃任务数量
        """
        with self._tasks_lock:
            return len(self._active_tasks)
    
    def disable(self):
        """禁用自动同步"""
        self._enabled = False
        logger.info("RAG auto-sync disabled")
    
    def enable(self):
        """启用自动同步"""
        self._enabled = True
        logger.info("RAG auto-sync enabled")
    
    def shutdown(self, wait: bool = True):
        """关闭线程池
        
        Args:
            wait: 是否等待所有任务完成
        """
        logger.info("Shutting down RAG sync hook...")
        self._executor.shutdown(wait=wait)
        logger.info("RAG sync hook shutdown complete")


# 全局钩子实例
_rag_sync_hook = RAGSyncHook()


def get_rag_sync_hook() -> RAGSyncHook:
    """获取 RAG 同步钩子实例"""
    return _rag_sync_hook
