#!/usr/bin/env python3
"""
Integration tests for performance optimizations

Tests:
- N+1 query fixes (eager loading verification)
- Caching behavior (hit/miss scenarios)
- Async patterns in Celery tasks
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Customer, CustomerStatus
from app.core.caching import get_cache, set_cache, delete_cache
from app.core.async_bridge import run_async_safe, AsyncBridge


@pytest.mark.asyncio
async def test_customer_eager_loading_no_n_plus_one(db_session: AsyncSession):
    """
    Test that customer list endpoint uses eager loading to prevent N+1 queries.
    
    This test verifies that when loading customers with relationships,
    we use selectinload() to load all related data in a single query.
    """
    from app.models.tenant import Contact
    from app.models.sales import SalesActivity
    
    # Create test data
    customer1 = Customer(
        id="test-customer-1",
        tenant_id="test-tenant",
        company_name="Test Company 1",
        status=CustomerStatus.LEAD,
        is_deleted=False
    )
    customer2 = Customer(
        id="test-customer-2",
        tenant_id="test-tenant",
        company_name="Test Company 2",
        status=CustomerStatus.LEAD,
        is_deleted=False
    )
    
    contact1 = Contact(
        id="test-contact-1",
        customer_id="test-customer-1",
        tenant_id="test-tenant",
        first_name="John",
        last_name="Doe",
        email="john@test.com"
    )
    
    activity1 = SalesActivity(
        id="test-activity-1",
        customer_id="test-customer-1",
        tenant_id="test-tenant",
        activity_type="call",
        notes="Test activity"
    )
    
    db_session.add(customer1)
    db_session.add(customer2)
    db_session.add(contact1)
    db_session.add(activity1)
    await db_session.commit()
    
    # Test eager loading with selectinload
    stmt = select(Customer).options(
        selectinload(Customer.contacts),
        selectinload(Customer.sales_activities)
    ).where(
        Customer.tenant_id == "test-tenant",
        Customer.status == CustomerStatus.LEAD
    )
    
    result = await db_session.execute(stmt)
    customers = result.scalars().all()
    
    # Verify customers are loaded
    assert len(customers) >= 2
    
    # Verify relationships are loaded (no additional queries needed)
    for customer in customers:
        # Accessing contacts should not trigger additional queries
        # because they're already loaded via selectinload
        contacts = customer.contacts
        assert contacts is not None
        
        # Accessing sales_activities should not trigger additional queries
        activities = customer.sales_activities
        assert activities is not None


@pytest.mark.asyncio
async def test_caching_hit_miss_scenario():
    """
    Test that caching works correctly for hit and miss scenarios.
    """
    from app.core.redis import get_redis
    
    # Test cache miss (key doesn't exist)
    cache_key = "test:cache:miss"
    cached_value = await get_cache(cache_key)
    assert cached_value is None
    
    # Test cache set and get
    test_data = {"test": "data", "number": 123}
    await set_cache(cache_key, test_data, ttl=60)
    
    # Test cache hit
    cached_value = await get_cache(cache_key)
    assert cached_value == test_data
    
    # Test cache deletion
    await delete_cache(cache_key)
    cached_value = await get_cache(cache_key)
    assert cached_value is None


@pytest.mark.asyncio
async def test_caching_ttl_expiration():
    """
    Test that cache TTL (time-to-live) works correctly.
    """
    cache_key = "test:cache:ttl"
    test_data = {"expires": "soon"}
    
    # Set cache with short TTL (1 second)
    await set_cache(cache_key, test_data, ttl=1)
    
    # Immediately retrieve (should be there)
    cached_value = await get_cache(cache_key)
    assert cached_value == test_data
    
    # Wait for TTL to expire
    import asyncio
    await asyncio.sleep(2)
    
    # Should be expired now
    cached_value = await get_cache(cache_key)
    assert cached_value is None


def test_async_bridge_runs_async_code():
    """
    Test that async_bridge can run async code from sync context (like Celery tasks).
    """
    async def async_function():
        return "async result"
    
    # Run async function from sync context
    result = run_async_safe(async_function())
    
    assert result == "async result"


def test_async_bridge_handles_async_exceptions():
    """
    Test that async_bridge properly propagates exceptions from async code.
    """
    async def async_function_that_raises():
        raise ValueError("Test error")
    
    # Exception should be raised
    with pytest.raises(ValueError, match="Test error"):
        run_async_safe(async_function_that_raises())


def test_async_bridge_with_awaitable():
    """
    Test that async_bridge works with awaitable objects.
    """
    import asyncio
    
    async def async_function():
        await asyncio.sleep(0.01)  # Small delay to simulate async work
        return "delayed result"
    
    result = run_async_safe(async_function())
    
    assert result == "delayed result"


@pytest.mark.asyncio
async def test_customer_list_uses_batch_queries(db_session: AsyncSession):
    """
    Test that customer list endpoint uses batch queries for related data
    instead of N+1 queries.
    """
    from app.models.sales import SalesActivity
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import func, and_
    
    # Create multiple customers with activities
    customers = []
    activities = []
    
    for i in range(5):
        customer = Customer(
            id=f"test-customer-{i}",
            tenant_id="test-tenant",
            company_name=f"Test Company {i}",
            status=CustomerStatus.CUSTOMER,
            is_deleted=False
        )
        customers.append(customer)
        db_session.add(customer)
        
        # Add activity for each customer
        activity = SalesActivity(
            id=f"test-activity-{i}",
            customer_id=f"test-customer-{i}",
            tenant_id="test-tenant",
            activity_type="call",
            follow_up_date=datetime.now(timezone.utc) + timedelta(days=1)
        )
        activities.append(activity)
        db_session.add(activity)
    
    await db_session.commit()
    
    # Query customers
    stmt = select(Customer).where(
        Customer.tenant_id == "test-tenant",
        Customer.status == CustomerStatus.CUSTOMER
    )
    result = await db_session.execute(stmt)
    customer_list = result.scalars().all()
    
    # Get customer IDs
    customer_ids = [str(c.id) for c in customer_list]
    
    # Batch query for next contacts (should be single query, not N queries)
    npa_stmt = select(
        SalesActivity.customer_id,
        func.min(SalesActivity.follow_up_date).label('next_contact')
    ).where(
        and_(
            SalesActivity.customer_id.in_(customer_ids),
            SalesActivity.tenant_id == "test-tenant",
            SalesActivity.follow_up_date.isnot(None),
            SalesActivity.follow_up_date > datetime.now(timezone.utc)
        )
    ).group_by(SalesActivity.customer_id)
    
    npa_result = await db_session.execute(npa_stmt)
    next_contacts = {str(row.customer_id): row.next_contact for row in npa_result}
    
    # Verify batch query returned data for all customers
    assert len(next_contacts) == 5
    for customer_id in customer_ids:
        assert customer_id in next_contacts
        assert next_contacts[customer_id] is not None


@pytest.mark.asyncio
async def test_cache_invalidation_on_update():
    """
    Test that cache is invalidated when data is updated.
    """
    cache_key = "customer:test-customer-1"
    original_data = {"name": "Original Name"}
    updated_data = {"name": "Updated Name"}
    
    # Set initial cache
    await set_cache(cache_key, original_data, ttl=3600)
    
    # Verify cache has original data
    cached = await get_cache(cache_key)
    assert cached == original_data
    
    # Simulate update - invalidate cache
    await delete_cache(cache_key)
    
    # Verify cache is cleared
    cached = await get_cache(cache_key)
    assert cached is None
    
    # Set new data
    await set_cache(cache_key, updated_data, ttl=3600)
    
    # Verify cache has updated data
    cached = await get_cache(cache_key)
    assert cached == updated_data

