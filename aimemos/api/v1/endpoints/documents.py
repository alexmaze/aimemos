"""文档相关的 API 端点。"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends, File, UploadFile, Form

from ....schemas.document import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentListResponse,
)
from ....services.document import get_document_service
from ...dependencies import get_current_user

router = APIRouter()


@router.post("", response_model=DocumentResponse, status_code=201, summary="创建笔记文档")
async def create_note(
    kb_id: str = Query(..., description="知识库ID"),
    document: DocumentCreate = None,
    current_user: str = Depends(get_current_user)
):
    """创建新笔记文档。
    
    需要认证。创建的文档会自动关联到指定知识库。
    """
    doc_service = get_document_service()
    try:
        return doc_service.create_note(current_user, kb_id, document)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/upload", response_model=DocumentResponse, status_code=201, summary="上传文档")
async def upload_document(
    kb_id: str = Form(..., description="知识库ID"),
    file: UploadFile = File(..., description="上传的文件"),
    folder_id: Optional[str] = Form(None, description="文件夹ID"),
    summary: Optional[str] = Form(None, description="文档摘要"),
    current_user: str = Depends(get_current_user)
):
    """上传文档到知识库。
    
    需要认证。支持的文件格式：txt, md, doc, docx, pdf
    """
    doc_service = get_document_service()
    try:
        return doc_service.upload_document(
            current_user, 
            kb_id, 
            file, 
            folder_id=folder_id, 
            summary=summary
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=DocumentListResponse, summary="列出文档")
async def list_documents(
    kb_id: str = Query(..., description="知识库ID"),
    folder_id: Optional[str] = Query(None, description="文件夹ID"),
    skip: int = Query(0, ge=0, description="跳过的数量"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大数量"),
    current_user: str = Depends(get_current_user)
):
    """列出知识库中的文档，支持按文件夹过滤和分页。
    
    需要认证。只返回当前用户的文档。
    """
    doc_service = get_document_service()
    items, total = doc_service.list_documents(
        current_user, 
        kb_id, 
        folder_id=folder_id,
        skip=skip, 
        limit=limit
    )
    return DocumentListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/search", response_model=list[DocumentResponse], summary="搜索文档")
async def search_documents(
    kb_id: str = Query(..., description="知识库ID"),
    q: str = Query(..., min_length=1, description="搜索关键词"),
    current_user: str = Depends(get_current_user)
):
    """在知识库中搜索文档。
    
    需要认证。在文档名称、内容和摘要中搜索匹配的文档。
    """
    doc_service = get_document_service()
    return doc_service.search_documents(current_user, kb_id, q)


@router.get("/{doc_id}", response_model=DocumentResponse, summary="获取文档详情")
async def get_document(
    doc_id: str,
    current_user: str = Depends(get_current_user)
):
    """根据 ID 获取指定文档。
    
    需要认证。只能获取当前用户的文档。
    """
    doc_service = get_document_service()
    doc = doc_service.get_document(current_user, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档未找到")
    return doc


@router.put("/{doc_id}", response_model=DocumentResponse, summary="更新文档")
async def update_document(
    doc_id: str,
    doc_update: DocumentUpdate,
    current_user: str = Depends(get_current_user)
):
    """更新指定文档。
    
    需要认证。只能更新当前用户的文档。
    笔记可以更新内容，上传文档只能更新元数据。
    """
    doc_service = get_document_service()
    doc = doc_service.update_document(current_user, doc_id, doc_update)
    if not doc:
        raise HTTPException(status_code=404, detail="文档未找到")
    return doc


@router.delete("/{doc_id}", status_code=204, summary="删除文档")
async def delete_document(
    doc_id: str,
    current_user: str = Depends(get_current_user)
):
    """删除指定文档。
    
    需要认证。只能删除当前用户的文档。
    上传文档会同时删除源文件。
    """
    doc_service = get_document_service()
    if not doc_service.delete_document(current_user, doc_id):
        raise HTTPException(status_code=404, detail="文档未找到")
