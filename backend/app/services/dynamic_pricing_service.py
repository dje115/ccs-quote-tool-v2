#!/usr/bin/env python3
"""
Dynamic Pricing Rules Engine
Handles FX tables, competitor matching, volume discounts, seasonal pricing, and dynamic rule evaluation
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime, timezone
from decimal import Decimal
import logging
import json
import uuid

from app.models.pricing_config import TenantPricingConfig, PricingConfigType
from app.services.price_intelligence_service import PriceIntelligenceService
from app.services.ai_provider_service import AIProviderService
from app.models.ai_prompt import PromptCategory

logger = logging.getLogger(__name__)


class DynamicPricingService:
    """Service for dynamic pricing rules and calculations"""
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.price_intel = PriceIntelligenceService(db, tenant_id)
        self.ai_service = AIProviderService(db, tenant_id=tenant_id)
    
    def calculate_dynamic_price(
        self,
        base_price: Decimal,
        product_name: str,
        quantity: int = 1,
        customer_id: Optional[str] = None,
        currency: str = "GBP",
        apply_rules: bool = True
    ) -> Dict[str, Any]:
        """
        Calculate dynamic price with all applicable rules
        
        Args:
            base_price: Base price of the product
            product_name: Product name for competitor matching
            quantity: Quantity for volume discounts
            customer_id: Customer ID for customer-specific pricing
            currency: Target currency (for FX conversion)
            apply_rules: Whether to apply dynamic pricing rules
        
        Returns:
            Dictionary with calculated price breakdown
        """
        result = {
            'base_price': float(base_price),
            'currency': currency,
            'quantity': quantity,
            'rules_applied': [],
            'adjustments': [],
            'final_price': float(base_price),
            'total_amount': float(base_price * quantity)
        }
        
        if not apply_rules:
            return result
        
        current_price = base_price
        
        # 1. FX Conversion (if currency differs from base)
        if currency != "GBP":
            fx_rate = self.get_fx_rate("GBP", currency)
            if fx_rate:
                current_price = current_price * Decimal(str(fx_rate))
                result['fx_rate'] = fx_rate
                result['fx_converted_price'] = float(current_price)
                result['rules_applied'].append('fx_conversion')
                result['adjustments'].append({
                    'type': 'fx_conversion',
                    'description': f'Converted from GBP to {currency}',
                    'rate': fx_rate,
                    'amount': float(current_price - base_price)
                })
        
        # 2. Competitor Price Matching
        competitor_price = self.get_competitor_price(product_name)
        if competitor_price:
            # Apply competitive pricing rule (e.g., match or beat by 5%)
            competitive_price = Decimal(str(competitor_price['price'])) * Decimal('0.95')  # Beat by 5%
            if competitive_price < current_price:
                adjustment = current_price - competitive_price
                current_price = competitive_price
                result['competitor_price'] = competitor_price
                result['rules_applied'].append('competitor_matching')
                result['adjustments'].append({
                    'type': 'competitor_matching',
                    'description': f'Matched competitor price from {competitor_price["supplier_name"]}',
                    'amount': -float(adjustment)
                })
        
        # 3. Volume Discounts
        volume_discount = self.get_volume_discount(quantity)
        if volume_discount:
            discount_amount = current_price * Decimal(str(volume_discount['discount_percentage'])) / Decimal('100')
            current_price = current_price - discount_amount
            result['volume_discount'] = volume_discount
            result['rules_applied'].append('volume_discount')
            result['adjustments'].append({
                'type': 'volume_discount',
                'description': f'Volume discount ({volume_discount["discount_percentage"]}%) for {quantity} units',
                'amount': -float(discount_amount)
            })
        
        # 4. Seasonal Pricing
        seasonal_adjustment = self.get_seasonal_adjustment()
        if seasonal_adjustment:
            adjustment_amount = current_price * Decimal(str(seasonal_adjustment['adjustment_percentage'])) / Decimal('100')
            current_price = current_price + adjustment_amount
            result['seasonal_adjustment'] = seasonal_adjustment
            result['rules_applied'].append('seasonal_pricing')
            result['adjustments'].append({
                'type': 'seasonal_pricing',
                'description': seasonal_adjustment['description'],
                'amount': float(adjustment_amount)
            })
        
        # 5. Customer-Specific Pricing
        if customer_id:
            customer_pricing = self.get_customer_pricing(customer_id, product_name)
            if customer_pricing:
                if customer_pricing.get('discount_percentage'):
                    discount = current_price * Decimal(str(customer_pricing['discount_percentage'])) / Decimal('100')
                    current_price = current_price - discount
                    result['customer_discount'] = customer_pricing
                    result['rules_applied'].append('customer_pricing')
                    result['adjustments'].append({
                        'type': 'customer_pricing',
                        'description': f'Customer-specific discount ({customer_pricing["discount_percentage"]}%)',
                        'amount': -float(discount)
                    })
                elif customer_pricing.get('fixed_price'):
                    current_price = Decimal(str(customer_pricing['fixed_price']))
                    result['customer_pricing'] = customer_pricing
                    result['rules_applied'].append('customer_pricing')
                    result['adjustments'].append({
                        'type': 'customer_pricing',
                        'description': 'Customer-specific fixed price',
                        'amount': float(current_price - base_price)
                    })
        
        result['final_price'] = float(current_price)
        result['total_amount'] = float(current_price * quantity)
        result['total_adjustment'] = float(current_price - base_price)
        
        return result
    
    def get_fx_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """
        Get FX exchange rate
        
        Args:
            from_currency: Source currency code
            to_currency: Target currency code
        
        Returns:
            Exchange rate (None if not available)
        """
        if from_currency == to_currency:
            return 1.0
        
        # Get FX rates from pricing config (stored in config_data)
        fx_config = self.db.query(TenantPricingConfig).filter(
            and_(
                TenantPricingConfig.tenant_id == self.tenant_id,
                TenantPricingConfig.config_type == 'fx_rates',
                TenantPricingConfig.is_active == True,
                TenantPricingConfig.is_deleted == False
            )
        ).first()
        
        if fx_config and fx_config.config_data:
            rates = fx_config.config_data.get('rates', {})
            # Check direct rate
            rate_key = f"{from_currency}_{to_currency}"
            if rate_key in rates:
                return float(rates[rate_key])
            
            # Check reverse rate
            reverse_key = f"{to_currency}_{from_currency}"
            if reverse_key in rates:
                return 1.0 / float(rates[reverse_key])
        
        # Fallback: Use AI to estimate or return None (would need external API in production)
        logger.warning(f"FX rate not found for {from_currency} to {to_currency}")
        return None
    
    def get_competitor_price(self, product_name: str) -> Optional[Dict[str, Any]]:
        """
        Get competitor price for a product
        
        Args:
            product_name: Product name to search for
        
        Returns:
            Competitor price information or None
        """
        competitors = self.price_intel.get_competitor_prices(product_name)
        
        if not competitors:
            return None
        
        # Return the lowest verified price, or lowest unverified if no verified prices
        verified_prices = [c for c in competitors if c.get('is_verified')]
        if verified_prices:
            return min(verified_prices, key=lambda x: x['price'])
        
        # Return lowest unverified price
        return min(competitors, key=lambda x: x['price'])
    
    def get_volume_discount(self, quantity: int) -> Optional[Dict[str, Any]]:
        """
        Get volume discount rule for quantity
        
        Args:
            quantity: Quantity ordered
        
        Returns:
            Volume discount rule or None
        """
        volume_rules = self.db.query(TenantPricingConfig).filter(
            and_(
                TenantPricingConfig.tenant_id == self.tenant_id,
                TenantPricingConfig.config_type == PricingConfigType.VOLUME_PRICING.value,
                TenantPricingConfig.is_active == True,
                TenantPricingConfig.is_deleted == False
            )
        ).order_by(TenantPricingConfig.priority.desc()).all()
        
        for rule in volume_rules:
            if not rule.config_data:
                continue
            
            min_quantity = rule.config_data.get('min_quantity', 0)
            max_quantity = rule.config_data.get('max_quantity', 999999)
            
            if min_quantity <= quantity <= max_quantity:
                return {
                    'rule_id': rule.id,
                    'rule_name': rule.name,
                    'min_quantity': min_quantity,
                    'max_quantity': max_quantity,
                    'discount_percentage': rule.config_data.get('discount_percentage', 0),
                    'discount_amount': rule.config_data.get('discount_amount')
                }
        
        return None
    
    def get_seasonal_adjustment(self) -> Optional[Dict[str, Any]]:
        """
        Get seasonal pricing adjustment for current date
        
        Returns:
            Seasonal adjustment rule or None
        """
        now = datetime.now(timezone.utc)
        
        seasonal_rules = self.db.query(TenantPricingConfig).filter(
            and_(
                TenantPricingConfig.tenant_id == self.tenant_id,
                TenantPricingConfig.config_type == 'seasonal_pricing',
                TenantPricingConfig.is_active == True,
                TenantPricingConfig.is_deleted == False,
                or_(
                    TenantPricingConfig.valid_from.is_(None),
                    TenantPricingConfig.valid_from <= now
                ),
                or_(
                    TenantPricingConfig.valid_until.is_(None),
                    TenantPricingConfig.valid_until >= now
                )
            )
        ).order_by(TenantPricingConfig.priority.desc()).first()
        
        if seasonal_rules and seasonal_rules.config_data:
            return {
                'rule_id': seasonal_rules.id,
                'rule_name': seasonal_rules.name,
                'adjustment_percentage': seasonal_rules.config_data.get('adjustment_percentage', 0),
                'description': seasonal_rules.config_data.get('description', seasonal_rules.name)
            }
        
        return None
    
    def get_customer_pricing(self, customer_id: str, product_name: str) -> Optional[Dict[str, Any]]:
        """
        Get customer-specific pricing rules
        
        Args:
            customer_id: Customer ID
            product_name: Product name
        
        Returns:
            Customer pricing rule or None
        """
        # Check for customer-specific pricing config
        customer_rules = self.db.query(TenantPricingConfig).filter(
            and_(
                TenantPricingConfig.tenant_id == self.tenant_id,
                TenantPricingConfig.config_type == 'customer_pricing',
                TenantPricingConfig.is_active == True,
                TenantPricingConfig.is_deleted == False
            )
        ).all()
        
        for rule in customer_rules:
            if not rule.config_data:
                continue
            
            # Check if this rule applies to this customer
            customer_ids = rule.config_data.get('customer_ids', [])
            if customer_id in customer_ids:
                # Check if product matches
                product_patterns = rule.config_data.get('product_patterns', [])
                if not product_patterns or any(pattern.lower() in product_name.lower() for pattern in product_patterns):
                    return {
                        'rule_id': rule.id,
                        'rule_name': rule.name,
                        'discount_percentage': rule.config_data.get('discount_percentage'),
                        'fixed_price': rule.config_data.get('fixed_price')
                    }
        
        return None
    
    async def suggest_optimal_price(
        self,
        product_name: str,
        base_price: Decimal,
        competitor_prices: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Use AI to suggest optimal pricing based on market analysis
        
        Args:
            product_name: Product name
            base_price: Base/cost price
            competitor_prices: Optional list of competitor prices
        
        Returns:
            AI-suggested pricing recommendation
        """
        try:
            # Get competitor prices if not provided
            if not competitor_prices:
                competitors = self.price_intel.get_competitor_prices(product_name)
                competitor_prices = competitors[:5]  # Top 5 competitors
            
            # Get price trends
            trends = self.price_intel.get_price_trends(product_name, days_back=90)
            
            # Build context for AI
            context = {
                'product_name': product_name,
                'base_price': float(base_price),
                'competitor_prices': competitor_prices,
                'price_trends': trends,
                'market_analysis': {
                    'min_competitor_price': min([c['price'] for c in competitor_prices]) if competitor_prices else None,
                    'max_competitor_price': max([c['price'] for c in competitor_prices]) if competitor_prices else None,
                    'avg_competitor_price': sum([c['price'] for c in competitor_prices]) / len(competitor_prices) if competitor_prices else None,
                    'trend': trends.get('trend', 'unknown')
                }
            }
            
            # Use database-driven AI prompt for pricing analysis
            prompt_result = await self.ai_service.generate_with_rendered_prompts(
                category=PromptCategory.PRICING_ANALYSIS,
                variables={
                    'product_name': product_name,
                    'base_price': str(base_price),
                    'competitor_prices': json.dumps(competitor_prices, indent=2),
                    'price_trends': json.dumps(trends, indent=2),
                    'market_context': json.dumps(context['market_analysis'], indent=2)
                }
            )
            
            if prompt_result and prompt_result.get('content'):
                # Parse AI response (expecting JSON with pricing recommendation)
                try:
                    # Try to extract JSON from response
                    response_text = prompt_result['content']
                    if '{' in response_text:
                        json_start = response_text.find('{')
                        json_end = response_text.rfind('}') + 1
                        json_str = response_text[json_start:json_end]
                        recommendation = json.loads(json_str)
                    else:
                        # Fallback: create recommendation from text
                        recommendation = {
                            'suggested_price': float(base_price),
                            'reasoning': response_text,
                            'confidence': 0.5
                        }
                    
                    return {
                        'success': True,
                        'recommendation': recommendation,
                        'context': context
                    }
                except json.JSONDecodeError:
                    # If JSON parsing fails, return text response
                    return {
                        'success': True,
                        'recommendation': {
                            'suggested_price': float(base_price),
                            'reasoning': prompt_result['content'],
                            'confidence': 0.5
                        },
                        'context': context
                    }
            
            # Fallback if AI fails
            return {
                'success': False,
                'recommendation': {
                    'suggested_price': float(base_price),
                    'reasoning': 'Unable to generate AI recommendation',
                    'confidence': 0.0
                },
                'context': context
            }
            
        except Exception as e:
            logger.error(f"Error generating AI pricing suggestion: {e}")
            return {
                'success': False,
                'error': str(e),
                'recommendation': {
                    'suggested_price': float(base_price),
                    'reasoning': 'Error generating recommendation',
                    'confidence': 0.0
                }
            }
    
    def create_fx_rate_config(
        self,
        rates: Dict[str, float],
        base_currency: str = "GBP"
    ) -> TenantPricingConfig:
        """
        Create or update FX rates configuration
        
        Args:
            rates: Dictionary of exchange rates (e.g., {"GBP_USD": 1.25, "GBP_EUR": 1.15})
            base_currency: Base currency code
        
        Returns:
            Created/updated pricing config
        """
        # Check if FX config exists
        existing = self.db.query(TenantPricingConfig).filter(
            and_(
                TenantPricingConfig.tenant_id == self.tenant_id,
                TenantPricingConfig.config_type == 'fx_rates',
                TenantPricingConfig.is_active == True
            )
        ).first()
        
        if existing:
            existing.config_data = {'rates': rates, 'base_currency': base_currency}
            existing.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            from app.services.pricing_config_service import PricingConfigService
            pricing_service = PricingConfigService(self.db, self.tenant_id)
            
            config = TenantPricingConfig(
                id=str(uuid.uuid4()),
                tenant_id=self.tenant_id,
                config_type='fx_rates',
                name='FX Exchange Rates',
                description=f'Exchange rates with base currency {base_currency}',
                config_data={'rates': rates, 'base_currency': base_currency},
                is_active=True,
                priority=0
            )
            
            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)
            return config

