"""Metadata normalization for video understanding output."""

import json
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
