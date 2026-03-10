from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.jwt import create_access_token, hash_password
from app.db.base import Base
from app.db.models import MandiPrice, Region, RegionCrop, User, WeatherForecast
from app.db.session import get_db_session
from app.main import create_app


@pytest.fixture
async def engine(tmp_path_factory: pytest.TempPathFactory):  # type: ignore[no-untyped-def]
    db_path = Path(tmp_path_factory.mktemp("db")) / "farmwise-test.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", future=True)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session_factory(engine):  # type: ignore[no-untyped-def]
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture
async def client(session_factory) -> AsyncGenerator[AsyncClient, None]:  # type: ignore[no-untyped-def]
    app = create_app()

    async def override_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest.fixture
async def seeded_region(session_factory) -> Region:  # type: ignore[no-untyped-def]
    async with session_factory() as session:
        region = Region(
            state="Tamil Nadu",
            district="Chennai",
            region_name="Cauvery Delta",
            dominant_soil_type="Red Laterite",
            default_water_availability="Tank irrigation",
            climate_zone="Tropical",
        )
        session.add(region)
        await session.flush()
        session.add_all(
            [
                RegionCrop(
                    region_id=region.id,
                    crop_name="Paddy",
                    crop_season="Kharif",
                    suitability_score=9.2,
                    notes="Primary seasonal crop",
                ),
                RegionCrop(
                    region_id=region.id,
                    crop_name="Groundnut",
                    crop_season="Zaid",
                    suitability_score=7.5,
                    notes="Supplementary crop",
                ),
            ]
        )
        today = date.today()
        for offset in range(7):
            session.add(
                WeatherForecast(
                    region_id=region.id,
                    forecast_date=today + timedelta(days=offset),
                    min_temp=25.0 + offset * 0.1,
                    max_temp=33.0 + offset * 0.1,
                    expected_rainfall_mm=5.0 + offset,
                    humidity_pct=70.0 + offset,
                    wind_speed_kmph=12.0 + offset,
                    forecast_generated_at=datetime.now(UTC),
                )
            )
        session.add_all(
            [
                MandiPrice(
                    region_id=region.id,
                    crop_name="Paddy",
                    price_per_quintal=2400.0,
                    recorded_date=today,
                ),
                MandiPrice(
                    region_id=region.id,
                    crop_name="Groundnut",
                    price_per_quintal=6100.0,
                    recorded_date=today,
                ),
            ]
        )
        await session.commit()
        await session.refresh(region)
        return region


@pytest.fixture
async def seeded_user(session_factory, seeded_region: Region) -> User:  # type: ignore[no-untyped-def]
    async with session_factory() as session:
        user = User(
            name="Test Farmer",
            email="farmer@example.com",
            phone_number="9999999999",
            password_hash=hash_password("pass123"),
            region_id=seeded_region.id,
            water_availability="Tank irrigation",
            irrigation_type="Flood",
            current_crop="Paddy",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest.fixture
def auth_headers(seeded_user: User) -> dict[str, str]:
    access_token, _ = create_access_token(str(seeded_user.id))
    return {"Authorization": f"Bearer {access_token}"}
