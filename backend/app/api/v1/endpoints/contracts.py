#!/usr/bin/env python3
"""
Enhanced Contracts API Endpoints
Multi-tenant contract management with AI generation, versioning, and JSON placeholders
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timezone
from pydantic import BaseModel, Field
import asyncio
import uuid

from app.core.database import get_async_db
from app.core.dependencies import get_current_user, get_current_tenant
from app.models.tenant import User, Tenant
from app.models.contracts import (
    Contract, EnhancedContractTemplate, ContractTemplateVersion,
    ContractType, ContractStatus
)
from app.models.crm import Customer
from app.models.opportunities import Opportunity
from app.services.contract_generator_service import ContractGeneratorService

router = APIRouter()


# Pydantic schemas
class ContractTemplateVersionCreate(BaseModel):
    template_id: str
    version_name: Optional[str] = None
    template_content: str
    placeholder_schema: Optional[Dict[str, Any]] = None
    default_values: Optional[Dict[str, Any]] = None
    description: Optional[str] = None


class ContractTemplateVersionResponse(BaseModel):
    id: str
    template_id: str
    version_number: int
    version_name: Optional[str]
    is_current: bool
    template_content: str
    placeholder_schema: Optional[Dict[str, Any]]
    default_values: Optional[Dict[str, Any]]
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContractTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    contract_type: str
    category: Optional[str] = None
    tags: Optional[List[str]] = None


class ContractTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    contract_type: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ContractTemplateResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    contract_type: str
    ai_generated: bool
    is_active: bool
    category: Optional[str]
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    versions: Optional[List[ContractTemplateVersionResponse]] = None

    class Config:
        from_attributes = True


class ContractCreate(BaseModel):
    customer_id: str
    template_id: Optional[str] = None
    template_version_id: Optional[str] = None
    contract_name: str
    description: Optional[str] = None
    contract_type: str
    start_date: date
    end_date: Optional[date] = None
    monthly_value: Optional[float] = None
    annual_value: Optional[float] = None
    setup_fee: Optional[float] = 0
    currency: str = "GBP"
    placeholder_values: Dict[str, Any]
    opportunity_id: Optional[str] = None
    quote_id: Optional[str] = None


class ContractUpdate(BaseModel):
    contract_name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    monthly_value: Optional[float] = None
    annual_value: Optional[float] = None
    placeholder_values: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class ContractResponse(BaseModel):
    id: str
    contract_number: str
    contract_name: str
    description: Optional[str]
    contract_type: str
    status: str
    start_date: date
    end_date: Optional[date]
    monthly_value: Optional[float]
    annual_value: Optional[float]
    customer_id: str
    template_id: Optional[str]
    opportunity_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AIContractGenerationRequest(BaseModel):
    contract_type: str
    description: str
    requirements: Optional[Dict[str, Any]] = None


# Contract Templates Endpoints
@router.get("/templates", response_model=List[ContractTemplateResponse])
async def list_contract_templates(
    contract_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """List contract templates for current tenant"""
    try:
        stmt = select(EnhancedContractTemplate).where(
            and_(
                EnhancedContractTemplate.tenant_id == current_tenant.id,
                EnhancedContractTemplate.is_deleted == False
            )
        )
        
        if contract_type:
            stmt = stmt.where(EnhancedContractTemplate.contract_type == ContractType(contract_type))
        if category:
            stmt = stmt.where(EnhancedContractTemplate.category == category)
        if is_active is not None:
            stmt = stmt.where(EnhancedContractTemplate.is_active == is_active)
        
        stmt = stmt.options(selectinload(EnhancedContractTemplate.versions))
        result = await db.execute(stmt)
        templates = result.scalars().all()
        
        response = []
        for template in templates:
            template_dict = {
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "contract_type": template.contract_type.value,
                "ai_generated": template.ai_generated,
                "is_active": template.is_active,
                "category": template.category,
                "tags": template.tags or [],
                "created_at": template.created_at,
                "updated_at": template.updated_at,
                "versions": [
                    ContractTemplateVersionResponse.model_validate(v) for v in template.versions
                ] if template.versions else []
            }
            response.append(ContractTemplateResponse(**template_dict))
        
        return response
    except Exception as e:
        print(f"Error listing contract templates: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/templates", response_model=ContractTemplateResponse)
async def create_contract_template(
    template_data: ContractTemplateCreate,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new contract template"""
    try:
        template = EnhancedContractTemplate(
            tenant_id=current_tenant.id,
            name=template_data.name,
            description=template_data.description,
            contract_type=ContractType(template_data.contract_type),
            category=template_data.category,
            tags=template_data.tags or []
        )
        
        db.add(template)
        await db.commit()
        await db.refresh(template)
        
        return ContractTemplateResponse.model_validate(template)
    except Exception as e:
        await db.rollback()
        print(f"Error creating contract template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/templates/generate", response_model=Dict[str, Any])
async def generate_contract_template_ai(
    request: AIContractGenerationRequest,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Generate a contract template using AI"""
    try:
        generator = ContractGeneratorService(db, current_tenant.id)
        
        result = await generator.generate_contract_template(
            contract_type=request.contract_type,
            description=request.description,
            requirements=request.requirements,
            user_id=current_user.id
        )
        
        return result
    except Exception as e:
        print(f"Error generating contract template: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/templates/{template_id}/versions", response_model=ContractTemplateVersionResponse)
async def create_template_version(
    template_id: str,
    version_data: ContractTemplateVersionCreate,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new version of a contract template"""
    try:
        # Get template
        stmt = select(EnhancedContractTemplate).where(
            and_(
                EnhancedContractTemplate.id == template_id,
                EnhancedContractTemplate.tenant_id == current_tenant.id
            )
        )
        result = await db.execute(stmt)
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Get current max version number
        version_stmt = select(ContractTemplateVersion).where(
            ContractTemplateVersion.template_id == template_id
        )
        version_result = await db.execute(version_stmt)
        existing_versions = version_result.scalars().all()
        
        max_version = max([v.version_number for v in existing_versions], default=0)
        new_version_number = max_version + 1
        
        # Set previous current version to false
        if existing_versions:
            update_stmt = update(ContractTemplateVersion).where(
                and_(
                    ContractTemplateVersion.template_id == template_id,
                    ContractTemplateVersion.is_current == True
                )
            ).values(is_current=False)
            await db.execute(update_stmt)
        
        # Create new version
        new_version = ContractTemplateVersion(
            tenant_id=current_tenant.id,
            template_id=template_id,
            version_number=new_version_number,
            version_name=version_data.version_name,
            is_current=True,
            template_content=version_data.template_content,
            placeholder_schema=version_data.placeholder_schema,
            default_values=version_data.default_values,
            description=version_data.description,
            created_by=current_user.id
        )
        
        db.add(new_version)
        await db.commit()
        await db.refresh(new_version)
        
        return ContractTemplateVersionResponse.model_validate(new_version)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        print(f"Error creating template version: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{template_id}", response_model=ContractTemplateResponse)
async def get_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Get a specific contract template"""
    try:
        stmt = select(EnhancedContractTemplate).where(
            and_(
                EnhancedContractTemplate.id == template_id,
                EnhancedContractTemplate.tenant_id == current_tenant.id
            )
        ).options(selectinload(EnhancedContractTemplate.versions))
        result = await db.execute(stmt)
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        template_dict = {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "contract_type": template.contract_type.value,
            "ai_generated": template.ai_generated,
            "is_active": template.is_active,
            "category": template.category,
            "tags": template.tags or [],
            "created_at": template.created_at,
            "updated_at": template.updated_at,
            "versions": [
                ContractTemplateVersionResponse.model_validate(v) for v in template.versions
            ] if template.versions else []
        }
        
        return ContractTemplateResponse(**template_dict)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/templates/{template_id}/copy", response_model=ContractTemplateResponse)
async def copy_template(
    template_id: str,
    new_name: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Copy a contract template to create a new one"""
    try:
        # Get original template
        stmt = select(EnhancedContractTemplate).where(
            and_(
                EnhancedContractTemplate.id == template_id,
                EnhancedContractTemplate.tenant_id == current_tenant.id
            )
        ).options(selectinload(EnhancedContractTemplate.versions))
        result = await db.execute(stmt)
        original = result.scalar_one_or_none()
        
        if not original:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Create new template
        new_template = EnhancedContractTemplate(
            tenant_id=current_tenant.id,
            name=new_name,
            description=original.description,
            contract_type=original.contract_type,
            category=original.category,
            tags=original.tags.copy() if original.tags else []
        )
        
        db.add(new_template)
        await db.flush()  # Get the new template ID
        
        # Copy current version if exists
        if original.versions:
            current_version = next((v for v in original.versions if v.is_current), None)
            if current_version:
                new_version = ContractTemplateVersion(
                    tenant_id=current_tenant.id,
                    template_id=new_template.id,
                    version_number=1,
                    version_name="Copied from template",
                    is_current=True,
                    template_content=current_version.template_content,
                    placeholder_schema=current_version.placeholder_schema,
                    default_values=current_version.default_values,
                    description=f"Copied from {original.name}",
                    created_by=current_user.id
                )
                db.add(new_version)
        
        await db.commit()
        await db.refresh(new_template)
        
        return ContractTemplateResponse.model_validate(new_template)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        print(f"Error copying template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Contracts Endpoints
@router.get("/", response_model=List[ContractResponse])
async def list_contracts(
    customer_id: Optional[str] = Query(None),
    opportunity_id: Optional[str] = Query(None),
    contract_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """List contracts for current tenant"""
    try:
        stmt = select(Contract).where(
            and_(
                Contract.tenant_id == current_tenant.id,
                Contract.is_deleted == False
            )
        )
        
        if customer_id:
            stmt = stmt.where(Contract.customer_id == customer_id)
        if opportunity_id:
            stmt = stmt.where(Contract.opportunity_id == opportunity_id)
        if contract_type:
            stmt = stmt.where(Contract.contract_type == ContractType(contract_type))
        if status:
            stmt = stmt.where(Contract.status == ContractStatus(status))
        
        result = await db.execute(stmt)
        contracts = result.scalars().all()
        
        # Convert contracts to response format, handling enums
        response_list = []
        for contract in contracts:
            contract_dict = {
                "id": str(contract.id),
                "contract_number": contract.contract_number,
                "contract_name": contract.contract_name,
                "description": contract.description,
                "contract_type": contract.contract_type.value if hasattr(contract.contract_type, 'value') else str(contract.contract_type),
                "status": contract.status.value if hasattr(contract.status, 'value') else str(contract.status),
                "start_date": contract.start_date,
                "end_date": contract.end_date,
                "monthly_value": float(contract.monthly_value) if contract.monthly_value else None,
                "annual_value": float(contract.annual_value) if contract.annual_value else None,
                "customer_id": str(contract.customer_id),
                "template_id": str(contract.template_id) if contract.template_id else None,
                "opportunity_id": str(contract.opportunity_id) if contract.opportunity_id else None,
                "created_at": contract.created_at,
                "updated_at": contract.updated_at
            }
            response_list.append(ContractResponse(**contract_dict))
        
        return response_list
    except Exception as e:
        print(f"Error listing contracts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=ContractResponse)
async def create_contract(
    contract_data: ContractCreate,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new contract from a template"""
    try:
        # Generate contract number
        contract_number = f"CON-{datetime.now().strftime('%y')}-{str(uuid.uuid4())[:6].upper()}"
        
        # Get template version if provided
        template_content = ""
        if contract_data.template_version_id:
            version_stmt = select(ContractTemplateVersion).where(
                ContractTemplateVersion.id == contract_data.template_version_id
            )
            version_result = await db.execute(version_stmt)
            version = version_result.scalar_one_or_none()
            if version:
                template_content = version.template_content
        elif contract_data.template_id:
            # Get current version of template
            template_stmt = select(EnhancedContractTemplate).where(
                EnhancedContractTemplate.id == contract_data.template_id
            ).options(selectinload(EnhancedContractTemplate.versions))
            template_result = await db.execute(template_stmt)
            template = template_result.scalar_one_or_none()
            if template and template.versions:
                current_version = next((v for v in template.versions if v.is_current), None)
                if current_version:
                    template_content = current_version.template_content
        
        # Fill template with values
        if template_content:
            generator = ContractGeneratorService(db, current_tenant.id)
            filled_content = generator.fill_contract_template(
                template_content,
                contract_data.placeholder_values or {}
            )
        else:
            filled_content = contract_data.contract_name  # Fallback
        
        # Create contract
        contract = Contract(
            tenant_id=current_tenant.id,
            customer_id=contract_data.customer_id,
            template_id=contract_data.template_id,
            template_version_id=contract_data.template_version_id,
            contract_number=contract_number,
            contract_name=contract_data.contract_name,
            description=contract_data.description,
            contract_type=ContractType(contract_data.contract_type),
            status=ContractStatus.DRAFT,
            start_date=contract_data.start_date,
            end_date=contract_data.end_date,
            monthly_value=contract_data.monthly_value,
            annual_value=contract_data.annual_value,
            setup_fee=contract_data.setup_fee or 0,
            currency=contract_data.currency,
            contract_content=filled_content,
            placeholder_values=contract_data.placeholder_values,
            opportunity_id=contract_data.opportunity_id,
            quote_id=contract_data.quote_id
        )
        
        db.add(contract)
        await db.commit()
        await db.refresh(contract)
        
        return ContractResponse.model_validate(contract)
    except Exception as e:
        await db.rollback()
        print(f"Error creating contract: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{contract_id}", response_model=ContractResponse)
async def get_contract(
    contract_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Get a specific contract"""
    try:
        stmt = select(Contract).where(
            and_(
                Contract.id == contract_id,
                Contract.tenant_id == current_tenant.id
            )
        )
        result = await db.execute(stmt)
        contract = result.scalar_one_or_none()
        
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        return ContractResponse.model_validate(contract)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting contract: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate", response_model=Dict[str, Any])
async def generate_contract_ai(
    request: AIContractGenerationRequest,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_db)
):
    """Generate a contract using AI"""
    try:
        generator = ContractGeneratorService(db, current_tenant.id)
        
        result = await generator.generate_contract_from_description(
            contract_type=request.contract_type,
            description=request.description,
            requirements=request.requirements,
            is_support_contract=False,
            user_id=current_user.id
        )
        
        return result
    except Exception as e:
        print(f"Error generating contract: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


class ContractGenerateQuoteRequest(BaseModel):
    generate_proposal: bool = True


@router.post("/{contract_id}/generate-quote")
async def generate_quote_from_contract(
    contract_id: str,
    request: ContractGenerateQuoteRequest = Body(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Generate a quote from a contract"""
    from app.services.contract_quote_service import ContractQuoteService
    from app.core.database import SessionLocal
    
    # Get contract
    contract_result = await db.execute(
        select(Contract).where(
            Contract.id == contract_id,
            Contract.tenant_id == current_tenant.id
        )
    )
    contract = contract_result.scalar_one_or_none()
    
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found"
        )
    
    # Convert contract to dict
    contract_data = {
        "customer_id": contract.customer_id,
        "contract_name": contract.contract_name,
        "description": contract.description,
        "contract_type": contract.contract_type.value if hasattr(contract.contract_type, 'value') else str(contract.contract_type),
        "monthly_value": float(contract.monthly_value) if contract.monthly_value else None,
        "annual_value": float(contract.annual_value) if contract.annual_value else None,
        "setup_fee": float(contract.setup_fee) if contract.setup_fee else 0,
        "sla_level": contract.sla_level,
        "terms": contract.terms,
        "included_services": contract.included_services,
        "start_date": contract.start_date.isoformat() if contract.start_date else None,
        "end_date": contract.end_date.isoformat() if contract.end_date else None
    }
    
    sync_db = SessionLocal()
    try:
        service = ContractQuoteService(sync_db, str(current_tenant.id))
        result = await service.generate_quote_from_contract(
            contract_data=contract_data,
            contract_type="regular_contract",
            generate_proposal=request.generate_proposal,
            user_id=str(current_user.id)
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to generate quote")
            )
        
        return {
            "success": True,
            "quote_id": result.get("quote_id"),
            "quote_number": result.get("quote_number"),
            "documents": [
                {
                    "id": doc.id,
                    "document_type": doc.document_type,
                    "version": doc.version
                }
                for doc in result.get("documents", [])
            ]
        }
    finally:
        sync_db.close()


@router.get("/{contract_id}/quote")
async def get_contract_quote(
    contract_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Get the associated quote for a contract"""
    from app.models.quotes import Quote
    
    # Get contract
    contract_result = await db.execute(
        select(Contract).where(
            Contract.id == contract_id,
            Contract.tenant_id == current_tenant.id
        )
    )
    contract = contract_result.scalar_one_or_none()
    
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found"
        )
    
    # Get quote if linked
    if contract.quote_id:
        quote_result = await db.execute(
            select(Quote).where(
                Quote.id == contract.quote_id,
                Quote.tenant_id == current_tenant.id
            )
        )
        quote = quote_result.scalar_one_or_none()
        
        if quote:
            return {
                "success": True,
                "quote": {
                    "id": quote.id,
                    "quote_number": quote.quote_number,
                    "title": quote.title,
                    "status": quote.status.value if hasattr(quote.status, 'value') else str(quote.status)
                }
            }
    
    return {
        "success": False,
        "message": "No associated quote found"
    }
