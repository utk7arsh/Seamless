"""Seamless ads package."""

from .schemas import (
    UserProfile,
    AdAttributes,
    VideoMetadata,
    SeamlessAdResponse,
    ProductResult,
)
from .service import SeamlessAdService

__all__ = [
    "UserProfile",
    "AdAttributes",
    "VideoMetadata",
    "SeamlessAdResponse",
    "ProductResult",
    "SeamlessAdService",
]
