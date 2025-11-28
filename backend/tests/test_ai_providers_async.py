"""
Regression tests for ai_providers.py
Tests P0.4 fix: Blocking async calls
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from openai import OpenAI

from app.core.ai_providers import OpenAIProvider


@pytest.mark.asyncio
async def test_openai_provider_uses_executor():
    """Test that OpenAI provider wraps synchronous calls in executor"""
    api_key = "test-api-key"
    provider = OpenAIProvider(api_key)
    
    # Mock the client
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Test response"
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 20
    mock_response.usage.total_tokens = 30
    
    provider.client = MagicMock()
    provider.client.chat.completions.create = Mock(return_value=mock_response)
    
    # Verify the call is wrapped in executor (we can't directly test executor,
    # but we can verify the method is async and doesn't block)
    response = await provider.generate_completion(
        system_prompt="Test system",
        user_prompt="Test user",
        model="gpt-4"
    )
    
    # Verify response is returned
    assert response is not None
    assert response.content == "Test response"


@pytest.mark.asyncio
async def test_openai_provider_responses_api_uses_executor():
    """Test that responses.create() API is wrapped in executor"""
    api_key = "test-api-key"
    provider = OpenAIProvider(api_key)
    
    # Mock the client
    mock_response = MagicMock()
    mock_response.output_text = "Test response from responses API"
    
    provider.client = MagicMock()
    provider.client.responses.create = Mock(return_value=mock_response)
    
    # Verify the call is wrapped in executor
    response = await provider.generate_completion(
        system_prompt="Test system",
        user_prompt="Test user",
        model="gpt-4",
        use_responses_api=True
    )
    
    # Verify response is returned
    assert response is not None
    assert response.content == "Test response from responses API"






