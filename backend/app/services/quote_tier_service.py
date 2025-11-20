#!/usr/bin/env python3
"""
Quote Tier Service

Handles 3-tier quote generation logic:
- Tier 1: Basic/Budget
- Tier 2: Standard/Recommended
- Tier 3: Premium/High-End
"""

import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class QuoteTierService:
    """
    Service for managing 3-tier quote logic
    
    Features:
    - Determine if quote should be 3-tier or single
    - Generate tier variations
    - Calculate tier pricing differences
    """
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
    
    def should_generate_tiers(self, quote_data: Dict[str, Any]) -> bool:
        """
        Determine if quote should be 3-tier or single
        
        Args:
            quote_data: AI-generated quote data
        
        Returns:
            True if 3-tier quote is appropriate
        """
        # Simple heuristic: if AI generated tiers, use them
        if quote_data.get("quote_type") == "three_tier":
            return True
        
        # Check if tiers exist in data
        if quote_data.get("tiers"):
            return True
        
        return False
    
    def extract_tier_pricing(self, quote_data: Dict[str, Any], tier: str) -> Dict[str, Any]:
        """
        Extract pricing for a specific tier
        
        Args:
            quote_data: AI-generated quote data
            tier: Tier name ('tier_1', 'tier_2', 'tier_3')
        
        Returns:
            Pricing breakdown for the tier
        """
        tiers = quote_data.get("tiers", {})
        tier_data = tiers.get(tier, {})
        
        return tier_data.get("pricing_breakdown", {})
    
    def get_tier_summary(self, quote_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get summary of all tiers
        
        Returns:
            Dict with tier summaries
        """
        tiers = quote_data.get("tiers", {})
        
        summary = {}
        for tier_key in ["tier_1", "tier_2", "tier_3"]:
            tier_data = tiers.get(tier_key, {})
            if tier_data:
                pricing = tier_data.get("pricing_breakdown", {})
                summary[tier_key] = {
                    "name": tier_data.get("name", ""),
                    "price_range": tier_data.get("price_range", ""),
                    "best_for": tier_data.get("best_for", ""),
                    "total": pricing.get("total", 0)
                }
        
        return summary

