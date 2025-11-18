"""
Regression tests for building_analysis_service.py
Tests P0.3 fix: Missing imports
"""
import pytest
from unittest.mock import Mock

from app.services.building_analysis_service import BuildingAnalysisService


def test_building_analysis_service_imports_available():
    """Test that Tenant and get_api_keys are imported"""
    # This test verifies imports are available by importing the service
    from app.services.building_analysis_service import BuildingAnalysisService
    
    # Verify the service class exists
    assert BuildingAnalysisService is not None
    
    # Verify imports are available in the module
    import app.services.building_analysis_service as building_module
    # These should not raise ImportError
    assert hasattr(building_module, 'Tenant') or 'Tenant' in dir(building_module)
    assert hasattr(building_module, 'get_api_keys') or 'get_api_keys' in dir(building_module)



