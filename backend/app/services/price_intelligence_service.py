#!/usr/bin/env python3
"""
Price Intelligence Service
Tracks historical pricing data and provides price intelligence insights
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import logging

from app.models.supplier import ProductContentHistory, Supplier, SupplierPricing
from app.models.product import Product

logger = logging.getLogger(__name__)


class PriceIntelligenceService:
    """Service for price intelligence and historical price tracking"""
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
    
    def record_price_history(
        self,
        supplier_id: str,
        product_name: str,
        price: Optional[Decimal],
        currency: str = "GBP",
        confidence_score: float = 0.5,
        source_url: Optional[str] = None,
        scraping_method: Optional[str] = None,
        scraped_content: Optional[str] = None,
        scraping_metadata: Optional[Dict[str, Any]] = None
    ) -> ProductContentHistory:
        """
        Record a price history entry from web scraping
        
        Args:
            supplier_id: Supplier ID
            product_name: Product name
            price: Extracted price (may be None if extraction failed)
            currency: Currency code
            confidence_score: Confidence in price accuracy (0.0-1.0)
            source_url: URL where price was scraped from
            scraping_method: Method used (direct_url, search, api, cached)
            scraped_content: Full HTML/text content (for analysis)
            scraping_metadata: Additional metadata (selectors, retries, etc.)
        
        Returns:
            Created ProductContentHistory record
        """
        history = ProductContentHistory(
            tenant_id=self.tenant_id,
            supplier_id=supplier_id,
            product_name=product_name,
            price=price,
            currency=currency,
            confidence_score=confidence_score,
            supplier_product_url=source_url,
            scraping_method=scraping_method,
            scraped_content=scraped_content,
            scraping_metadata=scraping_metadata,
            scraping_timestamp=datetime.now(timezone.utc),
            recorded_at=datetime.now(timezone.utc),
            is_verified=False,
            is_active=True
        )
        
        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)
        
        return history
    
    def get_price_history(
        self,
        product_name: Optional[str] = None,
        supplier_id: Optional[str] = None,
        days_back: int = 90,
        verified_only: bool = False
    ) -> List[ProductContentHistory]:
        """
        Get price history for a product or supplier
        
        Args:
            product_name: Filter by product name (partial match)
            supplier_id: Filter by supplier ID
            days_back: Number of days to look back
            verified_only: Only return verified prices
        
        Returns:
            List of price history records
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        
        query = self.db.query(ProductContentHistory).filter(
            and_(
                ProductContentHistory.tenant_id == self.tenant_id,
                ProductContentHistory.scraping_timestamp >= cutoff_date,
                ProductContentHistory.is_active == True
            )
        )
        
        if product_name:
            query = query.filter(ProductContentHistory.product_name.ilike(f'%{product_name}%'))
        
        if supplier_id:
            query = query.filter(ProductContentHistory.supplier_id == supplier_id)
        
        if verified_only:
            query = query.filter(ProductContentHistory.is_verified == True)
        
        return query.order_by(desc(ProductContentHistory.scraping_timestamp)).all()
    
    def get_price_trends(
        self,
        product_name: str,
        supplier_id: Optional[str] = None,
        days_back: int = 90
    ) -> Dict[str, Any]:
        """
        Analyze price trends for a product
        
        Returns:
            Dictionary with price statistics and trends
        """
        history = self.get_price_history(
            product_name=product_name,
            supplier_id=supplier_id,
            days_back=days_back,
            verified_only=False
        )
        
        if not history:
            return {
                'product_name': product_name,
                'supplier_id': supplier_id,
                'data_points': 0,
                'trend': 'no_data'
            }
        
        # Filter out None prices
        prices = [float(h.price) for h in history if h.price is not None]
        
        if not prices:
            return {
                'product_name': product_name,
                'supplier_id': supplier_id,
                'data_points': len(history),
                'trend': 'no_prices'
            }
        
        # Calculate statistics
        prices_sorted = sorted(prices)
        min_price = prices_sorted[0]
        max_price = prices_sorted[-1]
        avg_price = sum(prices) / len(prices)
        median_price = prices_sorted[len(prices_sorted) // 2]
        
        # Determine trend
        if len(prices) >= 2:
            recent_prices = prices[-min(10, len(prices)):]
            older_prices = prices[:max(1, len(prices) - 10)]
            recent_avg = sum(recent_prices) / len(recent_prices)
            older_avg = sum(older_prices) / len(older_prices)
            
            if recent_avg > older_avg * 1.05:
                trend = 'increasing'
            elif recent_avg < older_avg * 0.95:
                trend = 'decreasing'
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'
        
        return {
            'product_name': product_name,
            'supplier_id': supplier_id,
            'data_points': len(prices),
            'min_price': min_price,
            'max_price': max_price,
            'avg_price': avg_price,
            'median_price': median_price,
            'current_price': prices[-1] if prices else None,
            'trend': trend,
            'price_range': max_price - min_price,
            'volatility': (max_price - min_price) / avg_price if avg_price > 0 else 0
        }
    
    def get_competitor_prices(
        self,
        product_name: str,
        exclude_supplier_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get competitor prices for a product across all suppliers
        
        Args:
            product_name: Product name to search for
            exclude_supplier_id: Supplier ID to exclude from results
        
        Returns:
            List of competitor price information
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)  # Last 30 days
        
        query = self.db.query(
            ProductContentHistory,
            Supplier.name.label('supplier_name')
        ).join(
            Supplier, ProductContentHistory.supplier_id == Supplier.id
        ).filter(
            and_(
                ProductContentHistory.tenant_id == self.tenant_id,
                ProductContentHistory.product_name.ilike(f'%{product_name}%'),
                ProductContentHistory.scraping_timestamp >= cutoff_date,
                ProductContentHistory.price.isnot(None),
                ProductContentHistory.is_active == True,
                Supplier.is_active == True
            )
        )
        
        if exclude_supplier_id:
            query = query.filter(ProductContentHistory.supplier_id != exclude_supplier_id)
        
        # Get most recent price per supplier
        results = query.order_by(
            desc(ProductContentHistory.scraping_timestamp)
        ).all()
        
        # Group by supplier and get latest
        supplier_prices = {}
        for history, supplier_name in results:
            if history.supplier_id not in supplier_prices:
                supplier_prices[history.supplier_id] = {
                    'supplier_id': history.supplier_id,
                    'supplier_name': supplier_name,
                    'price': float(history.price),
                    'currency': history.currency,
                    'confidence_score': float(history.confidence_score),
                    'is_verified': history.is_verified,
                    'scraping_timestamp': history.scraping_timestamp.isoformat(),
                    'source_url': history.supplier_product_url
                }
        
        return list(supplier_prices.values())
    
    def verify_price(
        self,
        history_id: str,
        verified_by: str,
        verification_notes: Optional[str] = None
    ) -> bool:
        """
        Mark a price history entry as verified
        
        Args:
            history_id: ProductContentHistory ID
            verified_by: User ID who verified
            verification_notes: Optional notes
        
        Returns:
            True if verified successfully
        """
        history = self.db.query(ProductContentHistory).filter(
            and_(
                ProductContentHistory.id == history_id,
                ProductContentHistory.tenant_id == self.tenant_id
            )
        ).first()
        
        if not history:
            return False
        
        history.is_verified = True
        history.verified_by = verified_by
        history.verified_at = datetime.now(timezone.utc)
        history.verification_notes = verification_notes
        
        self.db.commit()
        
        return True
    
    def get_unverified_prices(
        self,
        min_confidence: float = 0.7,
        days_back: int = 7
    ) -> List[ProductContentHistory]:
        """
        Get unverified prices that need manual review
        
        Args:
            min_confidence: Minimum confidence score to include
            days_back: Number of days to look back
        
        Returns:
            List of unverified price history records
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        
        return self.db.query(ProductContentHistory).filter(
            and_(
                ProductContentHistory.tenant_id == self.tenant_id,
                ProductContentHistory.is_verified == False,
                ProductContentHistory.confidence_score >= min_confidence,
                ProductContentHistory.scraping_timestamp >= cutoff_date,
                ProductContentHistory.is_active == True,
                ProductContentHistory.price.isnot(None)
            )
        ).order_by(
            desc(ProductContentHistory.confidence_score),
            desc(ProductContentHistory.scraping_timestamp)
        ).all()

