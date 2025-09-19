"""Group service for collaborative donations."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.group import Group, GroupMembership


class GroupService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_group(
        self,
        *,
        name: str,
        description: str,
        target_amount: Decimal,
        fire_station_id: uuid.UUID,
        creator_id: uuid.UUID,
        invite_code: str,
        is_public: bool = True,
    ) -> Group:
        group = Group(
            name=name,
            description=description,
            target_amount=target_amount,
            fire_station_id=fire_station_id,
            creator_id=creator_id,
            invite_code=invite_code,
            is_public=is_public,
        )
        self._session.add(group)
        await self._session.flush()
        membership = GroupMembership(
            group_id=group.id,
            user_id=creator_id,
            role="creator",
        )
        self._session.add(membership)
        await self._session.flush()
        return group

    async def join_group(self, group_id: uuid.UUID, user_id: uuid.UUID) -> GroupMembership:
        membership = GroupMembership(group_id=group_id, user_id=user_id)
        self._session.add(membership)
        await self._session.flush()
        return membership

    async def list_groups(self, *, limit: int = 20) -> list[Group]:
        result = await self._session.execute(
            select(Group).order_by(Group.created_at.desc()).limit(limit)
        )
        return list(result.scalars())


__all__ = ["GroupService"]
