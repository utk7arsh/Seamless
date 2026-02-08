"""Tests for Seamless ad recommendation pipeline."""

import json
from pathlib import Path

from seamless_ads.metadata import GetMetadata
from seamless_ads.recommender import AdRecommender
from seamless_ads.kroger_search import MockKrogerToolClient, find_kroger_products
from seamless_ads.schemas import UserProfile
from seamless_ads.service import SeamlessAdService


def _load_sample(name: str) -> dict:
    path = Path(__file__).parents[1] / "seamless_ads" / "samples" / name
    return json.loads(path.read_text(encoding="utf-8"))


def test_metadata_normalization():
    data = _load_sample("scene_1.json")
    metadata = GetMetadata.from_json(data)
    assert metadata.scene_id == "st_s1e1_night_bikes_001"
    assert len(metadata.detected_objects) == 3
    assert metadata.episode is not None
    assert metadata.episode.show_title == "Stranger Things"
    assert metadata.episode.season == 1
    assert metadata.episode.episode == 1


def test_recommender_picks_pizza_from_episode_prominence():
    user = UserProfile(**_load_sample("user_1.json"))
    scene = GetMetadata.from_json(_load_sample("scene_2.json"))
    recommender = AdRecommender()
    product_key, rationale, targeting = recommender.recommend(user, scene)
    assert product_key == "pizza"
    assert "prominent" in " ".join(rationale).lower()
    assert targeting.target_category in {"frozen", "snacks", "beverage"}


def test_recommender_uses_episode_beverage_presence():
    user = UserProfile(**_load_sample("user_1.json"))
    scene = GetMetadata.from_json(_load_sample("scene_1.json"))
    recommender = AdRecommender()
    product_key, rationale, _ = recommender.recommend(user, scene)
    assert product_key == "coke"
    assert "beverage" in " ".join(rationale).lower()


def test_kroger_search_returns_images():
    user = UserProfile(**_load_sample("user_1.json"))
    scene = GetMetadata.from_json(_load_sample("scene_2.json"))
    recommender = AdRecommender()
    product_key, _, targeting = recommender.recommend(user, scene)
    results = find_kroger_products(
        product_key=product_key,
        user_profile=user,
        targeting_context=targeting,
        tool_client=MockKrogerToolClient(),
    )
    assert len(results) == 3 or len(results) > 0
    assert all(result.image_url for result in results)


def test_end_to_end_service():
    user = UserProfile(**_load_sample("user_1.json"))
    scene = GetMetadata.from_json(_load_sample("scene_2.json"))
    service = SeamlessAdService(tool_client=MockKrogerToolClient())
    response = service.generate_ad_response(user, scene)
    assert response.scene_id == scene.scene_id
    assert len(response.kroger_results) > 0
    assert response.overlay.selected_product_key in {"coke", "pizza", "laptop"}
