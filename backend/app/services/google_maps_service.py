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
    
    def __init__(self, api_key: Optional[str] = None):
        self.base_url = settings.GOOGLE_MAPS_BASE_URL
        self.api_key = api_key or settings.GOOGLE_MAPS_API_KEY
        self.timeout = 30.0
    
    async def search_company_locations(self, company_name: str) -> Dict[str, Any]:
        """
        Search for company locations using comprehensive multi-query strategy (v1 approach)
        Searches across 100+ UK regions and counties to find ALL company locations
        """
        try:
            # Build comprehensive search query list (matching v1)
            search_queries = [company_name]
            
            # Add search variations
            if ' ' in company_name:
                variations = [
                    f'"{company_name}"',  # Exact phrase search
                    f"{company_name} UK",  # UK-specific
                    f"{company_name} office",
                    f"{company_name} branch",
                    f"{company_name} location"
                ]
                search_queries.extend(variations)
            
            # Add comprehensive UK regional searches (matching v1)
            uk_searches = [
                # England Regions
                f"{company_name} South East England",
                f"{company_name} South West England",
                f"{company_name} London",
                f"{company_name} East Midlands",
                f"{company_name} West Midlands",
                f"{company_name} Yorkshire",
                f"{company_name} North West England",
                f"{company_name} North East England",
                f"{company_name} East of England",
                # Scotland
                f"{company_name} Scotland",
                f"{company_name} Central Scotland",
                f"{company_name} Highlands Scotland",
                # Wales
                f"{company_name} Wales",
                f"{company_name} South Wales",
                f"{company_name} North Wales",
                # Northern Ireland
                f"{company_name} Northern Ireland",
                f"{company_name} Belfast",
                # Major UK Counties
                f"{company_name} Dorset",
                f"{company_name} Hampshire",
                f"{company_name} Kent",
                f"{company_name} Surrey",
                f"{company_name} Sussex",
                f"{company_name} Berkshire",
                f"{company_name} Oxfordshire",
                f"{company_name} Buckinghamshire",
                f"{company_name} Essex",
                f"{company_name} Hertfordshire",
                f"{company_name} Cambridgeshire",
                f"{company_name} Norfolk",
                f"{company_name} Suffolk",
                f"{company_name} Leicestershire",
                f"{company_name} Derbyshire",
                f"{company_name} Nottinghamshire",
                f"{company_name} Staffordshire",
                f"{company_name} Warwickshire",
                f"{company_name} Worcestershire",
                f"{company_name} West Yorkshire",
                f"{company_name} South Yorkshire",
                f"{company_name} North Yorkshire",
                f"{company_name} Lancashire",
                f"{company_name} Greater Manchester",
                f"{company_name} Merseyside",
                f"{company_name} Tyne and Wear",
                f"{company_name} Durham",
                f"{company_name} Northumberland",
                # Scotland Cities
                f"{company_name} Edinburgh",
                f"{company_name} Glasgow",
                f"{company_name} Aberdeen",
                f"{company_name} Dundee",
                # Wales Cities
                f"{company_name} Cardiff",
                f"{company_name} Swansea",
                f"{company_name} Newport",
            ]
            search_queries.extend(uk_searches)
            
            print(f"[GOOGLE MAPS] Searching for '{company_name}' with {len(search_queries)} queries")
            
            all_locations = []
            seen_place_ids = set()
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Execute all search queries
                for i, query in enumerate(search_queries):
                    try:
                        search_response = await client.get(
                            f"{self.base_url}/place/textsearch/json",
                            params={
                                "query": query,
                                "key": self.api_key,
                                "type": "establishment"
                            }
                        )
                        
                        if search_response.status_code == 200:
                            search_data = search_response.json()
                            
                            if search_data.get("results"):
                                print(f"[GOOGLE MAPS] Query {i+1}/{len(search_queries)}: '{query}' found {len(search_data['results'])} results")
                                
                                # Get details for each unique place
                                for result in search_data["results"]:
                                    place_id = result.get("place_id")
                                    if place_id and place_id not in seen_place_ids:
                                        seen_place_ids.add(place_id)
                                        location_detail = await self._get_place_details(place_id, client)
                                        
                                        # Only add if it matches the company name reasonably well
                                        if self._is_relevant_location(location_detail, company_name):
                                            all_locations.append(location_detail)
                        
                        # Rate limiting - small delay between requests
                        if i % 10 == 0 and i > 0:
                            import asyncio
                            await asyncio.sleep(0.5)
                            
                    except Exception as e:
                        print(f"[GOOGLE MAPS] Error with query '{query}': {e}")
                        continue
            
            print(f"[GOOGLE MAPS] Found {len(all_locations)} unique locations for '{company_name}'")
            
            return {
                "company_name": company_name,
                "total_results": len(all_locations),
                "locations": all_locations,
                "searched_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"[ERROR] Google Maps search failed: {e}")
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
    
    def _is_relevant_location(self, location: Dict[str, Any], company_name: str) -> bool:
        """Check if a location is relevant to the company (matching v1 logic)"""
        try:
            if location.get("error"):
                return False
            
            location_name = str(location.get("name", "")).lower()
            company_name_lower = company_name.lower().strip()
            
            # Remove common suffixes for comparison
            company_name_clean = company_name_lower.replace(" ltd", "").replace(" limited", "").replace(" plc", "").strip()
            
            # Check if company name is in location name
            if company_name_clean in location_name:
                return True
            
            # Check if location name is in company name (for shorter company names)
            if location_name in company_name_lower:
                return True
            
            # Check for word-by-word match (at least 2 words match)
            company_words = set(company_name_clean.split())
            location_words = set(location_name.split())
            
            # Remove very common words
            common_words = {'ltd', 'limited', 'plc', 'the', 'and', 'of', 'in', 'at', 'uk', 'ltd.'}
            company_words -= common_words
            location_words -= common_words
            
            if len(company_words) >= 2:
                matches = company_words.intersection(location_words)
                if len(matches) >= 2:
                    return True
            
            return False
            
        except Exception as e:
            print(f"[ERROR] Error checking location relevance: {e}")
            return True  # Include by default if error

