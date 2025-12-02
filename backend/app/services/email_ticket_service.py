#!/usr/bin/env python3
"""
Email Ticket Service
Handles email-to-ticket conversion via IMAP/POP3
"""

import logging
import imaplib
import poplib
import email
import uuid
from email.header import decode_header
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.helpdesk import Ticket, TicketStatus, TicketPriority
from app.models.crm import Customer, Contact
from app.services.email_parser_service import EmailParserService

logger = logging.getLogger(__name__)


class EmailTicketService:
    """
    Service for email-to-ticket conversion
    
    Features:
    - IMAP/POP3 integration
    - Email-to-ticket conversion
    - Attachment handling
    - Customer identification
    """
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.parser = EmailParserService(db, tenant_id)
    
    def connect_to_email_server(
        self,
        email_address: str,
        password: str,
        server: str,
        port: int,
        use_ssl: bool = True,
        protocol: str = "imap"  # "imap" or "pop3"
    ) -> Any:
        """
        Connect to email server
        
        Args:
            email_address: Email address
            password: Email password or app password
            server: Email server (e.g., "imap.gmail.com")
            port: Server port
            use_ssl: Use SSL/TLS
            protocol: "imap" or "pop3"
        
        Returns:
            Connection object
        """
        try:
            if protocol.lower() == "imap":
                if use_ssl:
                    mail = imaplib.IMAP4_SSL(server, port)
                else:
                    mail = imaplib.IMAP4(server, port)
                
                mail.login(email_address, password)
                return mail
            elif protocol.lower() == "pop3":
                if use_ssl:
                    mail = poplib.POP3_SSL(server, port)
                else:
                    mail = poplib.POP3(server, port)
                
                mail.user(email_address)
                mail.pass_(password)
                return mail
            else:
                raise ValueError(f"Unsupported protocol: {protocol}")
        except Exception as e:
            logger.error(f"Failed to connect to email server: {e}")
            raise
    
    def fetch_emails(
        self,
        connection: Any,
        protocol: str = "imap",
        folder: str = "INBOX",
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Fetch emails from server
        
        Args:
            connection: Email connection object
            protocol: "imap" or "pop3"
            folder: IMAP folder (ignored for POP3)
            limit: Maximum number of emails to fetch
        
        Returns:
            List of email data dictionaries
        """
        emails = []
        
        try:
            if protocol.lower() == "imap":
                connection.select(folder)
                status, messages = connection.search(None, "UNSEEN")  # Only unread emails
                
                if status != "OK":
                    return emails
                
                email_ids = messages[0].split()
                email_ids = email_ids[-limit:]  # Get most recent
                
                for email_id in email_ids:
                    status, msg_data = connection.fetch(email_id, "(RFC822)")
                    if status == "OK":
                        email_body = msg_data[0][1]
                        email_message = email.message_from_bytes(email_body)
                        emails.append(self._parse_email_message(email_message, email_id))
            elif protocol.lower() == "pop3":
                num_messages = len(connection.list()[1])
                start = max(0, num_messages - limit)
                
                for i in range(start, num_messages):
                    msg_data = connection.retr(i + 1)
                    email_body = b"\n".join(msg_data[1])
                    email_message = email.message_from_bytes(email_body)
                    emails.append(self._parse_email_message(email_message, str(i + 1)))
            
            return emails
        except Exception as e:
            logger.error(f"Failed to fetch emails: {e}")
            return emails
    
    def _parse_email_message(self, email_message: email.message.Message, email_id: Any) -> Dict[str, Any]:
        """Parse email message into dictionary"""
        # Decode subject
        subject = ""
        if email_message["Subject"]:
            decoded_subject = decode_header(email_message["Subject"])
            subject = "".join([part[0].decode(part[1] or "utf-8") if isinstance(part[0], bytes) else part[0] 
                              for part in decoded_subject])
        
        # Decode from
        from_address = email_message["From"] or ""
        
        # Get body
        body = self._get_email_body(email_message)
        
        # Get attachments
        attachments = self._get_attachments(email_message)
        
        return {
            "email_id": str(email_id),
            "subject": subject,
            "from_address": from_address,
            "to_address": email_message.get("To", ""),
            "date": email_message.get("Date", ""),
            "body": body,
            "attachments": attachments,
            "raw_message": email_message
        }
    
    def _get_email_body(self, email_message: email.message.Message) -> str:
        """Extract email body text"""
        body = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        try:
                            body = payload.decode("utf-8")
                            break
                        except UnicodeDecodeError:
                            try:
                                body = payload.decode("latin-1")
                                break
                            except:
                                pass
        else:
            payload = email_message.get_payload(decode=True)
            if payload:
                try:
                    body = payload.decode("utf-8")
                except UnicodeDecodeError:
                    try:
                        body = payload.decode("latin-1")
                    except:
                        pass
        
        return body
    
    def _get_attachments(self, email_message: email.message.Message) -> List[Dict[str, Any]]:
        """Extract attachments from email"""
        attachments = []
        
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_disposition() == "attachment":
                    filename = part.get_filename()
                    if filename:
                        decoded_filename = decode_header(filename)
                        filename = "".join([part[0].decode(part[1] or "utf-8") if isinstance(part[0], bytes) else part[0] 
                                           for part in decoded_filename])
                        
                        payload = part.get_payload(decode=True)
                        attachments.append({
                            "filename": filename,
                            "content_type": part.get_content_type(),
                            "size": len(payload) if payload else 0,
                            "data": payload
                        })
        
        return attachments
    
    async def convert_email_to_ticket(
        self,
        email_data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Optional[Ticket]:
        """
        Convert email to ticket
        
        Args:
            email_data: Email data dictionary
            user_id: User ID creating the ticket
        
        Returns:
            Created Ticket or None if failed
        """
        try:
            # Parse email to extract ticket details
            parsed_data = await self.parser.parse_email(email_data)
            
            # Identify customer from email address
            customer = self.parser.identify_customer(email_data.get("from_address", ""))
            
            # Create ticket
            ticket = Ticket(
                id=str(uuid.uuid4()),
                tenant_id=self.tenant_id,
                customer_id=customer.id if customer else None,
                title=parsed_data.get("title", email_data.get("subject", "Email Ticket")),
                description=parsed_data.get("description", email_data.get("body", "")),
                status=TicketStatus.OPEN,
                priority=parsed_data.get("priority", TicketPriority.MEDIUM),
                source="email",
                source_reference=email_data.get("email_id"),
                created_by=user_id
            )
            
            self.db.add(ticket)
            self.db.commit()
            self.db.refresh(ticket)
            
            # Handle attachments (store in MinIO or similar)
            if email_data.get("attachments"):
                # TODO: Store attachments and link to ticket
                pass
            
            return ticket
            
        except Exception as e:
            logger.error(f"Failed to convert email to ticket: {e}")
            self.db.rollback()
            return None
    
    async def process_email_tickets(
        self,
        email_config: Dict[str, Any],
        user_id: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Process emails and convert to tickets
        
        Args:
            email_config: Email configuration dictionary
            user_id: User ID processing tickets
            limit: Maximum emails to process
        
        Returns:
            Dict with processing results
        """
        results = {
            "processed": 0,
            "created": 0,
            "errors": []
        }
        
        try:
            # Connect to email server
            connection = self.connect_to_email_server(
                email_address=email_config["email_address"],
                password=email_config["password"],
                server=email_config["server"],
                port=email_config.get("port", 993),
                use_ssl=email_config.get("use_ssl", True),
                protocol=email_config.get("protocol", "imap")
            )
            
            # Fetch emails
            emails = self.fetch_emails(
                connection=connection,
                protocol=email_config.get("protocol", "imap"),
                folder=email_config.get("folder", "INBOX"),
                limit=limit
            )
            
            # Process each email
            for email_data in emails:
                results["processed"] += 1
                try:
                    ticket = await self.convert_email_to_ticket(email_data, user_id)
                    if ticket:
                        results["created"] += 1
                except Exception as e:
                    results["errors"].append({
                        "email_id": email_data.get("email_id"),
                        "error": str(e)
                    })
            
            # Close connection
            if email_config.get("protocol", "imap") == "imap":
                connection.close()
                connection.logout()
            else:
                connection.quit()
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to process email tickets: {e}")
            results["errors"].append({"error": str(e)})
            return results

