"""文件夹相关的 API 端点。"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends

from ....schemas.folder import (
    FolderCreate,
    FolderUpdate,
    FolderResponse,
    FolderListResponse,
)
from ....services.folder import get_folder_service
from ...dependencies import get_current_user

router = APIRouter()


@router.post("", response_model=FolderResponse, status_code=201, summary="创建文件夹")
async def create_folder(
    kb_id: str = Query(..., description="知识库ID"),
    folder: FolderCreate = None,
    current_user: str = Depends(get_current_user)
):
    """创建新文件夹。
    
    需要认证。创建的文件夹会自动关联到指定知识库。
    """
    folder_service = get_folder_service()
    try:
        return folder_service.create_folder(current_user, kb_id, folder)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=FolderListResponse, summary="列出文件夹")
async def list_folders(
    kb_id: str = Query(..., description="知识库ID"),
    parent_folder_id: Optional[str] = Query(None, description="父文件夹ID"),
    current_user: str = Depends(get_current_user)
):
    """列出知识库中的文件夹。
    
    需要认证。只返回当前用户的文件夹。
    如果不指定parent_folder_id，则返回根目录下的文件夹。
    """
    folder_service = get_folder_service()
    items, total = folder_service.list_folders(
        current_user, 
        kb_id, 
        parent_folder_id=parent_folder_id
    )
    return FolderListResponse(items=items, total=total)


@router.get("/{folder_id}", response_model=FolderResponse, summary="获取文件夹详情")
async def get_folder(
    folder_id: str,
    current_user: str = Depends(get_current_user)
):
    """根据 ID 获取指定文件夹。
    
    需要认证。只能获取当前用户的文件夹。
    """
    folder_service = get_folder_service()
    folder = folder_service.get_folder(current_user, folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="文件夹未找到")
    return folder


@router.put("/{folder_id}", response_model=FolderResponse, summary="更新文件夹")
async def update_folder(
    folder_id: str,
    folder_update: FolderUpdate,
    current_user: str = Depends(get_current_user)
):
    """更新指定文件夹。
    
    需要认证。只能更新当前用户的文件夹。
    """
    folder_service = get_folder_service()
    try:
        folder = folder_service.update_folder(current_user, folder_id, folder_update)
        if not folder:
            raise HTTPException(status_code=404, detail="文件夹未找到")
        return folder
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{folder_id}", status_code=204, summary="删除文件夹")
async def delete_folder(
    folder_id: str,
    current_user: str = Depends(get_current_user)
):
    """删除指定文件夹。
    
    需要认证。只能删除当前用户的文件夹。
    级联删除子文件夹和文档。
    """
    folder_service = get_folder_service()
    if not folder_service.delete_folder(current_user, folder_id):
        raise HTTPException(status_code=404, detail="文件夹未找到")
