"""
Email testing endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.tenant import User, UserRole
from app.services.email_service import get_email_service

router = APIRouter()


class EmailTestRequest(BaseModel):
    """Request model for testing email"""
    to: EmailStr | List[EmailStr]
    subject: str = "Test Email from CCS Quote Tool"
    body: str = "This is a test email sent from the CCS Quote Tool system."
    body_html: Optional[str] = None


class EmailTestResponse(BaseModel):
    """Response model for email test"""
    success: bool
    message: str


@router.post("/test", response_model=EmailTestResponse)
async def test_email(
    request: EmailTestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Test email sending (admin only)
    
    This endpoint allows administrators to test email configuration
    by sending a test email. In development, emails are captured by MailHog.
    """
    # Check if user is admin
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    email_service = get_email_service()
    
    success = await email_service.send_email(
        to=request.to,
        subject=request.subject,
        body=request.body,
        body_html=request.body_html
    )
    
    if success:
        return EmailTestResponse(
            success=True,
            message=f"Test email sent successfully to {request.to}. Check MailHog at http://localhost:3006 if in development mode."
        )
    else:
        return EmailTestResponse(
            success=False,
            message="Failed to send test email. Please check email configuration."
        )


