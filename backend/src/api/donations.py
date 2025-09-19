"""Donation-related API endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Response, status
from pydantic import BaseModel, Field

router = APIRouter(tags=["donations"])


class DonationCreateRequest(BaseModel):
    fire_station_id: uuid.UUID
    amount: int = Field(..., ge=1000)
    type: str = Field(..., pattern="^(one_time|recurring)$")
    frequency: str | None = Field(default=None, pattern="^(monthly|yearly)$")
    message: str | None = Field(default=None, max_length=500)
    is_anonymous: bool = False


@router.get("/donations")
async def list_donations(page: int = 1, limit: int = 20, status_filter: str | None = None) -> dict:
    donation_id = uuid.uuid4()
    return {
        "donations": [
            {
                "id": str(donation_id),
                "amount": 20000,
                "type": "one_time",
                "status": status_filter or "pending",
                "fire_station": {
                    "id": str(uuid.uuid4()),
                    "name": "강남소방서",
                    "region": "서울",
                },
                "created_at": datetime.utcnow().isoformat() + "Z",
            }
        ],
        "total": 1,
        "page": page,
        "limit": limit,
    }


@router.post("/donations", status_code=status.HTTP_201_CREATED)
async def create_donation(payload: DonationCreateRequest) -> dict:
    donation_id = uuid.uuid4()
    order_id = f"bodam-{donation_id}"
    return {
        "donation_id": str(donation_id),
        "payment_url": "https://pay.toss.im/checkout",
        "order_id": order_id,
    }


@router.get("/donations/{donation_id}")
async def get_donation(donation_id: uuid.UUID) -> dict:
    return {
        "id": str(donation_id),
        "status": "pending",
        "payment_method": "card",
        "fire_station": {
            "id": str(uuid.uuid4()),
            "name": "강남소방서",
        },
    }


@router.get("/donations/{donation_id}/receipt")
async def get_receipt(donation_id: uuid.UUID) -> Response:
    pdf_bytes = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    headers = {"Content-Disposition": f"attachment; filename=receipt-{donation_id}.pdf"}
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


@router.post("/donations/{donation_id}/refund", status_code=status.HTTP_201_CREATED)
async def request_refund(donation_id: uuid.UUID, payload: dict) -> dict:
    return {
        "refund_id": str(uuid.uuid4()),
        "status": "pending_review",
        "message": "환불 요청이 접수되었습니다",
    }


@router.get("/subscriptions")
async def list_subscriptions() -> dict:
    return {
        "subscriptions": [
            {
                "id": str(uuid.uuid4()),
                "amount": 15000,
                "frequency": "monthly",
                "status": "active",
                "next_payment_date": datetime.utcnow().date().isoformat(),
            }
        ]
    }


@router.post("/subscriptions")
async def create_subscription(payload: dict) -> dict:
    return {
        "subscription_id": str(uuid.uuid4()),
        "status": "active",
    }


@router.post("/subscriptions/{subscription_id}/cancel")
async def cancel_subscription(subscription_id: uuid.UUID) -> dict:
    return {"message": "정기결제가 취소되었습니다"}


__all__ = ["router"]
