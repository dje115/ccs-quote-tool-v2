#!/usr/bin/env python3
"""
AI-assisted manual quote builder service.

Generates structured line items from natural language prompts and applies
them via the manual builder flow.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import json
import re
import textwrap
from typing import Any, Dict, List, Tuple

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import SessionLocal
from app.models.quotes import Quote, QuoteItem
from app.services.ai_provider_service import AIProviderService
from app.services.quote_manual_builder_service import (
    QuoteManualBuilderService,
    QuoteManualBuilderError,
)


class QuoteAIManualBuilderError(Exception):
    """Base error for AI manual builder failures."""


SYSTEM_PROMPT = textwrap.dedent(
    """
    You are QuoteBuilderAI, an expert solutions architect and estimator.
    Build complete manual quote line items for UK technology projects.

    Rules:
    1. Always answer with STRICT JSON using this schema (UTF-8, double quotes only):
       {
         "summary": "one paragraph overview",
         "assumptions": ["bullet", "..."],
         "items": [
           {
             "section": "Servers or Labour etc" | null,
             "category": "Hardware|Software|Licensing|Services|Labour|Support|Other",
             "description": "Detailed line item inc. make/model/spec",
             "quantity": number > 0,
             "unit_type": "each|hour|day|metre|package",
             "unit_cost": number >= 0,
             "unit_price": number >= unit_cost,
             "is_optional": boolean,
             "notes": "short optional notes"
           }
         ]
       }
    2. Monetary values must be in GBP excluding VAT. unit_price is customer sell price,
       unit_cost is estimated internal cost (≈80% of price unless user says otherwise).
    3. Provide 4‑12 high-quality items max. Group accessories sensibly.
    4. Prefer HP hardware/models when building server quotes, otherwise select credible UK-available products.
    5. Never include Markdown, code fences, commentary, or additional keys.
    """
).strip()


@dataclass
class AIGeneratedItem:
    """Lightweight representation of an AI generated line item."""

    section: str | None
    category: str | None
    description: str
    quantity: Decimal
    unit_type: str
    unit_cost: Decimal | None
    unit_price: Decimal
    is_optional: bool
    notes: str | None

    @property
    def total_price(self) -> Decimal:
        return self.quantity * self.unit_price


class QuoteAIManualBuilderService:
    """Encapsulates the AI quote building workflow."""

    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    async def build_items(
        self,
        quote_id: str,
        user_prompt: str,
        *,
        append: bool = False,
        target_margin_percent: float | None = None,
        tax_rate: float | None = None,
    ) -> Dict[str, Any]:
        """Generate line items from AI and apply them to the quote."""
        quote, existing_items = await self._load_quote_with_items(quote_id)
        context = self._build_context(quote, existing_items, user_prompt, target_margin_percent)

        sync_db = SessionLocal()
        try:
            ai_service = AIProviderService(sync_db, self.tenant_id)
            preferred_model = "gpt-5.1-mini"
            fallback_model = "gpt-4o-mini"
            try:
                ai_response = await ai_service.generate_with_rendered_prompts(
                    prompt=None,
                    system_prompt=SYSTEM_PROMPT,
                    user_prompt=context,
                    model=preferred_model,
                    temperature=0.1,
                    max_tokens=2200,
                    use_responses_api=True,
                )
            except Exception as exc:
                if fallback_model and self._should_fallback_to_gpt4(str(exc)):
                    ai_response = await ai_service.generate_with_rendered_prompts(
                        prompt=None,
                        system_prompt=SYSTEM_PROMPT,
                        user_prompt=context,
                        model=fallback_model,
                        temperature=0.1,
                        max_tokens=2000,
                        use_responses_api=False,
                    )
                else:
                    raise
        finally:
            sync_db.close()

        parsed = self._parse_ai_response(ai_response.content)
        ai_items = self._normalise_items(parsed.get("items", []))
        if not ai_items:
            raise QuoteAIManualBuilderError("AI response did not return any usable line items.")

        builder_payload = []
        sort_offset = 0

        if append and existing_items:
            builder_payload.extend(self._map_existing_items(existing_items))
            sort_offset = len(builder_payload)

        builder_payload.extend(
            self._map_generated_items(ai_items, start_index=sort_offset + 1)
        )

        manual_service = QuoteManualBuilderService(self.db, self.tenant_id)
        upsert_result = await manual_service.bulk_upsert_items(
            quote_id,
            builder_payload,
            tax_rate=tax_rate,
        )

        preview_items = [
            {
                "section": item.section,
                "description": item.description,
                "quantity": float(item.quantity),
                "unit_price": float(item.unit_price),
                "total_price": float(item.total_price),
                "is_optional": item.is_optional,
                "category": item.category,
                "notes": item.notes,
            }
            for item in ai_items
        ]

        return {
            "summary": parsed.get("summary", "AI generated a draft quote."),
            "assumptions": parsed.get("assumptions", []),
            "items_preview": preview_items,
            "items_added": len(ai_items),
            "append": append,
            "builder_result": upsert_result,
        }

    async def _load_quote_with_items(self, quote_id: str) -> Tuple[Quote, List[QuoteItem]]:
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

        items_stmt = (
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
        items_result = await self.db.execute(items_stmt)
        items = items_result.scalars().all()
        return quote, list(items)

    def _build_context(
        self,
        quote: Quote,
        existing_items: List[QuoteItem],
        user_prompt: str,
        target_margin_percent: float | None,
    ) -> str:
        lines: List[str] = []
        lines.append(
            f"Quote: {quote.title or quote.quote_number} "
            f"(type: {quote.quote_type or 'unspecified'}, manual mode: {quote.manual_mode})"
        )
        if quote.description:
            lines.append(f"Existing description: {quote.description.strip()}")
        lines.append(f"User request: {user_prompt.strip()}")
        if target_margin_percent is not None:
            lines.append(f"Target blended margin percent: {target_margin_percent:.1f}%")
        if existing_items:
            lines.append("Existing manual items (for awareness, do not duplicate):")
            for item in existing_items[:5]:
                lines.append(
                    f"- {item.section_name or 'General'} :: {item.description} "
                    f"(qty {item.quantity}, unit £{item.unit_price or 0})"
                )
            if len(existing_items) > 5:
                lines.append(f"- ...and {len(existing_items) - 5} more items.")
        return "\n".join(lines)

    def _parse_ai_response(self, raw_text: str) -> Dict[str, Any]:
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?", "", cleaned, count=1).strip()
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3].strip()
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        match = re.search(r"\{.*\}", raw_text, re.S)
        if match:
            try:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass
        raise QuoteAIManualBuilderError("AI response could not be parsed as JSON.")

    def _normalise_items(self, items: List[Dict[str, Any]]) -> List[AIGeneratedItem]:
        normalised: List[AIGeneratedItem] = []
        if not isinstance(items, list):
            return normalised

        for raw in items:
            description = (raw.get("description") or "").strip()
            if not description:
                continue
            quantity = self._to_decimal(raw.get("quantity"), default="1")
            if quantity <= 0:
                continue
            unit_price = self._to_decimal(raw.get("unit_price"), default="0")
            unit_cost = raw.get("unit_cost")
            if unit_cost is not None:
                unit_cost_decimal = self._to_decimal(unit_cost, default="0")
            else:
                unit_cost_decimal = unit_price * Decimal("0.8")
            item = AIGeneratedItem(
                section=(raw.get("section") or None),
                category=(raw.get("category") or None),
                description=description,
                quantity=quantity,
                unit_type=(raw.get("unit_type") or "each"),
                unit_cost=unit_cost_decimal,
                unit_price=unit_price,
                is_optional=bool(raw.get("is_optional", False)),
                notes=(raw.get("notes") or None),
            )
            normalised.append(item)

        return normalised[:25]

    def _map_generated_items(
        self, items: List[AIGeneratedItem], *, start_index: int
    ) -> List[Dict[str, Any]]:
        payload: List[Dict[str, Any]] = []
        for offset, item in enumerate(items):
            payload.append(
                {
                    "id": None,
                    "section_name": item.section,
                    "category": item.category,
                    "description": item.description,
                    "item_type": "standard",
                    "unit_type": item.unit_type or "each",
                    "quantity": float(item.quantity),
                    "unit_cost": float(item.unit_cost) if item.unit_cost is not None else None,
                    "unit_price": float(item.unit_price),
                    "discount_rate": 0,
                    "discount_amount": 0,
                    "is_optional": item.is_optional,
                    "is_alternate": False,
                    "alternate_group": None,
                    "bundle_parent_id": None,
                    "metadata": {},
                    "notes": item.notes,
                    "sort_order": start_index + offset,
                }
            )
        return payload

    def _map_existing_items(self, items: List[QuoteItem]) -> List[Dict[str, Any]]:
        payload: List[Dict[str, Any]] = []
        for index, item in enumerate(items, start=1):
            payload.append(
                {
                    "id": item.id,
                    "section_name": item.section_name,
                    "category": item.category,
                    "description": item.description,
                    "item_type": item.item_type or "standard",
                    "unit_type": item.unit_type or "each",
                    "quantity": float(item.quantity or 0),
                    "unit_cost": float(item.unit_cost) if item.unit_cost is not None else None,
                    "unit_price": float(item.unit_price or 0),
                    "discount_rate": float(item.discount_rate or 0),
                    "discount_amount": float(item.discount_amount or 0),
                    "is_optional": bool(item.is_optional),
                    "is_alternate": bool(item.is_alternate),
                    "alternate_group": item.alternate_group,
                    "bundle_parent_id": item.bundle_parent_id,
                    "metadata": item.item_metadata or {},
                    "notes": item.notes,
                    "sort_order": index,
                }
            )
        return payload

    @staticmethod
    def _to_decimal(value: Any, default: str = "0") -> Decimal:
        try:
            return Decimal(str(value))
        except Exception:
            return Decimal(default)

    @staticmethod
    def _should_fallback_to_gpt4(error_message: str) -> bool:
        lowered = (error_message or "").lower()
        keywords = [
            "model_not_found",
            "does not exist",
            "unsupported_model",
            "gpt-5",
        ]
        return any(keyword in lowered for keyword in keywords)
