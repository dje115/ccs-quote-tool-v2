#!/usr/bin/env python3
"""
WhatsApp Business API webhook endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
import hmac
import hashlib
import logging

from app.core.database import get_async_db, SessionLocal
from app.core.dependencies import get_current_tenant
from app.models.tenant import Tenant
from app.services.whatsapp_service import WhatsAppService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = None,
    hub_verify_token: str = None,
    hub_challenge: str = None,
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Verify WhatsApp webhook (required by Facebook)
    
    Args:
        hub_mode: Must be "subscribe"
        hub_verify_token: Verification token
        hub_challenge: Challenge string from Facebook
    
    Returns:
        Challenge string if verified
    """
    # Get tenant WhatsApp config
    whatsapp_config = current_tenant.metadata.get("whatsapp_config") if hasattr(current_tenant, 'metadata') else {}
    verify_token = whatsapp_config.get("verify_token")
    
    if hub_mode == "subscribe" and hub_verify_token == verify_token:
        logger.info(f"WhatsApp webhook verified for tenant {current_tenant.id}")
        return int(hub_challenge)
    else:
        raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def receive_webhook(
    request: Request,
    x_hub_signature_256: str = Header(None),
    db: AsyncSession = Depends(get_async_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Receive WhatsApp webhook messages
    
    Args:
        request: FastAPI request
        x_hub_signature_256: Webhook signature for verification
    
    Returns:
        Success response
    """
    try:
        # Verify webhook signature
        body = await request.body()
        
        # Get tenant WhatsApp config
        whatsapp_config = current_tenant.metadata.get("whatsapp_config") if hasattr(current_tenant, 'metadata') else {}
        app_secret = whatsapp_config.get("app_secret")
        
        if app_secret and x_hub_signature_256:
            # Verify signature
            expected_signature = hmac.new(
                app_secret.encode(),
                body,
                hashlib.sha256
            ).hexdigest()
            
            if f"sha256={expected_signature}" != x_hub_signature_256:
                logger.warning(f"Invalid WhatsApp webhook signature for tenant {current_tenant.id}")
                raise HTTPException(status_code=403, detail="Invalid signature")
        
        # Parse webhook data
        webhook_data = await request.json()
        
        # Process message
        sync_db = SessionLocal()
        try:
            service = WhatsAppService(sync_db, str(current_tenant.id))
            ticket = await service.receive_message(webhook_data)
            
            if ticket:
                logger.info(f"Created/updated ticket {ticket.id} from WhatsApp message")
            
            return {"success": True}
        finally:
            sync_db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process WhatsApp webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send")
async def send_whatsapp_message(
    phone_number: str,
    message: str,
    ticket_id: str = None,
    db: AsyncSession = Depends(get_async_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Send WhatsApp message"""
    sync_db = SessionLocal()
    try:
        service = WhatsAppService(sync_db, str(current_tenant.id))
        result = await service.send_message(
            phone_number=phone_number,
            message=message,
            ticket_id=ticket_id
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to send message")
            )
        
        return result
    finally:
        sync_db.close()

