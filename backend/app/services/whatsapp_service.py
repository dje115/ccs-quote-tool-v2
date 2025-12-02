#!/usr/bin/env python3
"""
WhatsApp Business API Service
Handles WhatsApp message-to-ticket conversion and two-way communication
"""

import logging
import httpx
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from app.models.helpdesk import Ticket, TicketStatus, TicketPriority
from app.models.crm import Customer, Contact
from app.services.email_parser_service import EmailParserService

logger = logging.getLogger(__name__)


class WhatsAppService:
    """
    Service for WhatsApp Business API integration
    
    Features:
    - Send messages via WhatsApp
    - Receive messages via webhook
    - Message-to-ticket conversion
    - Two-way communication
    """
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.parser = EmailParserService(db, tenant_id)
    
    async def send_message(
        self,
        phone_number: str,
        message: str,
        ticket_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send WhatsApp message
        
        Args:
            phone_number: Recipient phone number (E.164 format)
            message: Message text
            ticket_id: Optional ticket ID to link message
        
        Returns:
            Dict with send result
        """
        # Get tenant WhatsApp config
        whatsapp_config = self._get_whatsapp_config()
        
        if not whatsapp_config:
            return {
                "success": False,
                "error": "WhatsApp not configured for this tenant"
            }
        
        try:
            # WhatsApp Business API endpoint
            url = f"https://graph.facebook.com/v18.0/{whatsapp_config['phone_number_id']}/messages"
            
            headers = {
                "Authorization": f"Bearer {whatsapp_config['access_token']}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "text",
                "text": {
                    "body": message
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
            
            # Store message in database (if message tracking table exists)
            # TODO: Create message tracking table
            
            return {
                "success": True,
                "message_id": result.get("messages", [{}])[0].get("id"),
                "ticket_id": ticket_id
            }
            
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def receive_message(
        self,
        webhook_data: Dict[str, Any]
    ) -> Optional[Ticket]:
        """
        Process incoming WhatsApp message and convert to ticket
        
        Args:
            webhook_data: WhatsApp webhook payload
        
        Returns:
            Created or updated Ticket
        """
        try:
            # Extract message data from webhook
            entry = webhook_data.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            messages = value.get("messages", [])
            
            if not messages:
                return None
            
            message = messages[0]
            from_number = message.get("from")
            message_text = message.get("text", {}).get("body", "")
            message_id = message.get("id")
            
            # Check if ticket already exists for this conversation
            existing_ticket = self.db.query(Ticket).filter(
                Ticket.tenant_id == self.tenant_id,
                Ticket.source == "whatsapp",
                Ticket.source_reference == from_number,
                Ticket.status.in_([TicketStatus.OPEN, TicketStatus.IN_PROGRESS])
            ).first()
            
            if existing_ticket:
                # Add message as comment to existing ticket
                from app.models.helpdesk import TicketComment
                comment = TicketComment(
                    id=str(uuid.uuid4()),
                    tenant_id=self.tenant_id,
                    ticket_id=existing_ticket.id,
                    comment=message_text,
                    created_by=None,  # System-generated
                    is_internal=False
                )
                self.db.add(comment)
                self.db.commit()
                return existing_ticket
            
            # Create new ticket
            # Identify customer from phone number
            customer = self._identify_customer_from_phone(from_number)
            
            # Determine priority
            priority = self.parser.determine_priority("", message_text)
            
            ticket = Ticket(
                id=str(uuid.uuid4()),
                tenant_id=self.tenant_id,
                customer_id=customer.id if customer else None,
                title=f"WhatsApp Message from {from_number}",
                description=message_text,
                status=TicketStatus.OPEN,
                priority=priority,
                source="whatsapp",
                source_reference=from_number,
                created_by=None
            )
            
            self.db.add(ticket)
            self.db.commit()
            self.db.refresh(ticket)
            
            return ticket
            
        except Exception as e:
            logger.error(f"Failed to process WhatsApp message: {e}")
            self.db.rollback()
            return None
    
    def _get_whatsapp_config(self) -> Optional[Dict[str, Any]]:
        """Get WhatsApp configuration for tenant"""
        from app.models.tenant import Tenant
        
        tenant = self.db.query(Tenant).filter(Tenant.id == self.tenant_id).first()
        if not tenant:
            return None
        
        # Get from tenant metadata or separate config table
        # For now, return from tenant metadata
        whatsapp_config = tenant.metadata.get("whatsapp_config") if hasattr(tenant, 'metadata') else None
        
        return whatsapp_config
    
    def _identify_customer_from_phone(self, phone_number: str) -> Optional[Customer]:
        """Identify customer from phone number"""
        # Search contacts by phone
        contact = self.db.query(Contact).filter(
            Contact.tenant_id == self.tenant_id,
            Contact.phone.ilike(f"%{phone_number[-10:]}%")  # Last 10 digits
        ).first()
        
        if contact and contact.customer_id:
            return self.db.query(Customer).filter(
                Customer.id == contact.customer_id,
                Customer.tenant_id == self.tenant_id
            ).first()
        
        return None
    
    async def send_ticket_update(
        self,
        ticket: Ticket,
        message: str
    ) -> Dict[str, Any]:
        """
        Send ticket update via WhatsApp
        
        Args:
            ticket: Ticket object
            message: Update message
        
        Returns:
            Send result
        """
        if not ticket.source_reference or ticket.source != "whatsapp":
            return {
                "success": False,
                "error": "Ticket is not from WhatsApp"
            }
        
        # Get customer phone number
        phone_number = ticket.source_reference
        
        return await self.send_message(
            phone_number=phone_number,
            message=message,
            ticket_id=ticket.id
        )

