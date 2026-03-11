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
MANDI_HISTORY_DAYS = 7

SEED_REGIONS = [
    {
        "state": "Tamil Nadu",
        "district": "Chennai",
        "region_name": "Cauvery Delta",
        "dominant_soil_type": "Red Laterite",
        "default_water_availability": "Tank irrigation",
        "climate_zone": "Tropical",
        "crops": [
            ("Paddy", "Kharif", 9.4, "Reliable tank-fed staple crop."),
            ("Black Gram", "Rabi", 8.1, "Fits well after paddy harvest."),
            ("Groundnut", "Zaid", 7.6, "Works on lighter red soils."),
            ("Sugarcane", "Annual", 8.7, "Profitable where tank storage is stable."),
            ("Sesame", "Zaid", 7.2, "Short duration oilseed option."),
            ("Tomato", "Zaid", 7.5, "Common peri-urban cash crop near Chennai markets."),
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
            "Paddy": [2320, 2350, 2375, 2390, 2410, 2430, 2450],
            "Groundnut": [5920, 5980, 6030, 6090, 6130, 6175, 6200],
            "Black Gram": [7010, 7080, 7160, 7230, 7300, 7360, 7400],
            "Sesame": [8450, 8520, 8600, 8690, 8760, 8840, 8900],
            "Tomato": [1480, 1540, 1610, 1680, 1760, 1840, 1920],
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
            ("Soybean", "Kharif", 9.0, "Strong kharif fit on black cotton soils."),
            ("Onion", "Rabi", 9.3, "High mandi relevance in Nashik."),
            ("Bajra", "Kharif", 7.9, "Useful in lower rainfall belts."),
            ("Wheat", "Rabi", 8.0, "Moderate performance with irrigation."),
            ("Tomato", "Zaid", 7.8, "Profitable under managed irrigation."),
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
            "Soybean": [4470, 4510, 4540, 4580, 4610, 4630, 4650],
            "Onion": [1960, 1990, 2015, 2040, 2060, 2080, 2100],
            "Bajra": [2520, 2550, 2570, 2590, 2610, 2630, 2650],
            "Wheat": [2740, 2760, 2785, 2800, 2820, 2840, 2850],
            "Tomato": [1760, 1810, 1860, 1910, 1970, 2030, 2090],
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
            ("Wheat", "Rabi", 9.6, "Highest stability crop in the plains."),
            ("Paddy", "Kharif", 9.1, "Still dominant despite water pressure."),
            ("Maize", "Kharif", 7.8, "Useful diversification option."),
            ("Potato", "Rabi", 8.4, "Commercial crop with irrigation."),
            ("Moong", "Zaid", 7.1, "Short-duration pulse for rotation."),
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
            "Wheat": [2470, 2485, 2505, 2520, 2535, 2545, 2550],
            "Paddy": [2290, 2310, 2330, 2345, 2360, 2370, 2380],
            "Maize": [2140, 2160, 2175, 2190, 2200, 2210, 2220],
            "Potato": [1690, 1705, 1720, 1730, 1740, 1745, 1750],
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
            ("Coconut", "Annual", 9.5, "Backbone perennial crop."),
            ("Banana", "Annual", 8.9, "Very common under humid conditions."),
            ("Rice", "Kharif", 7.8, "Important in lowland areas."),
            ("Pepper", "Annual", 8.7, "Suitable as a spice crop."),
            ("Tapioca", "Zaid", 7.6, "Resilient food crop."),
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
            "Coconut": [2980, 3005, 3030, 3050, 3070, 3090, 3100],
            "Banana": [2460, 2490, 2520, 2550, 2570, 2590, 2600],
            "Rice": [2470, 2485, 2500, 2515, 2530, 2540, 2550],
            "Pepper": [52100, 52600, 52950, 53300, 53650, 53820, 54000],
        },
    },
    {
        "state": "Rajasthan",
        "district": "Jaipur",
        "region_name": "Thar Desert",
        "dominant_soil_type": "Sandy Arid",
        "default_water_availability": "Scarce drip only",
        "climate_zone": "Arid",
        "crops": [
            ("Bajra", "Kharif", 9.2, "Most dependable cereal under arid stress."),
            ("Mustard", "Rabi", 8.8, "Strong oilseed option in winter."),
            ("Cumin", "Rabi", 7.5, "Commercial spice with drip support."),
            ("Moong", "Kharif", 7.9, "Short duration pulse for low-moisture windows."),
            ("Guar", "Kharif", 8.4, "Useful drought-tolerant cash crop."),
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
            "Bajra": [2460, 2480, 2500, 2515, 2530, 2540, 2550],
            "Mustard": [5620, 5660, 5710, 5760, 5800, 5830, 5850],
            "Cumin": [18150, 18320, 18480, 18620, 18710, 18760, 18800],
            "Moong": [7350, 7400, 7450, 7490, 7530, 7570, 7600],
        },
    },
]

SEED_USERS = [
    ("Arun Prakash", "arun@farmwise.ai", "Tamil Nadu", "Tank irrigation", "Rice", 35),
    ("Meera Patil", "meera@farmwise.ai", "Maharashtra", "Borewell + Rain", "Tomato", 28),
    ("Gurpreet Singh", "gurpreet@farmwise.ai", "Punjab", "Canal irrigation", "Wheat", 42),
    ("Anila Joseph", "anila@farmwise.ai", "Kerala", "High rainfall", "Coconut", 20),
    ("Ravi Shekhawat", "ravi@farmwise.ai", "Rajasthan", "Scarce drip only", "Bajra", 30),
]


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
                    state=region_seed["state"],
                    district=region_seed["district"],
                    region_name=region_seed["region_name"],
                    dominant_soil_type=region_seed["dominant_soil_type"],
                    default_water_availability=region_seed["default_water_availability"],
                    climate_zone=region_seed["climate_zone"],
                )
                session.add(region)
                await session.flush()
                region_map[region.state] = region

                for crop_name, crop_season, suitability_score, notes in region_seed["crops"]:
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
                for offset, weather in enumerate(region_seed["weather"]):
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
                    if len(price_history) != MANDI_HISTORY_DAYS:
                        raise ValueError(
                            "Expected "
                            f"{MANDI_HISTORY_DAYS} mandi prices for "
                            f"{region.state} / {crop_name}, got {len(price_history)}."
                        )
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
            for (
                name,
                email,
                state,
                water_availability,
                current_crop,
                sowing_days_ago,
            ) in SEED_USERS:
                region = region_map[state]
                session.add(
                    User(
                        name=name,
                        email=email,
                        phone_number="9000000000",
                        password_hash=password_hash,
                        region_id=region.id,
                        water_availability=water_availability,
                        irrigation_type=region.default_water_availability,
                        current_crop=current_crop,
                        sowing_date=today - timedelta(days=sowing_days_ago),
                    )
                )

            await session.commit()
            print(
                "Seeded 5 regions, 7-day mandi history through March 12, 2026, "
                "regional datasets, and demo users (password: pass123)."
            )
    finally:
        await engine.dispose()


def main() -> None:
    asyncio.run(seed_database())


if __name__ == "__main__":
    main()
