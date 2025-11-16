#!/usr/bin/env python3
"""
Supplier Service for managing suppliers and categories
Multi-tenant aware
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.supplier import Supplier, SupplierCategory, SupplierPricing


class SupplierService:
    """Service for managing suppliers"""
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
    
    # Category methods
    def list_categories(self) -> List[SupplierCategory]:
        """List all supplier categories for tenant"""
        return self.db.query(SupplierCategory).filter(
            and_(
                SupplierCategory.tenant_id == self.tenant_id,
                SupplierCategory.is_active == True
            )
        ).all()
    
    def get_category(self, category_id: str) -> Optional[SupplierCategory]:
        """Get a supplier category"""
        return self.db.query(SupplierCategory).filter(
            and_(
                SupplierCategory.id == category_id,
                SupplierCategory.tenant_id == self.tenant_id
            )
        ).first()
    
    def create_category(self, name: str, description: Optional[str] = None) -> SupplierCategory:
        """Create a new supplier category"""
        category = SupplierCategory(
            tenant_id=self.tenant_id,
            name=name,
            description=description
        )
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category
    
    def update_category(
        self,
        category_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Optional[SupplierCategory]:
        """Update a supplier category"""
        category = self.get_category(category_id)
        if not category:
            return None
        
        if name is not None:
            category.name = name
        if description is not None:
            category.description = description
        if is_active is not None:
            category.is_active = is_active
        
        self.db.commit()
        self.db.refresh(category)
        return category
    
    def delete_category(self, category_id: str) -> bool:
        """Delete a supplier category"""
        category = self.get_category(category_id)
        if not category:
            return False
        
        # Soft delete
        category.is_active = False
        self.db.commit()
        return True
    
    # Supplier methods
    def list_suppliers(
        self,
        category_id: Optional[str] = None,
        is_preferred: Optional[bool] = None,
        is_active: Optional[bool] = True
    ) -> List[Supplier]:
        """List suppliers with optional filters"""
        from sqlalchemy.orm import joinedload
        query = self.db.query(Supplier).options(joinedload(Supplier.category)).filter(
            Supplier.tenant_id == self.tenant_id
        )
        
        if category_id:
            query = query.filter(Supplier.category_id == category_id)
        if is_preferred is not None:
            query = query.filter(Supplier.is_preferred == is_preferred)
        if is_active is not None:
            query = query.filter(Supplier.is_active == is_active)
        
        return query.all()
    
    def get_supplier(self, supplier_id: str) -> Optional[Supplier]:
        """Get a supplier"""
        return self.db.query(Supplier).filter(
            and_(
                Supplier.id == supplier_id,
                Supplier.tenant_id == self.tenant_id
            )
        ).first()
    
    def create_supplier(
        self,
        category_id: str,
        name: str,
        website: Optional[str] = None,
        pricing_url: Optional[str] = None,
        api_key: Optional[str] = None,
        notes: Optional[str] = None,
        scraping_config: Optional[str] = None,
        scraping_enabled: bool = True,
        scraping_method: str = "generic",
        is_preferred: bool = False
    ) -> Optional[Supplier]:
        """Create a new supplier"""
        # Verify category belongs to tenant
        category = self.get_category(category_id)
        if not category:
            return None
        
        supplier = Supplier(
            tenant_id=self.tenant_id,
            category_id=category_id,
            name=name,
            website=website,
            pricing_url=pricing_url,
            api_key=api_key,
            notes=notes,
            scraping_config=scraping_config,
            scraping_enabled=scraping_enabled,
            scraping_method=scraping_method,
            is_preferred=is_preferred
        )
        
        self.db.add(supplier)
        try:
            self.db.commit()
            self.db.refresh(supplier)
            # Eager load category relationship
            from sqlalchemy.orm import joinedload
            supplier = self.db.query(Supplier).options(joinedload(Supplier.category)).filter(
                Supplier.id == supplier.id
            ).first()
            return supplier
        except Exception as e:
            self.db.rollback()
            print(f"[SUPPLIER SERVICE] Error creating supplier: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def update_supplier(
        self,
        supplier_id: str,
        name: Optional[str] = None,
        category_id: Optional[str] = None,
        website: Optional[str] = None,
        pricing_url: Optional[str] = None,
        api_key: Optional[str] = None,
        notes: Optional[str] = None,
        scraping_config: Optional[str] = None,
        scraping_enabled: Optional[bool] = None,
        scraping_method: Optional[str] = None,
        is_preferred: Optional[bool] = None,
        is_active: Optional[bool] = None
    ) -> Optional[Supplier]:
        """Update a supplier"""
        supplier = self.get_supplier(supplier_id)
        if not supplier:
            return None
        
        if name is not None:
            supplier.name = name
        if category_id is not None:
            # Verify category belongs to tenant
            category = self.get_category(category_id)
            if category:
                supplier.category_id = category_id
        if website is not None:
            supplier.website = website
        if pricing_url is not None:
            supplier.pricing_url = pricing_url
        if api_key is not None:
            supplier.api_key = api_key
        if notes is not None:
            supplier.notes = notes
        if scraping_config is not None:
            supplier.scraping_config = scraping_config
        if scraping_enabled is not None:
            supplier.scraping_enabled = scraping_enabled
        if scraping_method is not None:
            supplier.scraping_method = scraping_method
        if is_preferred is not None:
            supplier.is_preferred = is_preferred
        if is_active is not None:
            supplier.is_active = is_active
        
        self.db.commit()
        self.db.refresh(supplier)
        return supplier
    
    def delete_supplier(self, supplier_id: str) -> bool:
        """Delete a supplier (soft delete)"""
        supplier = self.get_supplier(supplier_id)
        if not supplier:
            return False
        
        supplier.is_active = False
        self.db.commit()
        return True
    
    def get_supplier_pricing_count(self, supplier_id: str) -> int:
        """Get count of cached pricing items for a supplier"""
        return self.db.query(SupplierPricing).filter(
            and_(
                SupplierPricing.supplier_id == supplier_id,
                SupplierPricing.is_active == True
            )
        ).count()

