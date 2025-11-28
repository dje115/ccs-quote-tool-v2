#!/usr/bin/env python3
"""
Quote workflow & status transition service.

Responsibilities:
- Validate lifecycle transitions
- Update timestamp fields on Quote
- Persist workflow log entries
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional, Dict
from uuid import uuid4

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quotes import Quote, QuoteStatus, QuoteWorkflowLog

logger = logging.getLogger(__name__)


class QuoteWorkflowError(Exception):
    """Base class for workflow issues."""


class QuoteNotFoundError(QuoteWorkflowError):
    """Raised when a quote cannot be located for the tenant."""


class InvalidStatusTransitionError(QuoteWorkflowError):
    """Raised when a status transition isn't allowed."""


class QuoteWorkflowService:
    """Encapsulates workflow operations for quotes."""

    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

        self.allowed_transitions: Dict[QuoteStatus, set[QuoteStatus]] = {
            QuoteStatus.DRAFT: {
                QuoteStatus.SENT,
                QuoteStatus.CANCELLED,
            },
            QuoteStatus.SENT: {
                QuoteStatus.VIEWED,
                QuoteStatus.ACCEPTED,
                QuoteStatus.REJECTED,
                QuoteStatus.CANCELLED,
                QuoteStatus.EXPIRED,
            },
            QuoteStatus.VIEWED: {
                QuoteStatus.ACCEPTED,
                QuoteStatus.REJECTED,
                QuoteStatus.CANCELLED,
            },
            QuoteStatus.ACCEPTED: {
                QuoteStatus.CANCELLED,
            },
            QuoteStatus.REJECTED: set(),
            QuoteStatus.EXPIRED: set(),
            QuoteStatus.CANCELLED: set(),
        }

    async def change_status(
        self,
        quote_id: str,
        new_status: QuoteStatus,
        *,
        user_id: str,
        action: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> Quote:
        """
        Change the quote status and record the workflow log.
        """
        quote = await self._get_quote(quote_id)
        if quote.status == new_status:
            logger.info(
                "Quote %s already in status %s. Ignoring transition.",
                quote_id,
                new_status,
            )
            return quote

        if new_status not in self.allowed_transitions.get(quote.status, set()):
            raise InvalidStatusTransitionError(
                f"Cannot transition from {quote.status.value} to {new_status.value}"
            )

        await self._apply_status_side_effects(quote, new_status, comment=comment)

        await self._log_transition(
            quote=quote,
            from_status=quote.status,
            to_status=new_status,
            user_id=user_id,
            action=action,
            comment=comment,
        )

        quote.status = new_status
        await self.db.commit()
        await self.db.refresh(quote)
        return quote

    async def get_workflow_log(self, quote_id: str) -> list[QuoteWorkflowLog]:
        """
        Return workflow log entries for a quote ordered by creation time DESC.
        """
        stmt = (
            select(QuoteWorkflowLog)
            .where(
                and_(
                    QuoteWorkflowLog.quote_id == quote_id,
                    QuoteWorkflowLog.tenant_id == self.tenant_id,
                    QuoteWorkflowLog.is_deleted == False,  # noqa: E712
                )
            )
            .order_by(QuoteWorkflowLog.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def _get_quote(self, quote_id: str) -> Quote:
        stmt = select(Quote).where(
            and_(
                Quote.id == quote_id,
                Quote.tenant_id == self.tenant_id,
                Quote.is_deleted == False,  # noqa: E712
            )
        )
        result = await self.db.execute(stmt)
        quote = result.scalar_one_or_none()
        if not quote:
            raise QuoteNotFoundError(f"Quote {quote_id} not found")
        return quote

    async def _log_transition(
        self,
        *,
        quote: Quote,
        from_status: QuoteStatus,
        to_status: QuoteStatus,
        user_id: str,
        action: Optional[str],
        comment: Optional[str],
    ) -> None:
        log_entry = QuoteWorkflowLog(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            quote_id=quote.id,
            from_status=from_status.value if from_status else None,
            to_status=to_status.value,
            action=action or "status_change",
            comment=comment,
            created_by=user_id,
        )
        self.db.add(log_entry)

    async def _apply_status_side_effects(
        self,
        quote: Quote,
        new_status: QuoteStatus,
        *,
        comment: Optional[str],
    ) -> None:
        """
        Update timestamps + counters related to lifecycle changes.
        """
        now = datetime.now(timezone.utc)

        if new_status == QuoteStatus.SENT:
            quote.sent_at = now
        elif new_status == QuoteStatus.VIEWED:
            quote.viewed_at = now
            quote.viewed_count = (quote.viewed_count or 0) + 1
        elif new_status == QuoteStatus.ACCEPTED:
            quote.accepted_at = now
        elif new_status == QuoteStatus.REJECTED:
            quote.rejected_at = now
        elif new_status == QuoteStatus.CANCELLED:
            quote.cancelled_at = now
            if comment:
                quote.cancel_reason = comment
        elif new_status == QuoteStatus.EXPIRED:
            quote.cancelled_at = now
