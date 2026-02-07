"""End-to-end Seamless ad recommendation service."""

from typing import Optional

from .schemas import (
    UserProfile,
    VideoMetadata,
    OverlaySpec,
    SeamlessAdResponse,
)
from .recommender import AdRecommender
from .kroger_search import ToolClient, find_kroger_products


class SeamlessAdService:
    """Orchestrates metadata, recommendation, and Kroger discovery."""

    def __init__(self, tool_client: Optional[ToolClient] = None):
        self.tool_client = tool_client
        self.recommender = AdRecommender()

    def generate_ad_response(self, user: UserProfile, scene: VideoMetadata) -> SeamlessAdResponse:
        product_key, rationale, targeting = self.recommender.recommend(user, scene)
        overlay = self._select_overlay(scene, product_key)
        kroger_results = find_kroger_products(
            product_key=product_key,
            user_profile=user,
            targeting_context=targeting,
            tool_client=self.tool_client,
        )

        return SeamlessAdResponse(
            scene_id=scene.scene_id,
            timestamp_range=scene.timestamp_range,
            overlay=overlay,
            user_profile=user,
            targeting_context=targeting,
            kroger_results=kroger_results,
            rationale=rationale,
        )

    def _select_overlay(self, scene: VideoMetadata, product_key: str) -> OverlaySpec:
        label_map = {
            "pizza": {"pizza"},
            "coke": {"soda", "cola", "coke", "can", "beverage"},
            "laptop": {"laptop", "computer", "device"},
        }
        labels = label_map.get(product_key, set())
        chosen = None
        for obj in scene.detected_objects:
            if obj.label.lower() in labels:
                chosen = obj
                break
        if chosen is None and scene.detected_objects:
            chosen = max(scene.detected_objects, key=lambda o: o.confidence)

        if chosen is None:
            bbox = [0.1, 0.1, 0.2, 0.2]
            detected_label = "unknown"
        else:
            bbox = chosen.bbox
            detected_label = chosen.label

        return OverlaySpec(
            bbox=bbox,
            detected_label=detected_label,
            selected_product_key=product_key,
        )
