"""Pydantic schemas for Seamless in-movie ad recommendations."""

from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator


class UserProfile(BaseModel):
    """Netflix-like user profile attributes useful for ad targeting."""

    age_range: str = Field(description="Age range bucket, e.g. 18-24")
    household_size: int = Field(ge=1, le=8, description="Number of people in household")
    location_zip: Optional[str] = Field(default=None, description="User ZIP code")
    location_metro: Optional[str] = Field(default=None, description="Metro area identifier")
    dietary_preferences: list[str] = Field(default_factory=list, description="Dietary preferences/exclusions")
    brand_affinities: dict[str, float] = Field(default_factory=dict, description="Brand affinity scores")
    cuisine_affinities: dict[str, float] = Field(default_factory=dict, description="Cuisine affinity scores")
    watch_time_context: str = Field(description="Context like late_night/weekend")
    engagement_signals: dict[str, bool] = Field(default_factory=dict, description="Engagement signals")


class AdAttributes(BaseModel):
    """Ad targeting attributes derived from user profile."""

    target_category: str = Field(description="Ad category (beverage, frozen, snacks)")
    price_sensitivity: Literal["low", "med", "high"] = Field(description="Price sensitivity bucket")
    health_tilt: Literal["indulgent", "balanced", "healthy"] = Field(description="Health preference")
    delivery_preference: Literal["pickup", "delivery", "any"] = Field(description="Fulfillment preference")


class DetectedObject(BaseModel):
    """Detected object from scene understanding."""

    label: str = Field(description="Object label")
    confidence: float = Field(ge=0.0, le=1.0, description="Detection confidence")
    bbox: list[float] = Field(description="Bounding box [x, y, w, h]")

    @field_validator("bbox")
    @classmethod
    def validate_bbox(cls, v):
        if len(v) != 4:
            raise ValueError("bbox must be [x, y, w, h]")
        return v


class VideoMetadata(BaseModel):
    """Normalized metadata from video understanding system."""

    class EpisodeMetadata(BaseModel):
        """Show/episode-level metadata (stable across scenes)."""

        class ProductSignal(BaseModel):
            """Prominent product presence in the episode."""

            category: str = Field(description="Product category, e.g. pizza, beverage, tech")
            labels: list[str] = Field(default_factory=list, description="Observed product labels")
            brands: list[str] = Field(default_factory=list, description="Observed brands (if any)")
            prominence: Literal["low", "med", "high"] = Field(description="Visibility/prominence level")

        show_title: str = Field(description="Show title, e.g. Stranger Things")
        season: int = Field(ge=1, description="Season number (1-indexed)")
        episode: int = Field(ge=1, description="Episode number (1-indexed)")
        episode_title: str = Field(description="Episode title")
        original_release_date: Optional[str] = Field(
            default=None, description="Original release/air date, ISO-8601 (YYYY-MM-DD)"
        )
        running_time_minutes: Optional[int] = Field(default=None, ge=1, le=180, description="Runtime in minutes")
        maturity_rating: Optional[str] = Field(default=None, description="Rating, e.g. TV-14 / TV-MA")

        genres: list[str] = Field(default_factory=list, description="High-level genres")
        tone_tags: list[str] = Field(default_factory=list, description="Tone/mood tags")
        setting_tags: list[str] = Field(default_factory=list, description="Setting tags")
        keywords: list[str] = Field(default_factory=list, description="Non-spoilery episode keywords")
        prominent_products: list[ProductSignal] = Field(
            default_factory=list, description="Prominent food/drink/tech presence"
        )

    scene_id: str
    timestamp_range: list[float] = Field(description="Timestamp range [start_sec, end_sec]")
    detected_objects: list[DetectedObject] = Field(default_factory=list)
    scene_tags: list[str] = Field(default_factory=list)
    dialogue_keywords: list[str] = Field(default_factory=list)
    episode: Optional[EpisodeMetadata] = Field(default=None, description="Episode-level metadata")

    @field_validator("timestamp_range")
    @classmethod
    def validate_timestamp_range(cls, v):
        if len(v) != 2:
            raise ValueError("timestamp_range must be [start_sec, end_sec]")
        return v


class OverlaySpec(BaseModel):
    """Overlay placement for ad rendering."""

    bbox: list[float] = Field(description="Bounding box [x, y, w, h]")
    detected_label: str = Field(description="Label of detected object")
    selected_product_key: str = Field(description="Selected product key")


class ProductResult(BaseModel):
    """Product discovery result."""

    product_id: str
    name: str
    price: float
    size: str
    unit: str
    in_stock: bool
    image_url: str
    kroger_search_query: str


class SeamlessAdResponse(BaseModel):
    """Full response for Seamless ad layer."""

    scene_id: str
    timestamp_range: list[float]
    overlay: OverlaySpec
    user_profile: UserProfile
    targeting_context: AdAttributes
    kroger_results: list[ProductResult]
    rationale: list[str]
