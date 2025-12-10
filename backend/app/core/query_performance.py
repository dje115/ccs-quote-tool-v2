#!/usr/bin/env python3
"""
Query performance monitoring and logging

PERFORMANCE: Logs slow queries to help identify N+1 problems and optimization opportunities
"""

import logging
import time
from contextlib import contextmanager
from typing import Optional
from sqlalchemy import event
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

# Threshold for slow query logging (in seconds)
SLOW_QUERY_THRESHOLD = 0.1  # 100ms


@contextmanager
def log_query_performance(operation_name: str, threshold: float = SLOW_QUERY_THRESHOLD):
    """
    Context manager to log query performance
    
    Usage:
        with log_query_performance("get_customer_with_activities"):
            # Database operations
            customer = await db.execute(stmt)
    
    Args:
        operation_name: Name of the operation being performed
        threshold: Time threshold in seconds (default: 0.1s)
    """
    start_time = time.time()
    try:
        yield
    finally:
        elapsed = time.time() - start_time
        if elapsed > threshold:
            logger.warning(
                f"Slow query detected: {operation_name} took {elapsed:.3f}s (threshold: {threshold}s)",
                extra={
                    "operation": operation_name,
                    "duration": elapsed,
                    "threshold": threshold
                }
            )
        else:
            logger.debug(
                f"Query performance: {operation_name} took {elapsed:.3f}s",
                extra={
                    "operation": operation_name,
                    "duration": elapsed
                }
            )


def setup_query_logging():
    """
    Set up SQLAlchemy event listeners for query logging
    
    This will log all queries that take longer than SLOW_QUERY_THRESHOLD
    """
    @event.listens_for(Engine, "before_cursor_execute")
    def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        conn.info.setdefault('query_start_time', []).append(time.time())
    
    @event.listens_for(Engine, "after_cursor_execute")
    def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        total = time.time() - conn.info['query_start_time'].pop(-1)
        if total > SLOW_QUERY_THRESHOLD:
            logger.warning(
                f"Slow SQL query detected: {total:.3f}s",
                extra={
                    "duration": total,
                    "statement": statement[:200] if statement else None,  # First 200 chars
                    "threshold": SLOW_QUERY_THRESHOLD
                }
            )


def count_queries(operation_name: str):
    """
    Decorator to count and log number of queries executed
    
    Usage:
        @count_queries("get_customer")
        async def get_customer(...):
            # Database operations
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This would require more sophisticated query counting
            # For now, we'll use the context manager approach
            with log_query_performance(operation_name):
                return await func(*args, **kwargs)
        return wrapper
    return decorator

