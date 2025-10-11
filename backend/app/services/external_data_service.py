#!/usr/bin/env python3
"""
External data service for Companies House and Google Maps integration
"""

import requests
import json
from typing import Dict, Optional, Any
from app.core.config import settings


class ExternalDataService:
    """Service for fetching data from external APIs"""
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.companies_house_api_key = settings.COMPANIES_HOUSE_API_KEY
        self.google_maps_api_key = settings.GOOGLE_MAPS_API_KEY
    
    def get_companies_house_data(self, company_name: str) -> Dict[str, Any]:
        """Fetch company data from Companies House API"""
        if not self.companies_house_api_key:
            return {'success': False, 'error': 'Companies House API key not configured'}
        
        try:
            url = f"{settings.COMPANIES_HOUSE_BASE_URL}/search/companies"
            params = {'q': company_name}
            
            response = requests.get(
                url,
                params=params,
                auth=(self.companies_house_api_key, ''),
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('items'):
                    company = data['items'][0]
                    return {
                        'success': True,
                        'data': company
                    }
            
            return {'success': False, 'error': 'Company not found'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_google_maps_data(self, company_name: str) -> Dict[str, Any]:
        """Fetch location data from Google Maps API"""
        if not self.google_maps_api_key:
            return {'success': False, 'error': 'Google Maps API key not configured'}
        
        try:
            # Use Places API Text Search
            url = "https://places.googleapis.com/v1/places:searchText"
            
            headers = {
                'X-Goog-Api-Key': self.google_maps_api_key,
                'X-Goog-FieldMask': 'places.displayName,places.formattedAddress,places.location,places.types'
            }
            
            payload = {
                'textQuery': f"{company_name} UK"
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'data': data.get('places', [])
                }
            
            return {'success': False, 'error': f'API error: {response.status_code}'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_comprehensive_company_data(self, company_name: str, website: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive company data from all sources"""
        results = {
            'success': True,
            'data': {}
        }
        
        # Get Companies House data
        ch_data = self.get_companies_house_data(company_name)
        if ch_data['success']:
            results['data']['companies_house'] = ch_data['data']
        
        # Get Google Maps data
        gm_data = self.get_google_maps_data(company_name)
        if gm_data['success']:
            results['data']['google_maps'] = gm_data['data']
        
        return results



