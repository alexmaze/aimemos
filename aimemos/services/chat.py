"""聊天会话服务。"""

from typing import List, Optional, AsyncIterator, Dict, Any
import json

from ..db.repositories.chat_session import ChatSessionRepository
from ..db.repositories.chat_message import ChatMessageRepository
from ..models.chat_session import ChatSession
from ..models.chat_message import ChatMessage
from ..schemas.chat_session import ChatSessionCreate, ChatSessionUpdate
from ..schemas.chat_message import ChatMessageCreate, ChatStreamChunk

# Try to import RAG dependencies, but don't fail if not available
try:
    import sys
    import os
    # Add rag directory to path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'rag'))
    from rag.llm_client import LLMClient
    from rag.integration import create_rag_integration
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    LLMClient = None
    create_rag_integration = None


class ChatService:
    """聊天会话服务。
    
    处理聊天会话的业务逻辑，包括会话管理、消息发送和RAG集成。
    """
    
    def __init__(self):
        """初始化聊天服务。"""
        self.session_repo = ChatSessionRepository()
        self.message_repo = ChatMessageRepository()
        self.llm_client = LLMClient() if RAG_AVAILABLE else None
        self._rag_integration = None
    
    @property
    def rag_integration(self):
        """获取RAG集成实例（懒加载）。"""
        if not RAG_AVAILABLE:
            return None
        if self._rag_integration is None:
            self._rag_integration = create_rag_integration()
        return self._rag_integration
    
    def create_session(
        self,
        user_id: str,
        data: ChatSessionCreate
    ) -> ChatSession:
        """创建新的聊天会话。"""
        return self.session_repo.create(
            user_id=user_id,
            title=data.title,
            knowledge_base_id=data.knowledge_base_id
        )
    
    def get_session(self, user_id: str, session_id: str) -> Optional[ChatSession]:
        """获取指定的聊天会话。"""
        return self.session_repo.get_by_id(session_id, user_id)
    
    def list_sessions(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[ChatSession]:
        """列出用户的所有聊天会话。"""
        return self.session_repo.list_by_user(user_id, skip, limit)
    
    def update_session(
        self,
        user_id: str,
        session_id: str,
        data: ChatSessionUpdate
    ) -> Optional[ChatSession]:
        """更新聊天会话。"""
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return self.get_session(user_id, session_id)
        
        return self.session_repo.update(
            session_id=session_id,
            user_id=user_id,
            title=update_data.get('title'),
            knowledge_base_id=update_data.get('knowledge_base_id')
        )
    
    def delete_session(self, user_id: str, session_id: str) -> bool:
        """删除聊天会话及其所有消息。"""
        # 先删除所有消息
        self.message_repo.delete_by_session(session_id)
        # 再删除会话
        return self.session_repo.delete(session_id, user_id)
    
    def get_messages(
        self,
        session_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[ChatMessage]:
        """获取会话的所有消息。"""
        return self.message_repo.list_by_session(session_id, skip, limit)
    
    async def send_message_stream(
        self,
        user_id: str,
        session_id: str,
        data: ChatMessageCreate
    ) -> AsyncIterator[str]:
        """
        发送消息并以流式方式返回AI响应。
        
        如果会话关联了知识库，会使用RAG检索相关内容。
        返回Server-Sent Events格式的流。
        """
        # Check if RAG is available
        if not RAG_AVAILABLE:
            yield f"data: {json.dumps({'type': 'error', 'content': 'RAG功能未启用，请安装相关依赖'}, ensure_ascii=False)}\n\n"
            return
        
        # 验证会话存在
        session = self.get_session(user_id, session_id)
        if not session:
            yield f"data: {json.dumps({'type': 'error', 'content': '会话不存在'}, ensure_ascii=False)}\n\n"
            return
        
        # 保存用户消息
        user_message = self.message_repo.create(
            session_id=session_id,
            role='user',
            content=data.content
        )
        
        # 获取历史消息构建上下文
        history = self.message_repo.list_by_session(session_id, skip=0, limit=20)
        messages = []
        
        # 如果有关联知识库，执行RAG检索
        rag_context = None
        rag_sources = []
        if session.knowledge_base_id:
            try:
                # 步骤1: 开始RAG检索
                yield f"data: {json.dumps({'type': 'rag_step', 'step': 'search_start', 'data': {{'kb_id': session.knowledge_base_id}}}, ensure_ascii=False)}\n\n"
                
                # 执行向量搜索
                search_results = self.rag_integration.search_in_knowledge_base(
                    user_id=user_id,
                    kb_id=session.knowledge_base_id,
                    query=data.content,
                    top_k=5
                )
                
                # 步骤2: 检索完成
                yield f"data: {json.dumps({'type': 'rag_step', 'step': 'search_complete', 'data': {{'count': len(search_results)}}}, ensure_ascii=False)}\n\n"
                
                if search_results:
                    # 步骤3: 组织上下文
                    yield f"data: {json.dumps({'type': 'rag_step', 'step': 'context_build', 'data': {}}, ensure_ascii=False)}\n\n"
                    
                    # 构建RAG上下文
                    context_parts = []
                    for i, result in enumerate(search_results, 1):
                        context_parts.append(f"[文档{i}] {result['content']}")
                        rag_sources.append({
                            'source': result['source'],
                            'score': result['score'],
                            'metadata': result['metadata']
                        })
                    
                    rag_context = "\n\n".join(context_parts)
                    
                    # 添加系统提示，包含RAG上下文
                    messages.append({
                        'role': 'system',
                        'content': f"""你是一个专业的AI助手。请基于以下知识库内容回答用户的问题。

知识库内容：
{rag_context}

请根据上述内容准确回答问题，如果内容中没有相关信息，请如实告知。"""
                    })
                    
                    # 步骤4: 上下文构建完成
                    yield f"data: {json.dumps({'type': 'rag_step', 'step': 'context_complete', 'data': {{'sources': len(rag_sources)}}}, ensure_ascii=False)}\n\n"
            
            except Exception as e:
                # RAG失败时继续，但不使用上下文
                yield f"data: {json.dumps({'type': 'rag_step', 'step': 'search_error', 'data': {{'error': str(e)}}}, ensure_ascii=False)}\n\n"
        
        # 如果没有RAG上下文，添加默认系统提示
        if not rag_context:
            messages.append({
                'role': 'system',
                'content': '你是一个专业的AI助手，请友好地回答用户的问题。'
            })
        
        # 添加历史消息（最近10条）
        for msg in history[-10:]:
            messages.append({
                'role': msg.role,
                'content': msg.content
            })
        
        # 步骤5: 开始生成回复
        yield f"data: {json.dumps({'type': 'rag_step', 'step': 'generate_start', 'data': {}}, ensure_ascii=False)}\n\n"
        
        # 调用LLM流式生成
        assistant_content = ""
        try:
            for chunk in self.llm_client.chat_completion(
                messages=messages,
                stream=True,
                temperature=0.7,
                max_tokens=2000
            ):
                if 'choices' in chunk and len(chunk['choices']) > 0:
                    delta = chunk['choices'][0].get('delta', {})
                    if 'content' in delta:
                        content_chunk = delta['content']
                        assistant_content += content_chunk
                        # 发送消息块
                        yield f"data: {json.dumps({'type': 'message', 'content': content_chunk}, ensure_ascii=False)}\n\n"
        
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': f'生成回复失败: {str(e)}'}, ensure_ascii=False)}\n\n"
            return
        
        # 保存助手消息
        self.message_repo.create(
            session_id=session_id,
            role='assistant',
            content=assistant_content,
            rag_context=rag_context,
            rag_sources=json.dumps(rag_sources, ensure_ascii=False) if rag_sources else None
        )
        
        # 更新会话时间戳
        self.session_repo.touch(session_id, user_id)
        
        # 步骤6: 完成
        yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"


# 单例服务实例
_chat_service = None


def get_chat_service() -> ChatService:
    """获取聊天服务单例实例。"""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service
