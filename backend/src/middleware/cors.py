"""CORS configuration helper."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

ALLOWED_ORIGINS = [
    "https://app.bodam.example",
    "http://localhost:3000",
    "https://frontend-sigma-pearl-65.vercel.app",
    "https://bodam.website",
    "https://www.bodam.website",
]


def setup_cors(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


__all__ = ["setup_cors"]
