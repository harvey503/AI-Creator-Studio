from .generation import router as generation_router
from .upload import router as upload_router
from .image import router as image_router
from .video import router as video_router

__all__ = ["generation_router", "upload_router", "image_router", "video_router"]
