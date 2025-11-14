#!/usr/bin/env python3
"""
Product Service for managing product catalog
"""

from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from decimal import Decimal

from app.models.product import Product
import csv
import json


class ProductService:
    """Service for managing product catalog"""
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
    
    def create_product(
        self,
        name: str,
        base_price: float,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        code: Optional[str] = None,
        description: Optional[str] = None,
        unit: str = "each",
        cost_price: Optional[float] = None,
        supplier: Optional[str] = None,
        part_number: Optional[str] = None,
        is_service: bool = False
    ) -> Product:
        """Create a new product"""
        product = Product(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            code=code,
            name=name,
            description=description,
            category=category,
            subcategory=subcategory,
            unit=unit,
            base_price=Decimal(str(base_price)),
            cost_price=Decimal(str(cost_price)) if cost_price else None,
            supplier=supplier,
            part_number=part_number,
            is_active=True,
            is_service=is_service
        )
        
        self.db.add(product)
        self.db.flush()
        self.db.refresh(product)
        
        return product
    
    def get_product(self, product_id: str) -> Optional[Product]:
        """Get a product by ID"""
        return self.db.query(Product).filter(
            Product.id == product_id,
            Product.tenant_id == self.tenant_id
        ).first()
    
    def list_products(
        self,
        category: Optional[str] = None,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_service: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Product]:
        """List products with filters"""
        query = self.db.query(Product).filter(
            Product.tenant_id == self.tenant_id
        )
        
        if category:
            query = query.filter(Product.category == category)
        
        if search:
            search_filter = or_(
                Product.name.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%"),
                Product.code.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        if is_active is not None:
            query = query.filter(Product.is_active == is_active)
        
        if is_service is not None:
            query = query.filter(Product.is_service == is_service)
        
        return query.offset(skip).limit(limit).all()
    
    def update_product(
        self,
        product_id: str,
        **kwargs
    ) -> Optional[Product]:
        """Update a product"""
        product = self.get_product(product_id)
        
        if not product:
            return None
        
        # Update fields
        if 'name' in kwargs:
            product.name = kwargs['name']
        if 'description' in kwargs:
            product.description = kwargs['description']
        if 'category' in kwargs:
            product.category = kwargs['category']
        if 'subcategory' in kwargs:
            product.subcategory = kwargs['subcategory']
        if 'code' in kwargs:
            product.code = kwargs['code']
        if 'unit' in kwargs:
            product.unit = kwargs['unit']
        if 'base_price' in kwargs:
            product.base_price = Decimal(str(kwargs['base_price']))
        if 'cost_price' in kwargs:
            product.cost_price = Decimal(str(kwargs['cost_price'])) if kwargs['cost_price'] else None
        if 'supplier' in kwargs:
            product.supplier = kwargs['supplier']
        if 'part_number' in kwargs:
            product.part_number = kwargs['part_number']
        if 'is_active' in kwargs:
            product.is_active = kwargs['is_active']
        if 'is_service' in kwargs:
            product.is_service = kwargs['is_service']
        
        self.db.commit()
        self.db.refresh(product)
        
        return product
    
    def delete_product(self, product_id: str, soft_delete: bool = True) -> bool:
        """Delete a product"""
        product = self.get_product(product_id)
        
        if not product:
            return False
        
        if soft_delete:
            product.is_active = False
        else:
            self.db.delete(product)
        
        self.db.commit()
        return True
    
    def get_categories(self) -> List[str]:
        """Get all product categories"""
        categories = self.db.query(Product.category).filter(
            Product.tenant_id == self.tenant_id,
            Product.is_active == True,
            Product.category.isnot(None)
        ).distinct().all()
        
        return [cat[0] for cat in categories if cat[0]]
    
    def import_from_csv(self, csv_file_path: str) -> Dict[str, Any]:
        """Import products from CSV file"""
        imported = 0
        errors = []
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    try:
                        # Parse row data
                        name = row.get('name') or row.get('product_name') or ''
                        if not name:
                            continue
                        
                        base_price = float(row.get('price') or row.get('base_price') or 0)
                        category = row.get('category', '')
                        code = row.get('code') or row.get('sku', '')
                        unit = row.get('unit', 'each')
                        supplier = row.get('supplier', '')
                        part_number = row.get('part_number', '')
                        
                        # Check if product already exists
                        existing = self.db.query(Product).filter(
                            Product.tenant_id == self.tenant_id,
                            Product.code == code
                        ).first() if code else None
                        
                        if existing:
                            # Update existing
                            self.update_product(
                                existing.id,
                                name=name,
                                base_price=base_price,
                                category=category,
                                unit=unit,
                                supplier=supplier,
                                part_number=part_number
                            )
                        else:
                            # Create new
                            self.create_product(
                                name=name,
                                base_price=base_price,
                                category=category,
                                code=code,
                                unit=unit,
                                supplier=supplier,
                                part_number=part_number
                            )
                        
                        imported += 1
                    
                    except Exception as e:
                        errors.append(f"Row {row}: {str(e)}")
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'imported': imported,
                'errors': errors
            }
        
        return {
            'success': True,
            'imported': imported,
            'errors': errors
        }


# Import uuid
import uuid

