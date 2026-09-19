"""Entry point FastAPI.

Chạy (khuyến nghị, auto-reload khi sửa code):
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

Hoặc chạy trực tiếp:
    python main.py
"""

from __future__ import annotations

from fastapi import FastAPI

from src.api.routes import router
from src.utils.config import get_app_host, get_app_port

app = FastAPI(title="Vessel Chatbot API")
app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=get_app_host(), port=get_app_port())
