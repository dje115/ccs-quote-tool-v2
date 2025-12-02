#!/usr/bin/env python3
"""
Quote Pricing Service

Handles pricing integration from feeds:
- Pull from supplier_pricing table
- Real-time price updates
- Price history tracking
- Markup calculations
"""

import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime, timedelta

from app.models.supplier import SupplierPricing, Supplier
from app.models.product import Product
from app.services.supplier_pricing_service import SupplierPricingService
from app.services.pricing_config_service import PricingConfigService
from app.models.pricing_config import PricingConfigType

logger = logging.getLogger(__name__)


class QuotePricingService:
    """
    Service for quote pricing integration
    
    Features:
    - Pull pricing from supplier feeds
    - Calculate markups
    - Track price history
    - Real-time price updates
    """
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.supplier_pricing_service = SupplierPricingService(db, tenant_id)
        self.pricing_config_service = PricingConfigService(db, tenant_id)
    
    def get_supplier_pricing(
        self,
        product_name: Optional[str] = None,
        product_code: Optional[str] = None,
        supplier_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get supplier pricing from feeds
        
        Args:
            product_name: Filter by product name
            product_code: Filter by product code
            supplier_id: Filter by supplier
        
        Returns:
            List of pricing items
        """
        query = self.db.query(SupplierPricing).join(
            SupplierPricing.supplier
        ).filter(
            SupplierPricing.supplier.has(tenant_id=self.tenant_id),
            SupplierPricing.is_active == True,
            SupplierPricing.verification_status == "verified"
        )
        
        if product_name:
            query = query.filter(SupplierPricing.product_name.ilike(f"%{product_name}%"))
        
        if product_code:
            query = query.filter(SupplierPricing.product_code == product_code)
        
        if supplier_id:
            query = query.filter(SupplierPricing.supplier_id == supplier_id)
        
        results = query.limit(100).all()
        
        return [
            {
                "supplier_id": item.supplier_id,
                "product_name": item.product_name,
                "product_code": item.product_code,
                "cost_price": float(item.price),
                "sell_price": float(item.price * Decimal("1.2")),  # 20% markup default
                "currency": item.currency,
                "confidence_score": float(item.confidence_score)
            }
            for item in results
        ]
    
    def calculate_markup(
        self,
        cost_price: float,
        markup_percentage: float = 20.0
    ) -> float:
        """
        Calculate sell price with markup
        
        Args:
            cost_price: Cost price from supplier
            markup_percentage: Markup percentage (default 20%)
        
        Returns:
            Sell price with markup
        """
        return cost_price * (1 + markup_percentage / 100)
    
    def get_price_history(
        self,
        product_code: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get price history for a product
        
        Args:
            product_code: Product code
            days: Number of days to look back
        
        Returns:
            List of price history entries
        """
        from datetime import datetime, timedelta, timezone
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # This would query ProductContentHistory if implemented
        # For now, return empty list
        return []
    
    async def get_real_time_pricing(
        self,
        product_name: str,
        supplier_name: Optional[str] = None,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Get real-time pricing from supplier feeds
        
        Args:
            product_name: Product name to price
            supplier_name: Optional supplier name
            force_refresh: Force refresh from web scraper
        
        Returns:
            Dict with pricing information
        """
        try:
            # Try to get from SupplierPricingService (includes web scraping)
            if supplier_name:
                result = await self.supplier_pricing_service.get_product_price(
                    supplier_name=supplier_name,
                    product_name=product_name,
                    force_refresh=force_refresh
                )
                
                if result.get("success"):
                    return {
                        "success": True,
                        "cost_price": result.get("price", 0),
                        "sell_price": self.calculate_markup(result.get("price", 0)),
                        "source": result.get("source", "supplier_pricing"),
                        "supplier": supplier_name,
                        "product_name": product_name,
                        "currency": result.get("currency", "GBP"),
                        "confidence": result.get("confidence_score", 0.8)
                    }
            
            # Fallback to database pricing
            pricing_items = self.get_supplier_pricing(
                product_name=product_name,
                supplier_id=None
            )
            
            if pricing_items:
                # Return best match (highest confidence)
                best_match = max(pricing_items, key=lambda x: x.get("confidence_score", 0))
                return {
                    "success": True,
                    "cost_price": best_match["cost_price"],
                    "sell_price": best_match["sell_price"],
                    "source": "database",
                    "supplier": best_match.get("supplier_id"),
                    "product_name": product_name,
                    "currency": best_match.get("currency", "GBP"),
                    "confidence": best_match.get("confidence_score", 0.5)
                }
            
            # Fallback to product catalog
            product = self.db.query(Product).filter(
                Product.tenant_id == self.tenant_id,
                Product.name.ilike(f"%{product_name}%"),
                Product.is_active == True
            ).first()
            
            if product:
                return {
                    "success": True,
                    "cost_price": float(product.cost_price) if product.cost_price else 0,
                    "sell_price": float(product.base_price) if product.base_price else 0,
                    "source": "product_catalog",
                    "product_id": product.id,
                    "product_name": product_name,
                    "currency": "GBP",
                    "confidence": 0.7
                }
            
            return {
                "success": False,
                "error": f"No pricing found for {product_name}"
            }
            
        except Exception as e:
            logger.error(f"Failed to get real-time pricing: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def calculate_labor_cost(
        self,
        role: str,  # "engineer", "technician", "project_manager"
        hours: float,
        skill_level: Optional[str] = None,  # "junior", "standard", "senior", "specialist"
        include_overtime: bool = False,
        overtime_hours: float = 0.0,
        include_travel: bool = False
    ) -> Dict[str, Any]:
        """
        Calculate labor cost using day rate charts
        
        Args:
            role: Role type
            hours: Number of hours
            skill_level: Skill level
            include_overtime: Include overtime calculation
            overtime_hours: Overtime hours
            include_travel: Include travel costs
        
        Returns:
            Dict with labor cost breakdown
        """
        try:
            # Get day rate configs
            day_rates = self.pricing_config_service.get_day_rates(
                role=role,
                skill_level=skill_level
            )
            
            if not day_rates:
                return {
                    "success": False,
                    "error": f"No day rate found for role: {role}"
                }
            
            # Use first matching rate (or best match)
            day_rate = day_rates[0]
            base_rate = float(day_rate.base_rate)
            config_data = day_rate.config_data or {}
            hours_per_day = config_data.get("hours_per_day", 8)
            
            # Calculate base cost
            days = hours / hours_per_day
            base_cost = base_rate * days
            
            # Calculate overtime if applicable
            overtime_cost = 0.0
            if include_overtime and overtime_hours > 0:
                overtime_multiplier = config_data.get("overtime_multiplier", 1.5)
                hourly_rate = base_rate / hours_per_day
                overtime_cost = hourly_rate * overtime_hours * overtime_multiplier
            
            # Calculate travel if applicable
            travel_cost = 0.0
            if include_travel:
                travel_uplift = config_data.get("travel_uplift_percentage", 0)
                if travel_uplift:
                    travel_cost = base_cost * (travel_uplift / 100)
            
            total_cost = base_cost + overtime_cost + travel_cost
            
            return {
                "success": True,
                "base_cost": base_cost,
                "overtime_cost": overtime_cost,
                "travel_cost": travel_cost,
                "total_cost": total_cost,
                "breakdown": {
                    "role": role,
                    "skill_level": skill_level,
                    "hours": hours,
                    "days": days,
                    "base_rate_per_day": base_rate,
                    "overtime_hours": overtime_hours,
                    "hourly_rate": base_rate / hours_per_day
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate labor cost: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def calculate_quote_totals(
        self,
        items: List[Dict[str, Any]],
        tax_rate: float = 0.20
    ) -> Dict[str, Any]:
        """
        Calculate quote totals from items
        
        Args:
            items: List of quote items with pricing
            tax_rate: Tax rate (default 20% VAT)
        
        Returns:
            Dict with totals breakdown
        """
        subtotal = 0.0
        labor_total = 0.0
        materials_total = 0.0
        
        for item in items:
            total_price = float(item.get("total_price", 0))
            category = item.get("category", "").lower()
            
            subtotal += total_price
            
            if "labor" in category or "labour" in category:
                labor_total += total_price
            else:
                materials_total += total_price
        
        tax_amount = subtotal * tax_rate
        total_amount = subtotal + tax_amount
        
        return {
            "subtotal": subtotal,
            "labor_total": labor_total,
            "materials_total": materials_total,
            "tax_rate": tax_rate,
            "tax_amount": tax_amount,
            "total_amount": total_amount
        }
    
    async def update_quote_pricing(
        self,
        quote_id: str,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Update quote pricing from latest supplier feeds
        
        Args:
            quote_id: Quote ID to update
            force_refresh: Force refresh from web scraper
        
        Returns:
            Dict with update results
        """
        from app.models.quotes import Quote, QuoteItem
        
        quote = self.db.query(Quote).filter(
            Quote.id == quote_id,
            Quote.tenant_id == self.tenant_id
        ).first()
        
        if not quote:
            return {
                "success": False,
                "error": "Quote not found"
            }
        
        updated_items = []
        errors = []
        
        # Update each quote item
        for item in quote.items:
            if item.description:
                # Try to get updated pricing
                pricing = await self.get_real_time_pricing(
                    product_name=item.description,
                    force_refresh=force_refresh
                )
                
                if pricing.get("success"):
                    # Update item pricing
                    old_price = float(item.unit_price)
                    new_price = pricing.get("sell_price", old_price)
                    
                    if abs(new_price - old_price) > 0.01:  # Only update if significant change
                        item.unit_price = new_price
                        item.total_price = float(item.quantity) * new_price
                        updated_items.append({
                            "item_id": item.id,
                            "description": item.description,
                            "old_price": old_price,
                            "new_price": new_price
                        })
                else:
                    errors.append({
                        "item_id": item.id,
                        "description": item.description,
                        "error": pricing.get("error", "Failed to get pricing")
                    })
        
        # Recalculate quote totals
        quote.calculate_totals()
        
        self.db.commit()
        
        return {
            "success": True,
            "updated_items": updated_items,
            "errors": errors,
            "new_total": float(quote.total_amount)
        }
