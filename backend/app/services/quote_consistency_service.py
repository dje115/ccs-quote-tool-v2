#!/usr/bin/env python3
"""
Quote Consistency Service
Migrated from v1 QuoteConsistencyManager
Provides consistency checking and historical comparison for quotes
"""

import json
import statistics
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, extract

from app.models.quotes import Quote, QuoteStatus
from app.models.tenant import Tenant


class QuoteConsistencyService:
    """Service for analyzing quote consistency against historical data"""
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        
        self.standard_markup_percentages = {
            'materials': 1.15,  # 15% markup on materials
            'labor': 1.20,      # 20% markup on labor
            'travel': 1.00      # No markup on travel (cost recovery only)
        }
        
        self.standard_allowances = {
            'cabling_per_outlet': 0.4,      # Hours per outlet
            'wifi_per_ap': 2.0,             # Hours per access point
            'cctv_per_camera': 1.5,         # Hours per camera
            'testing_per_outlet': 0.1,      # Hours per outlet for testing
            'travel_per_hour': 0.5,         # Hours per hour of travel
            'setup_per_project': 4.0        # Hours for project setup
        }
    
    def analyze_quote_consistency(self, quote_id: str) -> Dict[str, Any]:
        """Analyze a quote against historical data for consistency"""
        try:
            quote = self.db.query(Quote).filter(
                and_(
                    Quote.id == quote_id,
                    Quote.tenant_id == self.tenant_id
                )
            ).first()
            
            if not quote:
                return {'error': 'Quote not found'}
            
            # Get similar historical quotes
            similar_quotes = self._find_similar_quotes(quote)
            
            analysis = {
                'quote_id': quote_id,
                'similar_quotes_count': len(similar_quotes),
                'consistency_score': 0,
                'recommendations': [],
                'pricing_comparison': {},
                'labor_comparison': {},
                'material_comparison': {},
                'flags': []
            }
            
            if similar_quotes:
                analysis.update(self._compare_with_historical(quote, similar_quotes))
            
            return analysis
            
        except Exception as e:
            return {'error': f'Analysis failed: {str(e)}'}
    
    def _find_similar_quotes(self, quote: Quote) -> List[Quote]:
        """Find historically similar quotes based on project characteristics"""
        try:
            # Define similarity criteria
            criteria = []
            
            # Building size similarity (±20%)
            if quote.building_size:
                min_size = quote.building_size * 0.8
                max_size = quote.building_size * 1.2
                criteria.append(and_(
                    Quote.building_size >= min_size,
                    Quote.building_size <= max_size
                ))
            
            # Room count similarity (±50%)
            if quote.number_of_rooms:
                min_rooms = max(1, int(quote.number_of_rooms * 0.5))
                max_rooms = int(quote.number_of_rooms * 1.5)
                criteria.append(and_(
                    Quote.number_of_rooms >= min_rooms,
                    Quote.number_of_rooms <= max_rooms
                ))
            
            # Service requirements match
            service_criteria = []
            if quote.wifi_requirements:
                service_criteria.append(Quote.wifi_requirements == True)
            if quote.cctv_requirements:
                service_criteria.append(Quote.cctv_requirements == True)
            if quote.door_entry_requirements:
                service_criteria.append(Quote.door_entry_requirements == True)
            
            # Building type similarity
            if quote.building_type:
                criteria.append(Quote.building_type.ilike(f'%{quote.building_type}%'))
            
            # Combine criteria with OR for flexible matching
            query = self.db.query(Quote).filter(
                and_(
                    Quote.id != quote.id,  # Exclude current quote
                    Quote.tenant_id == self.tenant_id,
                    Quote.created_at >= datetime.utcnow() - timedelta(days=365),  # Last year
                    Quote.status.in_([QuoteStatus.SENT.value, QuoteStatus.ACCEPTED.value])  # Only successful quotes
                )
            )
            
            if criteria:
                query = query.filter(or_(*criteria))
            
            if service_criteria:
                query = query.filter(or_(*service_criteria))
            
            return query.order_by(Quote.created_at.desc()).limit(10).all()
            
        except Exception as e:
            print(f"Error finding similar quotes: {e}")
            return []
    
    def _compare_with_historical(
        self,
        current_quote: Quote,
        similar_quotes: List[Quote]
    ) -> Dict[str, Any]:
        """Compare current quote with similar historical quotes"""
        try:
            analysis = {
                'pricing_comparison': {},
                'labor_comparison': {},
                'material_comparison': {},
                'consistency_score': 0,
                'recommendations': [],
                'flags': []
            }
            
            # Analyze pricing consistency
            current_pricing = self._extract_quote_pricing(current_quote)
            historical_pricing = [self._extract_quote_pricing(q) for q in similar_quotes]
            
            if current_pricing and historical_pricing:
                analysis['pricing_comparison'] = self._compare_pricing(current_pricing, historical_pricing)
                analysis['labor_comparison'] = self._compare_labor_rates(current_quote, similar_quotes)
                analysis['material_comparison'] = self._compare_material_costs(current_pricing, historical_pricing)
                
                # Calculate overall consistency score
                analysis['consistency_score'] = self._calculate_consistency_score(analysis)
                
                # Generate recommendations
                analysis['recommendations'] = self._generate_recommendations(analysis)
                analysis['flags'] = self._identify_consistency_flags(analysis)
            
            return analysis
            
        except Exception as e:
            print(f"Error comparing with historical data: {e}")
            return {}
    
    def _extract_quote_pricing(self, quote: Quote) -> Optional[Dict[str, Any]]:
        """Extract pricing data from quote"""
        try:
            # Try to get from quote_data JSON field
            if hasattr(quote, 'quote_data') and quote.quote_data:
                if isinstance(quote.quote_data, str):
                    quote_data = json.loads(quote.quote_data)
                else:
                    quote_data = quote.quote_data
                
                return {
                    'total_materials': quote_data.get('total_materials', 0),
                    'total_labor': quote_data.get('total_labor', 0),
                    'total_cost': quote_data.get('total_cost', 0) or float(quote.total_amount) if quote.total_amount else 0,
                    'materials': quote_data.get('materials', []),
                    'labor': quote_data.get('labor', []),
                    'building_size': quote.building_size
                }
            
            # Fallback to quote totals
            return {
                'total_materials': float(quote.subtotal) if quote.subtotal else 0,
                'total_labor': 0,
                'total_cost': float(quote.total_amount) if quote.total_amount else 0,
                'materials': [],
                'labor': [],
                'building_size': quote.building_size
            }
        except Exception as e:
            print(f"Error extracting quote pricing: {e}")
            return None
    
    def _compare_pricing(
        self,
        current: Dict,
        historical: List[Dict]
    ) -> Dict[str, Any]:
        """Compare current pricing with historical averages"""
        try:
            # Calculate historical averages
            hist_materials = [h['total_materials'] for h in historical if h.get('total_materials')]
            hist_labor = [h['total_labor'] for h in historical if h.get('total_labor')]
            hist_total = [h['total_cost'] for h in historical if h.get('total_cost')]
            
            comparison = {
                'materials': {
                    'current': current.get('total_materials', 0),
                    'historical_avg': statistics.mean(hist_materials) if hist_materials else 0,
                    'historical_median': statistics.median(hist_materials) if hist_materials else 0,
                    'variance_percent': 0
                },
                'labor': {
                    'current': current.get('total_labor', 0),
                    'historical_avg': statistics.mean(hist_labor) if hist_labor else 0,
                    'historical_median': statistics.median(hist_labor) if hist_labor else 0,
                    'variance_percent': 0
                },
                'total': {
                    'current': current.get('total_cost', 0),
                    'historical_avg': statistics.mean(hist_total) if hist_total else 0,
                    'historical_median': statistics.median(hist_total) if hist_total else 0,
                    'variance_percent': 0
                }
            }
            
            # Calculate variance percentages
            for category in ['materials', 'labor', 'total']:
                if comparison[category]['historical_avg'] > 0:
                    variance = ((comparison[category]['current'] - comparison[category]['historical_avg']) 
                              / comparison[category]['historical_avg']) * 100
                    comparison[category]['variance_percent'] = round(variance, 1)
            
            return comparison
            
        except Exception as e:
            print(f"Error comparing pricing: {e}")
            return {}
    
    def _compare_labor_rates(
        self,
        current_quote: Quote,
        similar_quotes: List[Quote]
    ) -> Dict[str, Any]:
        """Compare labor rates with historical data"""
        try:
            # Extract labor rates from quotes
            current_rate = self._extract_labor_rate(current_quote)
            historical_rates = [self._extract_labor_rate(q) for q in similar_quotes if self._extract_labor_rate(q)]
            
            if not historical_rates:
                return {}
            
            variance = 0
            if current_rate and historical_rates:
                avg_rate = statistics.mean(historical_rates)
                if avg_rate > 0:
                    variance = ((current_rate - avg_rate) / avg_rate) * 100
            
            return {
                'current_rate': current_rate,
                'historical_avg': statistics.mean(historical_rates) if historical_rates else 0,
                'historical_median': statistics.median(historical_rates) if historical_rates else 0,
                'rate_variance_percent': round(variance, 1)
            }
            
        except Exception as e:
            print(f"Error comparing labor rates: {e}")
            return {}
    
    def _extract_labor_rate(self, quote: Quote) -> Optional[float]:
        """Extract hourly labor rate from quote"""
        try:
            if quote.labour_breakdown:
                if isinstance(quote.labour_breakdown, str):
                    labour_data = json.loads(quote.labour_breakdown)
                else:
                    labour_data = quote.labour_breakdown
                
                if isinstance(labour_data, list) and labour_data:
                    # Look for day_rate in labor breakdown
                    for item in labour_data:
                        if 'day_rate' in item and item['day_rate']:
                            return float(item['day_rate']) / 8.0  # Convert to hourly
            
            return None
            
        except Exception as e:
            print(f"Error extracting labor rate: {e}")
            return None
    
    def _compare_material_costs(
        self,
        current: Dict,
        historical: List[Dict]
    ) -> Dict[str, Any]:
        """Compare material costs per unit with historical data"""
        try:
            # Extract material costs per square meter/room
            current_materials_per_sqm = 0
            if current.get('total_materials') and current.get('building_size'):
                current_materials_per_sqm = current['total_materials'] / current['building_size']
            
            historical_materials_per_sqm = []
            for hist in historical:
                if hist.get('total_materials') and hist.get('building_size'):
                    historical_materials_per_sqm.append(hist['total_materials'] / hist['building_size'])
            
            if not historical_materials_per_sqm:
                return {}
            
            variance = 0
            avg_per_sqm = statistics.mean(historical_materials_per_sqm)
            if avg_per_sqm > 0:
                variance = ((current_materials_per_sqm - avg_per_sqm) / avg_per_sqm) * 100
            
            return {
                'current_per_sqm': current_materials_per_sqm,
                'historical_avg_per_sqm': avg_per_sqm,
                'historical_median_per_sqm': statistics.median(historical_materials_per_sqm),
                'variance_percent': round(variance, 1)
            }
            
        except Exception as e:
            print(f"Error comparing material costs: {e}")
            return {}
    
    def _calculate_consistency_score(self, analysis: Dict) -> float:
        """Calculate overall consistency score (0-100)"""
        try:
            score = 100.0
            
            # Penalize large variances
            pricing = analysis.get('pricing_comparison', {})
            for category in ['materials', 'labor', 'total']:
                variance = abs(pricing.get(category, {}).get('variance_percent', 0))
                if variance > 50:
                    score -= 20
                elif variance > 30:
                    score -= 10
                elif variance > 15:
                    score -= 5
            
            return max(0, min(100, score))
            
        except Exception as e:
            print(f"Error calculating consistency score: {e}")
            return 0
    
    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """Generate recommendations for improving consistency"""
        recommendations = []
        
        pricing = analysis.get('pricing_comparison', {})
        
        for category in ['materials', 'labor', 'total']:
            variance = pricing.get(category, {}).get('variance_percent', 0)
            if abs(variance) > 30:
                recommendations.append(
                    f"{category.title()} pricing is {variance:+.1f}% different from historical average. "
                    f"Consider reviewing {category} estimates."
                )
            elif abs(variance) > 15:
                recommendations.append(
                    f"{category.title()} pricing is {variance:+.1f}% different from historical average. "
                    f"Verify {category} calculations."
                )
        
        return recommendations
    
    def _identify_consistency_flags(self, analysis: Dict) -> List[str]:
        """Identify potential consistency issues"""
        flags = []
        
        pricing = analysis.get('pricing_comparison', {})
        
        # Flag significant variances
        for category in ['materials', 'labor', 'total']:
            variance = abs(pricing.get(category, {}).get('variance_percent', 0))
            if variance > 50:
                flags.append(f"HIGH VARIANCE: {category.title()} pricing differs by {variance:.1f}% from historical average")
            elif variance > 30:
                flags.append(f"MEDIUM VARIANCE: {category.title()} pricing differs by {variance:.1f}% from historical average")
        
        # Flag missing historical data
        if analysis.get('similar_quotes_count', 0) < 3:
            flags.append("LIMITED DATA: Few similar historical quotes available for comparison")
        
        return flags
    
    def get_standard_pricing_templates(self) -> Dict[str, Any]:
        """Get standard pricing templates for common job types"""
        return {
            'office_refurbishment': {
                'materials_per_sqm': 25.0,
                'labor_per_outlet': 0.4,
                'testing_per_outlet': 0.1,
                'wifi_per_ap': 2.0,
                'description': 'Standard office refurbishment pricing'
            },
            'new_build': {
                'materials_per_sqm': 30.0,
                'labor_per_outlet': 0.3,
                'testing_per_outlet': 0.1,
                'wifi_per_ap': 1.5,
                'description': 'New build construction pricing'
            },
            'retail_space': {
                'materials_per_sqm': 20.0,
                'labor_per_outlet': 0.5,
                'testing_per_outlet': 0.1,
                'wifi_per_ap': 2.5,
                'description': 'Retail space pricing (higher labor due to access challenges)'
            },
            'industrial': {
                'materials_per_sqm': 35.0,
                'labor_per_outlet': 0.6,
                'testing_per_outlet': 0.15,
                'wifi_per_ap': 3.0,
                'description': 'Industrial environment pricing (higher materials and labor)'
            }
        }
    
    def get_consistency_context_for_ai(self, quote: Quote) -> str:
        """Generate consistency context to include in AI prompts"""
        try:
            context_parts = []
            
            # Get similar historical quotes
            similar_quotes = self._find_similar_quotes(quote)
            
            if similar_quotes:
                context_parts.append(f"**HISTORICAL CONTEXT:**")
                context_parts.append(f"Found {len(similar_quotes)} similar projects in the last 12 months:")
                
                # Add summary statistics
                total_costs = [float(q.total_amount) for q in similar_quotes if q.total_amount]
                building_sizes = [q.building_size for q in similar_quotes if q.building_size]
                
                if total_costs:
                    avg_cost = statistics.mean(total_costs)
                    context_parts.append(f"- Average project cost: £{avg_cost:,.0f}")
                
                if building_sizes:
                    avg_size = statistics.mean([s for s in building_sizes if s])
                    context_parts.append(f"- Average building size: {avg_size:.0f} sqm")
                
                # Add recent examples
                recent_quotes = sorted(similar_quotes, key=lambda x: x.created_at, reverse=True)[:2]
                for recent in recent_quotes:
                    context_parts.append(f"- Recent: {recent.title} - £{recent.total_amount:,.0f}")
                
                context_parts.append("")
                context_parts.append("**CONSISTENCY GUIDELINES:**")
                context_parts.append("- Ensure pricing aligns with historical averages (±20% is acceptable)")
                context_parts.append("- Use similar material specifications for comparable projects")
                context_parts.append("- Maintain consistent labor hour estimates for similar work types")
                context_parts.append("- Flag any significant deviations from historical patterns")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            print(f"Error generating consistency context: {e}")
            return ""


