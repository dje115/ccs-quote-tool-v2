#!/usr/bin/env python3
"""
Supplier Pricing Service
Integrates web scraping with database caching for multi-tenant quote system
Migrated from v1 PricingService
"""

import logging
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.supplier import Supplier, SupplierCategory, SupplierPricing
from app.services.web_pricing_scraper import WebPricingScraper

logger = logging.getLogger(__name__)


class SupplierPricingService:
    """Service for managing supplier pricing with caching"""
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.scraper = WebPricingScraper()
        self.cache_duration = timedelta(hours=24)  # Cache pricing for 24 hours
    
    async def get_product_price(
        self,
        supplier_name: str,
        product_name: str,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Get pricing for a product with caching
        
        Args:
            supplier_name: Name of the supplier
            product_name: Name of the product
            force_refresh: If True, bypass cache and fetch fresh pricing
        
        Returns:
            Pricing result dictionary
        """
        try:
            # Clean inputs
            supplier_name = supplier_name.strip()
            product_name = product_name.strip()
            
            # Check if we have a cached price that's still valid
            if not force_refresh:
                cached_price = self._get_cached_price(supplier_name, product_name)
                if cached_price:
                    return cached_price
            
            # Try to get pricing from web scraper
            pricing_result = await self.scraper.get_product_pricing(supplier_name, product_name)
            
            if pricing_result.get('success'):
                # Cache the result
                await self._cache_price(supplier_name, product_name, pricing_result)
                return pricing_result
            else:
                # Return cached price even if expired, or None if no cache
                cached_price = self._get_cached_price(supplier_name, product_name, ignore_expiry=True)
                return cached_price if cached_price else pricing_result
                
        except Exception as e:
            logger.error(f"Error getting product price: {e}")
            # Return cached price if available
            cached_price = self._get_cached_price(supplier_name, product_name, ignore_expiry=True)
            return cached_price if cached_price else {
                'success': False,
                'error': str(e)
            }
    
    def _get_cached_price(
        self,
        supplier_name: str,
        product_name: str,
        ignore_expiry: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Get cached price from database"""
        try:
            # Find supplier
            supplier = self.db.query(Supplier).filter(
                and_(
                    Supplier.tenant_id == self.tenant_id,
                    Supplier.name.ilike(f'%{supplier_name}%'),
                    Supplier.is_active == True
                )
            ).first()
            
            if not supplier:
                return None
            
            # Find cached pricing
            cached_pricing = self.db.query(SupplierPricing).filter(
                and_(
                    SupplierPricing.supplier_id == supplier.id,
                    SupplierPricing.product_name.ilike(f'%{product_name}%'),
                    SupplierPricing.is_active == True
                )
            ).order_by(SupplierPricing.last_updated.desc()).first()
            
            if not cached_pricing:
                return None
            
            # Check if cache is still valid
            if not ignore_expiry:
                if datetime.utcnow() - cached_pricing.last_updated.replace(tzinfo=None) > self.cache_duration:
                    return None
            
            return {
                'success': True,
                'price': float(cached_pricing.price),
                'currency': cached_pricing.currency,
                'source': 'cached',
                'cached_at': cached_pricing.last_updated.isoformat(),
                'product_name': cached_pricing.product_name,
                'supplier': supplier_name
            }
            
        except Exception as e:
            logger.error(f"Error getting cached price: {e}")
            return None
    
    async def _cache_price(
        self,
        supplier_name: str,
        product_name: str,
        pricing_result: Dict[str, Any]
    ):
        """Cache pricing result in database"""
        try:
            # Find supplier
            supplier = self.db.query(Supplier).filter(
                and_(
                    Supplier.tenant_id == self.tenant_id,
                    Supplier.name.ilike(f'%{supplier_name}%'),
                    Supplier.is_active == True
                )
            ).first()
            
            if not supplier:
                logger.warning(f"Supplier not found: {supplier_name}")
                return
            
            # Deactivate old cached entries for this product
            old_entries = self.db.query(SupplierPricing).filter(
                and_(
                    SupplierPricing.supplier_id == supplier.id,
                    SupplierPricing.product_name.ilike(f'%{product_name}%')
                )
            ).all()
            
            for entry in old_entries:
                entry.is_active = False
            
            # Create new cached entry
            cached_pricing = SupplierPricing(
                supplier_id=supplier.id,
                product_name=pricing_result.get('product_name', product_name),
                product_code=pricing_result.get('product_code', ''),
                price=pricing_result.get('price', 0),
                currency=pricing_result.get('currency', 'GBP'),
                is_active=True
            )
            
            self.db.add(cached_pricing)
            self.db.commit()
            
            logger.info(f"Cached pricing for {supplier_name} - {product_name}: £{pricing_result.get('price')}")
            
        except Exception as e:
            logger.error(f"Error caching price: {e}")
            self.db.rollback()
    
    async def refresh_all_pricing(self) -> Dict[str, Any]:
        """Refresh pricing for all active preferred suppliers"""
        try:
            suppliers = self.db.query(Supplier).filter(
                and_(
                    Supplier.tenant_id == self.tenant_id,
                    Supplier.is_active == True,
                    Supplier.is_preferred == True
                )
            ).all()
            
            refreshed_count = 0
            for supplier in suppliers:
                # Get common products for this supplier category
                products = self._get_common_products_for_supplier(supplier)
                
                for product in products:
                    result = await self.get_product_price(supplier.name, product, force_refresh=True)
                    if result and result.get('success'):
                        refreshed_count += 1
                        logger.info(f"Refreshed pricing for {supplier.name} - {product}")
            
            return {
                'success': True,
                'refreshed_count': refreshed_count,
                'message': f'Refreshed pricing for {refreshed_count} products'
            }
            
        except Exception as e:
            logger.error(f"Error refreshing all pricing: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_common_products_for_supplier(self, supplier: Supplier) -> List[str]:
        """Get common products for a supplier based on their category"""
        category_name = supplier.category.name.lower() if supplier.category else ''
        
        common_products = {
            'wifi': [
                'U6-Pro Access Point',
                'U6-Lite Access Point',
                'U6-LR Access Point',
                'Dream Machine',
                'Dream Machine Pro'
            ],
            'cabling': [
                'Cat6 UTP Cable 305m',
                '24-port Cat6 Patch Panel',
                'RJ45 Keystone Jack',
                'Cat6 Face Plate'
            ],
            'cctv': [
                'G4 Pro Camera',
                'G4 Bullet Camera',
                'G4 Dome Camera',
                'NVR Pro'
            ],
            'door entry': [
                'Paxton Net2',
                'Comelit Video Door Entry',
                'BPT Intercom'
            ],
            'network equipment': [
                '24-port PoE Switch',
                '48-port Switch',
                'Router',
                'Firewall'
            ]
        }
        
        return common_products.get(category_name, [])
    
    def get_supplier_pricing_summary(self) -> List[Dict[str, Any]]:
        """Get summary of cached pricing by supplier"""
        try:
            suppliers = self.db.query(Supplier).filter(
                and_(
                    Supplier.tenant_id == self.tenant_id,
                    Supplier.is_active == True
                )
            ).all()
            
            summary = []
            for supplier in suppliers:
                cached_count = self.db.query(SupplierPricing).filter(
                    and_(
                        SupplierPricing.supplier_id == supplier.id,
                        SupplierPricing.is_active == True
                    )
                ).count()
                
                summary.append({
                    'supplier_id': supplier.id,
                    'supplier_name': supplier.name,
                    'category': supplier.category.name if supplier.category else 'Unknown',
                    'cached_products': cached_count,
                    'is_preferred': supplier.is_preferred
                })
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting pricing summary: {e}")
            return []
    
    async def close(self):
        """Close the scraper session"""
        await self.scraper.close()


