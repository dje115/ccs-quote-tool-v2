#!/usr/bin/env python3
"""
Google Maps API Service for location data and company search
"""

import httpx
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.core.config import settings


class GoogleMapsService:
    """Service for Google Maps API integration"""
    
    def __init__(self):
        self.base_url = settings.GOOGLE_MAPS_BASE_URL
        self.api_key = settings.GOOGLE_MAPS_API_KEY
        self.timeout = 30.0
    
    async def search_company_locations(self, company_name: str) -> Dict[str, Any]:
        """Search for company locations using Google Maps"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Use Text Search API to find company locations
                search_response = await client.get(
                    f"{self.base_url}/place/textsearch/json",
                    params={
                        "query": company_name,
                        "key": self.api_key,
                        "type": "establishment"
                    }
                )
                search_response.raise_for_status()
                search_data = search_response.json()
                
                locations = []
                if search_data.get("results"):
                    for result in search_data["results"][:5]:  # Limit to 5 results
                        location_detail = await self._get_place_details(result["place_id"], client)
                        locations.append(location_detail)
                
                return {
                    "company_name": company_name,
                    "total_results": search_data.get("total_results", 0),
                    "locations": locations,
                    "searched_at": datetime.utcnow().isoformat()
                }
                
        except httpx.HTTPStatusError as e:
            return {"error": f"Google Maps API error: {e.response.status_code} - {e.response.text}"}
        except Exception as e:
            return {"error": f"Error searching company locations: {str(e)}"}
    
    async def _get_place_details(self, place_id: str, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Get detailed information about a place"""
        try:
            response = await client.get(
                f"{self.base_url}/place/details/json",
                params={
                    "place_id": place_id,
                    "key": self.api_key,
                    "fields": "name,formatted_address,geometry,formatted_phone_number,website,rating,user_ratings_total,business_status,types,opening_hours"
                }
            )
            response.raise_for_status()
            details_data = response.json()
            
            if details_data.get("result"):
                result = details_data["result"]
                return {
                    "place_id": place_id,
                    "name": result.get("name"),
                    "formatted_address": result.get("formatted_address"),
                    "geometry": result.get("geometry"),
                    "phone_number": result.get("formatted_phone_number"),
                    "website": result.get("website"),
                    "rating": result.get("rating"),
                    "user_ratings_total": result.get("user_ratings_total"),
                    "business_status": result.get("business_status"),
                    "types": result.get("types", []),
                    "opening_hours": result.get("opening_hours")
                }
            
            return {"place_id": place_id, "error": "No details found"}
            
        except Exception as e:
            return {"place_id": place_id, "error": str(e)}
    
    async def geocode_address(self, address: str) -> Dict[str, Any]:
        """Geocode an address to get coordinates"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/geocode/json",
                    params={
                        "address": address,
                        "key": self.api_key
                    }
                )
                response.raise_for_status()
                geocode_data = response.json()
                
                if geocode_data.get("results"):
                    result = geocode_data["results"][0]
                    return {
                        "address": address,
                        "formatted_address": result.get("formatted_address"),
                        "geometry": result.get("geometry"),
                        "place_id": result.get("place_id"),
                        "types": result.get("types", [])
                    }
                
                return {"address": address, "error": "No results found"}
                
        except Exception as e:
            return {"address": address, "error": str(e)}
    
    async def reverse_geocode(self, lat: float, lng: float) -> Dict[str, Any]:
        """Reverse geocode coordinates to get address"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/geocode/json",
                    params={
                        "latlng": f"{lat},{lng}",
                        "key": self.api_key
                    }
                )
                response.raise_for_status()
                geocode_data = response.json()
                
                if geocode_data.get("results"):
                    result = geocode_data["results"][0]
                    return {
                        "coordinates": {"lat": lat, "lng": lng},
                        "formatted_address": result.get("formatted_address"),
                        "place_id": result.get("place_id"),
                        "types": result.get("types", [])
                    }
                
                return {"coordinates": {"lat": lat, "lng": lng}, "error": "No results found"}
                
        except Exception as e:
            return {"coordinates": {"lat": lat, "lng": lng}, "error": str(e)}
    
    async def search_nearby_places(self, lat: float, lng: float, radius: int = 1000, keyword: str = None) -> Dict[str, Any]:
        """Search for places near a location"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {
                    "location": f"{lat},{lng}",
                    "radius": radius,
                    "key": self.api_key
                }
                
                if keyword:
                    params["keyword"] = keyword
                
                response = await client.get(
                    f"{self.base_url}/place/nearbysearch/json",
                    params=params
                )
                response.raise_for_status()
                nearby_data = response.json()
                
                places = []
                if nearby_data.get("results"):
                    for result in nearby_data["results"]:
                        places.append({
                            "name": result.get("name"),
                            "place_id": result.get("place_id"),
                            "geometry": result.get("geometry"),
                            "rating": result.get("rating"),
                            "types": result.get("types", []),
                            "vicinity": result.get("vicinity")
                        })
                
                return {
                    "location": {"lat": lat, "lng": lng},
                    "radius": radius,
                    "keyword": keyword,
                    "places": places,
                    "status": nearby_data.get("status")
                }
                
        except Exception as e:
            return {"error": f"Error searching nearby places: {str(e)}"}
    
    async def get_place_photos(self, place_id: str, max_photos: int = 5) -> List[Dict[str, Any]]:
        """Get photos for a place"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # First get place details to get photo references
                details_response = await client.get(
                    f"{self.base_url}/place/details/json",
                    params={
                        "place_id": place_id,
                        "key": self.api_key,
                        "fields": "photos"
                    }
                )
                details_response.raise_for_status()
                details_data = details_response.json()
                
                photos = []
                if details_data.get("result", {}).get("photos"):
                    photo_refs = details_data["result"]["photos"][:max_photos]
                    
                    for photo_ref in photo_refs:
                        photo_url = f"{self.base_url}/place/photo"
                        params = {
                            "photoreference": photo_ref["photo_reference"],
                            "maxwidth": 400,
                            "key": self.api_key
                        }
                        
                        photos.append({
                            "photo_reference": photo_ref["photo_reference"],
                            "photo_url": f"{photo_url}?photoreference={photo_ref['photo_reference']}&maxwidth=400&key={self.api_key}",
                            "width": photo_ref.get("width"),
                            "height": photo_ref.get("height")
                        })
                
                return photos
                
        except Exception as e:
            print(f"Error getting place photos: {e}")
            return []
    
    async def calculate_distance(self, origin: str, destination: str) -> Dict[str, Any]:
        """Calculate distance between two locations"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/distancematrix/json",
                    params={
                        "origins": origin,
                        "destinations": destination,
                        "key": self.api_key,
                        "units": "metric"
                    }
                )
                response.raise_for_status()
                distance_data = response.json()
                
                if distance_data.get("rows") and distance_data["rows"][0].get("elements"):
                    element = distance_data["rows"][0]["elements"][0]
                    return {
                        "origin": origin,
                        "destination": destination,
                        "distance": element.get("distance", {}),
                        "duration": element.get("duration", {}),
                        "status": element.get("status")
                    }
                
                return {"error": "No distance data found"}
                
        except Exception as e:
            return {"error": f"Error calculating distance: {str(e)}"}
