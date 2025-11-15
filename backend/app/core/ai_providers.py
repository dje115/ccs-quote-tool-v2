#!/usr/bin/env python3
"""
AI Provider Abstraction Layer
Provides unified interface for multiple AI providers (OpenAI, Google, Anthropic, etc.)
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
import httpx
import json
from openai import OpenAI
from datetime import datetime


class AIProviderResponse:
    """Standardized response format from AI providers"""
    def __init__(
        self,
        content: str,
        model: str,
        usage: Optional[Dict[str, Any]] = None,
        raw_response: Optional[Any] = None,
        sources: Optional[List[Dict[str, Any]]] = None
    ):
        self.content = content
        self.model = model
        self.usage = usage or {}
        self.raw_response = raw_response
        self.sources = sources or []


class AIProvider(ABC):
    """Base class for AI provider implementations"""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None, **kwargs):
        self.api_key = api_key
        self.base_url = base_url
        self.client = None
        self._initialize_client()
    
    @abstractmethod
    def _initialize_client(self):
        """Initialize the provider's client"""
        pass
    
    @abstractmethod
    async def generate_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 8000,
        **kwargs
    ) -> AIProviderResponse:
        """Generate a completion using the provider's API"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """Test the API connection and return status"""
        pass
    
    def get_supported_models(self) -> List[str]:
        """Get list of supported models for this provider"""
        return []


class OpenAIProvider(AIProvider):
    """OpenAI provider implementation (supports both chat.completions and responses.create)"""
    
    def _initialize_client(self):
        """Initialize OpenAI client"""
        try:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=300.0
            )
        except Exception as e:
            print(f"[OpenAI Provider] Error initializing client: {e}")
            self.client = None
    
    async def generate_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 8000,
        use_responses_api: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AIProviderResponse:
        """Generate completion using OpenAI API"""
        
        if not self.client:
            raise Exception("OpenAI client not initialized")
        
        try:
            # Use responses.create() API if requested (for web search, etc.)
            if use_responses_api or (tools and len(tools) > 0):
                input_string = f"{system_prompt}\n\n{user_prompt}"
                
                response = self.client.responses.create(
                    model=model,
                    input=input_string,
                    tools=tools or [],
                    tool_choice=kwargs.get("tool_choice", "auto")
                )
                
                # Extract content from responses.create() format
                content = None
                sources = []
                
                if hasattr(response, 'output_text') and response.output_text:
                    content = response.output_text.strip()
                elif hasattr(response, 'output') and isinstance(response.output, list):
                    for item in response.output:
                        if isinstance(item, dict) and "content" in item:
                            for block in item["content"]:
                                if block.get("type") == "output_text" and not content:
                                    content = block.get("text", "").strip()
                                elif block.get("type") == "tool_use" and block.get("tool") == "web_search_preview":
                                    web_results = block.get("results", [])
                                    for r in web_results:
                                        sources.append({
                                            "title": r.get("title", "Untitled"),
                                            "url": r.get("url", ""),
                                            "snippet": r.get("snippet", "")
                                        })
                elif hasattr(response, 'choices') and len(response.choices) > 0:
                    content = response.choices[0].message.content.strip()
                
                if not content:
                    raise Exception("No content extracted from OpenAI response")
                
                return AIProviderResponse(
                    content=content,
                    model=model,
                    usage={},
                    raw_response=response,
                    sources=sources
                )
            
            # Use standard chat.completions.create() API
            else:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_completion_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs
                )
                
                content = response.choices[0].message.content
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens if hasattr(response.usage, 'prompt_tokens') else 0,
                    "completion_tokens": response.usage.completion_tokens if hasattr(response.usage, 'completion_tokens') else 0,
                    "total_tokens": response.usage.total_tokens if hasattr(response.usage, 'total_tokens') else 0
                }
                
                return AIProviderResponse(
                    content=content,
                    model=model,
                    usage=usage,
                    raw_response=response
                )
        
        except Exception as e:
            print(f"[OpenAI Provider] Error generating completion: {e}")
            raise
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test OpenAI API connection"""
        try:
            if not self.client:
                return {"success": False, "error": "Client not initialized"}
            
            # Simple test call
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Test"}],
                max_completion_tokens=10
            )
            
            return {
                "success": True,
                "message": "OpenAI API connection successful",
                "model": "gpt-4o-mini"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_supported_models(self) -> List[str]:
        """Get supported OpenAI models"""
        return [
            "gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini",
            "gpt-5", "gpt-5-mini", "o1", "o1-mini"
        ]


class GoogleProvider(AIProvider):
    """Google Gemini provider implementation"""
    
    def _initialize_client(self):
        """Initialize Google client"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.client = genai
        except ImportError:
            print("[Google Provider] google-generativeai package not installed")
            self.client = None
        except Exception as e:
            print(f"[Google Provider] Error initializing client: {e}")
            self.client = None
    
    async def generate_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 8000,
        **kwargs
    ) -> AIProviderResponse:
        """Generate completion using Google Gemini API"""
        
        if not self.client:
            raise Exception("Google client not initialized")
        
        try:
            import google.generativeai as genai
            
            # Combine system and user prompts for Gemini
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Configure generation config
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
                **kwargs.get("generation_config", {})
            }
            
            # Get model
            gemini_model = genai.GenerativeModel(model)
            
            # Generate content
            response = await gemini_model.generate_content_async(
                full_prompt,
                generation_config=generation_config
            )
            
            content = response.text
            
            return AIProviderResponse(
                content=content,
                model=model,
                usage={},
                raw_response=response
            )
        
        except Exception as e:
            print(f"[Google Provider] Error generating completion: {e}")
            raise
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Google API connection"""
        try:
            if not self.client:
                return {"success": False, "error": "Client not initialized"}
            
            import google.generativeai as genai
            model = genai.GenerativeModel("gemini-pro")
            response = await model.generate_content_async("Test")
            
            return {
                "success": True,
                "message": "Google Gemini API connection successful",
                "model": "gemini-pro"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_supported_models(self) -> List[str]:
        """Get supported Google models"""
        return [
            "gemini-pro", "gemini-pro-vision", "gemini-1.5-pro",
            "gemini-1.5-flash", "gemini-2.0-flash-exp"
        ]


class AnthropicProvider(AIProvider):
    """Anthropic Claude provider implementation"""
    
    def _initialize_client(self):
        """Initialize Anthropic client"""
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
        except ImportError:
            print("[Anthropic Provider] anthropic package not installed")
            self.client = None
        except Exception as e:
            print(f"[Anthropic Provider] Error initializing client: {e}")
            self.client = None
    
    async def generate_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 8000,
        **kwargs
    ) -> AIProviderResponse:
        """Generate completion using Anthropic Claude API"""
        
        if not self.client:
            raise Exception("Anthropic client not initialized")
        
        try:
            from anthropic import Anthropic
            
            # Anthropic uses messages format
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
                **kwargs
            )
            
            content = response.content[0].text
            usage = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            }
            
            return AIProviderResponse(
                content=content,
                model=model,
                usage=usage,
                raw_response=response
            )
        
        except Exception as e:
            print(f"[Anthropic Provider] Error generating completion: {e}")
            raise
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Anthropic API connection"""
        try:
            if not self.client:
                return {"success": False, "error": "Client not initialized"}
            
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": "Test"}]
            )
            
            return {
                "success": True,
                "message": "Anthropic API connection successful",
                "model": "claude-3-haiku-20240307"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_supported_models(self) -> List[str]:
        """Get supported Anthropic models"""
        return [
            "claude-3-opus", "claude-3-sonnet", "claude-3-haiku",
            "claude-3-5-sonnet", "claude-3-5-haiku"
        ]


class OllamaProvider(AIProvider):
    """Ollama provider implementation (on-premise)"""
    
    def _initialize_client(self):
        """Initialize Ollama client"""
        self.base_url = self.base_url or "http://localhost:11434"
        self.client = None  # Ollama uses HTTP directly
    
    async def generate_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 8000,
        **kwargs
    ) -> AIProviderResponse:
        """Generate completion using Ollama API"""
        
        try:
            # Ollama uses OpenAI-compatible API
            base_url = f"{self.base_url}/v1"
            
            async with httpx.AsyncClient(timeout=300.0) as client:
                # Combine system and user prompts for Ollama
                full_prompt = f"{system_prompt}\n\n{user_prompt}"
                
                response = await client.post(
                    f"{base_url}/chat/completions",
                    json={
                        "model": model,
                        "messages": [
                            {"role": "user", "content": full_prompt}
                        ],
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        **kwargs
                    }
                )
                
                if response.status_code != 200:
                    raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
                
                result = response.json()
                content = result['choices'][0]['message']['content']
                usage = result.get('usage', {})
                
                return AIProviderResponse(
                    content=content,
                    model=model,
                    usage=usage,
                    raw_response=result
                )
        
        except Exception as e:
            print(f"[Ollama Provider] Error generating completion: {e}")
            raise
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Ollama connection"""
        try:
            base_url = self.base_url or "http://localhost:11434"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Test if Ollama is running
                response = await client.get(f"{base_url}/api/tags")
                
                if response.status_code == 200:
                    return {
                        "success": True,
                        "message": "Ollama connection successful",
                        "models": response.json().get("models", [])
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Ollama returned status {response.status_code}"
                    }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_supported_models(self) -> List[str]:
        """Get supported Ollama models (dynamic - depends on what's installed)"""
        return [
            "llama2", "llama3", "mistral", "codellama",
            "phi", "neural-chat", "starling-lm", "qwen", "llava"
        ]


class OpenAICompatibleProvider(AIProvider):
    """OpenAI-compatible provider for self-hosted models"""
    
    def _initialize_client(self):
        """Initialize OpenAI-compatible client"""
        try:
            self.client = OpenAI(
                api_key=self.api_key or "not-needed",
                base_url=self.base_url or "http://localhost:8000/v1",
                timeout=300.0
            )
        except Exception as e:
            print(f"[OpenAI Compatible Provider] Error initializing client: {e}")
            self.client = None
    
    async def generate_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 8000,
        **kwargs
    ) -> AIProviderResponse:
        """Generate completion using OpenAI-compatible API"""
        
        if not self.client:
            raise Exception("OpenAI-compatible client not initialized")
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_completion_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            
            content = response.choices[0].message.content
            usage = {
                "prompt_tokens": response.usage.prompt_tokens if hasattr(response.usage, 'prompt_tokens') else 0,
                "completion_tokens": response.usage.completion_tokens if hasattr(response.usage, 'completion_tokens') else 0,
                "total_tokens": response.usage.total_tokens if hasattr(response.usage, 'total_tokens') else 0
            }
            
            return AIProviderResponse(
                content=content,
                model=model,
                usage=usage,
                raw_response=response
            )
        
        except Exception as e:
            print(f"[OpenAI Compatible Provider] Error generating completion: {e}")
            raise
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test OpenAI-compatible API connection"""
        try:
            if not self.client:
                return {"success": False, "error": "Client not initialized"}
            
            # Try to list models
            response = self.client.models.list()
            
            return {
                "success": True,
                "message": "OpenAI-compatible API connection successful",
                "models": [m.id for m in response.data] if hasattr(response, 'data') else []
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_supported_models(self) -> List[str]:
        """Get supported models (dynamic - depends on what's available)"""
        return ["custom-model-1", "custom-model-2"]


# Provider Registry
PROVIDER_REGISTRY = {
    "openai": OpenAIProvider,
    "google": GoogleProvider,
    "anthropic": AnthropicProvider,
    "ollama": OllamaProvider,
    "openai-compatible": OpenAICompatibleProvider,
}


def get_provider_class(provider_slug: str) -> Optional[type]:
    """Get provider class by slug"""
    return PROVIDER_REGISTRY.get(provider_slug)


def create_provider(provider_slug: str, api_key: str, base_url: Optional[str] = None, **kwargs) -> Optional[AIProvider]:
    """Create a provider instance"""
    provider_class = get_provider_class(provider_slug)
    if not provider_class:
        return None
    
    try:
        return provider_class(api_key=api_key, base_url=base_url, **kwargs)
    except Exception as e:
        print(f"[Provider Factory] Error creating provider {provider_slug}: {e}")
        return None

