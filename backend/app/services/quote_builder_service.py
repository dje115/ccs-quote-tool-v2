#!/usr/bin/env python3
"""
Quote Builder Service

Orchestrates the creation of quotes with all document types:
- Parts list quote
- Technical document
- Overview document
- Build document

Uses AI generation service and creates Quote + QuoteDocument records.
"""

import logging
import json
import uuid
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.quotes import Quote, QuoteItem, QuoteStatus
from app.models.quote_documents import QuoteDocument, DocumentType
from app.models.quote_prompt_history import QuotePromptHistory
from app.models.crm import Customer
from app.models.leads import Lead
from app.services.quote_ai_generation_service import QuoteAIGenerationService

logger = logging.getLogger(__name__)


class QuoteBuilderService:
    """
    Service for building complete quotes with all document types
    
    Features:
    - AI-powered quote generation
    - Multi-part document creation
    - Pricing integration
    - Versioning support
    """
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.ai_service = QuoteAIGenerationService(db, tenant_id)
    
    async def build_quote(
        self,
        customer_request: str,
        quote_title: str,
        customer_id: Optional[str] = None,
        lead_id: Optional[str] = None,
        quote_type: Optional[str] = None,
        required_deadline: Optional[str] = None,
        location: Optional[str] = None,
        quantity: Optional[int] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build a complete quote with all document types
        
        Args:
            customer_id: Customer ID (if quote is for existing customer)
            lead_id: Lead ID (if quote is for lead)
            customer_request: Plain English description of what the client wants
            quote_title: Title for the quote
            quote_type: Type of quote (e.g., 'cabling', 'network_build')
            required_deadline: Required deadline
            location: Project location
            quantity: Quantity if applicable
            user_id: User creating the quote
        
        Returns:
            Dict with created quote and documents
        """
        try:
            # Validate customer or lead exists
            if customer_id:
                customer = self.db.query(Customer).filter(
                    Customer.id == customer_id,
                    Customer.tenant_id == self.tenant_id
                ).first()
                if not customer:
                    return {"success": False, "error": "Customer not found"}
            
            if lead_id:
                lead = self.db.query(Lead).filter(
                    Lead.id == lead_id,
                    Lead.tenant_id == self.tenant_id
                ).first()
                if not lead:
                    return {"success": False, "error": "Lead not found"}
            
            # 1. Generate quote using AI
            ai_result = await self.ai_service.generate_quote(
                customer_request=customer_request,
                required_deadline=required_deadline,
                location=location,
                quantity=quantity,
                user_id=user_id
            )
            
            if not ai_result.get("success"):
                return {"success": False, "error": ai_result.get("error", "AI generation failed")}
            
            quote_data = ai_result["quote_data"]
            tier_type = quote_data.get("quote_type", "single")
            prompt_metadata = quote_data.get("_prompt_metadata", {})
            
            # 2. Generate quote number
            quote_number = self._generate_quote_number()
            
            # 3. Create Quote record
            quote = Quote(
                id=str(uuid.uuid4()),
                tenant_id=self.tenant_id,
                customer_id=customer_id,
                lead_id=lead_id,
                quote_number=quote_number,
                title=quote_title,
                description=customer_request,
                quote_type=quote_type,
                tier_type=tier_type,
                status=QuoteStatus.DRAFT,
                ai_generation_data=quote_data.get("ai_generation_data"),
                created_by=user_id
            )
            
            # Store last prompt text on quote
            if prompt_metadata.get("prompt_text"):
                quote.last_prompt_text = prompt_metadata["prompt_text"]
            
            # 4. Calculate pricing and create quote items
            # Extract pricing from quote_data
            pricing_result = self._extract_pricing_from_quote_data(quote_data)
            
            quote.subtotal = pricing_result.get("subtotal", 0)
            quote.tax_amount = pricing_result.get("tax_amount", 0)
            quote.total_amount = pricing_result.get("total_amount", 0)
            
            # Create quote items
            for item_data in pricing_result.get("items", []):
                quote_item = QuoteItem(
                    id=str(uuid.uuid4()),
                    tenant_id=self.tenant_id,
                    quote_id=quote.id,
                    description=item_data.get("description", ""),
                    category=item_data.get("category"),
                    quantity=item_data.get("quantity", 1),
                    unit_price=item_data.get("unit_price", 0),
                    total_price=item_data.get("total_price", 0),
                    sort_order=item_data.get("sort_order", 0)
                )
                self.db.add(quote_item)
            
            self.db.add(quote)
            self.db.flush()
            
            # 4.5. Save prompt history
            if prompt_metadata:
                # Clean quote_data to remove any circular references before storing
                quote_data_for_history = prompt_metadata.get("generated_quote_data", {})
                if quote_data_for_history:
                    # Convert to JSON string and back to ensure it's serializable
                    try:
                        quote_data_json = json.dumps(quote_data_for_history, default=str)
                        quote_data_for_history = json.loads(quote_data_json)
                    except (TypeError, ValueError) as e:
                        logger.warning(f"Could not serialize quote_data for history: {e}")
                        # Store a simplified version instead
                        quote_data_for_history = {
                            "quote_type": quote_data.get("quote_type"),
                            "industry_detected": quote_data.get("industry_detected"),
                            "ai_generation_data": quote_data.get("ai_generation_data")
                        }
                
                prompt_history = QuotePromptHistory(
                    id=str(uuid.uuid4()),
                    tenant_id=self.tenant_id,
                    quote_id=quote.id,
                    prompt_text=prompt_metadata.get("prompt_text", ""),
                    prompt_variables=prompt_metadata.get("prompt_variables", {}),
                    ai_model=prompt_metadata.get("ai_model"),
                    ai_provider=prompt_metadata.get("ai_provider"),
                    temperature=float(prompt_metadata.get("temperature")) if prompt_metadata.get("temperature") else None,
                    max_tokens=prompt_metadata.get("max_tokens"),
                    generation_successful=prompt_metadata.get("generation_successful", True),
                    generated_quote_data=quote_data_for_history,
                    created_by=user_id
                )
                self.db.add(prompt_history)
            
            # 5. Create document types
            documents = []
            
            # Parts List Document
            parts_list_doc = self._create_document(
                quote=quote,
                document_type=DocumentType.PARTS_LIST.value,
                content=self._build_parts_list_content(quote_data, pricing_result),
                user_id=user_id
            )
            documents.append(parts_list_doc)
            
            # Technical Document
            technical_doc = self._create_document(
                quote=quote,
                document_type=DocumentType.TECHNICAL.value,
                content=self._build_technical_content(quote_data),
                user_id=user_id
            )
            documents.append(technical_doc)
            
            # Overview Document
            overview_doc = self._create_document(
                quote=quote,
                document_type=DocumentType.OVERVIEW.value,
                content=self._build_overview_content(quote_data),
                user_id=user_id
            )
            documents.append(overview_doc)
            
            # Build Document
            build_doc = self._create_document(
                quote=quote,
                document_type=DocumentType.BUILD.value,
                content=self._build_build_content(quote_data, pricing_result),
                user_id=user_id
            )
            documents.append(build_doc)
            
            self.db.commit()
            self.db.refresh(quote)
            
            return {
                "success": True,
                "quote": quote,
                "documents": documents,
                "quote_data": quote_data
            }
        
        except Exception as e:
            logger.error(f"Error building quote: {e}", exc_info=True)
            self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    def _extract_pricing_from_quote_data(self, quote_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract pricing information from AI-generated quote data"""
        items = []
        subtotal = 0.0
        
        def safe_float(value, default=0.0):
            """Safely convert value to float, handling strings and None"""
            if value is None:
                return default
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                try:
                    return float(value.replace(',', '').strip())
                except (ValueError, AttributeError):
                    return default
            return default
        
        # Extract pricing from tiers or single quote
        if quote_data.get("quote_type") == "three_tier":
            # Use tier 2 (standard) as default pricing
            tier_2 = quote_data.get("tiers", {}).get("tier_2", {})
            pricing_breakdown = tier_2.get("pricing_breakdown", {})
        else:
            pricing_breakdown = quote_data.get("single_quote", {}).get("pricing_breakdown", {})
        
        # Extract labour items
        labour_items = pricing_breakdown.get("labour", {}).get("items", [])
        for item in labour_items:
            total_price = safe_float(item.get("total", 0))
            items.append({
                "description": item.get("description", ""),
                "part_number": item.get("part_number", ""),
                "category": "Labour",
                "quantity": safe_float(item.get("hours", 1)),
                "unit_price": safe_float(item.get("rate", 0)),
                "cost_price": safe_float(item.get("cost_price", item.get("rate", 0))),
                "total_price": total_price,
                "supplier": item.get("supplier", ""),
                "notes": item.get("notes", ""),
                "sort_order": len(items)
            })
            subtotal += total_price
        
        # Extract material items
        material_items = pricing_breakdown.get("materials", {}).get("items", [])
        for item in material_items:
            total_price = safe_float(item.get("total", 0))
            items.append({
                "description": item.get("description", ""),
                "part_number": item.get("part_number", ""),
                "category": "Materials",
                "quantity": safe_float(item.get("quantity", 1)),
                "unit_price": safe_float(item.get("unit_price", 0)),
                "cost_price": safe_float(item.get("cost_price", item.get("unit_price", 0))),
                "total_price": total_price,
                "supplier": item.get("supplier", ""),
                "notes": item.get("notes", ""),
                "sort_order": len(items)
            })
            subtotal += total_price
        
        tax_rate = 0.20  # 20% VAT default
        tax_amount = subtotal * tax_rate
        total_amount = subtotal + tax_amount
        
        return {
            "success": True,
            "items": items,
            "subtotal": subtotal,
            "tax_rate": tax_rate,
            "tax_amount": tax_amount,
            "total_amount": total_amount,
            "parts_list": items  # For parts list document
        }
    
    def _create_document(
        self,
        quote: Quote,
        document_type: str,
        content: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> QuoteDocument:
        """Create a quote document"""
        document = QuoteDocument(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            quote_id=quote.id,
            document_type=document_type,
            content=content,
            version=1,
            created_by=user_id
        )
        
        self.db.add(document)
        return document
    
    def _build_parts_list_content(
        self,
        quote_data: Dict[str, Any],
        pricing_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build parts list document content with line items"""
        items = pricing_result.get("items", [])
        
        # Format line items with all required fields
        line_items = []
        for idx, item in enumerate(items, 1):
            line_items.append({
                "id": f"item_{idx}",
                "line_number": idx,
                "description": item.get("description", ""),
                "part_number": item.get("part_number", ""),
                "quantity": float(item.get("quantity", 1)),
                "unit_price": float(item.get("unit_price", 0)),
                "cost_price": float(item.get("cost_price", item.get("unit_price", 0))),  # Default to unit_price if no cost_price
                "total_price": float(item.get("total_price", 0)),
                "category": item.get("category", ""),
                "supplier": item.get("supplier", ""),
                "notes": item.get("notes", "")
            })
        
        return {
            "line_items": line_items,
            "pricing_summary": {
                "subtotal": float(pricing_result.get("subtotal", 0)),
                "tax_rate": float(pricing_result.get("tax_rate", 20)),
                "tax_amount": float(pricing_result.get("tax_amount", 0)),
                "total_amount": float(pricing_result.get("total_amount", 0))
            },
            "metadata": {
                "generated_by": "ai",
                "document_type": "parts_list",
                "item_count": len(line_items),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        }
    
    def _build_technical_content(self, quote_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build technical document content"""
        sow = quote_data.get("statement_of_work", {})
        
        return {
            "sections": [
                {
                    "id": "technical_specs",
                    "title": "Technical Specifications",
                    "content": quote_data.get("technical_specifications", ""),
                    "order": 1
                },
                {
                    "id": "deliverables",
                    "title": "Deliverables",
                    "content": sow.get("deliverables", []),
                    "order": 2
                },
                {
                    "id": "requirements",
                    "title": "Technical Requirements",
                    "content": quote_data.get("technical_requirements", ""),
                    "order": 3
                }
            ],
            "metadata": {
                "generated_by": "ai",
                "document_type": "technical"
            }
        }
    
    def _build_overview_content(self, quote_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build overview document content"""
        return {
            "sections": [
                {
                    "id": "executive_summary",
                    "title": "Executive Summary",
                    "content": quote_data.get("executive_summary", ""),
                    "order": 1
                },
                {
                    "id": "tiers",
                    "title": "Solution Options",
                    "content": quote_data.get("tiers", {}),
                    "order": 2
                },
                {
                    "id": "benefits",
                    "title": "Key Benefits",
                    "content": quote_data.get("key_benefits", []),
                    "order": 3
                }
            ],
            "metadata": {
                "generated_by": "ai",
                "document_type": "overview"
            }
        }
    
    def _build_build_content(
        self,
        quote_data: Dict[str, Any],
        pricing_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build internal build document content"""
        sow = quote_data.get("statement_of_work", {})
        
        return {
            "sections": [
                {
                    "id": "build_instructions",
                    "title": "Build Instructions",
                    "content": quote_data.get("build_instructions", ""),
                    "order": 1
                },
                {
                    "id": "resource_requirements",
                    "title": "Resource Requirements",
                    "content": pricing_result.get("resource_requirements", {}),
                    "order": 2
                },
                {
                    "id": "timeline",
                    "title": "Timeline and Milestones",
                    "content": sow.get("timescales", ""),
                    "order": 3
                },
                {
                    "id": "dependencies",
                    "title": "Dependencies and Prerequisites",
                    "content": quote_data.get("dependencies", []),
                    "order": 4
                }
            ],
            "metadata": {
                "generated_by": "ai",
                "document_type": "build",
                "internal_only": True
            }
        }
    
    def _generate_quote_number(self) -> str:
        """Generate unique quote number"""
        from datetime import datetime
        prefix = "QT"
        timestamp = datetime.now().strftime("%Y%m%d")
        # Get count of quotes today for sequence number
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        count = self.db.query(Quote).filter(
            Quote.tenant_id == self.tenant_id,
            Quote.created_at >= today_start
        ).count()
        sequence = str(count + 1).zfill(4)
        return f"{prefix}-{timestamp}-{sequence}"

