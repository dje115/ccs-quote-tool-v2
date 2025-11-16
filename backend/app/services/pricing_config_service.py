#!/usr/bin/env python3
"""
Pricing Configuration Service
Manages tenant-specific pricing configurations: day rates, bundles, managed services
"""

import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, desc
from datetime import datetime, timezone
from decimal import Decimal

from app.models.pricing_config import TenantPricingConfig, PricingBundleItem, PricingConfigType
from app.models.tenant import Tenant


class PricingConfigService:
    """Service for managing tenant pricing configurations"""
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
    
    def create_day_rate(
        self,
        name: str,
        base_rate: Decimal,
        engineers: int = 2,
        hours_per_day: int = 8,
        includes_travel: bool = False,
        description: Optional[str] = None,
        code: Optional[str] = None,
        priority: int = 0,
        valid_from: Optional[datetime] = None,
        valid_until: Optional[datetime] = None
    ) -> TenantPricingConfig:
        """Create a day rate configuration"""
        config = TenantPricingConfig(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            config_type=PricingConfigType.DAY_RATE.value,
            name=name,
            description=description,
            code=code,
            base_rate=base_rate,
            unit="day",
            config_data={
                "engineers": engineers,
                "hours_per_day": hours_per_day,
                "includes_travel": includes_travel
            },
            priority=priority,
            valid_from=valid_from,
            valid_until=valid_until,
            is_active=True,
            version=1
        )
        
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        
        return config
    
    def create_bundle(
        self,
        name: str,
        bundle_price: Decimal,
        items: List[Dict[str, Any]],
        description: Optional[str] = None,
        code: Optional[str] = None,
        discount_percentage: Optional[float] = None,
        priority: int = 0,
        valid_from: Optional[datetime] = None,
        valid_until: Optional[datetime] = None
    ) -> TenantPricingConfig:
        """Create a bundle configuration"""
        config = TenantPricingConfig(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            config_type=PricingConfigType.BUNDLE.value,
            name=name,
            description=description,
            code=code,
            base_rate=bundle_price,
            unit="bundle",
            config_data={
                "discount_percentage": discount_percentage,
                "item_count": len(items)
            },
            priority=priority,
            valid_from=valid_from,
            valid_until=valid_until,
            is_active=True,
            version=1
        )
        
        self.db.add(config)
        self.db.flush()
        
        # Add bundle items
        for idx, item in enumerate(items):
            bundle_item = PricingBundleItem(
                id=str(uuid.uuid4()),
                tenant_id=self.tenant_id,
                bundle_config_id=config.id,
                item_type=item.get("type", "product"),
                item_id=item.get("item_id"),
                item_name=item.get("name", ""),
                item_code=item.get("code"),
                quantity=Decimal(str(item.get("quantity", 1))),
                unit_price=Decimal(str(item.get("unit_price", 0))) if item.get("unit_price") else None,
                bundle_price=Decimal(str(item.get("bundle_price", 0))) if item.get("bundle_price") else None,
                display_order=idx,
                item_data=item.get("data")
            )
            self.db.add(bundle_item)
        
        self.db.commit()
        self.db.refresh(config)
        
        return config
    
    def get_active_day_rate(self) -> Optional[TenantPricingConfig]:
        """Get the active day rate configuration for the tenant"""
        now = datetime.now(timezone.utc)
        
        config = self.db.query(TenantPricingConfig).filter(
            and_(
                TenantPricingConfig.tenant_id == self.tenant_id,
                TenantPricingConfig.config_type == PricingConfigType.DAY_RATE.value,
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
        ).order_by(desc(TenantPricingConfig.priority)).first()
        
        return config
    
    def get_day_rate_info(self) -> str:
        """Get formatted day rate information for AI prompts"""
        config = self.get_active_day_rate()
        
        if config:
            data = config.config_data or {}
            engineers = data.get("engineers", 2)
            hours_per_day = data.get("hours_per_day", 8)
            includes_travel = data.get("includes_travel", False)
            rate = float(config.base_rate) if config.base_rate else 300
            
            travel_note = " (includes travel)" if includes_travel else ""
            return f"**Labour Rate:** £{rate:.2f} per pair of engineers per day ({hours_per_day}-hour day){travel_note}\n**CRITICAL: £{rate:.2f} is the TOTAL cost for BOTH engineers working together for one day**"
        
        # Default fallback
        return "**Labour Rate:** £300 per pair of engineers per day (8-hour day)\n**CRITICAL: £300 is the TOTAL cost for BOTH engineers working together for one day**"
    
    def list_configs(
        self,
        config_type: Optional[str] = None,
        include_inactive: bool = False
    ) -> List[TenantPricingConfig]:
        """List pricing configurations"""
        query = self.db.query(TenantPricingConfig).filter(
            and_(
                TenantPricingConfig.tenant_id == self.tenant_id,
                TenantPricingConfig.is_deleted == False
            )
        )
        
        if config_type:
            query = query.filter(TenantPricingConfig.config_type == config_type)
        
        if not include_inactive:
            query = query.filter(TenantPricingConfig.is_active == True)
        
        return query.order_by(desc(TenantPricingConfig.priority), desc(TenantPricingConfig.created_at)).all()
    
    def get_config(self, config_id: str) -> Optional[TenantPricingConfig]:
        """Get a specific pricing configuration"""
        return self.db.query(TenantPricingConfig).filter(
            and_(
                TenantPricingConfig.id == config_id,
                TenantPricingConfig.tenant_id == self.tenant_id,
                TenantPricingConfig.is_deleted == False
            )
        ).first()
    
    def update_config(
        self,
        config_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        base_rate: Optional[Decimal] = None,
        config_data: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None,
        priority: Optional[int] = None,
        valid_from: Optional[datetime] = None,
        valid_until: Optional[datetime] = None
    ) -> Optional[TenantPricingConfig]:
        """Update a pricing configuration"""
        config = self.get_config(config_id)
        
        if not config:
            return None
        
        if name is not None:
            config.name = name
        if description is not None:
            config.description = description
        if base_rate is not None:
            config.base_rate = base_rate
        if config_data is not None:
            config.config_data = config_data
        if is_active is not None:
            config.is_active = is_active
        if priority is not None:
            config.priority = priority
        if valid_from is not None:
            config.valid_from = valid_from
        if valid_until is not None:
            config.valid_until = valid_until
        
        self.db.commit()
        self.db.refresh(config)
        
        return config
    
    def delete_config(self, config_id: str) -> bool:
        """Soft delete a pricing configuration"""
        config = self.get_config(config_id)
        
        if not config:
            return False
        
        config.is_deleted = True
        config.deleted_at = datetime.now(timezone.utc)
        
        self.db.commit()
        
        return True
    
    def get_bundle_items(self, bundle_config_id: str) -> List[PricingBundleItem]:
        """Get items for a bundle configuration"""
        return self.db.query(PricingBundleItem).filter(
            and_(
                PricingBundleItem.bundle_config_id == bundle_config_id,
                PricingBundleItem.tenant_id == self.tenant_id,
                PricingBundleItem.is_deleted == False
            )
        ).order_by(PricingBundleItem.display_order).all()

