#!/usr/bin/env python3
"""
AI Provider Abstraction Layer
Provides unified interface for multiple AI providers (OpenAI, Google, Anthropic, etc.)
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
import httpx
import json
import asyncio
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
                
                # Wrap synchronous call in executor to avoid blocking event loop
                response = await asyncio.run_in_executor(
                    None,
                    lambda: self.client.responses.create(
                        model=model,
                        input=input_string,
                        tools=tools or [],
                        tool_choice=kwargs.get("tool_choice", "auto")
                    )
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
                # Handle max_completion_tokens vs max_tokens
                # OpenAI uses max_completion_tokens, but we accept max_tokens for consistency
                completion_kwargs = kwargs.copy()
                if "max_completion_tokens" in completion_kwargs:
                    # Use the explicit max_completion_tokens if provided
                    pass
                else:
                    # Map max_tokens to max_completion_tokens for OpenAI
                    completion_kwargs["max_completion_tokens"] = max_tokens
                    # Remove max_tokens if present to avoid confusion
                    completion_kwargs.pop("max_tokens", None)
                
                # Wrap synchronous call in executor to avoid blocking event loop
                response = await asyncio.run_in_executor(
                    None,
                    lambda: self.client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=temperature,
                        **completion_kwargs
                    )
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
        """Generate completion using Google Gemini API
        
        Google's Generative AI SDK supports async methods natively.
        """
        
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
            
            # Generate content (Google SDK has native async support)
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
            import asyncio
            
            # Anthropic SDK is synchronous, so we run it in executor
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_prompt}
                    ],
                    **kwargs
                )
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
            
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=10,
                    messages=[{"role": "user", "content": "Test"}]
                )
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
            # Handle max_completion_tokens vs max_tokens (OpenAI-compatible API)
            completion_kwargs = kwargs.copy()
            if "max_completion_tokens" in completion_kwargs:
                # Use the explicit max_completion_tokens if provided
                pass
            else:
                # Map max_tokens to max_completion_tokens for OpenAI-compatible API
                completion_kwargs["max_completion_tokens"] = max_tokens
                # Remove max_tokens if present to avoid confusion
                completion_kwargs.pop("max_tokens", None)
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                **completion_kwargs
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


class CohereProvider(AIProvider):
    """Cohere provider implementation
    
    According to Cohere API docs (https://docs.cohere.com/):
    - Uses Cohere SDK with chat() method
    - Also supports OpenAI-compatible API via compatibility endpoint
    """
    
    def _initialize_client(self):
        """Initialize Cohere client"""
        try:
            import cohere
            self.client = cohere.Client(api_key=self.api_key)
        except ImportError:
            print("[Cohere Provider] cohere package not installed")
            self.client = None
        except Exception as e:
            print(f"[Cohere Provider] Error initializing client: {e}")
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
        """Generate completion using Cohere Chat API
        
        Cohere chat API format:
        - message: The user message (system prompt is typically included in the message)
        - chat_history: Optional conversation history
        - preamble: System-level instructions (equivalent to system prompt)
        """
        
        if not self.client:
            raise Exception("Cohere client not initialized")
        
        try:
            import asyncio
            import cohere
            
            # Cohere chat API supports system prompts via 'preamble' parameter
            # Combine system and user prompts, or use preamble for system
            # According to Cohere docs, preamble is for system-level instructions
            
            # Cohere SDK is synchronous, so we run it in executor
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat(
                    model=model,
                    message=user_prompt,
                    preamble=system_prompt if system_prompt else None,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
            )
            
            content = response.text
            # Cohere response includes usage in meta.billed_units
            usage = {}
            if hasattr(response, 'meta') and hasattr(response.meta, 'billed_units'):
                billed_units = response.meta.billed_units
                usage = {
                    "input_tokens": getattr(billed_units, 'input_tokens', 0),
                    "output_tokens": getattr(billed_units, 'output_tokens', 0)
                }
            
            return AIProviderResponse(
                content=content,
                model=model,
                usage=usage,
                raw_response=response
            )
        
        except Exception as e:
            print(f"[Cohere Provider] Error generating completion: {e}")
            raise
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Cohere API connection"""
        try:
            if not self.client:
                return {"success": False, "error": "Client not initialized"}
            
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat(
                    model="command",
                    message="Test",
                    max_tokens=10
                )
            )
            
            return {
                "success": True,
                "message": "Cohere API connection successful",
                "model": "command"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_supported_models(self) -> List[str]:
        """Get supported Cohere models"""
        return ["command", "command-light", "command-r", "command-r-plus"]


class MistralProvider(AIProvider):
    """Mistral AI provider implementation
    
    According to Mistral API docs (https://docs.mistral.ai/api):
    - Uses mistral.chat.complete() method
    - Supports messages array with role and content
    - SDK is synchronous, wrapped in executor for async compatibility
    """
    
    def _initialize_client(self):
        """Initialize Mistral client"""
        try:
            from mistralai import Mistral
            # Mistral SDK can be used as context manager, but we'll use it directly
            self.client = Mistral(api_key=self.api_key)
        except ImportError:
            print("[Mistral Provider] mistralai package not installed")
            self.client = None
        except Exception as e:
            print(f"[Mistral Provider] Error initializing client: {e}")
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
        """Generate completion using Mistral Chat API
        
        Mistral API format (https://docs.mistral.ai/api):
        - messages: Array of message objects with role and content
        - model: Model ID (e.g., "mistral-small-latest", "mistral-large-latest")
        - temperature: Sampling temperature (0.0-1.0, recommended 0.0-0.7)
        - max_tokens: Maximum tokens to generate
        """
        
        if not self.client:
            raise Exception("Mistral client not initialized")
        
        try:
            from mistralai import Mistral
            import asyncio
            
            # Build messages array - Mistral supports system messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": user_prompt})
            
            # Mistral SDK is synchronous, so we run it in executor
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat.complete(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
            )
            
            # Extract content from response
            content = response.choices[0].message.content
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            return AIProviderResponse(
                content=content,
                model=model,
                usage=usage,
                raw_response=response
            )
        
        except Exception as e:
            print(f"[Mistral Provider] Error generating completion: {e}")
            raise
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Mistral API connection"""
        try:
            if not self.client:
                return {"success": False, "error": "Client not initialized"}
            
            import asyncio
            loop = asyncio.get_event_loop()
            # Use a common model name for testing
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat.complete(
                    model="mistral-small-latest",
                    messages=[{"role": "user", "content": "Test"}],
                    max_tokens=10
                )
            )
            
            return {
                "success": True,
                "message": "Mistral API connection successful",
                "model": "mistral-small-latest"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_supported_models(self) -> List[str]:
        """Get supported Mistral models
        
        According to Mistral docs, common models include:
        - mistral-tiny-latest, mistral-small-latest
        - mistral-medium-latest, mistral-large-latest
        - pixtral-12b (multimodal)
        """
        return [
            "mistral-tiny-latest",
            "mistral-small-latest",
            "mistral-medium-latest",
            "mistral-large-latest",
            "pixtral-12b"
        ]


class DeepSeekProvider(AIProvider):
    """DeepSeek provider implementation (uses OpenAI-compatible API)"""
    
    def _initialize_client(self):
        """Initialize DeepSeek client (OpenAI-compatible)
        
        According to DeepSeek API docs:
        - base_url: https://api.deepseek.com (or https://api.deepseek.com/v1 for compatibility)
        - Uses OpenAI-compatible API format
        """
        try:
            # Use base_url from config, or default to https://api.deepseek.com
            # The /v1 suffix is optional for OpenAI compatibility
            base_url = self.base_url or "https://api.deepseek.com"
            # Ensure it ends with /v1 for OpenAI SDK compatibility
            if not base_url.endswith('/v1'):
                if base_url.endswith('/'):
                    base_url = base_url + 'v1'
                else:
                    base_url = base_url + '/v1'
            
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=base_url,
                timeout=300.0
            )
        except Exception as e:
            print(f"[DeepSeek Provider] Error initializing client: {e}")
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
        """Generate completion using DeepSeek API (OpenAI-compatible)"""
        
        if not self.client:
            raise Exception("DeepSeek client not initialized")
        
        try:
            # Handle max_completion_tokens vs max_tokens (OpenAI-compatible API)
            completion_kwargs = kwargs.copy()
            if "max_completion_tokens" in completion_kwargs:
                # Use the explicit max_completion_tokens if provided
                pass
            else:
                # Map max_tokens to max_completion_tokens for OpenAI-compatible API
                completion_kwargs["max_completion_tokens"] = max_tokens
                # Remove max_tokens if present to avoid confusion
                completion_kwargs.pop("max_tokens", None)
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                **completion_kwargs
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
            print(f"[DeepSeek Provider] Error generating completion: {e}")
            raise
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test DeepSeek API connection"""
        try:
            if not self.client:
                return {"success": False, "error": "Client not initialized"}
            
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": "Test"}],
                max_completion_tokens=10
            )
            
            return {
                "success": True,
                "message": "DeepSeek API connection successful",
                "model": "deepseek-chat"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_supported_models(self) -> List[str]:
        """Get supported DeepSeek models"""
        return ["deepseek-chat", "deepseek-coder"]


class GrokProvider(AIProvider):
    """Grok (xAI) provider implementation (uses OpenAI-compatible API)"""
    
    def _initialize_client(self):
        """Initialize Grok client (OpenAI-compatible)"""
        try:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url or "https://api.x.ai/v1",
                timeout=300.0
            )
        except Exception as e:
            print(f"[Grok Provider] Error initializing client: {e}")
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
        """Generate completion using Grok API (OpenAI-compatible)"""
        
        if not self.client:
            raise Exception("Grok client not initialized")
        
        try:
            # Handle max_completion_tokens vs max_tokens (OpenAI-compatible API)
            completion_kwargs = kwargs.copy()
            if "max_completion_tokens" in completion_kwargs:
                # Use the explicit max_completion_tokens if provided
                pass
            else:
                # Map max_tokens to max_completion_tokens for OpenAI-compatible API
                completion_kwargs["max_completion_tokens"] = max_tokens
                # Remove max_tokens if present to avoid confusion
                completion_kwargs.pop("max_tokens", None)
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                **completion_kwargs
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
            print(f"[Grok Provider] Error generating completion: {e}")
            raise
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Grok API connection"""
        try:
            if not self.client:
                return {"success": False, "error": "Client not initialized"}
            
            response = self.client.chat.completions.create(
                model="grok-beta",
                messages=[{"role": "user", "content": "Test"}],
                max_completion_tokens=10
            )
            
            return {
                "success": True,
                "message": "Grok API connection successful",
                "model": "grok-beta"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_supported_models(self) -> List[str]:
        """Get supported Grok models"""
        return ["grok-beta", "grok-2"]


# Provider Registry
PROVIDER_REGISTRY = {
    "openai": OpenAIProvider,
    "google": GoogleProvider,
    "anthropic": AnthropicProvider,
    "cohere": CohereProvider,
    "mistral": MistralProvider,
    "deepseek": DeepSeekProvider,
    "grok": GrokProvider,
    "ollama": OllamaProvider,
    "openai_compatible": OpenAICompatibleProvider,
    "openai-compatible": OpenAICompatibleProvider,  # Alias
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

