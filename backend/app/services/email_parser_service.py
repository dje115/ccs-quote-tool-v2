#!/usr/bin/env python3
"""
Email Parser Service
Extracts ticket details from emails
"""

import logging
import re
from typing import Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.crm import Customer, Contact
from app.models.helpdesk import TicketPriority

logger = logging.getLogger(__name__)


class EmailParserService:
    """
    Service for parsing emails and extracting ticket information
    
    Features:
    - Extract ticket details from email
    - Identify customer from email address
    - Parse email body and subject
    - Determine priority
    """
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
    
    async def parse_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse email and extract ticket information
        
        Args:
            email_data: Email data dictionary
        
        Returns:
            Dict with parsed ticket data
        """
        subject = email_data.get("subject", "")
        body = email_data.get("body", "")
        from_address = email_data.get("from_address", "")
        
        # Extract title from subject
        title = self.parse_email_subject(subject)
        
        # Extract description from body
        description = self.parse_email_body(body)
        
        # Determine priority
        priority = self.determine_priority(subject, body)
        
        # Extract category/tags
        category = self.extract_category(subject, body)
        
        return {
            "title": title,
            "description": description,
            "priority": priority,
            "category": category,
            "from_address": from_address
        }
    
    def parse_email_subject(self, subject: str) -> str:
        """Parse email subject to extract ticket title"""
        # Remove common prefixes like "Re:", "Fwd:", etc.
        subject = re.sub(r'^(Re:|Fwd:|RE:|FWD:)\s*', '', subject, flags=re.IGNORECASE)
        
        # Remove ticket number references if present
        subject = re.sub(r'\[.*?\]', '', subject)
        
        return subject.strip()
    
    def parse_email_body(self, body: str) -> str:
        """Parse email body to extract description"""
        # Remove email signatures (common patterns)
        # Remove everything after "---" or "Sent from" or similar
        body = re.split(r'---|Sent from|Best regards|Regards', body, flags=re.IGNORECASE)[0]
        
        # Remove excessive whitespace
        body = re.sub(r'\n{3,}', '\n\n', body)
        
        return body.strip()
    
    def identify_customer(self, from_address: str) -> Optional[Customer]:
        """
        Identify customer from email address
        
        Args:
            from_address: Email address (e.g., "John Doe <john@example.com>")
        
        Returns:
            Customer if found, None otherwise
        """
        # Extract email address
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', from_address)
        if not email_match:
            return None
        
        email_address = email_match.group(0).lower()
        
        # Search for customer by email in contacts
        contact = self.db.query(Contact).filter(
            Contact.tenant_id == self.tenant_id,
            or_(
                Contact.email == email_address,
                Contact.email.ilike(f"%{email_address}%")
            )
        ).first()
        
        if contact and contact.customer_id:
            return self.db.query(Customer).filter(
                Customer.id == contact.customer_id,
                Customer.tenant_id == self.tenant_id
            ).first()
        
        # Try to find customer by domain
        domain = email_address.split('@')[1] if '@' in email_address else None
        if domain:
            # Search for customer with matching website or company name
            customer = self.db.query(Customer).filter(
                Customer.tenant_id == self.tenant_id,
                or_(
                    Customer.website.ilike(f"%{domain}%"),
                    Customer.company_name.ilike(f"%{domain.split('.')[0]}%")
                )
            ).first()
            
            if customer:
                return customer
        
        return None
    
    def determine_priority(self, subject: str, body: str) -> TicketPriority:
        """Determine ticket priority from subject and body"""
        text = f"{subject} {body}".lower()
        
        # High priority keywords
        high_priority_keywords = ["urgent", "critical", "down", "broken", "emergency", "asap", "immediate"]
        if any(keyword in text for keyword in high_priority_keywords):
            return TicketPriority.HIGH
        
        # Low priority keywords
        low_priority_keywords = ["question", "inquiry", "info", "information", "when", "how"]
        if any(keyword in text for keyword in low_priority_keywords):
            return TicketPriority.LOW
        
        # Default to medium
        return TicketPriority.MEDIUM
    
    def extract_category(self, subject: str, body: str) -> Optional[str]:
        """Extract category from email content"""
        text = f"{subject} {body}".lower()
        
        # Common categories
        categories = {
            "technical": ["error", "bug", "issue", "problem", "not working", "broken"],
            "billing": ["invoice", "payment", "billing", "charge", "refund"],
            "support": ["help", "support", "assistance", "question"],
            "feature": ["feature", "enhancement", "request", "suggestion"]
        }
        
        for category, keywords in categories.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return None

