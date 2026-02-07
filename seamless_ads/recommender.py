"""Deterministic ad recommendation logic."""

from .schemas import UserProfile, VideoMetadata, AdAttributes


class AdRecommender:
    """Recommend a product archetype based on user + scene."""

    def recommend(self, user: UserProfile, scene: VideoMetadata) -> tuple[str, list[str], AdAttributes]:
        targeting = self._build_targeting_context(user, scene)
        product_key, rationale = self._select_product(user, scene, targeting)
        return product_key, rationale, targeting

    def _build_targeting_context(self, user: UserProfile, scene: VideoMetadata) -> AdAttributes:
        price_sensitivity = "med"
        if user.engagement_signals.get("often_uses_deals"):
            price_sensitivity = "low"
        if user.engagement_signals.get("prefers_premium"):
            price_sensitivity = "high"

        health_tilt = "balanced"
        prefs = {p.lower() for p in user.dietary_preferences}
        if "low_sugar" in prefs or "low_fat" in prefs or "healthy" in prefs:
            health_tilt = "healthy"
        if "indulgent" in prefs or "comfort_food" in prefs:
            health_tilt = "indulgent"

        delivery_preference = "any"
        if user.engagement_signals.get("prefers_delivery"):
            delivery_preference = "delivery"
        if user.engagement_signals.get("prefers_pickup"):
            delivery_preference = "pickup"

        target_category = "snacks"
        if any(tag in scene.scene_tags for tag in ["pizza", "dinner", "late_night"]):
            target_category = "frozen"
        if any(tag in scene.scene_tags for tag in ["beverage", "soda", "cola", "drink"]):
            target_category = "beverage"

        return AdAttributes(
            target_category=target_category,
            price_sensitivity=price_sensitivity,
            health_tilt=health_tilt,
            delivery_preference=delivery_preference,
        )

    def _select_product(
        self,
        user: UserProfile,
        scene: VideoMetadata,
        targeting: AdAttributes,
    ) -> tuple[str, list[str]]:
        labels = {obj.label.lower() for obj in scene.detected_objects}
        tags = {tag.lower() for tag in scene.scene_tags}
        dialogue = {kw.lower() for kw in scene.dialogue_keywords}
        rationale: list[str] = []

        pizza_signals = {"pizza"} & (labels | tags | dialogue)
        beverage_signals = {"soda", "cola", "coke", "beverage", "drink", "can"} & (labels | tags | dialogue)
        tech_signals = {"laptop", "computer", "device", "work"} & (labels | tags | dialogue)

        coke_affinity = user.brand_affinities.get("Coca-Cola", 0.0)

        if pizza_signals:
            rationale.append("Scene contains pizza cues")
            if "late_night" in user.watch_time_context:
                rationale.append("Late-night context favors warm comfort food")
            return "pizza", rationale

        if beverage_signals or coke_affinity >= 0.6:
            if beverage_signals:
                rationale.append("Scene contains beverage cues")
            if coke_affinity >= 0.6:
                rationale.append("High Coca-Cola brand affinity")
            return "coke", rationale

        if tech_signals:
            rationale.append("Scene suggests tech/work context")
            return "laptop", rationale

        rationale.append("Defaulted to universal placement")
        if targeting.target_category == "beverage":
            rationale.append("Targeting favors beverage category")
            return "coke", rationale
        if targeting.target_category == "frozen":
            rationale.append("Targeting favors frozen category")
            return "pizza", rationale
        return "laptop", rationale
