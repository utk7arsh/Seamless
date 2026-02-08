"""Curated user personas for Seamless ad targeting."""

from .schemas import UserProfile

USER_PERSONAS: dict[str, UserProfile] = {
    "A": UserProfile(
        age_range="25-34",
        household_size=2,
        location_zip="94107",
        location_metro="SF Bay Area",
        dietary_preferences=["comfort_food", "no_beef"],
        brand_affinities={"Coca-Cola": 0.85, "Pepsi": 0.2},
        cuisine_affinities={"Italian": 0.7, "Mexican": 0.4},
        watch_time_context="late_night",
        engagement_signals={
            "often_pauses_for_food_scenes": True,
            "often_uses_deals": True,
            "prefers_delivery": True,
        },
    ),
    "B": UserProfile(
        age_range="30-44",
        household_size=1,
        location_zip="98109",
        location_metro="Seattle Metro",
        dietary_preferences=["balanced", "low_sugar"],
        brand_affinities={"Spindrift": 0.6, "Coca-Cola": 0.3},
        cuisine_affinities={"Japanese": 0.6, "Mediterranean": 0.5},
        watch_time_context="weekday_evening",
        engagement_signals={
            "prefers_pickup": True,
            "prefers_premium": True,
        },
    ),
}


def get_user_profile(user_key: str) -> UserProfile:
    normalized = user_key.strip().upper()
    if normalized not in USER_PERSONAS:
        raise ValueError(f"Unknown user_key '{user_key}'. Available: {', '.join(USER_PERSONAS)}")
    return USER_PERSONAS[normalized].model_copy(deep=True)
