"""
文件上传相关API路由
"""
import os
import uuid
import shutil
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/upload", tags=["Upload"])

# 上传文件存储目录
UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# 支持的图片格式
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".webm"}

# 最大文件大小（10MB）
MAX_FILE_SIZE = 10 * 1024 * 1024


class UploadResponse(BaseModel):
    """上传响应"""
    filename: str
    original_name: str
    file_type: str
    url: str
    size: int


class MultiUploadResponse(BaseModel):
    """批量上传响应"""
    files: List[UploadResponse]
    count: int


def get_file_extension(filename: str) -> str:
    """获取文件扩展名"""
    return Path(filename).suffix.lower()


def generate_unique_filename(original_filename: str) -> str:
    """生成唯一文件名"""
    ext = get_file_extension(original_filename)
    unique_id = uuid.uuid4().hex[:12]
    return f"{unique_id}{ext}"


def get_file_type(extension: str) -> str:
    """判断文件类型"""
    if extension in ALLOWED_IMAGE_EXTENSIONS:
        return "image"
    elif extension in ALLOWED_VIDEO_EXTENSIONS:
        return "video"
    return "unknown"


async def save_upload_file(upload_file: UploadFile, category: str) -> UploadResponse:
    """
    保存上传的文件
    
    Args:
        upload_file: 上传的文件
        category: 文件分类（product/model/reference）
    
    Returns:
        UploadResponse
    """
    # 验证文件扩展名
    ext = get_file_extension(upload_file.filename)
    file_type = get_file_type(ext)
    
    if file_type == "unknown":
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的文件格式: {ext}，支持的格式: {ALLOWED_IMAGE_EXTENSIONS | ALLOWED_VIDEO_EXTENSIONS}"
        )
    
    # 读取文件内容以检查大小
    content = await upload_file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制 ({MAX_FILE_SIZE // 1024 // 1024}MB)"
        )
    
    # 创建分类目录
    category_dir = UPLOAD_DIR / category
    category_dir.mkdir(exist_ok=True)
    
    # 生成唯一文件名并保存
    unique_filename = generate_unique_filename(upload_file.filename)
    file_path = category_dir / unique_filename
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    return UploadResponse(
        filename=unique_filename,
        original_name=upload_file.filename,
        file_type=file_type,
        url=f"/api/v1/upload/files/{category}/{unique_filename}",
        size=len(content)
    )


@router.post("/product", response_model=MultiUploadResponse)
async def upload_product_images(files: List[UploadFile] = File(...)):
    """
    上传产品图片
    
    支持批量上传，最多5张图片
    """
    if len(files) > 5:
        raise HTTPException(status_code=400, detail="最多上传5张产品图片")
    
    results = []
    for file in files:
        result = await save_upload_file(file, "product")
        results.append(result)
    
    return MultiUploadResponse(files=results, count=len(results))


@router.post("/model", response_model=MultiUploadResponse)
async def upload_model_images(files: List[UploadFile] = File(...)):
    """
    上传模特图片
    
    支持批量上传，最多3张图片
    """
    if len(files) > 3:
        raise HTTPException(status_code=400, detail="最多上传3张模特图片")
    
    results = []
    for file in files:
        result = await save_upload_file(file, "model")
        results.append(result)
    
    return MultiUploadResponse(files=results, count=len(results))


@router.post("/reference", response_model=UploadResponse)
async def upload_reference_video(file: UploadFile = File(...)):
    """
    上传参考视频
    
    只支持单个视频文件
    """
    ext = get_file_extension(file.filename)
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的视频格式: {ext}，支持的格式: {ALLOWED_VIDEO_EXTENSIONS}"
        )
    
    return await save_upload_file(file, "reference")


@router.post("/single", response_model=UploadResponse)
async def upload_single_file(
    file: UploadFile = File(...),
    category: str = Form(default="general")
):
    """
    通用单文件上传
    
    Args:
        file: 上传的文件
        category: 文件分类
    """
    allowed_categories = {"product", "model", "reference", "general"}
    if category not in allowed_categories:
        category = "general"
    
    return await save_upload_file(file, category)


@router.get("/files/{category}/{filename}")
async def get_uploaded_file(category: str, filename: str):
    """
    获取上传的文件
    """
    file_path = UPLOAD_DIR / category / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 确定MIME类型
    ext = get_file_extension(filename)
    media_type_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".mp4": "video/mp4",
        ".mov": "video/quicktime",
        ".avi": "video/x-msvideo",
        ".webm": "video/webm",
    }
    media_type = media_type_map.get(ext, "application/octet-stream")
    
    return FileResponse(file_path, media_type=media_type)


@router.delete("/files/{category}/{filename}")
async def delete_uploaded_file(category: str, filename: str):
    """
    删除上传的文件
    """
    file_path = UPLOAD_DIR / category / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    try:
        os.remove(file_path)
        return {"message": "文件已删除", "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")
