from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime, timedelta

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
        "prices": [("Paddy", 2450), ("Groundnut", 6200), ("Black Gram", 7400), ("Sesame", 8900)],
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
        "prices": [("Soybean", 4650), ("Onion", 2100), ("Bajra", 2650), ("Wheat", 2850)],
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
        "prices": [("Wheat", 2550), ("Paddy", 2380), ("Maize", 2220), ("Potato", 1750)],
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
        "prices": [("Coconut", 3100), ("Banana", 2600), ("Rice", 2550), ("Pepper", 54000)],
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
        "prices": [("Bajra", 2550), ("Mustard", 5850), ("Cumin", 18800), ("Moong", 7600)],
    },
]

SEED_USERS = [
    ("Arun Prakash", "arun@farmwise.ai", "Tamil Nadu", "Tank irrigation", "Paddy"),
    ("Meera Patil", "meera@farmwise.ai", "Maharashtra", "Borewell + Rain", "Onion"),
    ("Gurpreet Singh", "gurpreet@farmwise.ai", "Punjab", "Canal irrigation", "Wheat"),
    ("Anila Joseph", "anila@farmwise.ai", "Kerala", "High rainfall", "Banana"),
    ("Ravi Shekhawat", "ravi@farmwise.ai", "Rajasthan", "Scarce drip only", "Bajra"),
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
            today = date.today()

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

                for crop_name, price in region_seed["prices"]:
                    session.add(
                        MandiPrice(
                            region_id=region.id,
                            crop_name=crop_name,
                            price_per_quintal=price,
                            recorded_date=today,
                        )
                    )

            password_hash = hash_password("pass123")
            for name, email, state, water_availability, current_crop in SEED_USERS:
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
                    )
                )

            await session.commit()
            print("Seeded 5 regions, regional datasets, and demo users (password: pass123).")
    finally:
        await engine.dispose()


def main() -> None:
    asyncio.run(seed_database())


if __name__ == "__main__":
    main()
