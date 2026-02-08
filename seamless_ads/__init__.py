"""Seamless ads package."""

from .schemas import (
    UserProfile,
    AdAttributes,
    VideoMetadata,
    SeamlessAdResponse,
    ProductResult,
)
from .service import SeamlessAdService
from .user_profiles import USER_PERSONAS, get_user_profile

__all__ = [
    "UserProfile",
    "AdAttributes",
    "VideoMetadata",
    "SeamlessAdResponse",
    "ProductResult",
    "SeamlessAdService",
    "USER_PERSONAS",
    "get_user_profile",
]
