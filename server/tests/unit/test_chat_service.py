from __future__ import annotations

import json

from app.services.chat_service import _detect_metadata


def test_detect_metadata_returns_plain_for_text_reply() -> None:
    assert _detect_metadata("Is there an organic alternative?") == {
        "source": "agent_service",
        "structured": False,
    }


def test_detect_metadata_normalizes_crop_recommendation() -> None:
    reply = json.dumps(
        {
            "intent": "crop_recommendation",
            "crops": [
                {
                    "name": "Tomato",
                    "sowing_window": "June - July",
                    "harvest_window": "September - November",
                    "water_requirement": "Moderate",
                    "estimated_cost_per_ha": 45000,
                    "expected_yield_qtl_per_ha": 250,
                    "expected_price_per_qtl": 1200,
                    "expected_revenue_per_ha": 300000,
                    "why_recommended": "High suitability for black cotton soil.",
                    "scheme": "PMFBY available.",
                }
            ],
            "summary": "Tomato is your best option this Kharif season.",
        }
    )

    assert _detect_metadata(reply) == {
        "source": "agent_service",
        "structured": True,
        "intent": "crop_recommendation",
        "data": {
            "crop": "Tomato",
            "season": None,
            "sowing_window": "June - July",
            "harvest_window": "September - November",
            "water_requirement": "Moderate",
            "estimated_cost": 45000,
            "expected_yield": 250,
            "expected_revenue": 300000,
            "notes": (
                "High suitability for black cotton soil. PMFBY available. "
                "Tomato is your best option this Kharif season."
            ),
        },
    }


def test_detect_metadata_normalizes_pest_diagnosis() -> None:
    reply = json.dumps(
        {
            "intent": "pest_diagnosis",
            "crop": "Tomato",
            "diagnosis": "Early Blight",
            "confidence": "High",
            "symptoms_matched": ["dark circular spots", "yellow halo"],
            "treatment": {
                "chemical": "Mancozeb 75% WP",
                "organic": "Copper oxychloride",
                "dosage": "2 g/litre",
                "frequency": "Every 7-10 days",
            },
            "spray_warning": "Spray today or wait until Day 4.",
            "prevention": "Avoid overhead irrigation.",
            "summary": "Your tomato likely has Early Blight.",
        }
    )

    assert _detect_metadata(reply) == {
        "source": "agent_service",
        "structured": True,
        "intent": "pest_diagnosis",
        "data": {
            "pest_name": "Early Blight",
            "crop": "Tomato",
            "symptoms": "dark circular spots, yellow halo",
            "treatment": "Mancozeb 75% WP",
            "dosage": "2 g/litre",
            "frequency": "Every 7-10 days",
            "organic_alternative": "Copper oxychloride",
            "warning": "Spray today or wait until Day 4.",
        },
    }


def test_detect_metadata_normalizes_irrigation_schedule() -> None:
    reply = json.dumps(
        {
            "intent": "irrigation_schedule",
            "crop": "Tomato",
            "days_since_sowing": 42,
            "growth_stage": "Flowering",
            "irrigation_type": "drip",
            "schedule": [
                {
                    "date": "2026-03-13",
                    "action": "irrigate",
                    "amount": "4 L/plant",
                    "reason": "Flowering stage - critical water period",
                },
                {
                    "date": "2026-03-14",
                    "action": "skip",
                    "amount": None,
                    "reason": "Rain forecast - 12 mm expected",
                },
            ],
            "summary": "Skip the next day due to forecast rain.",
        }
    )

    assert _detect_metadata(reply) == {
        "source": "agent_service",
        "structured": True,
        "intent": "irrigation_schedule",
        "data": {
            "next_watering_date": "2026-03-13",
            "skip_dates": ["2026-03-14"],
            "expected_rainfall_mm": 12.0,
            "rainfall_date": "2026-03-14",
            "reason": (
                "Skip the next day due to forecast rain. "
                "Flowering stage - critical water period Rain forecast - 12 mm expected"
            ),
        },
    }


def test_detect_metadata_normalizes_market_timing() -> None:
    reply = json.dumps(
        {
            "intent": "market_timing",
            "crop": "Tomato",
            "current_price_per_qtl": 1450,
            "price_7d_ago": 980,
            "trend": "rising",
            "trend_pct": 48,
            "msp": None,
            "recommendation": "hold",
            "reasoning": "Price has risen 48% in 7 days.",
            "sell_by": "Within 2 weeks",
            "summary": "Hold your stock for up to 2 more weeks.",
        }
    )

    assert _detect_metadata(reply) == {
        "source": "agent_service",
        "structured": True,
        "intent": "market_timing",
        "data": {
            "crop": "Tomato",
            "current_price": 1450,
            "price_unit": "qtl",
            "trend": "rising",
            "trend_pct": 48,
            "advice": "Price has risen 48% in 7 days. Hold your stock for up to 2 more weeks.",
        },
    }


def test_detect_metadata_returns_plain_for_unknown_intent() -> None:
    reply = json.dumps({"intent": "advisory_summary", "summary": "Use compost."})
    assert _detect_metadata(reply) == {"source": "agent_service", "structured": False}
