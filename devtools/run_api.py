from pathlib import Path

import uvicorn


def main() -> None:
    """Run FastAPI with reload; `app` package resolves under apps/api."""
    root = Path(__file__).resolve().parents[1]
    app_dir = root / "apps" / "api"
    uvicorn.run(
        "app.main:app",
        app_dir=str(app_dir),
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
