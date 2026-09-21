"""Entry point FastAPI.

Chạy (khuyến nghị, auto-reload khi sửa code):
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

Hoặc chạy trực tiếp:
    python main.py
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.api.routes import router
from src.utils.config import get_app_host, get_app_port

app = FastAPI(title="Vessel Chatbot API")
app.include_router(router)  # dang ky truoc StaticFiles de /conversations, /health khong bi static che

WEB_DIR = Path(__file__).resolve().parent / "web"
if WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=get_app_host(), port=get_app_port())
