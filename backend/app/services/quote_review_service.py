#!/usr/bin/env python3
"""
Quote review service that leverages GPT-5 Mini via the Conversation API style prompt.
"""

from __future__ import annotations

from typing import List, Dict, Any, Tuple
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import SessionLocal
from app.models.quotes import Quote, QuoteItem
from app.models.crm import Customer
from app.models.ai_prompt import PromptCategory
from app.services.ai_provider_service import AIProviderService
from app.services.ai_prompt_service import AIPromptService

MASTER_PROMPT = """You are QuoteCheckAI, a highly experienced commercial quotation reviewer.

Your job is to analyse ANY quotation provided — regardless of industry, size, or complexity — and help the user improve it.

Your tasks:

1. Identify unclear, missing, or ambiguous information.
2. Detect pricing or scope inconsistencies, unrealistic claims, or risks.
3. Flag anything that could cause misunderstandings, disputes, or unexpected costs.
4. Highlight compliance or regulatory considerations (in a general way, not legal advice).
5. Suggest ways to improve structure, clarity, and professionalism.
6. Ask intelligent clarification questions when needed.
7. Provide optional improvements, alternative wording, or better layout.
8. Offer ideas the user may not have considered (upsells, options, alternative approaches).
9. Maintain a helpful and collaborative tone.
10. Avoid assuming industry unless stated by the user.

Important behavioural rules:
- Do NOT rewrite the entire quote unless explicitly asked.
- Do NOT change pricing unless the user asks for help costing it.
- Do NOT assume industry-specific details unless mentioned.
- Always explain WHY something is unclear or risky.
- Use short bullet points for clarity.
- Offer optional enhancements rather than forcing changes.

Output format:
1. Summary of your understanding
2. Issues, risks, or missing details
3. Questions for the user (if needed)
4. Suggested improvements
5. Optional: alternative structures or additional options

When appropriate, double-check high level math/consistency. If the user ever asks to rewrite professionally, provide a polished quote.
"""


class QuoteReviewService:
    """Encapsulates GPT-powered quote review logic."""

    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    async def _load_quote_with_items(self, quote_id: str) -> Tuple[Quote, List[QuoteItem], Customer | None]:
        quote_stmt = select(Quote).where(
            and_(
                Quote.id == quote_id,
                Quote.tenant_id == self.tenant_id,
                Quote.is_deleted == False  # noqa: E712
            )
        )
        quote_result = await self.db.execute(quote_stmt)
        quote = quote_result.scalar_one_or_none()
        if not quote:
            raise ValueError("Quote not found")

        items_stmt = select(QuoteItem).where(
            and_(
                QuoteItem.quote_id == quote.id,
                QuoteItem.tenant_id == self.tenant_id,
                QuoteItem.is_deleted == False  # noqa: E712
            )
        ).order_by(QuoteItem.sort_order.asc())
        items_result = await self.db.execute(items_stmt)
        items = items_result.scalars().all()

        customer = None
        if quote.customer_id:
            customer_stmt = select(Customer).where(
                and_(
                    Customer.id == quote.customer_id,
                    Customer.tenant_id == self.tenant_id,
                    Customer.is_deleted == False  # noqa: E712
                )
            )
            customer_result = await self.db.execute(customer_stmt)
            customer = customer_result.scalar_one_or_none()

        return quote, items, customer

    def _decimal_to_float(self, value: Decimal | None) -> float:
        if value is None:
            return 0.0
        return float(value)

    def _build_quote_context(
        self,
        quote: Quote,
        items: List[QuoteItem],
        customer: Customer | None,
        include_line_items: bool = True
    ) -> str:
        parts: List[str] = []
        parts.append(f"Quote: {quote.title} ({quote.quote_number})")
        parts.append(f"Status: {quote.status.value if hasattr(quote.status, 'value') else quote.status}")
        parts.append(f"Customer: {customer.company_name if customer else quote.customer_id or 'N/A'}")
        parts.append(f"Description: {quote.description or 'No description provided.'}")
        parts.append(
            f"Totals: subtotal £{self._decimal_to_float(quote.subtotal):,.2f}, "
            f"tax £{self._decimal_to_float(quote.tax_amount):,.2f}, "
            f"total £{self._decimal_to_float(quote.total_amount):,.2f}"
        )
        if quote.valid_until:
            parts.append(f"Valid until: {quote.valid_until.isoformat()}")
        if quote.notes:
            parts.append(f"Notes: {quote.notes}")

        if include_line_items:
            parts.append("\nLine Items:")
            if not items:
                parts.append("- No manual line items captured.")
            else:
                for idx, item in enumerate(items[:40], start=1):
                    line = (
                        f"{idx}. {item.description} | qty {float(item.quantity or 0)} {item.unit_type or ''} | "
                        f"price £{self._decimal_to_float(item.unit_price):,.2f} | "
                        f"line total £{self._decimal_to_float(item.total_price):,.2f}"
                    )
                    if item.section_name:
                        line += f" | section: {item.section_name}"
                    if item.is_optional:
                        line += " | OPTIONAL"
                    if item.is_alternate:
                        line += f" | ALTERNATE group {item.alternate_group or ''}"
                    parts.append(line)

                if len(items) > 40:
                    parts.append(f"... {len(items) - 40} additional items not shown ...")

        return "\n".join(parts)

    async def run_review(
        self,
        quote_id: str,
        messages: List[Dict[str, str]],
        include_line_items: bool = True,
        model: str = "gpt-5.1-mini"
    ) -> Dict[str, Any]:
        quote, items, customer = await self._load_quote_with_items(quote_id)
        context_block = self._build_quote_context(quote, items, customer, include_line_items=include_line_items)

        conversation_snippets = [f"[QUOTE DATA]\n{context_block}\n"]
        for msg in messages:
            role = msg.get("role", "user").upper()
            conversation_snippets.append(f"{role}: {msg.get('content', '')}")
        user_prompt = "\n\n".join(conversation_snippets)

        sync_db = SessionLocal()
        try:
            prompt_service = AIPromptService(sync_db, tenant_id=self.tenant_id)
            prompt_obj = await prompt_service.get_prompt(
                PromptCategory.MANUAL_QUOTE_REVIEW.value,
                tenant_id=self.tenant_id
            )
            system_prompt = prompt_obj.system_prompt if prompt_obj and prompt_obj.system_prompt else MASTER_PROMPT

            ai_service = AIProviderService(sync_db, self.tenant_id)
            requested_model = model or "gpt-5.1-mini"
            lower_requested = requested_model.lower()
            # GPT-5.1 miniature models are not yet available on chat/responses APIs in this environment.
            # Fall back to the widely-available GPT-4o Mini so the feature still works.
            effective_model = "gpt-4o-mini" if lower_requested.startswith("gpt-5") else requested_model
            lower_model = effective_model.lower()
            use_responses_api = lower_requested.startswith(("gpt-5", "gpt-4.1", "o1", "o3"))
            ai_response = await ai_service.generate_with_rendered_prompts(
                prompt=prompt_obj,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=effective_model,
                temperature=0.2,
                max_tokens=2000,
                use_responses_api=use_responses_api
            )

            return {
                "message": ai_response.content,
                "model": ai_response.model,
                "usage": ai_response.usage,
                "context": context_block
            }
        finally:
            sync_db.close()
