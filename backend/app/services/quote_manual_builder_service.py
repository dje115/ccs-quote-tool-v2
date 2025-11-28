#!/usr/bin/env python3
"""
Manual quote builder service for spreadsheet-style editing.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quotes import Quote, QuoteItem


class QuoteManualBuilderError(Exception):
    """Base error for manual builder operations."""


class QuoteManualBuilderValidationError(QuoteManualBuilderError):
    """Raised when the payload fails validation."""


@dataclass
class QuoteItemDTO:
    """Internal DTO for quote items."""

    id: Optional[str]
    description: str
    category: Optional[str]
    item_type: Optional[str]
    unit_type: Optional[str]
    section_name: Optional[str]
    quantity: Decimal
    unit_cost: Optional[Decimal]
    unit_price: Decimal
    discount_rate: Decimal
    discount_amount: Decimal
    total_price: Decimal
    margin_percent: Optional[float]
    tax_rate: Optional[float]
    supplier_id: Optional[str]
    is_optional: bool
    is_alternate: bool
    alternate_group: Optional[str]
    bundle_parent_id: Optional[str]
    metadata: Optional[Dict[str, Any]]
    notes: Optional[str]
    sort_order: int

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["quantity"] = float(self.quantity)
        payload["unit_cost"] = float(self.unit_cost) if self.unit_cost is not None else None
        payload["unit_price"] = float(self.unit_price)
        payload["discount_rate"] = float(self.discount_rate)
        payload["discount_amount"] = float(self.discount_amount)
        payload["total_price"] = float(self.total_price)
        return payload


class QuoteManualBuilderService:
    """Service encapsulating manual quote builder logic."""

    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    async def bulk_upsert_items(
        self,
        quote_id: str,
        items_payload: List[Dict[str, Any]],
        *,
        tax_rate: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Replace/update quote items using spreadsheet-style payload.
        """
        if not items_payload:
            raise QuoteManualBuilderValidationError("Provide at least one line item.")

        quote = await self._get_quote(quote_id)
        existing_items = await self._get_existing_items(quote_id)
        existing_map = {item.id: item for item in existing_items}

        updated_items: List[QuoteItemDTO] = []
        subtotal = Decimal("0")

        for index, payload in enumerate(items_payload, start=1):
            dto = self._build_dto(payload, index)
            subtotal += dto.total_price

            item = existing_map.pop(dto.id, None) if dto.id else None
            if not item:
                item = QuoteItem(
                    id=dto.id or str(uuid.uuid4()),
                    tenant_id=self.tenant_id,
                    quote_id=quote.id,
                )
                self.db.add(item)

            self._apply_dto_to_item(item, dto)
            updated_items.append(dto)

        # Soft-delete any items not present in payload
        now = datetime.now(timezone.utc)
        for leftover in existing_map.values():
            leftover.is_deleted = True
            leftover.deleted_at = now

        # Update quote totals
        quote.manual_mode = True
        quote.subtotal = subtotal
        if tax_rate is not None:
            quote.tax_rate = float(tax_rate)

        effective_tax_rate = Decimal(str(quote.tax_rate or 0))
        quote.tax_amount = subtotal * effective_tax_rate
        quote.total_amount = subtotal + (quote.tax_amount or Decimal("0"))

        await self.db.commit()
        await self.db.refresh(quote)

        return {
            "success": True,
            "quote_id": quote.id,
            "subtotal": float(quote.subtotal or 0),
            "tax_rate": float(quote.tax_rate or 0),
            "tax_amount": float(quote.tax_amount or 0),
            "total_amount": float(quote.total_amount or 0),
            "item_count": len(updated_items),
            "items": [item.to_dict() for item in updated_items],
        }

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
            raise QuoteManualBuilderError("Quote not found.")
        return quote

    async def _get_existing_items(self, quote_id: str) -> List[QuoteItem]:
        stmt = (
            select(QuoteItem)
            .where(
                and_(
                    QuoteItem.quote_id == quote_id,
                    QuoteItem.tenant_id == self.tenant_id,
                    QuoteItem.is_deleted == False,  # noqa: E712
                )
            )
            .order_by(QuoteItem.sort_order.asc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    def _build_dto(self, payload: Dict[str, Any], sort_order: int) -> QuoteItemDTO:
        description = (payload.get("description") or "").strip()
        if not description:
            raise QuoteManualBuilderValidationError("Each item requires a description.")

        quantity = self._as_decimal(payload.get("quantity"), default="1")
        if quantity < 0:
            raise QuoteManualBuilderValidationError("Quantity must be zero or positive.")

        unit_price = self._as_decimal(payload.get("unit_price"), default="0")
        unit_cost = self._as_decimal(payload.get("unit_cost"), default=None)
        discount_rate = self._as_decimal(payload.get("discount_rate"), default="0")
        discount_amount = payload.get("discount_amount")
        if discount_amount is None:
            discount_amount = (quantity * unit_price * discount_rate)
        else:
            discount_amount = self._as_decimal(discount_amount, default="0")

        total_price = quantity * unit_price - discount_amount
        if total_price < 0:
            total_price = Decimal("0")

        dto = QuoteItemDTO(
            id=payload.get("id"),
            description=description,
            category=payload.get("category"),
            item_type=payload.get("item_type") or "standard",
            unit_type=payload.get("unit_type") or "each",
            section_name=payload.get("section_name"),
            quantity=quantity,
            unit_cost=unit_cost,
            unit_price=unit_price,
            discount_rate=discount_rate,
            discount_amount=discount_amount,
            total_price=total_price,
            margin_percent=payload.get("margin_percent"),
            tax_rate=payload.get("tax_rate"),
            supplier_id=payload.get("supplier_id"),
            is_optional=bool(payload.get("is_optional")),
            is_alternate=bool(payload.get("is_alternate")),
            alternate_group=payload.get("alternate_group"),
            bundle_parent_id=payload.get("bundle_parent_id"),
            metadata=payload.get("metadata"),
            notes=payload.get("notes"),
            sort_order=payload.get("sort_order") or sort_order,
        )
        return dto

    def _apply_dto_to_item(self, item: QuoteItem, dto: QuoteItemDTO) -> None:
        item.description = dto.description
        item.category = dto.category
        item.item_type = dto.item_type
        item.unit_type = dto.unit_type
        item.section_name = dto.section_name
        item.quantity = dto.quantity
        item.unit_cost = dto.unit_cost
        item.unit_price = dto.unit_price
        item.discount_rate = dto.discount_rate
        item.discount_amount = dto.discount_amount
        item.total_price = dto.total_price
        item.margin_percent = dto.margin_percent
        item.tax_rate = dto.tax_rate
        item.supplier_id = dto.supplier_id
        item.is_optional = dto.is_optional
        item.is_alternate = dto.is_alternate
        item.alternate_group = dto.alternate_group
        item.bundle_parent_id = dto.bundle_parent_id
        item.item_metadata = dto.metadata
        item.notes = dto.notes
        item.sort_order = dto.sort_order
        item.is_deleted = False
        item.deleted_at = None

    @staticmethod
    def _as_decimal(value: Any, default: Optional[str]) -> Decimal:
        if value is None:
            if default is None:
                return None  # type: ignore[return-value]
            return Decimal(default)
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError) as exc:  # pragma: no cover - defensive
            raise QuoteManualBuilderValidationError("Invalid numeric value provided.") from exc
