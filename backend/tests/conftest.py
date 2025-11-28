"""
Pytest configuration and fixtures
"""
import pytest
from unittest.mock import Mock
from sqlalchemy.orm import Session


@pytest.fixture
def mock_db():
    """Mock database session"""
    return Mock(spec=Session)


@pytest.fixture
def test_tenant_id():
    """Test tenant ID"""
    return "test-tenant-id-12345"


@pytest.fixture
def test_user_id():
    """Test user ID"""
    return "test-user-id-12345"






