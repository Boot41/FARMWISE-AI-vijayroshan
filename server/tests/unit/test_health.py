from __future__ import annotations

from app.main import create_app


def test_app_metadata() -> None:
    app = create_app()
    assert app.title == "FarmWise AI Backend"
