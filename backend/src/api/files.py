"""File upload API."""

from __future__ import annotations

import uuid

from fastapi import APIRouter

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/presign")
async def create_presigned_url(payload: dict) -> dict:
    return {
        "upload_url": f"https://s3.example.com/uploads/{uuid.uuid4()}",
        "fields": {"policy": "dummy"},
    }


__all__ = ["router"]
