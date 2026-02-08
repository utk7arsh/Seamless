"""Deterministic ad recommendation logic."""

from .schemas import UserProfile, VideoMetadata, AdAttributes


class AdRecommender:
    """Recommend a product archetype based on user + scene."""

    def recommend(self, user: UserProfile, scene: VideoMetadata) -> tuple[str, list[str], AdAttributes]:
        targeting = self._build_targeting_context(user, scene)
        product_key, rationale = self._select_product(user, scene, targeting)
        return product_key, rationale, targeting

    def _build_targeting_context(self, user: UserProfile, scene: VideoMetadata) -> AdAttributes:
        episode_terms = self._episode_terms(scene)
        prominent_products = self._prominent_products(scene)

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
        if "pizza" in prominent_products:
            target_category = "frozen"
        if "beverage" in prominent_products or "soda" in prominent_products or "cola" in prominent_products:
            target_category = "beverage"
        if any(tag in scene.scene_tags for tag in ["pizza", "dinner", "late_night"]) or (
            {"late_night", "sleepover", "game_night"} & episode_terms
        ):
            target_category = "frozen"
        if any(tag in scene.scene_tags for tag in ["beverage", "soda", "cola", "drink"]) or (
            {"beverage", "soda", "cola"} & episode_terms
        ):
            target_category = "beverage"

        return AdAttributes(
            target_category=target_category,
            price_sensitivity=price_sensitivity,
            health_tilt=health_tilt,
            delivery_preference=delivery_preference,
        )

    @staticmethod
    def _episode_terms(scene: VideoMetadata) -> set[str]:
        if scene.episode is None:
            return set()
        episode = scene.episode
        return {
            *(g.lower() for g in episode.genres),
            *(t.lower() for t in episode.tone_tags),
            *(s.lower() for s in episode.setting_tags),
            *(k.lower() for k in episode.keywords),
            (episode.show_title or "").lower(),
            (episode.episode_title or "").lower(),
        }

    @staticmethod
    def _prominent_products(scene: VideoMetadata) -> set[str]:
        if scene.episode is None:
            return set()
        signals = set()
        for product in scene.episode.prominent_products:
            signals.add(product.category.lower())
            signals.update(label.lower() for label in product.labels)
            signals.update(brand.lower() for brand in product.brands)
        return signals

    def _select_product(
        self,
        user: UserProfile,
        scene: VideoMetadata,
        targeting: AdAttributes,
    ) -> tuple[str, list[str]]:
        labels = {obj.label.lower() for obj in scene.detected_objects}
        tags = {tag.lower() for tag in scene.scene_tags}
        dialogue = {kw.lower() for kw in scene.dialogue_keywords}
        episode_terms = self._episode_terms(scene)
        prominent_products = self._prominent_products(scene)
        rationale: list[str] = []

        all_terms = labels | tags | dialogue | episode_terms

        # Scene-level cues still win, but episode metadata can break ties or fill gaps.
        pizza_signals = {"pizza", "slice", "cheesy"} & all_terms
        beverage_signals = {"soda", "cola", "coke", "beverage", "drink", "can"} & all_terms
        tech_signals = {"laptop", "computer", "device", "work", "surveillance", "lab", "investigation"} & all_terms

        hangout_signals = {
            "kids",
            "friends",
            "sleepover",
            "game_night",
            "dungeons & dragons",
            "dungeons_and_dragons",
            "arcade",
            "suburb",
            "small_town",
        } & all_terms

        coke_affinity = user.brand_affinities.get("Coca-Cola", 0.0)

        if "pizza" in prominent_products:
            rationale.append("Episode metadata shows prominent pizza presence")
            return "pizza", rationale

        if {"beverage", "soda", "cola"} & prominent_products:
            rationale.append("Episode metadata shows prominent beverage presence")
            if coke_affinity >= 0.6:
                rationale.append("User affinity tilts toward Coca-Cola")
            return "coke", rationale

        if pizza_signals:
            rationale.append("Scene contains food/hangout cues aligned with pizza")
            if "late_night" in user.watch_time_context or "late_night" in all_terms or "night" in all_terms:
                rationale.append("Night context favors warm comfort food")
            return "pizza", rationale

        if tech_signals:
            rationale.append("Episode/scene suggests tech/work context")
            return "laptop", rationale

        if hangout_signals:
            rationale.append("Episode/scene suggests a group hangout vibe (pizza-friendly)")
            return "pizza", rationale

        if beverage_signals:
            rationale.append("Scene contains beverage cues")
            if coke_affinity >= 0.6:
                rationale.append("High Coca-Cola brand affinity")
            return "coke", rationale

        if coke_affinity >= 0.6 and (targeting.target_category == "beverage" or {"beverage", "soda", "cola"} & all_terms):
            rationale.append("No strong visual cues; fell back to top brand affinity (Coca-Cola)")
            return "coke", rationale

        rationale.append("Defaulted to universal placement")
        if targeting.target_category == "beverage":
            rationale.append("Targeting favors beverage category")
            return "coke", rationale
        if targeting.target_category == "frozen":
            rationale.append("Targeting favors frozen category")
            return "pizza", rationale
        return "laptop", rationale
