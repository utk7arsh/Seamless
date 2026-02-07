"""CLI entrypoint for Seamless ads."""

import json
import sys
from pathlib import Path

from .metadata import GetMetadata
from .schemas import UserProfile
from .service import SeamlessAdService


def _load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    if len(sys.argv) < 3:
        print("Usage: python -m seamless_ads <scene_json> <user_json>", file=sys.stderr)
        sys.exit(1)

    scene_path = sys.argv[1]
    user_path = sys.argv[2]

    user = UserProfile(**_load_json(user_path))
    scene = GetMetadata.from_file(scene_path)

    service = SeamlessAdService()
    try:
        response = service.generate_ad_response(user, scene)
        print(json.dumps(response.model_dump(), indent=2))
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
