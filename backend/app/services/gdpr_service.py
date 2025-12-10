#!/usr/bin/env python3
"""
GDPR Service

COMPLIANCE: Handles GDPR-related operations including:
- Data collection analysis
- Subject Access Request (SAR) data export
- GDPR policy generation
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.models.tenant import User, Tenant
from app.models.crm import Customer, Contact
from app.models.quotes import Quote
from app.models.helpdesk import Ticket
from app.models.sales import SalesActivity
from app.models.leads import Lead
from app.models.gdpr import DataCollectionRecord, PrivacyPolicy, SubjectAccessRequest, SARStatus
from app.core.config import settings

logger = logging.getLogger(__name__)


class GDPRService:
    """Service for GDPR compliance operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def analyze_data_collection(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze what personal data is collected and why
        
        Returns:
            Dictionary with data collection analysis
        """
        analysis = {
            "data_categories": {
                "user_data": {
                    "collected": [
                        "Email address",
                        "Full name (first_name, last_name)",
                        "Username",
                        "Phone number (optional)",
                        "Role and permissions",
                        "Login history and authentication data",
                        "Password hash (encrypted)",
                        "2FA settings (if enabled)"
                    ],
                    "purpose": [
                        "User authentication and authorization",
                        "Account management",
                        "Communication with users",
                        "Access control and security"
                    ],
                    "legal_basis": "Contractual necessity and legitimate interest (security)"
                },
                "customer_data": {
                    "collected": [
                        "Company name",
                        "Business contact information (email, phone)",
                        "Business address",
                        "Website URL",
                        "Business sector and size",
                        "Company description",
                        "LinkedIn data (if available)",
                        "Companies House data (if available)",
                        "Google Maps location data"
                    ],
                    "purpose": [
                        "CRM and customer relationship management",
                        "Sales and marketing activities",
                        "Quote generation and order processing",
                        "Customer support and service delivery"
                    ],
                    "legal_basis": "Legitimate interest (business relationship) and contractual necessity"
                },
                "contact_data": {
                    "collected": [
                        "Full name",
                        "Email address",
                        "Phone number",
                        "Job title",
                        "Role in organization",
                        "Communication preferences"
                    ],
                    "purpose": [
                        "Business communication",
                        "Sales and marketing activities",
                        "Customer support"
                    ],
                    "legal_basis": "Legitimate interest (business relationship)"
                },
                "transaction_data": {
                    "collected": [
                        "Quote details and pricing",
                        "Order information",
                        "Payment records (if applicable)",
                        "Contract details",
                        "Support ticket information"
                    ],
                    "purpose": [
                        "Order processing and fulfillment",
                        "Contract management",
                        "Customer support",
                        "Financial record keeping"
                    ],
                    "legal_basis": "Contractual necessity and legal obligation"
                },
                "communication_data": {
                    "collected": [
                        "Email communications",
                        "Sales activity notes",
                        "Support ticket conversations",
                        "Meeting notes",
                        "WhatsApp messages (if integrated)"
                    ],
                    "purpose": [
                        "Business communication records",
                        "Customer service history",
                        "Sales process tracking"
                    ],
                    "legal_basis": "Legitimate interest (business relationship) and contractual necessity"
                },
                "technical_data": {
                    "collected": [
                        "IP addresses",
                        "User agent strings",
                        "Login timestamps",
                        "Security event logs",
                        "API usage statistics"
                    ],
                    "purpose": [
                        "Security and fraud prevention",
                        "System monitoring and troubleshooting",
                        "Compliance and auditing"
                    ],
                    "legal_basis": "Legitimate interest (security) and legal obligation"
                }
            },
            "data_retention": {
                "user_data": "Retained while account is active, deleted 30 days after account closure",
                "customer_data": "Retained for duration of business relationship + 7 years for legal compliance",
                "transaction_data": "Retained for 7 years for tax and legal compliance",
                "communication_data": "Retained for duration of business relationship + 2 years",
                "technical_data": "Retained for 90 days for security monitoring"
            },
            "data_sharing": {
                "third_parties": [
                    {
                        "name": "OpenAI",
                        "purpose": "AI-powered features and analysis",
                        "data_shared": "Company information, descriptions, and business context",
                        "legal_basis": "Legitimate interest (service delivery)"
                    },
                    {
                        "name": "Companies House API",
                        "purpose": "Company information verification",
                        "data_shared": "Company registration numbers and names",
                        "legal_basis": "Legitimate interest (data verification)"
                    },
                    {
                        "name": "Google Maps API",
                        "purpose": "Location services and mapping",
                        "data_shared": "Address information",
                        "legal_basis": "Legitimate interest (service delivery)"
                    }
                ],
                "internal_sharing": "Data is shared within the tenant organization for business purposes"
            },
            "data_subject_rights": {
                "right_to_access": "Users can request a copy of their personal data (SAR)",
                "right_to_rectification": "Users can update their personal information",
                "right_to_erasure": "Users can request deletion of their data (subject to legal obligations)",
                "right_to_restrict_processing": "Users can request restriction of data processing",
                "right_to_data_portability": "Users can export their data in a machine-readable format",
                "right_to_object": "Users can object to processing based on legitimate interest"
            },
            "security_measures": [
                "Encryption of data in transit (TLS/SSL)",
                "Encryption of sensitive data at rest (API keys, passwords)",
                "Access controls and authentication",
                "Regular security audits and monitoring",
                "Data backup and disaster recovery procedures"
            ],
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        
        return analysis
    
    def generate_sar_export_from_user(self, user_id: str, tenant_id: str) -> Dict[str, Any]:
        """
        Generate data export for a user (without requiring a SAR record)
        
        Args:
            user_id: User ID to export data for
            tenant_id: Tenant ID
            
        Returns:
            Dictionary containing all user data
        """
        export = {
            "export_date": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "tenant_id": tenant_id,
            "data": {}
        }
        
        # Get user data
        user = self.db.query(User).filter(
            and_(User.id == user_id, User.tenant_id == tenant_id)
        ).first()
        
        if user:
            export["data"]["user_profile"] = {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone": user.phone,
                "role": user.role.value if user.role else None,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None
            }
        
        # Get quotes created by user
        quotes = self.db.query(Quote).filter(
            and_(Quote.tenant_id == tenant_id, Quote.created_by == user_id)
        ).all()
        
        export["data"]["quotes"] = [
            {
                "id": quote.id,
                "quote_number": quote.quote_number,
                "customer_id": quote.customer_id,
                "status": quote.status.value if quote.status else None,
                "total_amount": float(quote.total_amount) if quote.total_amount else None,
                "created_at": quote.created_at.isoformat() if quote.created_at else None,
                "updated_at": quote.updated_at.isoformat() if quote.updated_at else None
            }
            for quote in quotes
        ]
        
        # Get tickets
        tickets = []
        if user_id:
            tickets = self.db.query(Ticket).filter(
                and_(
                    Ticket.tenant_id == tenant_id,
                    (Ticket.created_by == user_id) | (Ticket.assigned_to == user_id)
                )
            ).all()
        
        export["data"]["tickets"] = [
            {
                "id": ticket.id,
                "ticket_number": ticket.ticket_number,
                "subject": ticket.subject,
                "status": ticket.status.value if ticket.status else None,
                "priority": ticket.priority.value if ticket.priority else None,
                "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
                "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None
            }
            for ticket in tickets
        ]
        
        # Get sales activities
        activities = []
        if user_id:
            activities = self.db.query(SalesActivity).filter(
                and_(SalesActivity.tenant_id == tenant_id, SalesActivity.user_id == user_id)
            ).all()
        
        export["data"]["sales_activities"] = [
            {
                "id": activity.id,
                "customer_id": activity.customer_id,
                "activity_type": activity.activity_type.value if activity.activity_type else None,
                "notes": activity.notes,
                "created_at": activity.created_at.isoformat() if activity.created_at else None
            }
            for activity in activities
        ]
        
        return export
    
    def generate_sar_export(self, sar_id: str) -> Dict[str, Any]:
        """
        Generate data export for a Subject Access Request
        
        Args:
            sar_id: Subject Access Request ID
            
        Returns:
            Dictionary containing all user data
        """
        stmt = select(SubjectAccessRequest).where(SubjectAccessRequest.id == sar_id)
        result = self.db.execute(stmt)
        sar = result.scalar_one_or_none()
        
        if not sar:
            raise ValueError("Subject Access Request not found")
        
        if not sar.verified:
            raise ValueError("SAR must be verified before export")
        
        # Get user if requestor is a user
        user_id = sar.requestor_id
        tenant_id = sar.tenant_id
        
        export = {
            "export_date": datetime.now(timezone.utc).isoformat(),
            "request_id": sar.id,
            "requestor_email": sar.requestor_email,
            "requestor_name": sar.requestor_name,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "data": {}
        }
        
        # Get user data if requestor is a user
        if user_id:
            user = self.db.query(User).filter(
                and_(User.id == user_id, User.tenant_id == tenant_id)
            ).first()
        
        if user:
            export["data"]["user_profile"] = {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone": user.phone,
                "role": user.role.value if user.role else None,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None
            }
        
        # Get quotes created by or associated with user
        quotes = self.db.query(Quote).filter(
            and_(Quote.tenant_id == tenant_id, Quote.created_by == user_id)
        ).all()
        
        export["data"]["quotes"] = [
            {
                "id": quote.id,
                "quote_number": quote.quote_number,
                "customer_id": quote.customer_id,
                "status": quote.status.value if quote.status else None,
                "total_amount": float(quote.total_amount) if quote.total_amount else None,
                "created_at": quote.created_at.isoformat() if quote.created_at else None,
                "updated_at": quote.updated_at.isoformat() if quote.updated_at else None
            }
            for quote in quotes
        ]
        
        # Get tickets
        tickets = []
        if user_id:
            tickets = self.db.query(Ticket).filter(
                and_(
                    Ticket.tenant_id == tenant_id,
                    (Ticket.created_by == user_id) | (Ticket.assigned_to == user_id)
                )
            ).all()
        elif customers:
            customer_ids = [c.id for c in customers]
            tickets = self.db.query(Ticket).filter(
                and_(
                    Ticket.tenant_id == tenant_id,
                    Ticket.customer_id.in_(customer_ids)
                )
            ).all()
        
        export["data"]["tickets"] = [
            {
                "id": ticket.id,
                "ticket_number": ticket.ticket_number,
                "subject": ticket.subject,
                "status": ticket.status.value if ticket.status else None,
                "priority": ticket.priority.value if ticket.priority else None,
                "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
                "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None
            }
            for ticket in tickets
        ]
        
        # Get sales activities (only if user_id exists)
        activities = []
        if user_id:
            activities = self.db.query(SalesActivity).filter(
                and_(SalesActivity.tenant_id == tenant_id, SalesActivity.user_id == user_id)
            ).all()
        
        export["data"]["sales_activities"] = [
            {
                "id": activity.id,
                "customer_id": activity.customer_id,
                "activity_type": activity.activity_type.value if activity.activity_type else None,
                "notes": activity.notes,
                "created_at": activity.created_at.isoformat() if activity.created_at else None
            }
            for activity in activities
        ]
        
        return export
    
    async def generate_privacy_policy(
        self,
        tenant_id: str,
        use_ai: bool = True,
        include_iso: bool = False,
        custom_prompt: Optional[str] = None
    ) -> PrivacyPolicy:
        """
        Generate a privacy policy using AI based on data collection records
        
        Args:
            tenant_id: Tenant ID
            use_ai: Whether to use AI generation (default: True)
            include_iso: Whether to include ISO 27001 and ISO 9001 references
            custom_prompt: Optional custom prompt for AI generation (overrides database prompt)
            
        Returns:
            Generated PrivacyPolicy
        """
        import uuid
        from app.services.ai_prompt_service import AIPromptService
        from app.services.ai_provider_service import AIProviderService
        from app.models.ai_prompt import PromptCategory
        
        # Get data collection analysis
        data_analysis = self.analyze_data_collection(tenant_id=tenant_id)
        rendered = None
        
        if use_ai:
            # Get prompt from database
            prompt_service = AIPromptService(self.db, tenant_id=tenant_id)
            prompt_obj = await prompt_service.get_prompt(
                category=PromptCategory.GDPR_PRIVACY_POLICY.value,
                tenant_id=tenant_id
            )
            
            if not prompt_obj:
                error_msg = f"GDPR privacy policy prompt not found in database for tenant {tenant_id}. Please seed prompts using backend/scripts/seed_ai_prompts.py"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Prepare ISO sections if requested
            iso_sections = ""
            if include_iso:
                iso_sections = "\n\nAdditionally, include references to ISO 27001 (Information Security Management) and ISO 9001 (Quality Management) compliance where relevant."
            
            # Render prompt with variables
            rendered = prompt_service.render_prompt(prompt_obj, {
                "data_categories": json.dumps(data_analysis['data_categories'], indent=2),
                "data_retention": json.dumps(data_analysis['data_retention'], indent=2),
                "data_sharing": json.dumps(data_analysis['data_sharing'], indent=2),
                "data_subject_rights": json.dumps(data_analysis['data_subject_rights'], indent=2),
                "security_measures": json.dumps(data_analysis['security_measures'], indent=2),
                "iso_sections": iso_sections
            })
            
            # Use AI provider service
            provider_service = AIProviderService(self.db, tenant_id=tenant_id)
            
            # Generate policy using the prompt from database
            response = await provider_service.generate(
                prompt=prompt_obj,
                variables={
                    "data_categories": json.dumps(data_analysis['data_categories'], indent=2),
                    "data_retention": json.dumps(data_analysis['data_retention'], indent=2),
                    "data_sharing": json.dumps(data_analysis['data_sharing'], indent=2),
                    "data_subject_rights": json.dumps(data_analysis['data_subject_rights'], indent=2),
                    "security_measures": json.dumps(data_analysis['security_measures'], indent=2),
                    "iso_sections": iso_sections
                }
            )
            
            policy_content = response.content if hasattr(response, 'content') else str(response)
        else:
            # Generate template policy without AI
            policy_content = self._generate_template_policy_from_analysis(data_analysis)
        
        # Get latest version number
        stmt = select(PrivacyPolicy).where(
            PrivacyPolicy.tenant_id == tenant_id
        ).order_by(PrivacyPolicy.created_at.desc())
        result = self.db.execute(stmt)
        latest = result.scalars().first()
        
        version = "1.0"
        if latest:
            try:
                current_version = float(latest.version)
                version = f"{current_version + 0.1:.1f}"
            except ValueError:
                version = "1.0"
        
        # Create policy
        policy = PrivacyPolicy(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            version=version,
            title=f"Privacy Policy v{version}",
            content=policy_content,
            is_active=True,
            generated_by_ai=use_ai,
            generation_prompt=custom_prompt if custom_prompt else (rendered.get('user_prompt', '') if use_ai and rendered else None),
            effective_date=datetime.now(timezone.utc),
            next_review_date=datetime.now(timezone.utc) + timedelta(days=365)
        )
        
        # Deactivate old policies
        stmt = select(PrivacyPolicy).where(
            and_(
                PrivacyPolicy.tenant_id == tenant_id,
                PrivacyPolicy.is_active == True
            )
        )
        result = self.db.execute(stmt)
        for old_policy in result.scalars().all():
            old_policy.is_active = False
        
        self.db.add(policy)
        self.db.commit()
        self.db.refresh(policy)
        
        return policy
    
    def _generate_template_policy_from_analysis(self, data_analysis: Dict[str, Any]) -> str:
        """Generate a template privacy policy without AI from data analysis"""
        return f"""
# Privacy Policy

## 1. Introduction
This privacy policy explains how we collect, use, and protect your personal data in accordance with GDPR.

## 2. Data We Collect
{json.dumps(data_analysis['data_categories'], indent=2)}

## 3. Legal Basis
We process your data based on: contract performance, legal obligations, legitimate interests, and consent where applicable.

## 4. Your Rights
{json.dumps(data_analysis['data_subject_rights'], indent=2)}

## 5. Contact
For data protection inquiries, contact: {settings.SMTP_FROM_EMAIL}
"""
