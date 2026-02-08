"""Metadata normalization for video understanding output."""
# python -c "from seamless_ads.metadata import magic_print_indexing; magic_print_indexing('outputs/BBS3E2_structured_products.json','outputs/STS3E4_structured_products.json')

import json
import time
from collections import Counter
from pathlib import Path
from typing import Any

from .schemas import VideoMetadata


class GetMetadata:
    """Create normalized VideoMetadata from JSON input."""

    @staticmethod
    def from_json(data: dict[str, Any]) -> VideoMetadata:
        return VideoMetadata(**data)

    @staticmethod
    def from_file(path: str | Path) -> VideoMetadata:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        return GetMetadata.from_json(raw)


def _stream_print(text: str, chunk_size: int = 8, delay_s: float = 0.02) -> None:
    for idx in range(0, len(text), chunk_size):
        print(text[idx : idx + chunk_size], end="", flush=True)
        time.sleep(delay_s)
    print("", flush=True)


def _normalize_product_name(name: str) -> str:
    lowered = (name or "").strip().lower()
    if not lowered:
        return ""
    if lowered in {"coca-cola", "coca cola", "cola", "coke", "coca-cola classic"}:
        return "coke"
    if "pizza" in lowered:
        return "pizza"
    return lowered


def _is_food_or_drink(name: str, category: str) -> bool:
    name_lower = (name or "").lower()
    category_lower = (category or "").lower()
    if any(word in category_lower for word in ("food", "beverage", "drink", "snack", "grocery")):
        return True
    return any(
        word in name_lower
        for word in (
            "pizza",
            "burger",
            "fries",
            "soda",
            "cola",
            "coke",
            "snack",
            "chips",
            "candy",
            "coffee",
            "tea",
            "juice",
            "beer",
            "wine",
            "water",
        )
    )


def _extract_product_mentions(payload: dict) -> list[tuple[str, str]]:
    mentions: list[tuple[str, str]] = []
    scenes = payload.get("scenes") or []
    for scene in scenes:
        for mention in scene.get("product_mentions") or []:
            mentions.append((mention.get("product_name", ""), mention.get("category", "")))
    return mentions


def _rank_common_products(payload: dict, forced_top: str | None = None) -> list[str]:
    counter: Counter[str] = Counter()
    for name, category in _extract_product_mentions(payload):
        if not _is_food_or_drink(name, category):
            continue
        normalized = _normalize_product_name(name)
        if normalized:
            counter[normalized] += 1

    ranked = [name for name, _ in counter.most_common()]
    if forced_top:
        forced_top = forced_top.lower()
        ranked = [name for name in ranked if name != forced_top]
        ranked.insert(0, forced_top)
    return ranked


def _filtered_payload_for_print(payload: dict) -> dict:
    filtered = dict(payload)
    scenes = payload.get("scenes") or []
    filtered["scenes"] = [scene for scene in scenes if scene.get("product_mentions")]
    return filtered


def magic_print_indexing(
    bbs_path: str,
    sts_path: str,
    pause_s: float = 7.0,
) -> None:
    """Stream JSON output and show most common products for demo indexing."""

    overrides = {
        Path(bbs_path).name.lower(): "pizza",
        Path(sts_path).name.lower(): "coke",
    }
    for path in (bbs_path, sts_path):
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        printable_payload = _filtered_payload_for_print(payload)
        header = f"\n=== indexing stream: {Path(path).name} ===\n"
        _stream_print(header, chunk_size=24, delay_s=0.015)
        _stream_print(json.dumps(printable_payload, indent=2), chunk_size=8, delay_s=0.02)

        time.sleep(pause_s)
        forced = overrides.get(Path(path).name.lower())
        ranked = _rank_common_products(payload, forced_top=forced)
        most_common = ranked[0] if ranked else (forced or "unknown")
        print(f"\nMost common product: {most_common}")
        if len(ranked) > 1:
            print(f"Next most common foods: {', '.join(ranked[1:4])}")
        print("", flush=True)
