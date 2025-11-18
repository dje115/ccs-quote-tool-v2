#!/usr/bin/env python3
"""
Microsoft Copilot Service

Handles Microsoft Copilot integration with Microsoft Graph API.
Important for customers who want Microsoft Graph integration and data control.

Features:
- OAuth2 authentication with Azure AD
- Microsoft Graph API integration
- Copilot Pro API access
- Tenant-aware data control
"""

import httpx
import json
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.ai_provider import AIProvider, ProviderAPIKey
from app.models.tenant import Tenant
from app.core.config import settings


class MicrosoftCopilotService:
    """
    Service for Microsoft Copilot integration
    
    Handles:
    - OAuth2 token management
    - Microsoft Graph API calls
    - Copilot Pro API integration
    - Data residency and control
    """
    
    def __init__(self, db: Session, tenant_id: Optional[str] = None):
        self.db = db
        self.tenant_id = tenant_id
        self.graph_api_base = "https://graph.microsoft.com/v1.0"
        self.copilot_api_base = "https://api.copilot.microsoft.com/v1"  # Placeholder - actual endpoint may vary
        
    def get_access_token(self) -> Optional[str]:
        """
        Get Microsoft Graph access token for tenant
        
        Returns:
            Access token or None if not available
        """
        if not self.tenant_id:
            return None
        
        # Get provider
        provider = self.db.query(AIProvider).filter(
            AIProvider.slug == "microsoft_copilot",
            AIProvider.is_active == True
        ).first()
        
        if not provider:
            return None
        
        # Get tenant API key (contains access token or client secret)
        api_key = self.db.query(ProviderAPIKey).filter(
            ProviderAPIKey.provider_id == provider.id,
            ProviderAPIKey.tenant_id == self.tenant_id,
            ProviderAPIKey.is_valid == True
        ).first()
        
        if not api_key:
            # Try system key
            api_key = self.db.query(ProviderAPIKey).filter(
                ProviderAPIKey.provider_id == provider.id,
                ProviderAPIKey.tenant_id.is_(None),
                ProviderAPIKey.is_valid == True
            ).first()
        
        if api_key:
            # TODO: Implement OAuth2 token refresh if needed
            # For now, assume api_key contains access token or client secret
            return api_key.api_key
        
        return None
    
    async def get_oauth_token(
        self,
        client_id: str,
        client_secret: str,
        tenant_id: str,
        scope: str = "https://graph.microsoft.com/.default"
    ) -> Dict[str, Any]:
        """
        Get OAuth2 access token from Azure AD
        
        Args:
            client_id: Azure AD app client ID
            client_secret: Azure AD app client secret
            tenant_id: Azure AD tenant ID
            scope: OAuth2 scope (default: Microsoft Graph)
        
        Returns:
            Dict with access_token, expires_in, etc.
        """
        token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "scope": scope,
                    "grant_type": "client_credentials"
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Failed to get OAuth token: {response.text}")
    
    async def call_graph_api(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
        access_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Call Microsoft Graph API
        
        Args:
            endpoint: Graph API endpoint (e.g., "/users", "/me")
            method: HTTP method (GET, POST, etc.)
            data: Request body data
            access_token: OAuth2 access token (if not provided, will be fetched)
        
        Returns:
            API response data
        """
        if not access_token:
            access_token = self.get_access_token()
        
        if not access_token:
            raise Exception("No Microsoft Graph access token available")
        
        url = f"{self.graph_api_base}{endpoint}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "POST":
                response = await client.post(url, headers=headers, json=data)
            elif method == "PATCH":
                response = await client.patch(url, headers=headers, json=data)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            if response.status_code >= 400:
                raise Exception(f"Microsoft Graph API error: {response.status_code} - {response.text}")
            
            return response.json() if response.content else {}
    
    async def generate_with_copilot(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = "copilot-pro",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate text using Microsoft Copilot API
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            model: Copilot model to use
            **kwargs: Additional parameters
        
        Returns:
            Generated text and metadata
        """
        access_token = self.get_access_token()
        if not access_token:
            raise Exception("No Microsoft Copilot access token available")
        
        # Call Copilot API
        # Note: Actual API endpoint and format may vary
        url = f"{self.copilot_api_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model,
            "messages": messages,
            **kwargs
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            
            if response.status_code >= 400:
                raise Exception(f"Microsoft Copilot API error: {response.status_code} - {response.text}")
            
            return response.json()
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test Microsoft Copilot connection
        
        Returns:
            Connection status and details
        """
        access_token = self.get_access_token()
        
        if not access_token:
            return {
                "success": False,
                "error": "No access token available. Please configure Microsoft Copilot API key in admin portal."
            }
        
        # Try a simple Graph API call to test connection
        try:
            import asyncio
            result = asyncio.run(self.call_graph_api("/me"))
            return {
                "success": True,
                "message": "Microsoft Copilot connection successful",
                "graph_api_accessible": True
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "graph_api_accessible": False
            }

