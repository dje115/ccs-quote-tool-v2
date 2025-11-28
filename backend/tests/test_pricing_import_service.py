"""
Regression tests for pricing_import_service.py
Tests P0.1 fix: openai_api_key attribute assignment
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from app.services.pricing_import_service import PricingImportService


def test_pricing_import_service_stores_openai_api_key():
    """Test that openai_api_key parameter is stored in __init__"""
    db = Mock(spec=Session)
    tenant_id = "test-tenant-id"
    api_key = "test-api-key-12345"
    
    service = PricingImportService(db, tenant_id, openai_api_key=api_key)
    
    # Verify the attribute is stored
    assert hasattr(service, 'openai_api_key')
    assert service.openai_api_key == api_key


def test_pricing_import_service_without_api_key():
    """Test that service works without openai_api_key"""
    db = Mock(spec=Session)
    tenant_id = "test-tenant-id"
    
    service = PricingImportService(db, tenant_id)
    
    # Verify the attribute exists but is None
    assert hasattr(service, 'openai_api_key')
    assert service.openai_api_key is None






