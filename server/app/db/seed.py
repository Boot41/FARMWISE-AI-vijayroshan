from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime, timedelta
from typing import cast

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.jwt import hash_password
from app.core.config import get_settings
from app.db.base import Base
from app.db.models import (
    ChatMessage,
    ChatSession,
    MandiPrice,
    RefreshToken,
    Region,
    RegionCrop,
    User,
    WeatherForecast,
)

SEED_REFERENCE_DATE = date(2026, 3, 12)
MANDI_HISTORY_DAYS = 14

DOCUMENTED_CROPS = {
    "Banana",
    "Bajra",
    "Cluster Bean (Guar)",
    "Coconut",
    "Cumin",
    "Groundnut",
    "Maize",
    "Mustard",
    "Onion",
    "Pepper",
    "Rice",
    "Sugarcane",
    "Tomato",
    "Wheat",
}


def build_price_history(start_price: int, daily_changes: list[int]) -> list[int]:
    prices = [start_price]
    for change in daily_changes:
        prices.append(prices[-1] + change)
    if len(prices) != MANDI_HISTORY_DAYS:
        raise ValueError(
            f"Expected {MANDI_HISTORY_DAYS} mandi prices, generated {len(prices)} values."
        )
    return prices


SEED_REGIONS = [
    {
        "state": "Tamil Nadu",
        "district": "Chennai",
        "region_name": "Cauvery Delta",
        "dominant_soil_type": "Red Laterite",
        "default_water_availability": "Tank irrigation",
        "climate_zone": "Tropical",
        "crops": [
            ("Rice", "Kharif", 9.4, "Kuruvai rice is strongly supported in the Cauvery Delta."),
            ("Groundnut", "Rabi", 8.3, "Fits the documented Tamil Nadu crop calendar well."),
            ("Sugarcane", "Annual", 7.9, "Profitable where tank storage remains dependable."),
        ],
        "weather": [
            (27.0, 33.0, 12.0, 78.0, 18.0),
            (27.5, 34.0, 4.0, 74.0, 16.0),
            (26.8, 33.8, 0.0, 72.0, 15.0),
            (27.2, 34.5, 6.0, 73.0, 17.0),
            (27.1, 33.9, 8.0, 76.0, 19.0),
            (26.7, 33.5, 14.0, 81.0, 20.0),
            (26.5, 32.9, 18.0, 83.0, 21.0),
        ],
        "prices": {
            "Rice": build_price_history(2260, [15, 20, 10, 25, 20, 10, 15, 20, 15, 10, 25, 15, 20]),
            "Groundnut": build_price_history(
                5840, [20, 30, 15, 25, 20, 15, 25, 20, 15, 25, 20, 15, 20]
            ),
            "Sugarcane": build_price_history(3180, [5, 10, 5, 0, 10, 5, 0, 10, 5, 5, 10, 0, 10]),
        },
    },
    {
        "state": "Maharashtra",
        "district": "Nashik",
        "region_name": "Deccan Plateau",
        "dominant_soil_type": "Black Cotton",
        "default_water_availability": "Borewell + Rain",
        "climate_zone": "Semi-arid",
        "crops": [
            (
                "Tomato",
                "Zaid",
                9.2,
                "Documented crop with strong mandi relevance in the Nashik belt.",
            ),
            ("Onion", "Rabi", 9.4, "Matches both the Nashik calendar and the seasonal advisory."),
            ("Wheat", "Rabi", 7.9, "Suitable where irrigation is available through late winter."),
        ],
        "weather": [
            (19.0, 32.0, 0.0, 38.0, 14.0),
            (18.5, 33.0, 0.0, 35.0, 13.0),
            (19.2, 33.5, 0.0, 34.0, 15.0),
            (20.0, 34.0, 1.0, 36.0, 16.0),
            (20.3, 34.6, 0.0, 33.0, 17.0),
            (19.8, 33.9, 2.0, 39.0, 14.0),
            (19.1, 32.8, 3.0, 42.0, 13.0),
        ],
        "prices": {
            "Tomato": build_price_history(
                1540, [35, 30, 45, 25, 35, 40, 30, 45, 35, 30, 25, 40, 30]
            ),
            "Onion": build_price_history(
                1820, [20, 15, 20, 10, 15, 20, 15, 10, 20, 15, 10, 15, 20]
            ),
            "Wheat": build_price_history(
                2680, [10, 15, 10, 15, 10, 10, 15, 10, 10, 15, 10, 10, 15]
            ),
        },
    },
    {
        "state": "Punjab",
        "district": "Ludhiana",
        "region_name": "Punjab Plains",
        "dominant_soil_type": "Alluvial",
        "default_water_availability": "Canal irrigation",
        "climate_zone": "Sub-tropical",
        "crops": [
            ("Wheat", "Rabi", 9.6, "Primary documented Rabi crop in Punjab."),
            ("Rice", "Kharif", 8.9, "Direct-seeded rice remains a key kharif option."),
            ("Maize", "Kharif", 8.1, "Supported as a diversification crop in the Punjab calendar."),
            ("Mustard", "Rabi", 7.2, "Useful border-row and diversification option."),
        ],
        "weather": [
            (15.0, 28.0, 0.0, 48.0, 11.0),
            (15.8, 29.0, 0.0, 44.0, 10.0),
            (16.4, 29.6, 0.0, 42.0, 12.0),
            (17.1, 30.1, 0.0, 40.0, 14.0),
            (17.4, 30.7, 1.0, 43.0, 15.0),
            (16.9, 29.8, 0.0, 46.0, 13.0),
            (16.0, 28.9, 0.0, 49.0, 11.0),
        ],
        "prices": {
            "Wheat": build_price_history(
                2440, [10, 15, 10, 10, 15, 10, 10, 15, 10, 10, 15, 10, 10]
            ),
            "Rice": build_price_history(2260, [10, 15, 10, 10, 15, 10, 10, 15, 10, 10, 15, 10, 10]),
            "Maize": build_price_history(
                2080, [15, 20, 15, 10, 15, 10, 15, 20, 10, 15, 10, 10, 15]
            ),
            "Mustard": build_price_history(
                5480, [25, 30, 20, 25, 30, 20, 25, 30, 20, 25, 20, 25, 30]
            ),
        },
    },
    {
        "state": "Kerala",
        "district": "Thrissur",
        "region_name": "Malabar Coast",
        "dominant_soil_type": "Laterite + Loam",
        "default_water_availability": "High rainfall",
        "climate_zone": "Tropical humid",
        "crops": [
            ("Coconut", "Annual", 9.5, "Most stable perennial crop in the Kerala docs set."),
            ("Pepper", "Annual", 8.8, "Matches the black pepper calendar and pest guide."),
            ("Banana", "Annual", 8.6, "Strong fit for humid conditions and the advisory corpus."),
        ],
        "weather": [
            (24.0, 31.0, 24.0, 86.0, 13.0),
            (24.2, 31.3, 18.0, 84.0, 12.0),
            (24.1, 30.9, 20.0, 85.0, 14.0),
            (23.9, 30.7, 28.0, 88.0, 15.0),
            (24.0, 31.1, 32.0, 89.0, 16.0),
            (24.3, 31.5, 14.0, 82.0, 12.0),
            (24.1, 31.0, 22.0, 86.0, 13.0),
        ],
        "prices": {
            "Coconut": build_price_history(
                2920, [15, 20, 15, 10, 20, 10, 15, 20, 15, 10, 15, 10, 15]
            ),
            "Pepper": build_price_history(
                50800, [140, 160, 120, 180, 140, 160, 120, 180, 140, 120, 160, 140, 180]
            ),
            "Banana": build_price_history(
                2380, [20, 20, 15, 20, 15, 20, 15, 20, 15, 20, 15, 20, 15]
            ),
        },
    },
    {
        "state": "Rajasthan",
        "district": "Jaipur",
        "region_name": "Thar Desert",
        "dominant_soil_type": "Sandy Arid",
        "default_water_availability": "Scarce irrigation",
        "climate_zone": "Arid",
        "crops": [
            ("Bajra", "Kharif", 9.2, "Primary documented dryland cereal in Rajasthan."),
            ("Mustard", "Rabi", 8.9, "Strong winter oilseed option with good advisory coverage."),
            ("Cumin", "Rabi", 7.8, "Commercial spice crop supported in the Rajasthan calendar."),
            (
                "Cluster Bean (Guar)",
                "Kharif",
                8.3,
                "Drought-tolerant kharif cash crop in the advisory.",
            ),
        ],
        "weather": [
            (18.0, 34.0, 0.0, 21.0, 20.0),
            (18.8, 35.0, 0.0, 19.0, 22.0),
            (19.5, 35.6, 0.0, 18.0, 24.0),
            (20.0, 36.2, 0.0, 17.0, 25.0),
            (20.4, 36.5, 0.0, 16.0, 23.0),
            (19.7, 35.8, 0.0, 18.0, 21.0),
            (18.9, 34.7, 0.0, 20.0, 19.0),
        ],
        "prices": {
            "Bajra": build_price_history(
                2380, [15, 20, 15, 10, 15, 10, 15, 20, 10, 15, 10, 15, 10]
            ),
            "Mustard": build_price_history(
                5520, [30, 25, 30, 20, 25, 30, 20, 25, 30, 20, 25, 30, 20]
            ),
            "Cumin": build_price_history(
                17600, [140, 120, 160, 120, 140, 160, 120, 140, 160, 120, 140, 160, 120]
            ),
            "Cluster Bean (Guar)": build_price_history(
                4320, [40, 35, 30, 25, 35, 30, 25, 35, 30, 25, 35, 30, 25]
            ),
        },
    },
]

SEED_USERS = [
    {
        "name": "Arun Prakash",
        "email": "arun@farmwise.ai",
        "state": "Tamil Nadu",
        "water_availability": "Tank irrigation",
        "irrigation_type": "Flood",
        "current_crop": "Groundnut",
        "sowing_days_ago": 78,
    },
    {
        "name": "Meera Patil",
        "email": "meera@farmwise.ai",
        "state": "Maharashtra",
        "water_availability": "Borewell + Rain",
        "irrigation_type": "Drip",
        "current_crop": "Tomato",
        "sowing_days_ago": 42,
    },
    {
        "name": "Gurpreet Singh",
        "email": "gurpreet@farmwise.ai",
        "state": "Punjab",
        "water_availability": "Canal irrigation",
        "irrigation_type": "Flood",
        "current_crop": "Wheat",
        "sowing_days_ago": 110,
    },
    {
        "name": "Anila Joseph",
        "email": "anila@farmwise.ai",
        "state": "Kerala",
        "water_availability": "High rainfall",
        "irrigation_type": "Basin",
        "current_crop": "Coconut",
        "sowing_days_ago": 240,
    },
    {
        "name": "Ravi Shekhawat",
        "email": "ravi@farmwise.ai",
        "state": "Rajasthan",
        "water_availability": "Scarce irrigation",
        "irrigation_type": "Drip",
        "current_crop": "Mustard",
        "sowing_days_ago": 105,
    },
]


def _validate_seed_configuration() -> None:
    region_crops_by_state: dict[str, set[str]] = {}

    for region_seed in SEED_REGIONS:
        crops = cast(list[tuple[str, str, float, str]], region_seed["crops"])
        price_map = cast(dict[str, list[int]], region_seed["prices"])
        crop_names = {crop_name for crop_name, _, _, _ in crops}
        region_state = cast(str, region_seed["state"])

        undocumented_crops = sorted(crop_names - DOCUMENTED_CROPS)
        if undocumented_crops:
            raise ValueError(
                f"Seed region {region_state} includes crops not grounded in Agents/docs: "
                f"{', '.join(undocumented_crops)}"
            )

        missing_price_rows = sorted(crop_names - set(price_map))
        if missing_price_rows:
            raise ValueError(
                f"Seed region {region_state} is missing mandi history for: "
                f"{', '.join(missing_price_rows)}"
            )

        extra_price_rows = sorted(set(price_map) - crop_names)
        if extra_price_rows:
            raise ValueError(
                f"Seed region {region_state} has mandi prices for unknown crops: "
                f"{', '.join(extra_price_rows)}"
            )

        for crop_name, price_history in price_map.items():
            if len(price_history) != MANDI_HISTORY_DAYS:
                raise ValueError(
                    f"Expected {MANDI_HISTORY_DAYS} mandi prices for {region_state} / "
                    f"{crop_name}, got {len(price_history)}."
                )

        region_crops_by_state[region_state] = crop_names

    for user_seed in SEED_USERS:
        state = cast(str, user_seed["state"])
        current_crop = cast(str, user_seed["current_crop"])
        if current_crop not in region_crops_by_state[state]:
            raise ValueError(
                f"Demo user crop {current_crop} is not seeded for region state {state}."
            )


async def reset_database(session: AsyncSession) -> None:
    for model in [
        ChatMessage,
        ChatSession,
        RefreshToken,
        MandiPrice,
        WeatherForecast,
        RegionCrop,
        User,
        Region,
    ]:
        await session.execute(delete(model))
    await session.commit()


async def seed_database() -> None:
    _validate_seed_configuration()

    settings = get_settings()
    engine = create_async_engine(settings.effective_db_url, echo=False, future=True)
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as session:
            await reset_database(session)
            region_map: dict[str, Region] = {}
            today = SEED_REFERENCE_DATE

            for region_seed in SEED_REGIONS:
                region = Region(
                    state=cast(str, region_seed["state"]),
                    district=cast(str, region_seed["district"]),
                    region_name=cast(str, region_seed["region_name"]),
                    dominant_soil_type=cast(str, region_seed["dominant_soil_type"]),
                    default_water_availability=cast(str, region_seed["default_water_availability"]),
                    climate_zone=cast(str, region_seed["climate_zone"]),
                )
                session.add(region)
                await session.flush()
                region_map[region.state] = region

                for crop_name, crop_season, suitability_score, notes in cast(
                    list[tuple[str, str, float, str]], region_seed["crops"]
                ):
                    session.add(
                        RegionCrop(
                            region_id=region.id,
                            crop_name=crop_name,
                            crop_season=crop_season,
                            suitability_score=suitability_score,
                            notes=notes,
                        )
                    )

                generated_at = datetime.now(UTC)
                for offset, weather in enumerate(
                    cast(list[tuple[float, float, float, float, float]], region_seed["weather"])
                ):
                    min_temp, max_temp, rainfall, humidity, wind_speed = weather
                    session.add(
                        WeatherForecast(
                            region_id=region.id,
                            forecast_date=today + timedelta(days=offset),
                            min_temp=min_temp,
                            max_temp=max_temp,
                            expected_rainfall_mm=rainfall,
                            humidity_pct=humidity,
                            wind_speed_kmph=wind_speed,
                            forecast_generated_at=generated_at,
                        )
                    )

                price_map = cast(dict[str, list[int]], region_seed["prices"])
                for crop_name, price_history in price_map.items():
                    for day_offset, price in enumerate(price_history):
                        session.add(
                            MandiPrice(
                                region_id=region.id,
                                crop_name=crop_name,
                                price_per_quintal=price,
                                recorded_date=today
                                - timedelta(days=MANDI_HISTORY_DAYS - day_offset - 1),
                            )
                        )

            password_hash = hash_password("pass123")
            for user_seed in SEED_USERS:
                region = region_map[cast(str, user_seed["state"])]
                session.add(
                    User(
                        name=cast(str, user_seed["name"]),
                        email=cast(str, user_seed["email"]),
                        phone_number="9000000000",
                        password_hash=password_hash,
                        region_id=region.id,
                        water_availability=cast(str, user_seed["water_availability"]),
                        irrigation_type=cast(str, user_seed["irrigation_type"]),
                        current_crop=cast(str, user_seed["current_crop"]),
                        sowing_date=today - timedelta(days=cast(int, user_seed["sowing_days_ago"])),
                    )
                )

            await session.commit()
            print(
                "Seeded 5 regions with documented crops, 14-day mandi history through "
                "March 12, 2026, 7-day weather forecasts, and demo users "
                "(password: pass123)."
            )
    finally:
        await engine.dispose()


def main() -> None:
    asyncio.run(seed_database())


if __name__ == "__main__":
    main()
