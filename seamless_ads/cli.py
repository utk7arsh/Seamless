"""CLI entrypoint for Seamless ads."""

import argparse
import json
from pathlib import Path

from .metadata import GetMetadata
from .schemas import UserProfile
from .service import SeamlessAdService
from .user_profiles import USER_PERSONAS, get_user_profile


def _load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description="Generate Seamless ad recommendations.")
    parser.add_argument("scene_json", help="Path to scene metadata JSON.")
    parser.add_argument("user_json", nargs="?", help="Path to user profile JSON.")
    parser.add_argument(
        "--user-key",
        choices=sorted(USER_PERSONAS.keys()),
        help="Use a predefined user persona key.",
    )
    args = parser.parse_args()

    if args.user_key:
        user = get_user_profile(args.user_key)
    elif args.user_json:
        user = UserProfile(**_load_json(args.user_json))
    else:
        parser.error("Provide a user JSON path or --user-key.")

    scene = GetMetadata.from_file(args.scene_json)

    service = SeamlessAdService()
    response = service.generate_ad_response(user, scene)
    print(json.dumps(response.model_dump(), indent=2))


if __name__ == "__main__":
    main()
