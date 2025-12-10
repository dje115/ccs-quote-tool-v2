#!/usr/bin/env python3
"""
Async-to-sync bridge for Celery tasks

PERFORMANCE: Provides a safe way to run async code from synchronous Celery tasks
without using asyncio.run() which creates new event loops and can cause issues.
"""

import asyncio
import threading
from typing import Callable, Any, Coroutine
from functools import wraps


class AsyncBridge:
    """
    Bridge to run async code from sync contexts (like Celery tasks)
    
    SECURITY: Uses thread-local event loops to avoid conflicts
    PERFORMANCE: Reuses event loops when possible instead of creating new ones
    """
    
    _thread_local = threading.local()
    
    @classmethod
    def get_event_loop(cls) -> asyncio.AbstractEventLoop:
        """
        Get or create event loop for current thread
        
        Returns:
            Event loop for current thread
        """
        if not hasattr(cls._thread_local, 'loop') or cls._thread_local.loop.is_closed():
            cls._thread_local.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(cls._thread_local.loop)
        return cls._thread_local.loop
    
    @classmethod
    def run_async(cls, coro: Coroutine) -> Any:
        """
        Run async coroutine from sync context
        
        Args:
            coro: Async coroutine to run
            
        Returns:
            Result of coroutine execution
        """
        loop = cls.get_event_loop()
        if loop.is_running():
            # If loop is already running, we need to use a different approach
            # This shouldn't happen in Celery tasks, but handle it gracefully
            import nest_asyncio
            nest_asyncio.apply(loop)
            return loop.run_until_complete(coro)
        else:
            return loop.run_until_complete(coro)
    
    @classmethod
    def sync_wrapper(cls, async_func: Callable) -> Callable:
        """
        Decorator to convert async function to sync function
        
        Usage:
            @AsyncBridge.sync_wrapper
            async def my_async_function():
                # async code
                
            # Can now be called from sync context
            result = my_async_function()
        
        Args:
            async_func: Async function to wrap
            
        Returns:
            Synchronous wrapper function
        """
        @wraps(async_func)
        def wrapper(*args, **kwargs):
            coro = async_func(*args, **kwargs)
            return cls.run_async(coro)
        return wrapper


def run_async_safe(coro: Coroutine) -> Any:
    """
    Convenience function to run async code from sync context
    
    Usage:
        result = run_async_safe(my_async_function())
    
    Args:
        coro: Async coroutine to run
        
    Returns:
        Result of coroutine execution
    """
    return AsyncBridge.run_async(coro)

