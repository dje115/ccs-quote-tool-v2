"""
Planning Application Service
Handles fetching planning application data from UK planning portals and AI analysis
"""

import json
import httpx
import asyncio
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.models import Tenant, PlanningApplication, PlanningApplicationCampaign, PlanningApplicationKeyword, ApplicationType, PlanningApplicationStatus, PlanningCampaignStatus, Lead, LeadSource, LeadStatus
from app.services.ai_analysis_service import AIAnalysisService
from app.services.ai_provider_service import AIProviderService
from app.core.config import settings


class PlanningApplicationService:
    """Service for managing planning application data and campaigns"""
    
    # UK County planning portal configurations
    PLANNING_PORTALS = {
        "leicestershire": {
            "name": "Leicestershire",
            "base_url": "https://leicester.opendatasoft.com/api/records/1.0/search/",
            "dataset_id": "valid-planning-applications",
            "enabled": True
        },
        "nottinghamshire": {
            "name": "Nottinghamshire", 
            "base_url": "https://www.nottinghamshire.gov.uk/api/records/1.0/search",
            "dataset_id": "planning-applications",
            "enabled": True,
            "alternative_urls": [
                "https://nottingham.opendatasoft.com/api/records/1.0/search",
                "https://data.nottinghamshire.gov.uk/api/records/1.0/search",
                "https://open.nottinghamshire.gov.uk/api/records/1.0/search"
            ]
        },
        # Add more counties as needed
    }

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.ai_service = AIAnalysisService(tenant_id=tenant_id, db=db)
        self.provider_service = AIProviderService(db, tenant_id=tenant_id)

    async def fetch_planning_data(self, campaign: PlanningApplicationCampaign, days_back: int = None) -> List[Dict[str, Any]]:
        """Fetch planning application data from the specified portal"""
        days_back = days_back or campaign.days_to_monitor
        
        if campaign.county.lower() not in self.PLANNING_PORTALS:
            raise ValueError(f"Unsupported county: {campaign.county}")
        
        portal_config = self.PLANNING_PORTALS[campaign.county.lower()]
        
        if not portal_config["enabled"]:
            raise ValueError(f"Portal for {campaign.county} is not enabled")
        
        return await self._fetch_from_portal(portal_config, campaign, days_back)

    async def _fetch_from_portal(self, portal_config: Dict[str, str], campaign: PlanningApplicationCampaign, days_back: int) -> List[Dict[str, Any]]:
        """Fetch data from specific planning portal"""
        records = []
        start = 0
        max_records = campaign.max_results_per_run or 300  # Default to 300 like your working example
        
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            while len(records) < max_records:
                # Build parameters - first try without sort to see available fields
                params = {
                    "dataset": portal_config["dataset_id"],
                    "rows": min(100, max_records - len(records)),
                    "start": start
                    # Removed sort parameter temporarily - "date_validated" field not recognized
                }
                
                response = None
                try:
                    print(f"🔍 Making API request to: {portal_config['base_url']}")
                    print(f"🔍 With params: {params}")
                    
                    # Make the request - try without User-Agent first, like your working example
                    response = await client.get(portal_config["base_url"], params=params)
                    print(f"🔍 Response status: {response.status_code}")
                    
                    # Check for 404 or other error status before trying to parse JSON
                    data = None
                    if response.status_code == 404:
                        print(f"❌ Got 404 - API endpoint doesn't exist on {portal_config['base_url']}")
                        # Try alternative URLs if this is the first batch
                        if start == 0 and portal_config.get("alternative_urls"):
                            alternative_urls = portal_config.get("alternative_urls", [])
                            print(f"🔄 Trying alternative URLs for {portal_config['name']}...")
                            for alt_url in alternative_urls:
                                try:
                                    print(f"🔄 Trying alternative URL: {alt_url}")
                                    alt_response = await client.get(alt_url, params=params)
                                    print(f"🔄 Alternative URL status: {alt_response.status_code}")
                                    if alt_response.status_code == 200:
                                        alt_response.raise_for_status()
                                        alt_data = alt_response.json()
                                        # Update the portal config to use the working URL
                                        portal_config["base_url"] = alt_url
                                        print(f"✅ Updated {portal_config['name']} to use: {alt_url}")
                                        response = alt_response
                                        data = alt_data
                                        break
                                    else:
                                        print(f"❌ Alternative URL also failed with status: {alt_response.status_code}")
                                except Exception as alt_error:
                                    print(f"❌ Alternative URL failed: {alt_url} - {str(alt_error)}")
                                    continue
                        else:
                            print(f"❌ 404 error and no alternative URLs or not first batch - stopping")
                    else:
                        response.raise_for_status()
                        data = response.json()
                    
                    # Only proceed if we have valid data
                    if data is None:
                        print(f"❌ Could not get valid data from any API endpoint")
                        break
                    
                    # Debug logging to see what we're getting
                    print(f"🔍 API response keys: {list(data.keys())}")
                    print(f"🔍 Total records in response: {data.get('nhits', 'unknown')}")
                    
                    batch = data.get("records", [])
                    print(f"🔍 Batch size: {len(batch)}")
                    if not batch:
                        break
                    
                    # Process batch
                    if batch and len(batch) > 0:
                        # Debug: show structure of first record
                        first_record = batch[0]
                        print(f"🔍 First record keys: {list(first_record.keys())}")
                        if "fields" in first_record:
                            print(f"🔍 First record fields keys: {list(first_record['fields'].keys())}")
                            # Check for date fields
                            date_fields = [k for k in first_record['fields'].keys() if 'date' in k.lower()]
                            print(f"🔍 Date-related fields: {date_fields}")
                    
                    processed_count = 0
                    for record in batch:
                        processed = self._process_portal_record(record, campaign.county, portal_config["name"])
                        if processed:
                            records.append(processed)
                            processed_count += 1
                    
                    print(f"🔍 Processed {processed_count}/{len(batch)} records successfully")
                    
                    if len(batch) < 100:
                        break
                    start += 100
                    
                except Exception as e:
                    error_msg = str(e)
                    print(f"❌ Error fetching from portal: {error_msg}")
                    
                    # Check if this is a 404 error by examining response if available
                    is_http_error = False
                    if response is not None:
                        print(f"❌ Response status from failed request: {response.status_code}")
                        if response.status_code == 404:
                            print(f"❌ Got 404 - endpoint doesn't exist")
                            is_http_error = True
                            try:
                                response_text = response.text
                                if "page doesn't exist" in response_text.lower():
                                    print(f"❌ Confirmed: API endpoint doesn't exist (404 HTML page returned)")
                                else:
                                    print(f"❌ Response body sample: {response_text[:200]}...")
                            except:
                                pass
                    
                    # Try alternative URLs for Nottinghamshire if primary fails
                    success_with_alt = False
                    if (("Name or service not known" in error_msg or "[Errno -2]" in error_msg or is_http_error) and start == 0):
                        alternative_urls = portal_config.get("alternative_urls", [])
                        if alternative_urls:
                            print(f"🔄 Trying alternative URLs for {portal_config['name']}...")
                            for alt_url in alternative_urls:
                                try:
                                    print(f"🔄 Trying alternative URL: {alt_url}")
                                    response = await client.get(alt_url, params=params)
                                    print(f"✅ Alternative URL success: {response.status_code}")
                                    response.raise_for_status()
                                    data = response.json()
                                    
                                    # Update the portal config to use the working URL
                                    portal_config["base_url"] = alt_url
                                    print(f"✅ Updated {portal_config['name']} to use: {alt_url}")
                                    
                                    # Process the successful response (continue normal flow)
                                    batch = data.get("records", [])
                                    print(f"🔍 Batch size from alternative URL: {len(batch)}")
                                    if not batch:
                                        break
                                    
                                    # Process batch (same logic as main success path)
                                    processed_count = 0
                                    for record in batch:
                                        processed = self._process_portal_record(record, campaign.county, portal_config["name"])
                                        if processed:
                                            records.append(processed)
                                            processed_count += 1
                                    
                                    print(f"🔍 Processed {processed_count}/{len(batch)} records successfully from alternative URL")
                                    
                                    if len(batch) < 100:
                                        break
                                    start += 100
                                    success_with_alt = True
                                    break  # Exit the alternative URL loop
                                    
                                except Exception as alt_error:
                                    print(f"❌ Alternative URL failed: {alt_url} - {str(alt_error)}")
                                    continue
                            
                            if not success_with_alt:
                                print(f"❌ All alternative URLs failed for {portal_config['name']}")
                                break
                        else:
                            print(f"❌ DNS resolution failed for {portal_config['base_url']}")
                            print(f"❌ This could be a temporary network issue or the API endpoint may have changed")
                            break
                    else:
                        # Other types of errors
                        if "timeout" in error_msg.lower():
                            print(f"❌ Request timed out - the API may be slow or unavailable")
                        
                        try:
                            if response is not None:
                                error_text = await response.aread()
                                print(f"❌ Error response body: {error_text.decode('utf-8', errors='ignore')}")
                        except Exception as text_error:
                            print(f"❌ Could not read error response: {text_error}")
                        
                        if not success_with_alt:
                            break
        
        # Filter by date
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        filtered_records = []
        
        print(f"🔍 Filtering {len(records)} records by date (cutoff: {cutoff_date})")
        
        for record in records:
            if record.get("date_validated"):
                try:
                    if isinstance(record["date_validated"], str):
                        parsed_date = datetime.fromisoformat(record["date_validated"].replace('Z', '+00:00'))
                    else:
                        parsed_date = record["date_validated"]
                    
                    if parsed_date >= cutoff_date:
                        filtered_records.append(record)
                except Exception as e:
                    print(f"⚠️ Error parsing date {record.get('date_validated')}: {e}")
                    continue
            else:
                print(f"🔍 Record missing date_validated field: {record.keys()}")
        
        print(f"🔍 After date filtering: {len(filtered_records)} records remain")
        return filtered_records

    def _process_portal_record(self, record: Dict[str, Any], county: str, portal_name: str) -> Optional[Dict[str, Any]]:
        """Process a single record from the planning portal"""
        try:
            fields = record.get("fields", {})
            
            # Extract geo coordinates
            geo_point = fields.get("geo_point_2d")
            lat, lon = None, None
            if geo_point and isinstance(geo_point, list) and len(geo_point) >= 2:
                lat, lon = geo_point[0], geo_point[1]
            
            # Map field names - different portals use different field names
            processed = {
                "reference": fields.get("application_number") or fields.get("reference") or fields.get("app_ref"),
                "address": fields.get("location") or fields.get("address") or fields.get("site_address"),
                "proposal": fields.get("proposal") or fields.get("description") or fields.get("development_description") or "",
                # Try multiple possible date fields across different portals
                "date_validated": fields.get("date_validated") or fields.get("date_received") or fields.get("date_submitted") or fields.get("validated_date"),
                "status": fields.get("status", "validated"),
                "latitude": lat,
                "longitude": lon,
                "postcode": self._extract_postcode(fields.get("location", "") or fields.get("address", "")),
                "county": county,
                "source_portal": f"{portal_name.lower()}_opendatasoft"
            }
            
            # If no date_validated in fields, try to use record_timestamp
            if not processed["date_validated"] and "record_timestamp" in record:
                processed["date_validated"] = record["record_timestamp"]
            
            # Only return if we have essential data - adjust for Leicester field names
            if processed["reference"] and processed["address"]:
                # Debug: show what we got for the first few records
                if len(processed) > 0:  # This is always true, let's check something else
                    pass
                return processed
            else:
                # Debug: why was this record rejected?
                if len(fields) > 0:  # Only log for first few failures to avoid spam
                    print(f"🔍 Record rejected - reference: '{processed['reference']}', address: '{processed['address']}'")
                
        except Exception as e:
            print(f"⚠️ Error processing record: {e}")
        
        return None

    def _extract_postcode(self, address: str) -> Optional[str]:
        """Extract UK postcode from address string"""
        if not address:
            return None
        
        # UK postcode pattern
        postcode_pattern = r'\b[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}\b'
        match = re.search(postcode_pattern, address.upper())
        return match.group() if match else None

    def classify_application(self, proposal: str, tenant_id: str = None) -> Tuple[str, int]:
        """Classify application type and calculate relevance score for tenant"""
        if not proposal:
            return "other", 0
        
        proposal_lower = proposal.lower()
        
        # Get tenant-specific keywords
        keywords = self._get_tenant_keywords(tenant_id or self.tenant_id)
        
        # Classification logic
        if any(kw in proposal_lower for kw in ["residential", "dwelling", "flat", "apartment", "house"]):
            base_type = "residential"
        elif any(kw in proposal_lower for kw in ["industrial", "warehouse", "factory", "manufacturing"]):
            base_type = "industrial"
        elif any(kw in proposal_lower for kw in ["office", "retail", "commercial"]):
            base_type = "commercial"
        elif "change of use" in proposal_lower:
            base_type = "change_of_use"
        else:
            base_type = "other"
        
        # Calculate relevance score based on tenant keywords
        score = 0
        for keyword in keywords.get("include", []):
            if keyword["keyword"].lower() in proposal_lower:
                score += keyword.get("weight", 10)
        
        # Deduct for excluded keywords
        for keyword in keywords.get("exclude", []):
            if keyword["keyword"].lower() in proposal_lower:
                score -= keyword.get("weight", 10)
        
        return base_type, max(0, min(100, score))

    def _get_tenant_keywords(self, tenant_id: str) -> Dict[str, List[Dict]]:
        """Get tenant-specific keywords for classification"""
        keywords = self.db.query(PlanningApplicationKeyword).filter(
            PlanningApplicationKeyword.tenant_id == tenant_id,
            PlanningApplicationKeyword.is_active == True
        ).all()
        
        result = {"include": [], "exclude": []}
        for kw in keywords:
            result[kw.keyword_type].append({
                "keyword": kw.keyword,
                "weight": kw.weight,
                "category": kw.category
            })
        
        return result

    async def analyze_applications_with_ai(self, applications: List[Dict[str, Any]], tenant_id: str, max_analysis: int = 20) -> List[Dict[str, Any]]:
        """Analyze planning applications using AI"""
        print(f"🔍 analyze_applications_with_ai called with {len(applications)} applications")
        
        if not applications:
            print(f"⚠️ Skipping AI analysis - no applications")
            return applications
        
        # Sort by relevance score and take top N
        sorted_apps = sorted(applications, key=lambda x: x.get("relevance_score", 0), reverse=True)
        apps_to_analyze = sorted_apps[:max_analysis]
        
        if not apps_to_analyze:
            return applications
        
        # Get tenant context for AI analysis
        tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
        tenant_context = self._get_tenant_context(tenant)
        
        try:
            # Prepare prompt for AI analysis
            prompt = self._build_ai_analysis_prompt(apps_to_analyze, tenant_context)
            print(f"🤖 Calling AI provider with {len(apps_to_analyze)} applications...")
            
            # Use AIProviderService
            provider_response = await self.provider_service.generate_with_rendered_prompts(
                prompt=None,
                system_prompt="You are an expert at analyzing planning applications and matching them to business opportunities. Always return valid JSON arrays.",
                user_prompt=prompt,
                temperature=0.4,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            print(f"✅ AI provider response received")
            ai_results = json.loads(provider_response.content.strip())
            print(f"✅ Parsed {len(ai_results)} AI analysis results")
            
            # Apply AI results to applications
            for i, result in enumerate(ai_results):
                if i < len(apps_to_analyze):
                    apps_to_analyze[i].update({
                        "ai_summary": result.get("summary", ""),
                        "why_fit": result.get("why_fit", ""),
                        "suggested_sales_approach": result.get("suggested_sales_approach", "")
                    })
        
        except Exception as e:
            print(f"⚠️ Error in AI analysis: {e}")
            import traceback
            traceback.print_exc()
        
        return applications

    def _get_tenant_context(self, tenant: Tenant) -> str:
        """Get tenant context for AI analysis"""
        context_parts = []
        
        if tenant.company_description:
            context_parts.append(f"Company: {tenant.company_description}")
        
        if tenant.products_services:
            context_parts.append(f"Services: {', '.join(tenant.products_services)}")
        
        if tenant.target_markets:
            context_parts.append(f"Target markets: {', '.join(tenant.target_markets)}")
        
        return "\n".join(context_parts) if context_parts else "General business services company"

    def _build_ai_analysis_prompt(self, applications: List[Dict[str, Any]], tenant_context: str) -> str:
        """Build AI analysis prompt for planning applications"""
        return f"""
You are a UK business development analyst helping to identify sales opportunities from planning applications.

Tenant Context:
{tenant_context}

For each planning application below, provide a JSON array with these fields:
- summary: A short description of the project (1-2 sentences)
- why_fit: Why this project might need the tenant's services
- suggested_sales_approach: A brief sales approach recommendation (1-2 sentences)

Applications to analyze:
{json.dumps([{
    "reference": app.get("reference"),
    "address": app.get("address"),
    "proposal": app.get("proposal", "")[:500],  # Truncate for token limits
    "relevance_score": app.get("relevance_score", 0)
} for app in applications], indent=2)}

Return only a valid JSON array with the analysis for each application.
"""

    async def run_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Run a planning application campaign"""
        campaign = self.db.query(PlanningApplicationCampaign).filter(
            PlanningApplicationCampaign.id == campaign_id,
            PlanningApplicationCampaign.tenant_id == self.tenant_id
        ).first()
        
        if not campaign:
            raise ValueError("Campaign not found")
        
        try:
            # Update campaign status
            campaign.status = PlanningCampaignStatus.ACTIVE
            campaign.last_run_at = datetime.now(timezone.utc)
            self.db.commit()
            
            # Fetch planning data
            print(f"🔍 Fetching planning data for {campaign.county}...")
            raw_applications = await self.fetch_planning_data(campaign)
            print(f"🔍 Raw applications fetched: {len(raw_applications)}")
            
            # Filter applications based on campaign settings
            filtered_apps = self._filter_applications(raw_applications, campaign)
            print(f"🔍 Applications after filtering: {len(filtered_apps)}")
            
            # Classify and score applications
            for app in filtered_apps:
                app_type, score = self.classify_application(app.get("proposal", ""), self.tenant_id)
                app["application_type"] = app_type
                app["relevance_score"] = score
                app["tenant_classification"] = app_type
            
            # AI Analysis if enabled
            print(f"🔍 Campaign AI analysis enabled: {campaign.enable_ai_analysis}")
            print(f"🔍 Filtered applications count: {len(filtered_apps)}")
            if campaign.enable_ai_analysis and filtered_apps:
                print(f"🤖 Running AI analysis on {len(filtered_apps)} applications...")
                filtered_apps = await self.analyze_applications_with_ai(
                    filtered_apps, 
                    self.tenant_id, 
                    campaign.max_ai_analysis_per_run
                )
            else:
                print(f"⚠️ AI analysis skipped - enabled: {campaign.enable_ai_analysis}, apps: {len(filtered_apps)}")
            
            # Store applications in database
            new_applications = await self._store_applications(filtered_apps, campaign)
            
            # Update campaign statistics
            campaign.total_applications_found = len(filtered_apps)
            campaign.new_applications_this_run = len(new_applications)
            campaign.ai_analysis_completed = len([app for app in filtered_apps if app.get("ai_summary")])
            campaign.consecutive_failures = 0
            campaign.last_error = None
            
            # Set next run time if scheduled
            if campaign.is_scheduled:
                campaign.next_run_at = datetime.now(timezone.utc) + timedelta(days=campaign.schedule_frequency_days)
            
            self.db.commit()
            
            return {
                "total_found": len(filtered_apps),
                "new_applications": len(new_applications),
                "ai_analyzed": campaign.ai_analysis_completed
            }
            
        except Exception as e:
            print(f"❌ Campaign run failed: {e}")
            campaign.consecutive_failures += 1
            campaign.last_error = str(e)
            self.db.commit()
            raise

    def _filter_applications(self, applications: List[Dict[str, Any]], campaign: PlanningApplicationCampaign) -> List[Dict[str, Any]]:
        """Filter applications based on campaign settings"""
        filtered = []
        
        for app in applications:
            proposal = app.get("proposal", "").lower()
            
            # Check application type filters
            if not campaign.include_residential and "residential" in proposal:
                continue
            if not campaign.include_commercial and "commercial" in proposal:
                continue
            if not campaign.include_industrial and "industrial" in proposal:
                continue
            if not campaign.include_change_of_use and "change of use" in proposal:
                continue
            
            # Check keyword filters
            if campaign.exclude_keywords:
                if any(kw.lower() in proposal for kw in campaign.exclude_keywords):
                    continue
            
            filtered.append(app)
        
        return filtered

    async def _store_applications(self, applications: List[Dict[str, Any]], campaign: PlanningApplicationCampaign) -> List[PlanningApplication]:
        """Store applications in database, avoiding duplicates"""
        new_applications = []
        
        for app_data in applications:
            # Check if application already exists
            existing = self.db.query(PlanningApplication).filter(
                PlanningApplication.reference == app_data["reference"],
                PlanningApplication.tenant_id == self.tenant_id
            ).first()
            
            if existing:
                continue  # Skip duplicates
            
            # Create new planning application record
            planning_app = PlanningApplication(
                tenant_id=self.tenant_id,  # Explicitly set tenant_id
                reference=app_data["reference"],
                address=app_data["address"],
                proposal=app_data["proposal"],
                application_type=ApplicationType(app_data.get("application_type", "other")),
                status=PlanningApplicationStatus.VALIDATED,  # Default status
                date_validated=self._parse_date(app_data.get("date_validated")),
                latitude=app_data.get("latitude"),
                longitude=app_data.get("longitude"),
                postcode=app_data.get("postcode"),
                county=app_data["county"],
                source_portal=app_data["source_portal"],
                tenant_classification=app_data.get("tenant_classification"),
                relevance_score=app_data.get("relevance_score"),
                ai_summary=app_data.get("ai_summary"),
                why_fit=app_data.get("why_fit"),
                suggested_sales_approach=app_data.get("suggested_sales_approach")
            )
            
            # Store AI analysis as JSON
            if any(app_data.get(key) for key in ["ai_summary", "why_fit", "suggested_sales_approach"]):
                planning_app.ai_analysis = {
                    "summary": app_data.get("ai_summary"),
                    "why_fit": app_data.get("why_fit"),
                    "suggested_sales_approach": app_data.get("suggested_sales_approach"),
                    "analysis_date": datetime.now(timezone.utc).isoformat()
                }
            
            self.db.add(planning_app)
            new_applications.append(planning_app)
        
        self.db.commit()
        return new_applications

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if not date_str:
            return None
        
        try:
            if isinstance(date_str, str):
                # Try ISO format first
                if 'T' in date_str or 'Z' in date_str:
                    return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                else:
                    # Try other formats
                    for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"]:
                        try:
                            return datetime.strptime(date_str[:10], fmt).replace(tzinfo=timezone.utc)
                        except ValueError:
                            continue
            return None
        except Exception:
            return None

    def get_available_counties(self) -> List[Dict[str, str]]:
        """Get list of available UK counties for planning monitoring"""
        return [
            {
                "code": code,
                "name": config["name"],
                "enabled": config["enabled"]
            }
            for code, config in self.PLANNING_PORTALS.items()
        ]
