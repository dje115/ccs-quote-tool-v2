#!/usr/bin/env python3
"""
Quote Pricing Service for calculating quote pricing
Migrated from v1 PricingHelper.calculate_quote_pricing()
"""

import json
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from decimal import Decimal

from app.models.quotes import Quote, QuoteItem
from app.models.product import Product, PricingRule


class QuotePricingService:
    """Service for calculating quote pricing"""
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
    
    def calculate_quote_pricing(self, quote: Quote) -> Dict[str, Any]:
        """
        Calculate pricing for a quote
        
        Returns pricing breakdown with materials, labor, and totals
        """
        try:
            pricing_breakdown = {
                'materials': [],
                'labor': [],
                'travel': [],
                'total_materials': Decimal('0.00'),
                'total_labor': Decimal('0.00'),
                'total_travel': Decimal('0.00'),
                'subtotal': Decimal('0.00'),
                'tax_amount': Decimal('0.00'),
                'total_cost': Decimal('0.00'),
                'breakdown': {}
            }
            
            # Calculate labor costs from labour_breakdown
            if quote.labour_breakdown:
                labor_total = self._calculate_labour_cost(quote.labour_breakdown)
                pricing_breakdown['labor'] = labor_total['items']
                pricing_breakdown['total_labor'] = labor_total['total']
            
            # Calculate material costs from recommended_products
            if quote.recommended_products:
                materials_total = self._calculate_material_cost(quote.recommended_products)
                pricing_breakdown['materials'] = materials_total['items']
                pricing_breakdown['total_materials'] = materials_total['total']
            
            # Add travel costs
            if quote.travel_cost:
                pricing_breakdown['travel'].append({
                    'item': 'Travel Costs',
                    'quantity': 1,
                    'unit': 'trip',
                    'unit_price': float(quote.travel_cost),
                    'total': float(quote.travel_cost),
                    'notes': f'Distance: {quote.travel_distance_km or 0}km, Time: {quote.travel_time_minutes or 0}min'
                })
                pricing_breakdown['total_travel'] = Decimal(str(quote.travel_cost))
            
            # Calculate subtotal
            pricing_breakdown['subtotal'] = (
                pricing_breakdown['total_materials'] +
                pricing_breakdown['total_labor'] +
                pricing_breakdown['total_travel']
            )
            
            # Calculate tax
            tax_rate = float(quote.tax_rate) if quote.tax_rate else 0.20
            pricing_breakdown['tax_amount'] = pricing_breakdown['subtotal'] * Decimal(str(tax_rate))
            
            # Calculate total
            pricing_breakdown['total_cost'] = pricing_breakdown['subtotal'] + pricing_breakdown['tax_amount']
            
            # Update quote totals
            quote.subtotal = float(pricing_breakdown['subtotal'])
            quote.tax_amount = float(pricing_breakdown['tax_amount'])
            quote.total_amount = float(pricing_breakdown['total_cost'])
            
            return pricing_breakdown
        
        except Exception as e:
            print(f"[QUOTE PRICING] Error calculating pricing: {e}")
            import traceback
            traceback.print_exc()
            return {
                'error': str(e),
                'materials': [],
                'labor': [],
                'total_materials': Decimal('0.00'),
                'total_labor': Decimal('0.00'),
                'total_cost': Decimal('0.00')
            }
    
    def _calculate_labour_cost(self, labour_breakdown: Any) -> Dict[str, Any]:
        """Calculate labor costs from labour breakdown"""
        items = []
        total = Decimal('0.00')
        
        try:
            # Parse JSON if string
            if isinstance(labour_breakdown, str):
                labour_data = json.loads(labour_breakdown)
            else:
                labour_data = labour_breakdown
            
            if not isinstance(labour_data, list):
                return {'items': items, 'total': total}
            
            # Calculate total hours and find day rate
            total_hours = 0
            day_rate = None
            
            for item in labour_data:
                days = item.get('days', 0) or 0
                hours = item.get('hours', 0) or 0
                rate = item.get('day_rate', 0) or item.get('rate', 0)
                
                if rate and not day_rate:
                    day_rate = float(rate)
                
                if days:
                    total_hours += float(days) * 8
                elif hours:
                    total_hours += float(hours)
            
            # Calculate total cost
            if total_hours > 0 and day_rate:
                # Round to nearest 0.5 day
                total_days = max(0.5, round(total_hours / 8 * 2) / 2)
                total_cost = Decimal(str(total_days * day_rate))
                
                items.append({
                    'item': 'Project Labour (All Tasks)',
                    'quantity': total_days,
                    'unit': 'days',
                    'unit_price': day_rate,
                    'total': float(total_cost),
                    'notes': f'Total project time: {total_hours:.1f} hours rounded to {total_days} days'
                })
                
                total = total_cost
            else:
                # Fallback: use individual task costs
                for item in labour_data:
                    cost = item.get('cost', 0) or 0
                    days = item.get('days', 0) or 0
                    rate = item.get('day_rate', 0) or item.get('rate', 0) or 0
                    
                    if cost:
                        item_cost = Decimal(str(float(cost)))
                    elif days and rate:
                        item_cost = Decimal(str(float(days) * float(rate)))
                    else:
                        continue
                    
                    items.append({
                        'item': item.get('task', 'Labour'),
                        'quantity': float(days) if days else 1,
                        'unit': 'days',
                        'unit_price': float(rate) if rate else float(item_cost),
                        'total': float(item_cost)
                    })
                    
                    total += item_cost
        
        except Exception as e:
            print(f"[QUOTE PRICING] Error calculating labour cost: {e}")
        
        return {'items': items, 'total': total}
    
    def _calculate_material_cost(self, recommended_products: Any) -> Dict[str, Any]:
        """Calculate material costs from recommended products"""
        items = []
        total = Decimal('0.00')
        
        try:
            # Parse JSON if string
            if isinstance(recommended_products, str):
                products_data = json.loads(recommended_products)
            else:
                products_data = recommended_products
            
            if not isinstance(products_data, list):
                return {'items': items, 'total': total}
            
            for product in products_data:
                # Extract pricing
                unit_price = product.get('unit_price', 0) or 0
                total_price = product.get('total_price', 0) or 0
                quantity = product.get('quantity', 1) or 1
                
                # Convert to numbers
                try:
                    if isinstance(quantity, str):
                        import re
                        quantity_match = re.search(r'(\d+\.?\d*)', str(quantity))
                        quantity = float(quantity_match.group(1)) if quantity_match else 1.0
                    else:
                        quantity = float(quantity)
                    
                    unit_price = float(unit_price) if unit_price else 0
                    total_price = float(total_price) if total_price else 0
                except (ValueError, TypeError):
                    quantity = 1.0
                    unit_price = 0
                    total_price = 0
                
                # Use provided pricing or calculate
                if unit_price > 0 and total_price > 0:
                    item_total = Decimal(str(total_price))
                elif unit_price > 0:
                    item_total = Decimal(str(unit_price * quantity))
                else:
                    # Try to get from product catalog
                    product_name = product.get('item') or product.get('name') or ''
                    catalog_price = self._get_product_price(product_name)
                    if catalog_price:
                        unit_price = catalog_price
                        item_total = Decimal(str(catalog_price * quantity))
                    else:
                        continue  # Skip if no pricing available
                
                items.append({
                    'item': product.get('item') or product.get('name', ''),
                    'quantity': quantity,
                    'unit': product.get('unit', 'each'),
                    'unit_price': unit_price if unit_price > 0 else float(item_total / Decimal(str(quantity))),
                    'total': float(item_total),
                    'part_number': product.get('part_number', ''),
                    'category': product.get('category', ''),
                    'pricing_source': product.get('pricing_source', 'estimated')
                })
                
                total += item_total
        
        except Exception as e:
            print(f"[QUOTE PRICING] Error calculating material cost: {e}")
            import traceback
            traceback.print_exc()
        
        return {'items': items, 'total': total}
    
    def _get_product_price(self, product_name: str) -> Optional[float]:
        """Get product price from catalog"""
        try:
            # Search products table
            product = self.db.query(Product).filter(
                Product.tenant_id == self.tenant_id,
                Product.is_active == True,
                Product.name.ilike(f"%{product_name}%")
            ).first()
            
            if product:
                return float(product.base_price)
        except Exception as e:
            print(f"[QUOTE PRICING] Error getting product price: {e}")
        
        return None
    
    def apply_pricing_rules(self, quote: Quote, rules: Optional[List[PricingRule]] = None) -> Dict[str, Any]:
        """Apply pricing rules (volume discounts, bundles, etc.)"""
        # TODO: Implement pricing rules engine
        # This would check conditions and apply discounts
        return {
            'discounts_applied': [],
            'total_discount': Decimal('0.00')
        }
    
    def get_product_pricing(self, products: List[str]) -> Dict[str, float]:
        """Get pricing for a list of products"""
        pricing = {}
        
        for product_name in products:
            price = self._get_product_price(product_name)
            if price:
                pricing[product_name] = price
        
        return pricing


