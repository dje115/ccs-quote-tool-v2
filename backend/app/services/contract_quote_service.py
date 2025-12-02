#!/usr/bin/env python3
"""
Contract to Quote Generation Service
Generates quotes and proposals from contract data
"""

import json
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.services.quote_builder_service import QuoteBuilderService
from app.models.support_contract import SupportContract
from app.models.contracts import Contract


class ContractQuoteService:
    """Service for generating quotes and proposals from contract data"""
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.quote_builder = QuoteBuilderService(db, tenant_id)
    
    async def generate_quote_from_contract(
        self,
        contract_data: Dict[str, Any],
        contract_type: str = "support_contract",  # "support_contract" or "regular_contract"
        generate_proposal: bool = True,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a quote and proposal from contract data
        
        Args:
            contract_data: Contract data dictionary with all contract fields
            contract_type: Type of contract ("support_contract" or "regular_contract")
            generate_proposal: Whether to generate a proposal document
            user_id: User ID creating the quote
        
        Returns:
            Dict with created quote and documents
        """
        try:
            # Build customer request description from contract data
            customer_request = self._build_customer_request_from_contract(contract_data, contract_type)
            
            # Build quote title
            quote_title = f"{contract_data.get('contract_name', 'Contract')} - Quote & Proposal"
            
            # Generate quote using QuoteBuilderService
            result = await self.quote_builder.build_quote(
                customer_request=customer_request,
                quote_title=quote_title,
                customer_id=contract_data.get('customer_id'),
                quote_type=self._map_contract_type_to_quote_type(contract_data.get('contract_type')),
                required_deadline=self._calculate_valid_until(contract_data),
                location=None,  # Could extract from customer data if available
                quantity=None,
                user_id=user_id
            )
            
            if not result.get("success"):
                return result
            
            quote = result["quote"]
            
            # If proposal requested, enhance the overview document to be more proposal-like
            if generate_proposal:
                # Enhance overview document with contract-specific proposal content
                await self._enhance_proposal_document(quote, contract_data, result.get("documents", []))
            
            return {
                "success": True,
                "quote": quote,
                "quote_id": quote.id,
                "quote_number": quote.quote_number,
                "documents": result.get("documents", [])
            }
            
        except Exception as e:
            print(f"Error generating quote from contract: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }
    
    def _build_customer_request_from_contract(
        self,
        contract_data: Dict[str, Any],
        contract_type: str
    ) -> str:
        """Build a customer request description from contract data"""
        parts = []
        
        # Contract name and type
        contract_name = contract_data.get('contract_name', 'Contract')
        contract_type_str = contract_data.get('contract_type', '').replace('_', ' ').title()
        parts.append(f"Request for {contract_type_str}: {contract_name}")
        
        # Description
        if contract_data.get('description'):
            parts.append(f"\nDescription: {contract_data.get('description')}")
        
        # Pricing
        if contract_data.get('annual_value'):
            parts.append(f"\nAnnual Value: £{contract_data.get('annual_value'):,.2f}")
        elif contract_data.get('monthly_value'):
            parts.append(f"\nMonthly Value: £{contract_data.get('monthly_value'):,.2f} (Annual: £{float(contract_data.get('monthly_value', 0)) * 12:,.2f})")
        
        if contract_data.get('setup_fee'):
            parts.append(f"Setup Fee: £{contract_data.get('setup_fee'):,.2f}")
        
        # SLA Requirements
        if contract_data.get('sla_level'):
            parts.append(f"\nSLA Requirements: {contract_data.get('sla_level')}")
        
        if contract_data.get('support_hours_included'):
            parts.append(f"Support Hours Included: {contract_data.get('support_hours_included')} hours")
        
        # Renewal Terms
        if contract_data.get('renewal_frequency'):
            renewal_freq = contract_data.get('renewal_frequency', '').replace('_', ' ').title()
            parts.append(f"\nRenewal: {renewal_freq}")
            if contract_data.get('auto_renew'):
                parts.append("Auto-renewal: Enabled")
        
        # Terms and Conditions
        if contract_data.get('terms'):
            parts.append(f"\nTerms & Conditions:\n{contract_data.get('terms')[:500]}...")  # First 500 chars
        
        # Dates
        if contract_data.get('start_date'):
            parts.append(f"\nContract Start Date: {contract_data.get('start_date')}")
        if contract_data.get('end_date'):
            parts.append(f"Contract End Date: {contract_data.get('end_date')}")
        
        return "\n".join(parts)
    
    def _map_contract_type_to_quote_type(self, contract_type: Optional[str]) -> Optional[str]:
        """Map contract type to quote type"""
        if not contract_type:
            return None
        
        mapping = {
            "managed_services": "managed_services",
            "software_license": "software",
            "saas_subscription": "saas",
            "maintenance": "maintenance",
            "support_hours": "support",
            "consulting": "consulting",
            "warranty": "warranty"
        }
        
        return mapping.get(contract_type)
    
    def _calculate_valid_until(self, contract_data: Dict[str, Any]) -> Optional[str]:
        """Calculate quote valid until date (typically 30 days from now)"""
        valid_until = datetime.now() + timedelta(days=30)
        return valid_until.isoformat()
    
    async def _enhance_proposal_document(
        self,
        quote,
        contract_data: Dict[str, Any],
        documents: List
    ):
        """Enhance overview document with contract-specific proposal content"""
        from app.models.quote_documents import QuoteDocument, DocumentType
        
        # Find overview document
        overview_doc = None
        for doc in documents:
            if doc.document_type == DocumentType.OVERVIEW.value:
                overview_doc = doc
                break
        
        if overview_doc:
            # Enhance content with contract terms
            content = overview_doc.content or {}
            sections = content.get("sections", [])
            
            # Add contract-specific section
            contract_section = {
                "id": "contract_terms",
                "title": "Contract Terms & Conditions",
                "content": self._format_contract_terms_for_proposal(contract_data),
                "order": len(sections) + 1
            }
            sections.append(contract_section)
            
            content["sections"] = sections
            overview_doc.content = content
            self.db.commit()
    
    def _format_contract_terms_for_proposal(self, contract_data: Dict[str, Any]) -> str:
        """Format contract terms for inclusion in proposal document"""
        terms_parts = []
        
        if contract_data.get('sla_level'):
            terms_parts.append(f"**Service Level Agreement:** {contract_data.get('sla_level')}")
        
        if contract_data.get('renewal_frequency'):
            renewal_freq = contract_data.get('renewal_frequency', '').replace('_', ' ').title()
            terms_parts.append(f"**Renewal Frequency:** {renewal_freq}")
            if contract_data.get('auto_renew'):
                terms_parts.append("**Auto-Renewal:** Enabled")
        
        if contract_data.get('support_hours_included'):
            terms_parts.append(f"**Support Hours Included:** {contract_data.get('support_hours_included')} hours")
        
        if contract_data.get('cancellation_notice_days'):
            terms_parts.append(f"**Cancellation Notice:** {contract_data.get('cancellation_notice_days')} days")
        
        if contract_data.get('terms'):
            terms_parts.append(f"\n**Full Terms & Conditions:**\n{contract_data.get('terms')[:1000]}...")
        
        return "\n\n".join(terms_parts) if terms_parts else "Standard contract terms apply."
    
    def _map_contract_type_to_quote_data(
        self,
        contract_data: Dict[str, Any],
        contract_type: str
    ) -> Dict[str, Any]:
        """Map contract data to quote data structure for better AI generation"""
        quote_data = {
            "contract_type": contract_type,
            "contract_name": contract_data.get('contract_name'),
            "description": contract_data.get('description'),
            "pricing": {}
        }
        
        # Map pricing
        if contract_data.get('annual_value'):
            quote_data["pricing"]["annual"] = float(contract_data.get('annual_value', 0))
        elif contract_data.get('monthly_value'):
            monthly = float(contract_data.get('monthly_value', 0))
            quote_data["pricing"]["monthly"] = monthly
            quote_data["pricing"]["annual"] = monthly * 12
        
        if contract_data.get('setup_fee'):
            quote_data["pricing"]["setup_fee"] = float(contract_data.get('setup_fee', 0))
        
        # Map SLA
        if contract_data.get('sla_level'):
            quote_data["sla_requirements"] = contract_data.get('sla_level')
        
        # Map services
        if contract_data.get('included_services'):
            quote_data["included_services"] = contract_data.get('included_services')
        
        return quote_data


