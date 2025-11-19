"""
Regression tests for activity_service.py
Tests P0.2 fix: Import order issue
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from app.services.activity_service import ActivityService
from app.models.tenant import Tenant
from app.core.api_keys import get_api_keys


def test_activity_service_imports_available():
    """Test that Tenant and get_api_keys are imported at module level"""
    # This test verifies imports are available by importing the service
    # If imports were missing, this would fail
    from app.services.activity_service import ActivityService
    
    # Verify the service class exists
    assert ActivityService is not None
    
    # Verify imports are available in the module
    import app.services.activity_service as activity_module
    # These should not raise ImportError
    assert hasattr(activity_module, 'Tenant') or 'Tenant' in dir(activity_module)
    assert hasattr(activity_module, 'get_api_keys') or 'get_api_keys' in dir(activity_module)




