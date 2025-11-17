"""聊天会话相关的 API 端点。"""

from typing import List
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import StreamingResponse

from ....schemas.chat_session import (
    ChatSessionCreate,
    ChatSessionUpdate,
    ChatSessionResponse
)
from ....schemas.chat_message import (
    ChatMessageCreate,
    ChatMessageResponse
)
from ....services.chat import get_chat_service
from ...dependencies import get_current_user

router = APIRouter()


@router.post("", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED, summary="创建聊天会话")
async def create_session(
    data: ChatSessionCreate,
    current_user: str = Depends(get_current_user)
):
    """
    创建新的聊天会话。
    
    可选择关联知识库以启用RAG功能。
    
    需要认证。
    """
    chat_service = get_chat_service()
    
    # 如果指定了知识库，验证知识库存在且属于当前用户
    if data.knowledge_base_id:
        from ....services.knowledge_base import get_knowledge_base_service
        kb_service = get_knowledge_base_service()
        kb = kb_service.get_knowledge_base(current_user, data.knowledge_base_id)
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="知识库不存在"
            )
    
    session = chat_service.create_session(current_user, data)
    return ChatSessionResponse.model_validate(session)


@router.get("", response_model=List[ChatSessionResponse], summary="列出聊天会话")
async def list_sessions(
    skip: int = 0,
    limit: int = 100,
    current_user: str = Depends(get_current_user)
):
    """
    列出当前用户的所有聊天会话。
    
    按更新时间倒序排列。
    
    需要认证。
    """
    chat_service = get_chat_service()
    sessions = chat_service.list_sessions(current_user, skip, limit)
    return [ChatSessionResponse.model_validate(s) for s in sessions]


@router.get("/{session_id}", response_model=ChatSessionResponse, summary="获取聊天会话")
async def get_session(
    session_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    获取指定的聊天会话详情。
    
    需要认证。只能访问自己的会话。
    """
    chat_service = get_chat_service()
    session = chat_service.get_session(current_user, session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    return ChatSessionResponse.model_validate(session)


@router.put("/{session_id}", response_model=ChatSessionResponse, summary="更新聊天会话")
async def update_session(
    session_id: str,
    data: ChatSessionUpdate,
    current_user: str = Depends(get_current_user)
):
    """
    更新聊天会话信息。
    
    可以更新标题或关联的知识库。
    
    需要认证。只能更新自己的会话。
    """
    chat_service = get_chat_service()
    
    # 如果要更新知识库，验证知识库存在且属于当前用户
    if data.knowledge_base_id is not None:
        from ....services.knowledge_base import get_knowledge_base_service
        kb_service = get_knowledge_base_service()
        kb = kb_service.get_knowledge_base(current_user, data.knowledge_base_id)
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="知识库不存在"
            )
    
    session = chat_service.update_session(current_user, session_id, data)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    return ChatSessionResponse.model_validate(session)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除聊天会话")
async def delete_session(
    session_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    删除聊天会话及其所有消息。
    
    需要认证。只能删除自己的会话。
    """
    chat_service = get_chat_service()
    
    # 先验证会话存在
    session = chat_service.get_session(current_user, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    chat_service.delete_session(current_user, session_id)


@router.get("/{session_id}/messages", response_model=List[ChatMessageResponse], summary="获取会话消息")
async def get_messages(
    session_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: str = Depends(get_current_user)
):
    """
    获取会话的所有消息历史。
    
    按时间顺序排列。
    
    需要认证。只能访问自己的会话消息。
    """
    chat_service = get_chat_service()
    
    # 验证会话存在且属于当前用户
    session = chat_service.get_session(current_user, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    messages = chat_service.get_messages(session_id, skip, limit)
    
    # 转换响应格式
    result = []
    for msg in messages:
        msg_dict = msg.model_dump()
        # 解析 rag_sources JSON 字符串
        if msg_dict.get('rag_sources'):
            try:
                import json
                msg_dict['rag_sources'] = json.loads(msg_dict['rag_sources'])
            except:
                msg_dict['rag_sources'] = None
        result.append(ChatMessageResponse.model_validate(msg_dict))
    
    return result


@router.post("/{session_id}/messages", summary="发送消息（流式响应）")
async def send_message(
    session_id: str,
    data: ChatMessageCreate,
    current_user: str = Depends(get_current_user)
):
    """
    向会话发送消息并接收AI助手的流式响应。
    
    响应格式为Server-Sent Events (SSE)。
    
    如果会话关联了知识库，会使用RAG检索相关内容并：
    1. 返回RAG检索过程（search_start, search_complete, context_build等）
    2. 流式返回AI生成的内容
    3. 返回完成标记
    
    需要认证。只能向自己的会话发送消息。
    """
    chat_service = get_chat_service()
    
    # 验证会话存在且属于当前用户
    session = chat_service.get_session(current_user, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    return StreamingResponse(
        chat_service.send_message_stream(current_user, session_id, data),
        media_type="text/event-stream"
    )
