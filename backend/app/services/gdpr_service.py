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
    
    def generate_sar_export(self, user_id: str, tenant_id: str) -> Dict[str, Any]:
        """
        Generate Subject Access Request (SAR) data export for a user
        
        Args:
            user_id: ID of the user requesting their data
            tenant_id: Tenant ID for data isolation
            
        Returns:
            Dictionary containing all personal data for the user
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
        
        # Get tickets created by or assigned to user
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
    
    def generate_privacy_policy(
        self,
        tenant_id: str,
        use_ai: bool = True,
        custom_prompt: Optional[str] = None
    ) -> PrivacyPolicy:
        """
        Generate a GDPR policy using AI based on data collection analysis
        
        Args:
            data_analysis: Output from analyze_data_collection()
            include_iso: Whether to include ISO 27001 and ISO 9001 references
            tenant_id: Tenant ID for AI provider resolution
            
        Returns:
            Generated GDPR policy text
        """
        from app.services.ai_provider_service import AIProviderService
        
        prompt = f"""Generate a comprehensive GDPR Privacy Policy based on the following data collection analysis:

DATA COLLECTED:
{json.dumps(data_analysis['data_categories'], indent=2)}

DATA RETENTION:
{json.dumps(data_analysis['data_retention'], indent=2)}

DATA SHARING:
{json.dumps(data_analysis['data_sharing'], indent=2)}

DATA SUBJECT RIGHTS:
{json.dumps(data_analysis['data_subject_rights'], indent=2)}

SECURITY MEASURES:
{json.dumps(data_analysis['security_measures'], indent=2)}

Please generate a GDPR-compliant privacy policy that includes:
1. Introduction and controller information
2. What personal data we collect
3. How we use personal data (legal basis for each)
4. Data retention periods
5. Data sharing and third parties
6. Data subject rights and how to exercise them
7. Security measures
8. Contact information for data protection inquiries
9. Right to lodge a complaint with supervisory authority
10. Changes to this policy"""
        
        if include_iso:
            prompt += "\n\nAdditionally, include references to ISO 27001 (Information Security Management) and ISO 9001 (Quality Management) compliance where relevant."
        
        prompt += "\n\nThe policy should be clear, comprehensive, and compliant with GDPR Article 13 (Information to be provided) and Article 14 (Information to be provided where personal data have not been obtained from the data subject). Format the output as a well-structured privacy policy document suitable for publication on a website."
        
        # Use AI provider service with generate_with_rendered_prompts (no prompt object needed)
        provider_service = AIProviderService(self.db, tenant_id=tenant_id)
        
        response = await provider_service.generate_with_rendered_prompts(
            prompt=None,  # Use system default provider
            system_prompt="You are a legal compliance expert specializing in GDPR and data protection regulations. Generate clear, comprehensive, and legally compliant privacy policies.",
            user_prompt=prompt,
            model="gpt-4",  # Use GPT-4 for better legal document generation
            temperature=0.3,  # Lower temperature for more consistent legal documents
            max_tokens=4000  # Longer documents need more tokens
        )
        
        return response.content if hasattr(response, 'content') else str(response)
