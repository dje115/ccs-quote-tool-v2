#!/usr/bin/env python3
"""
Email Service
Handles email sending using fastapi-mail with MailHog integration for testing
"""

from typing import List, Optional, Dict, Any
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from jinja2 import Template
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails"""
    
    def __init__(self):
        """Initialize email service with configuration"""
        self.config = ConnectionConfig(
            MAIL_USERNAME=settings.SMTP_USERNAME,
            MAIL_PASSWORD=settings.SMTP_PASSWORD,
            MAIL_FROM=settings.SMTP_FROM_EMAIL,
            MAIL_FROM_NAME=settings.SMTP_FROM_NAME,
            MAIL_PORT=settings.SMTP_PORT,
            MAIL_SERVER=settings.SMTP_HOST,
            MAIL_STARTTLS=settings.SMTP_TLS,
            MAIL_SSL_TLS=False,  # MailHog doesn't use SSL
            USE_CREDENTIALS=bool(settings.SMTP_USERNAME and settings.SMTP_PASSWORD),
            VALIDATE_CERTS=False,  # MailHog doesn't need cert validation
            TEMPLATE_FOLDER=None  # We'll handle templates manually
        )
        self.fastmail = FastMail(self.config)
    
    async def send_email(
        self,
        to: str | List[str],
        subject: str,
        body: str,
        body_html: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Send an email
        
        Args:
            to: Recipient email address(es)
            subject: Email subject
            body: Plain text body
            body_html: Optional HTML body
            cc: Optional CC recipients
            bcc: Optional BCC recipients
            attachments: Optional list of attachments (dict with 'file' and 'filename' keys)
        
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Convert single email to list
            recipients = [to] if isinstance(to, str) else to
            
            message = MessageSchema(
                subject=subject,
                recipients=recipients,
                body=body,
                subtype=MessageType.html if body_html else MessageType.plain,
                cc=cc or [],
                bcc=bcc or [],
                attachments=attachments or []
            )
            
            if body_html:
                message.body = body_html
                message.subtype = MessageType.html
            
            await self.fastmail.send_message(message)
            logger.info(f"Email sent successfully to {recipients}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    async def send_template_email(
        self,
        to: str | List[str],
        subject: str,
        template: str,
        template_vars: Dict[str, Any],
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """
        Send an email using a Jinja2 template
        
        Args:
            to: Recipient email address(es)
            subject: Email subject
            template: Jinja2 template string
            template_vars: Variables to render in template
            cc: Optional CC recipients
            bcc: Optional BCC recipients
        
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Render template
            jinja_template = Template(template)
            body_html = jinja_template.render(**template_vars)
            
            # Also create plain text version (simple strip of HTML tags)
            body_plain = self._html_to_plain_text(body_html)
            
            return await self.send_email(
                to=to,
                subject=subject,
                body=body_plain,
                body_html=body_html,
                cc=cc,
                bcc=bcc
            )
            
        except Exception as e:
            logger.error(f"Failed to send template email: {e}")
            return False
    
    def _html_to_plain_text(self, html: str) -> str:
        """Convert HTML to plain text (simple implementation)"""
        import re
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html)
        # Decode HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()


# Global email service instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create email service instance"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service




