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
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.models.tenant import User, Tenant
from app.models.crm import Customer, Contact
from app.models.quotes import Quote
from app.models.helpdesk import Ticket, TicketComment
from app.models.sales import SalesActivity
from app.models.leads import Lead
from app.models.gdpr import DataCollectionRecord, PrivacyPolicy, SubjectAccessRequest, SARStatus
from app.core.config import settings
from app.services.sar_document_generator import SARDocumentGenerator
from app.services.storage_service import get_storage_service

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
    
    def _redact_other_people_names(self, text: str, subject_name: str, all_contact_names: List[str]) -> str:
        """
        Redact names of other people from text, keeping only the subject's name
        
        Args:
            text: Text to redact
            subject_name: Full name of the subject (e.g., "John Smith")
            all_contact_names: List of all contact names in the system to redact
            
        Returns:
            Text with other people's names redacted as [REDACTED]
        """
        if not text:
            return text
        
        # Create a set of names to redact (excluding the subject)
        names_to_redact = set()
        for name in all_contact_names:
            if name.lower() != subject_name.lower():
                # Add full name and individual parts
                parts = name.split()
                for part in parts:
                    if len(part) > 2:  # Only redact names longer than 2 characters
                        names_to_redact.add(part)
                names_to_redact.add(name)
        
        # Redact names (case-insensitive)
        redacted_text = text
        for name in sorted(names_to_redact, key=len, reverse=True):  # Sort by length to redact longer names first
            if len(name) > 2:
                # Redact full name
                import re
                pattern = re.compile(re.escape(name), re.IGNORECASE)
                redacted_text = pattern.sub("[REDACTED]", redacted_text)
        
        return redacted_text
    
    def generate_sar_export_for_person(
        self,
        tenant_id: str,
        contact_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate GDPR-compliant SAR export for a specific person (contact or user)
        
        Args:
            tenant_id: Tenant ID
            contact_id: Contact ID (for customer contacts)
            user_id: User ID (for internal users)
            
        Returns:
            GDPR-compliant SAR report as dictionary
        """
        from app.models.crm import Contact, Customer
        from app.models.helpdesk import Ticket, TicketComment
        from app.models.quotes import Quote
        from app.models.sales import SalesActivity
        
        # Get all contact names for redaction (contacts are linked through customers)
        all_customers = self.db.query(Customer).filter(Customer.tenant_id == tenant_id).all()
        customer_ids = [c.id for c in all_customers]
        all_contacts = self.db.query(Contact).filter(Contact.customer_id.in_(customer_ids)).all() if customer_ids else []
        all_contact_names = [f"{c.first_name} {c.last_name}" for c in all_contacts]
        all_users = self.db.query(User).filter(User.tenant_id == tenant_id).all()
        all_user_names = [f"{u.first_name} {u.last_name}" for u in all_users if u.first_name and u.last_name]
        all_people_names = all_contact_names + all_user_names
        
        # Identify the subject
        subject_name = None
        subject_email = None
        subject_phone = None
        subject_role = None
        company_name = None
        
        contact = None
        customer = None
        if contact_id:
            contact = self.db.query(Contact).filter(Contact.id == contact_id).first()
            if not contact:
                raise ValueError("Contact not found")
            
            # Verify contact belongs to tenant through customer
            customer = self.db.query(Customer).filter(
                and_(Customer.id == contact.customer_id, Customer.tenant_id == tenant_id)
            ).first()
            if not customer:
                raise ValueError("Contact not found or does not belong to this tenant")
            
            subject_name = f"{contact.first_name} {contact.last_name}"
            subject_email = contact.email
            subject_phone = contact.phone
            subject_role = contact.job_title or (contact.role.value if contact.role else None)
            company_name = customer.company_name
        elif user_id:
            user = self.db.query(User).filter(
                and_(User.id == user_id, User.tenant_id == tenant_id)
            ).first()
            if not user:
                raise ValueError("User not found")
            subject_name = f"{user.first_name} {user.last_name}" if user.first_name and user.last_name else user.email
            subject_email = user.email
            subject_phone = user.phone
            subject_role = user.role.value if user.role else None
        else:
            raise ValueError("Either contact_id or user_id must be provided")
        
        # Build GDPR-compliant SAR report
        export_date = datetime.now(timezone.utc)
        sar_id = f"SAR-{export_date.strftime('%Y%m%d')}-{contact_id or user_id}"
        
        report = {
            "report_type": "Subject Access Request (SAR) Response Report",
            "company": "CCS Quote Tool",  # TODO: Get from tenant settings
            "requesting_party": subject_name,
            "date_of_response": export_date.isoformat(),
            "reference": sar_id,
            "introduction": f"This report has been prepared in response to a Subject Access Request (SAR) submitted by {subject_name}. Under the UK GDPR and Data Protection Act 2018, this report covers personal data relating to {subject_name}.",
            "data_subject": {
                "name": subject_name,
                "email": subject_email,
                "phone": subject_phone,
                "role": subject_role,
                "company": company_name
            },
            "categories_of_personal_data": {},
            "data": {}
        }
        
        # 1. Contact Information
        report["categories_of_personal_data"]["contact_information"] = {
            "full_name": subject_name,
            "job_title_role": subject_role,
            "work_email_address": subject_email,
            "work_telephone": subject_phone,
            "company_address": company_name
        }
        
        # 2. Communications (only AI-cleaned versions, redacted)
        communications = []
        
        # Get tickets where this person is mentioned or is the contact
        if contact_id and contact and customer:
                tickets = self.db.query(Ticket).filter(
                    and_(
                        Ticket.tenant_id == tenant_id,
                        Ticket.customer_id == customer.id
                    )
                ).all()
                
                for ticket in tickets:
                    # Only include cleaned_description (AI-cleaned), not original or internal notes
                    if ticket.cleaned_description:
                        redacted_desc = self._redact_other_people_names(
                            ticket.cleaned_description,
                            subject_name,
                            all_people_names
                        )
                        communications.append({
                            "type": "Support Ticket",
                            "ticket_number": ticket.ticket_number,
                            "subject": ticket.subject,
                            "description": redacted_desc,  # Only AI-cleaned version
                            "status": ticket.status.value if ticket.status else None,
                            "created_at": ticket.created_at.isoformat() if ticket.created_at else None
                        })
                    
                    # Get ticket comments (only non-internal, AI-cleaned if available)
                    comments = self.db.query(TicketComment).filter(
                        and_(
                            TicketComment.ticket_id == ticket.id,
                            TicketComment.is_internal == False  # Exclude internal notes
                        )
                    ).all()
                    
                    for comment in comments:
                        # Prefer AI-cleaned version if available, otherwise use content
                        content = comment.content
                        if hasattr(comment, 'cleaned_content') and comment.cleaned_content:
                            content = comment.cleaned_content
                        
                        redacted_content = self._redact_other_people_names(
                            content,
                            subject_name,
                            all_people_names
                        )
                        communications.append({
                            "type": "Ticket Comment",
                            "ticket_number": ticket.ticket_number,
                            "content": redacted_content,
                            "created_at": comment.created_at.isoformat() if comment.created_at else None
                        })
        
        # Get sales activities (only AI-cleaned notes, redacted)
        if contact_id:
            activities = self.db.query(SalesActivity).filter(
                and_(
                    SalesActivity.tenant_id == tenant_id,
                    SalesActivity.contact_id == contact_id
                )
            ).all()
        elif user_id:
            activities = self.db.query(SalesActivity).filter(
                and_(
                    SalesActivity.tenant_id == tenant_id,
                    SalesActivity.user_id == user_id
                )
            ).all()
        else:
            activities = []
        
        for activity in activities:
            # Only include notes_cleaned (AI-cleaned version), not original notes
            if activity.notes_cleaned:
                redacted_notes = self._redact_other_people_names(
                    activity.notes_cleaned,
                    subject_name,
                    all_people_names
                )
                communications.append({
                    "type": activity.activity_type.value.title() if activity.activity_type else "Activity",
                    "subject": activity.subject,
                    "notes": redacted_notes,  # Only AI-cleaned version
                    "date": activity.activity_date.isoformat() if activity.activity_date else None,
                    "duration_minutes": activity.duration_minutes
                })
        
        report["data"]["communications"] = communications
        
        # 3. Contract and Account Data
        contract_data = []
        
        if contact_id:
            customer = self.db.query(Customer).filter(Customer.id == contact.customer_id).first()
            if customer:
                quotes = self.db.query(Quote).filter(
                    and_(
                        Quote.tenant_id == tenant_id,
                        Quote.customer_id == customer.id
                    )
                ).all()
                
                for quote in quotes:
                    contract_data.append({
                        "type": "Quote",
                        "quote_number": quote.quote_number,
                        "status": quote.status.value if quote.status else None,
                        "total_amount": float(quote.total_amount) if quote.total_amount else None,
                        "created_at": quote.created_at.isoformat() if quote.created_at else None
                    })
        elif user_id:
            quotes = self.db.query(Quote).filter(
                and_(
                    Quote.tenant_id == tenant_id,
                    Quote.created_by == user_id
                )
            ).all()
            
            for quote in quotes:
                contract_data.append({
                    "type": "Quote",
                    "quote_number": quote.quote_number,
                    "status": quote.status.value if quote.status else None,
                    "total_amount": float(quote.total_amount) if quote.total_amount else None,
                    "created_at": quote.created_at.isoformat() if quote.created_at else None
                })
        
        report["data"]["contracts_and_accounts"] = contract_data
        
        # 4. Technical or System Data
        technical_data = []
        
        if user_id:
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                technical_data.append({
                    "type": "User Account",
                    "username": user.username,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "last_login": user.updated_at.isoformat() if user.updated_at else None
                })
        
        report["data"]["technical_data"] = technical_data
        
        # 5. Source of Personal Data
        report["source_of_data"] = [
            "Individuals directly",
            "The company (via onboarding, contracts, or communications)",
            "Our internal staff logging interactions",
            "Automated collection from systems used by the company"
        ]
        
        # 6. Purpose and Lawful Basis
        report["purpose_and_lawful_basis"] = {
            "delivering_contracted_services": {
                "purpose": "Delivering contracted services",
                "lawful_basis": "Article 6(1)(b) – Contract",
                "details": "Needed to manage account, provide support, fulfil services"
            },
            "communications": {
                "purpose": "Communications",
                "lawful_basis": "Article 6(1)(f) – Legitimate Interest",
                "details": "For operational communication, support, updates"
            },
            "billing": {
                "purpose": "Billing and account administration",
                "lawful_basis": "Article 6(1)(c) – Legal Obligation",
                "details": "Maintaining accurate financial records"
            },
            "support": {
                "purpose": "Issue logging and support tickets",
                "lawful_basis": "Article 6(1)(f) – Legitimate Interest",
                "details": "Ensuring service quality & technical support"
            },
            "security": {
                "purpose": "Security & access control",
                "lawful_basis": "Article 6(1)(f) – Legitimate Interest",
                "details": "Protecting systems and data"
            }
        }
        
        # 7. Retention Periods
        report["retention_periods"] = {
            "emails": "6 years - Standard business practice",
            "contracts_quotes": "6–7 years - Legal and accounting requirements",
            "crm_notes": "Duration of contract + 2 years - For continuity & dispute resolution",
            "support_tickets": "3–6 years - Depending on issue severity",
            "system_logs": "30–365 days - Depending on security requirements"
        }
        
        # 8. Data Subject Rights
        report["data_subject_rights"] = {
            "right_to_access": "Access their personal data",
            "right_to_rectification": "Request correction of inaccurate data",
            "right_to_erasure": "Request erasure where legally applicable",
            "right_to_restrict_processing": "Restrict processing",
            "right_to_object": "Object to processing",
            "right_to_data_portability": "Request data portability",
            "right_to_complain": "Complain to the ICO (Information Commissioner's Office)"
        }
        
        # Add legacy fields for backward compatibility
        report["export_date"] = export_date.isoformat()
        report["user_id"] = user_id if user_id else None
        report["tenant_id"] = tenant_id
        
        return report
    
    def generate_and_store_sar_document(
        self,
        sar_data: Dict[str, Any],
        tenant_id: str,
        contact_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate PDF document for SAR and store it in MinIO
        
        Args:
            sar_data: SAR report data dictionary
            tenant_id: Tenant ID
            contact_id: Contact ID (if applicable)
            user_id: User ID (if applicable)
            
        Returns:
            Dictionary with document_path, download_url, and sar_record_id
        """
        import uuid
        
        # Generate PDF document
        doc_generator = SARDocumentGenerator()
        pdf_buffer = doc_generator.generate_pdf(sar_data)
        pdf_bytes = pdf_buffer.read()
        
        # Create SAR record in database
        sar_id = str(uuid.uuid4())
        sar_record = SubjectAccessRequest(
            id=sar_id,
            tenant_id=tenant_id,
            requestor_email=sar_data.get('data_subject', {}).get('email') or 'unknown@example.com',
            requestor_name=sar_data.get('data_subject', {}).get('name'),
            requestor_id=user_id,
            status=SARStatus.COMPLETED.value,
            request_date=datetime.now(timezone.utc),
            due_date=datetime.now(timezone.utc) + timedelta(days=30),
            completed_date=datetime.now(timezone.utc),
            verified=True,  # Auto-verified for internal requests
            data_export_path=None  # Will be set after upload
        )
        
        self.db.add(sar_record)
        self.db.flush()  # Get the ID without committing
        
        # Store PDF in MinIO with tenant isolation
        storage_service = get_storage_service()
        reference = sar_data.get('reference', f'SAR-{sar_id}')
        filename = f"{reference}.pdf"
        object_name = f"sar/{tenant_id}/{sar_id}/{filename}"
        
        # Upload to MinIO (synchronous call, but storage service handles it)
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        uploaded_path = loop.run_until_complete(
            storage_service.upload_file(
                file_data=pdf_bytes,
                object_name=object_name,
                content_type='application/pdf',
                metadata={
                    'sar_id': sar_id,
                    'tenant_id': tenant_id,
                    'reference': reference,
                    'generated_at': datetime.now(timezone.utc).isoformat()
                }
            )
        )
        
        # Update SAR record with document path
        sar_record.data_export_path = object_name
        self.db.commit()
        
        # Generate presigned download URL (valid for 7 days)
        download_url = storage_service.get_presigned_url(
            object_name=object_name,
            expires=timedelta(days=7)
        )
        
        return {
            "sar_id": sar_id,
            "document_path": object_name,
            "download_url": download_url,
            "filename": filename,
            "reference": reference
        }
    
    async def send_sar_email(
        self,
        recipient_email: str,
        recipient_name: str,
        download_url: str,
        reference: str,
        tenant_id: str
    ) -> bool:
        """
        Send SAR document via email
        
        Args:
            recipient_email: Email address to send to
            recipient_name: Name of recipient
            download_url: Presigned URL to download the document
            reference: SAR reference number
            tenant_id: Tenant ID
            
        Returns:
            True if email sent successfully
        """
        try:
            from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
            from app.core.config import settings
            
            # Configure email
            conf = ConnectionConfig(
                MAIL_USERNAME=settings.SMTP_USERNAME,
                MAIL_PASSWORD=settings.SMTP_PASSWORD,
                MAIL_FROM=settings.SMTP_FROM_EMAIL,
                MAIL_PORT=settings.SMTP_PORT,
                MAIL_SERVER=settings.SMTP_HOST,
                MAIL_FROM_NAME=settings.SMTP_FROM_NAME,
                MAIL_STARTTLS=settings.SMTP_TLS,
                MAIL_SSL_TLS=False,
                USE_CREDENTIALS=True if settings.SMTP_USERNAME else False,
                VALIDATE_CERTS=False
            )
            
            fm = FastMail(conf)
            
            # Create email message
            message = MessageSchema(
                subject=f"Your Subject Access Request - {reference}",
                recipients=[recipient_email],
                body=f"""
Dear {recipient_name},

Your Subject Access Request (SAR) has been processed and is now available for download.

Reference: {reference}

You can download your SAR document using the following link (valid for 7 days):
{download_url}

This document contains all personal data we hold about you, in compliance with GDPR Article 15.

If you have any questions, please contact us using the details provided in the document.

Best regards,
{settings.SMTP_FROM_NAME}
                """,
                subtype="plain"
            )
            
            await fm.send_message(message)
            logger.info(f"SAR email sent to {recipient_email} for reference {reference}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending SAR email: {e}", exc_info=True)
            return False
    
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
