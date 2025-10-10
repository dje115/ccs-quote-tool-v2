#!/usr/bin/env python3
"""
Companies House API Service for company data retrieval
"""

import httpx
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.core.config import settings


class CompaniesHouseService:
    """Service for Companies House API integration"""
    
    def __init__(self):
        self.base_url = settings.COMPANIES_HOUSE_BASE_URL
        self.api_key = settings.COMPANIES_HOUSE_API_KEY
        self.timeout = 30.0
    
    async def get_company_profile(self, company_number: str) -> Dict[str, Any]:
        """Get comprehensive company profile"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Get basic company information
                company_response = await client.get(
                    f"{self.base_url}/company/{company_number}",
                    auth=(self.api_key, '')
                )
                company_response.raise_for_status()
                company_data = company_response.json()
                
                # Get officers/directors
                officers_data = await self._get_officers(company_number, client)
                
                # Get filing history
                filing_history = await self._get_filing_history(company_number, client)
                
                # Get financial data
                financial_data = await self._get_financial_data(company_number, client)
                
                return {
                    "company_number": company_number,
                    "company_profile": company_data,
                    "officers": officers_data,
                    "filing_history": filing_history,
                    "financial_data": financial_data,
                    "retrieved_at": datetime.utcnow().isoformat()
                }
                
        except httpx.HTTPStatusError as e:
            return {"error": f"Companies House API error: {e.response.status_code} - {e.response.text}"}
        except Exception as e:
            return {"error": f"Error retrieving company data: {str(e)}"}
    
    async def _get_officers(self, company_number: str, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        """Get company officers/directors"""
        try:
            response = await client.get(
                f"{self.base_url}/company/{company_number}/officers",
                auth=(self.api_key, '')
            )
            response.raise_for_status()
            officers_data = response.json()
            return officers_data.get("items", [])
        except Exception as e:
            print(f"Error getting officers: {e}")
            return []
    
    async def _get_filing_history(self, company_number: str, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        """Get company filing history"""
        try:
            response = await client.get(
                f"{self.base_url}/company/{company_number}/filing-history",
                auth=(self.api_key, '')
            )
            response.raise_for_status()
            filing_data = response.json()
            return filing_data.get("items", [])[:10]  # Last 10 filings
        except Exception as e:
            print(f"Error getting filing history: {e}")
            return []
    
    async def _get_financial_data(self, company_number: str, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Get financial data from latest accounts"""
        try:
            # Get accounts list
            accounts_response = await client.get(
                f"{self.base_url}/company/{company_number}/accounts",
                auth=(self.api_key, '')
            )
            accounts_response.raise_for_status()
            accounts_data = accounts_response.json()
            
            # Get the most recent accounts
            if accounts_data.get("items"):
                latest_accounts = accounts_data["items"][0]
                accounts_id = latest_accounts.get("id")
                
                if accounts_id:
                    # Get detailed accounts data
                    detailed_response = await client.get(
                        f"{self.base_url}/company/{company_number}/accounts/{accounts_id}",
                        auth=(self.api_key, '')
                    )
                    detailed_response.raise_for_status()
                    return detailed_response.json()
            
            return {}
            
        except Exception as e:
            print(f"Error getting financial data: {e}")
            return {}
    
    async def search_companies(self, query: str, items_per_page: int = 20) -> Dict[str, Any]:
        """Search for companies by name"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/search/companies",
                    params={"q": query, "items_per_page": items_per_page},
                    auth=(self.api_key, '')
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            return {"error": f"Companies House search error: {e.response.status_code} - {e.response.text}"}
        except Exception as e:
            return {"error": f"Error searching companies: {str(e)}"}
    
    async def get_financial_data(self, company_number: str) -> Dict[str, Any]:
        """Get comprehensive financial data for analysis"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Get accounts overview
                accounts_response = await client.get(
                    f"{self.base_url}/company/{company_number}/accounts",
                    auth=(self.api_key, '')
                )
                accounts_response.raise_for_status()
                accounts_data = accounts_response.json()
                
                financial_summary = {
                    "accounts_available": bool(accounts_data.get("items")),
                    "total_count": accounts_data.get("total_count", 0),
                    "latest_accounts": None,
                    "financial_metrics": {}
                }
                
                if accounts_data.get("items"):
                    latest_accounts = accounts_data["items"][0]
                    financial_summary["latest_accounts"] = {
                        "period_end_on": latest_accounts.get("period_end_on"),
                        "period_start_on": latest_accounts.get("period_start_on"),
                        "accounts_category": latest_accounts.get("accounts_category"),
                        "accounts_status": latest_accounts.get("accounts_status"),
                        "accounts_type": latest_accounts.get("accounts_type")
                    }
                    
                    # Try to get detailed financial data
                    accounts_id = latest_accounts.get("id")
                    if accounts_id:
                        try:
                            detailed_response = await client.get(
                                f"{self.base_url}/company/{company_number}/accounts/{accounts_id}",
                                auth=(self.api_key, '')
                            )
                            detailed_response.raise_for_status()
                            detailed_data = detailed_response.json()
                            
                            # Extract key financial metrics
                            financial_summary["financial_metrics"] = self._extract_financial_metrics(detailed_data)
                            
                        except Exception as e:
                            print(f"Error getting detailed accounts: {e}")
                
                return financial_summary
                
        except Exception as e:
            return {"error": f"Error getting financial data: {str(e)}"}
    
    def _extract_financial_metrics(self, accounts_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key financial metrics from accounts data"""
        metrics = {}
        
        try:
            # This is a simplified extraction - in practice, you'd need to parse
            # the specific account structure based on the company's filing type
            if "accounts" in accounts_data:
                accounts = accounts_data["accounts"]
                
                # Extract common financial metrics
                if "balance_sheet" in accounts:
                    balance_sheet = accounts["balance_sheet"]
                    metrics["total_assets"] = balance_sheet.get("total_assets", {})
                    metrics["net_assets"] = balance_sheet.get("net_assets", {})
                    metrics["total_liabilities"] = balance_sheet.get("total_liabilities", {})
                
                if "profit_and_loss" in accounts:
                    pnl = accounts["profit_and_loss"]
                    metrics["turnover"] = pnl.get("turnover", {})
                    metrics["gross_profit"] = pnl.get("gross_profit", {})
                    metrics["net_profit"] = pnl.get("net_profit", {})
                
                metrics["accounting_reference_date"] = accounts.get("accounting_reference_date")
                metrics["last_accounts_made_up_to"] = accounts.get("last_accounts_made_up_to")
                
        except Exception as e:
            print(f"Error extracting financial metrics: {e}")
        
        return metrics
    
    async def get_company_charges(self, company_number: str) -> List[Dict[str, Any]]:
        """Get company charges (mortgages, etc.)"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/company/{company_number}/charges",
                    auth=(self.api_key, '')
                )
                response.raise_for_status()
                charges_data = response.json()
                return charges_data.get("items", [])
                
        except Exception as e:
            print(f"Error getting company charges: {e}")
            return []
    
    async def get_company_persons_with_significant_control(self, company_number: str) -> List[Dict[str, Any]]:
        """Get persons with significant control"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/company/{company_number}/persons-with-significant-control",
                    auth=(self.api_key, '')
                )
                response.raise_for_status()
                psc_data = response.json()
                return psc_data.get("items", [])
                
        except Exception as e:
            print(f"Error getting PSC data: {e}")
            return []
