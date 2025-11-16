#!/usr/bin/env python3
"""
Building Analysis Service
AI-powered building analysis with Google Maps integration
Migrated from v1
"""

import json
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import httpx

from app.models.ai_prompt import PromptCategory
from app.models.tenant import Tenant
from app.services.ai_prompt_service import AIPromptService
from app.services.ai_provider_service import AIProviderService
from app.services.google_maps_service import GoogleMapsService
from app.core.api_keys import get_api_keys


class BuildingAnalysisService:
    """Service for AI-powered building analysis"""
    
    def __init__(self, db: Session, tenant_id: str, openai_api_key: Optional[str] = None):
        self.db = db
        self.tenant_id = tenant_id
        self.provider_service = AIProviderService(db, tenant_id=tenant_id)
    
    async def analyze_building(
        self,
        address: str,
        building_type: Optional[str] = None,
        building_size: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Analyze building for cabling requirements
        
        Args:
            address: Building address
            building_type: Optional building type
            building_size: Optional building size in sqm
        
        Returns:
            Building analysis with recommendations
        """
        try:
            # Get building info from Google Maps if API key available
            building_info = None
            tenant = self.db.query(Tenant).filter(Tenant.id == self.tenant_id).first()
            if tenant:
                api_keys = get_api_keys(self.db, tenant)
                if api_keys.google_maps:
                    maps_service = GoogleMapsService(api_key=api_keys.google_maps)
                    building_info = await maps_service.get_place_details(address)
                    
                    # Estimate building size if not provided
                    if not building_size and building_info:
                        building_size = self._estimate_building_size(building_info)
            
            # Get prompt from database
            prompt_service = AIPromptService(self.db, tenant_id=self.tenant_id)
            prompt_obj = await prompt_service.get_prompt(
                category=PromptCategory.BUILDING_ANALYSIS.value,
                tenant_id=self.tenant_id
            )
            
            if not prompt_obj:
                # Fallback analysis
                return {
                    "address": address,
                    "building_type": building_type or "Unknown",
                    "building_size": building_size,
                    "cable_routing": "Standard cable routing recommended",
                    "equipment_placement": "Central location recommended",
                    "power_requirements": "Standard power requirements",
                    "access_considerations": "Standard access",
                    "complexity": "Medium",
                    "special_considerations": []
                }
            
            # Build analysis context
            analysis_context = {
                "address": address,
                "building_type": building_type or (building_info.get('types', [])[0] if building_info else "Unknown"),
                "building_size": str(building_size) if building_size else "Unknown"
            }
            
            # Render prompt
            rendered = prompt_service.render_prompt(prompt_obj, analysis_context)
            
            # Use AIProviderService
            provider_response = await self.provider_service.generate(
                prompt=prompt_obj,
                variables=analysis_context
            )
            
            response_text = provider_response.content
            
            # Parse JSON response
            try:
                if response_text.strip().startswith('{'):
                    analysis = json.loads(response_text)
                    # Add building info if available
                    if building_info:
                        analysis['google_maps_info'] = {
                            'name': building_info.get('name'),
                            'formatted_address': building_info.get('formatted_address'),
                            'types': building_info.get('types', []),
                            'coordinates': building_info.get('geometry', {}).get('location')
                        }
                    return analysis
            except json.JSONDecodeError:
                pass
            
            # Fallback response
            return {
                "address": address,
                "building_type": building_type or "Unknown",
                "building_size": building_size,
                "analysis": response_text,
                "cable_routing": "Standard routing",
                "equipment_placement": "Central location",
                "power_requirements": "Standard",
                "access_considerations": "Standard access",
                "complexity": "Medium"
            }
            
        except Exception as e:
            print(f"[BUILDING ANALYSIS] Error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "error": str(e),
                "address": address
            }
    
    def _estimate_building_size(self, place_info: Dict[str, Any]) -> float:
        """Estimate building size based on place type"""
        types = place_info.get('types', [])
        
        # Default size estimates based on building type
        size_estimates = {
            'residential': 150,  # Average house
            'commercial': 500,   # Small office
            'retail': 300,       # Small shop
            'industrial': 1000,  # Warehouse
            'educational': 800,  # School building
            'health': 600,       # Medical building
        }
        
        for place_type in types:
            if place_type in size_estimates:
                return size_estimates[place_type]
        
        # Default for unknown types
        return 200


