#!/usr/bin/env python3
"""
Companies House API Service for company data retrieval
"""

import httpx
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from app.core.config import settings
from app.services.storage_service import get_storage_service


class CompaniesHouseService:
    """Service for Companies House API integration"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.base_url = settings.COMPANIES_HOUSE_BASE_URL
        self.api_key = api_key or settings.COMPANIES_HOUSE_API_KEY
        self.timeout = 30.0
    
    async def search_company(self, company_name: str) -> Optional[Dict[str, Any]]:
        """Search for a company by name"""
        try:
            headers = {'Authorization': self.api_key}
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/search/companies",
                    headers=headers,
                    params={'q': company_name, 'items_per_page': 1}
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get('items'):
                    company = data['items'][0]
                    return {
                        'company_number': company.get('company_number', ''),
                        'company_status': company.get('company_status', ''),
                        'company_type': company.get('company_type', ''),
                        'title': company.get('title', ''),
                        'address_snippet': company.get('address_snippet', ''),
                        'description': company.get('description', ''),
                        'date_of_creation': company.get('date_of_creation', '')
                    }
                return None
                
        except Exception as e:
            print(f"⚠️ Companies House search error: {e}")
            return None
    
    async def get_company_profile(self, company_number: str, customer_id: Optional[str] = None, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive company profile with tenant isolation for MinIO storage"""
        try:
            if not tenant_id:
                raise ValueError("tenant_id is required for tenant isolation")
                
            headers = {'Authorization': self.api_key}
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Get basic company information
                company_response = await client.get(
                    f"{self.base_url}/company/{company_number}",
                    headers=headers
                )
                company_response.raise_for_status()
                company_data = company_response.json()
                
                # Get officers/directors
                officers_data = await self._get_officers(company_number, client, headers)
                
                # Get filing history
                filing_history = await self._get_filing_history(company_number, client, headers)
                
                # Get financial data (now returns dict with financial_history and accounts_documents)
                financial_data_result = await self._get_financial_data(company_number, client, headers, customer_id, tenant_id)
                financial_history = financial_data_result.get('financial_history', [])
                accounts_documents = financial_data_result.get('accounts_documents', [])
                
                # Process into v1-compatible accounts_detail structure
                accounts_detail = await self._build_accounts_detail(
                    company_number, company_data, officers_data, filing_history, financial_history, client, headers
                )
                
                return {
                    "company_number": company_number,
                    "company_profile": company_data,
                    "officers": officers_data,
                    "filing_history": filing_history,
                    "financial_data": financial_history,  # Keep backward compatibility
                    "accounts_documents": accounts_documents,  # New: MinIO paths for accounts documents
                    "accounts_detail": accounts_detail,  # V1-compatible structure
                    "retrieved_at": datetime.utcnow().isoformat()
                }
                
        except httpx.HTTPStatusError as e:
            return {"error": f"Companies House API error: {e.response.status_code} - {e.response.text}"}
        except Exception as e:
            return {"error": f"Error retrieving company data: {str(e)}"}
    
    async def _get_officers(self, company_number: str, client: httpx.AsyncClient, headers: dict) -> List[Dict[str, Any]]:
        """Get company officers/directors"""
        try:
            response = await client.get(
                f"{self.base_url}/company/{company_number}/officers",
                headers=headers
            )
            response.raise_for_status()
            officers_data = response.json()
            return officers_data.get("items", [])
        except Exception as e:
            print(f"Error getting officers: {e}")
            return []
    
    async def _get_filing_history(self, company_number: str, client: httpx.AsyncClient, headers: dict) -> List[Dict[str, Any]]:
        """Get company filing history"""
        try:
            response = await client.get(
                f"{self.base_url}/company/{company_number}/filing-history",
                headers=headers
            )
            response.raise_for_status()
            filing_data = response.json()
            return filing_data.get("items", [])[:10]  # Last 10 filings
        except Exception as e:
            print(f"Error getting filing history: {e}")
            return []
    
    async def _get_financial_data(self, company_number: str, client: httpx.AsyncClient, headers: dict, customer_id: Optional[str] = None, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get financial data from multiple years of iXBRL accounts documents and store them in MinIO with tenant isolation"""
        try:
            storage_service = get_storage_service()
            accounts_documents = []  # Store MinIO paths for accounts documents
            
            if not tenant_id:
                raise ValueError("tenant_id is required for tenant isolation")
            
            # Get filing history for accounts
            response = await client.get(
                f"{self.base_url}/company/{company_number}/filing-history",
                params={'category': 'accounts', 'items_per_page': 5},
                headers=headers
            )
            response.raise_for_status()
            filing_data = response.json()
            
            financial_history = []
            filings = filing_data.get("items", [])
            
            # Process last 5 years of accounts (store all available, up to 5 years)
            for i, filing in enumerate(filings[:5]):
                if filing.get('type') == 'AA':  # Annual Accounts
                    year_data = {
                        'filing_date': filing.get('date'),
                        'description': filing.get('description', ''),
                        'made_up_date': filing.get('description_values', {}).get('made_up_date'),
                        'transaction_id': filing.get('transaction_id')
                    }
                    
                    links = filing.get('links', {})
                    document_metadata_url = links.get('document_metadata')
                    content = None
                    content_type = None
                    transaction_id = filing.get('transaction_id')
                    
                    if document_metadata_url:
                        try:
                            print(f"[IXBRL] Year {i+1}: Attempting to retrieve document: {document_metadata_url}")
                            
                            # Get document metadata
                            metadata_response = await client.get(
                                document_metadata_url,
                                headers={'api_key': self.api_key}
                            )
                            
                            if metadata_response.status_code == 200:
                                metadata = metadata_response.json()
                                resources = metadata.get('resources', [])
                                
                                # Find iXBRL content type
                                target_content_type = None
                                for resource in resources:
                                    ct = resource.get('content_type', '')
                                    if 'xhtml' in ct.lower() or 'ixbrl' in ct.lower():
                                        target_content_type = ct
                                        content_type = ct
                                        break
                                
                                if target_content_type:
                                    # Extract document ID from URL
                                    document_id = document_metadata_url.split('/')[-1]
                                    content_url = f"https://document-api.company-information.service.gov.uk/document/{document_id}/content"
                                    
                                    # Download the iXBRL document
                                    content_response = await client.get(
                                        content_url,
                                        headers={
                                            'api_key': self.api_key,
                                            'Accept': target_content_type
                                        },
                                        follow_redirects=True
                                    )
                                    
                                    if content_response.status_code == 200:
                                        content = content_response.text
                                        print(f"[IXBRL] Year {i+1}: Downloaded via API, size: {len(content)} chars")
                                    else:
                                        print(f"[IXBRL] Year {i+1}: API download failed: {content_response.status_code}")
                                else:
                                    print(f"[IXBRL] Year {i+1}: No suitable content type found")
                            else:
                                print(f"[IXBRL] Year {i+1}: Metadata failed: {metadata_response.status_code}")
                            
                            # V1 FALLBACK: Try public web URL when Document API fails
                            if not content and transaction_id:
                                try:
                                    direct_ixbrl_url = f"https://find-and-update.company-information.service.gov.uk/company/{company_number}/filing-history/{transaction_id}/document?format=xhtml&download=1"
                                    print(f"[IXBRL] Year {i+1}: Trying web URL fallback")
                                    
                                    # Use httpx without auth for public URL
                                    direct_response = await client.get(direct_ixbrl_url, follow_redirects=True, timeout=30.0)
                                    
                                    if direct_response.status_code == 200:
                                        content = direct_response.text
                                        content_type = direct_response.headers.get('content-type', 'application/xhtml+xml')
                                        print(f"[IXBRL] Year {i+1}: Downloaded via web URL, size: {len(content)} chars")
                                    else:
                                        print(f"[IXBRL] Year {i+1}: Web URL failed: {direct_response.status_code}")
                                except Exception as web_e:
                                    print(f"[IXBRL] Year {i+1}: Web URL exception: {web_e}")
                            
                            # Store document in MinIO if we have content
                            if content:
                                try:
                                    # Generate object path with tenant isolation: accounts/{tenant_id}/{customer_id}/{company_number}/{year}/{transaction_id}.xhtml
                                    made_up_date = year_data.get('made_up_date', '')
                                    year = made_up_date.split('-')[0] if made_up_date else year_data.get('filing_date', '').split('-')[0] if year_data.get('filing_date') else 'unknown'
                                    
                                    # Always include tenant_id for security and isolation
                                    if customer_id:
                                        object_path = f"accounts/{tenant_id}/{customer_id}/{company_number}/{year}/{transaction_id or 'unknown'}.xhtml"
                                    else:
                                        # Fallback: use tenant_id and company_number only (shouldn't happen in normal flow)
                                        object_path = f"accounts/{tenant_id}/{company_number}/{year}/{transaction_id or 'unknown'}.xhtml"
                                    
                                    # Upload to MinIO
                                    await storage_service.upload_file(
                                        file_data=content.encode('utf-8'),
                                        object_name=object_path,
                                        content_type=content_type or 'application/xhtml+xml',
                                        metadata={
                                            'company_number': company_number,
                                            'filing_date': year_data.get('filing_date', ''),
                                            'made_up_date': made_up_date,
                                            'transaction_id': transaction_id or '',
                                            'description': year_data.get('description', '')
                                        }
                                    )
                                    
                                    # Store document info
                                    doc_info = {
                                        'minio_path': object_path,
                                        'filing_date': year_data.get('filing_date'),
                                        'made_up_date': made_up_date,
                                        'year': year,
                                        'transaction_id': transaction_id,
                                        'description': year_data.get('description', ''),
                                        'content_type': content_type or 'application/xhtml+xml',
                                        'size_bytes': len(content.encode('utf-8'))
                                    }
                                    accounts_documents.append(doc_info)
                                    print(f"[IXBRL] Year {i+1}: Stored document in MinIO: {object_path}")
                                    
                                except Exception as storage_e:
                                    print(f"[IXBRL] Year {i+1}: Error storing document in MinIO: {storage_e}")
                                
                                # Parse the iXBRL document
                                parsed_data = await self._parse_ixbrl_document(content)
                                
                                if parsed_data:
                                    print(f"[IXBRL] Year {i+1}: Extracted {list(parsed_data.keys())}")
                                    year_data.update(parsed_data)
                                    financial_history.append(year_data)
                                else:
                                    print(f"[IXBRL] Year {i+1}: No data extracted from document")
                            else:
                                print(f"[IXBRL] Year {i+1}: No content downloaded")
                        
                        except Exception as e:
                            print(f"[IXBRL] Year {i+1}: Error processing: {e}")
                            continue
            
            print(f"[IXBRL] Total years of financial data collected: {len(financial_history)}")
            print(f"[IXBRL] Total accounts documents stored: {len(accounts_documents)}")
            
            # Add accounts_documents to the return data
            return {
                'financial_history': financial_history,
                'accounts_documents': accounts_documents
            }
            
        except Exception as e:
            print(f"Error getting financial data: {e}")
            return {'financial_history': [], 'accounts_documents': []}
    
    async def search_companies(self, query: str, items_per_page: int = 20) -> Dict[str, Any]:
        """Search for companies by name"""
        try:
            headers = {'Authorization': self.api_key}
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/search/companies",
                    params={"q": query, "items_per_page": items_per_page},
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            print(f"[CH ERROR] Search failed: {e.response.status_code} - {e.response.text}")
            return {"error": f"Companies House search error: {e.response.status_code} - {e.response.text}"}
        except Exception as e:
            print(f"[CH ERROR] Exception: {str(e)}")
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
                    "last_accounts_date": accounts_data.get("last_accounts", {}).get("made_up_to"),
                    "next_accounts_due": accounts_data.get("next_accounts", {}).get("due_on"),
                    "overdue": accounts_data.get("next_accounts", {}).get("overdue", False)
                }
                
                return financial_summary
                
        except Exception as e:
            return {"error": str(e)}
    
    async def _parse_ixbrl_document(self, content: str) -> Dict[str, Any]:
        """Parse iXBRL document to extract financial data"""
        try:
            import xml.etree.ElementTree as ET
            
            financial_data = {}
            
            # Parse the XML content
            root = ET.fromstring(content)
            
            # Define namespace mappings for iXBRL
            ix_namespace = 'http://www.xbrl.org/2008/inlineXBRL'
            if 'http://www.xbrl.org/2013/inlineXBRL' in content:
                ix_namespace = 'http://www.xbrl.org/2013/inlineXBRL'
            
            # Detect taxonomy version from schemaRef in document
            taxonomy_version = '2023-01-01'
            if 'FRS-102/2024-01-01' in content or 'fr/2024-01-01' in content:
                taxonomy_version = '2024-01-01'
            elif 'FRS-102/2022-01-01' in content or 'fr/2022-01-01' in content:
                taxonomy_version = '2022-01-01'
            
            namespaces = {
                'ix': ix_namespace,
                'xbrli': 'http://www.xbrl.org/2003/instance',
                'core': f'http://xbrl.frc.org.uk/fr/{taxonomy_version}/core',
                'e': f'http://xbrl.frc.org.uk/fr/{taxonomy_version}/core',
                'bus': f'http://xbrl.frc.org.uk/cd/{taxonomy_version}/business',
                'b': f'http://xbrl.frc.org.uk/FRS-102/{taxonomy_version}',
                'd': f'http://xbrl.frc.org.uk/cd/{taxonomy_version}/business'
            }
            
            print(f"[IXBRL] Using taxonomy version: {taxonomy_version}")
            
            # Extract financial data using XBRL tags
            # Note: Different accounting standards (FRS-102, FRS-105, etc.) use different tag names
            tag_variations = [
                ('net_assets', ['e:NetAssetsLiabilities', 'core:NetAssetsLiabilities', 'e:NetAssets', 'core:NetAssets', 'e:Equity', 'core:Equity']),
                ('cash_at_bank', ['e:CashBankOnHand', 'core:CashBankOnHand', 'e:CashAtBank', 'core:CashAtBank', 'e:CashBankInHand', 'core:CashBankInHand']),
                ('total_equity', ['e:Equity', 'core:Equity', 'e:TotalEquity', 'core:TotalEquity', 'e:ShareholderFunds', 'core:ShareholderFunds']),
                ('ppe', ['e:PropertyPlantEquipment', 'core:PropertyPlantEquipment', 'e:PPE', 'core:PPE', 'e:TangibleFixedAssets', 'core:TangibleFixedAssets']),
                ('trade_debtors', ['e:TradeDebtorsTradeReceivables', 'core:TradeDebtorsTradeReceivables', 'e:TradeDebtors', 'core:TradeDebtors', 'e:Debtors', 'core:Debtors']),
                # Turnover: Many variations across different accounting standards and years
                ('turnover', [
                    'e:TurnoverRevenue', 'core:TurnoverRevenue', 
                    'e:Revenue', 'core:Revenue', 
                    'e:Turnover', 'core:Turnover',
                    'bus:TurnoverRevenue', 'd:TurnoverRevenue',
                    'bus:Revenue', 'd:Revenue',
                    'bus:Turnover', 'd:Turnover',
                    # FRS-102 variations
                    'b:TurnoverRevenue', 'b:Revenue', 'b:Turnover',
                    # Older taxonomy variations
                    'uk-gaap:TurnoverRevenue', 'uk-gaap:Revenue', 'uk-gaap:Turnover',
                    # Micro-entity variations
                    'micro:TurnoverRevenue', 'micro:Revenue', 'micro:Turnover',
                    # Additional common variations
                    'e:TotalRevenue', 'core:TotalRevenue',
                    'bus:TotalRevenue', 'd:TotalRevenue',
                ]),
                ('profit_before_tax', ['e:ProfitLossOnOrdinaryActivitiesBeforeTax', 'core:ProfitLossOnOrdinaryActivitiesBeforeTax', 'e:ProfitBeforeTax', 'core:ProfitBeforeTax', 'e:ProfitLossBeforeTax', 'core:ProfitLossBeforeTax']),
                ('operating_profit', ['e:OperatingProfitLoss', 'core:OperatingProfitLoss', 'e:OperatingProfit', 'core:OperatingProfit', 'e:ProfitLossFromOperations', 'core:ProfitLossFromOperations']),
                ('gross_profit', ['e:GrossProfitLoss', 'core:GrossProfitLoss', 'e:GrossProfit', 'core:GrossProfit']),
                ('cost_of_sales', ['e:CostSales', 'core:CostSales', 'e:CostOfSales', 'core:CostOfSales']),
                ('admin_expenses', ['e:AdministrativeExpenses', 'core:AdministrativeExpenses', 'e:AdminExpenses', 'core:AdminExpenses'])
            ]
            
            for field_name, tag_list in tag_variations:
                for tag in tag_list:
                    # Try with namespaces first
                    elements = root.findall(f'.//ix:nonFraction[@name="{tag}"]', namespaces)
                    if not elements:
                        # Try without namespace prefix (some documents use different structures)
                        elements = root.findall(f'.//*[@name="{tag}"]')
                    if not elements:
                        # Try with different namespace variations
                        for ns_prefix in ['e', 'core', 'bus', 'd', 'b']:
                            if tag.startswith(f'{ns_prefix}:'):
                                tag_without_ns = tag.split(':', 1)[1]
                                elements = root.findall(f'.//ix:nonFraction[@name="{tag_without_ns}"]', namespaces)
                                if elements:
                                    break
                    
                    if elements:
                        # For turnover, collect all values and take the largest positive one
                        # (turnover should be positive and the largest value is likely the correct one)
                        all_values = []
                        for elem in elements:
                            try:
                                value_text = elem.text.strip() if elem.text else ''
                                # Remove currency symbols and commas
                                value_text = value_text.replace('£', '').replace('$', '').replace(',', '').replace(' ', '').replace('(', '-').replace(')', '')
                                if value_text and value_text != '-' and value_text != '':
                                    value = float(value_text)
                                    # For turnover, only consider positive values >= 10000 (to avoid note numbers like "3")
                                    if field_name == 'turnover':
                                        if value >= 10000:  # Minimum reasonable turnover
                                            all_values.append((value, elem.get('contextRef', 'unknown')))
                                        else:
                                            print(f"[IXBRL] Skipping turnover value {value} (too small, likely a note number)")
                                    else:
                                        all_values.append((value, elem.get('contextRef', 'unknown')))
                            except Exception as e:
                                if field_name == 'turnover':
                                    print(f"[IXBRL] Failed to parse {tag}: {e}, text: {elem.text if elem.text else 'empty'}")
                                continue
                        
                        if all_values:
                            if field_name == 'turnover' and len(all_values) > 1:
                                # For turnover, take the largest value (most likely the correct one)
                                all_values.sort(key=lambda x: x[0], reverse=True)
                                value, context_ref = all_values[0]
                                financial_data[field_name] = value
                                print(f"[IXBRL] Extracted {field_name} = £{value:,.0f} using tag: {tag}, contextRef: {context_ref} (from {len(all_values)} matches, took max)")
                            else:
                                # For other fields, take the first valid value
                                value, context_ref = all_values[0]
                                financial_data[field_name] = value
                                if field_name == 'turnover':
                                    print(f"[IXBRL] Extracted {field_name} = £{value:,.0f} using tag: {tag}, contextRef: {context_ref}")
                        if field_name in financial_data:
                            break
            
            # Extract employee count
            employee_tag_variations = [
                'e:AverageNumberEmployeesDuringPeriod',
                'core:AverageNumberEmployeesDuringPeriod',
                'e:NumberOfEmployees',
                'core:NumberOfEmployees',
                'e:Employees',
                'core:Employees',
                'bus:AverageNumberEmployees',
                'd:AverageNumberEmployees'
            ]
            
            for tag in employee_tag_variations:
                elements = root.findall(f'.//ix:nonFraction[@name="{tag}"]', namespaces)
                if elements:
                    for elem in elements[:1]:
                        try:
                            value = int(float(elem.text))
                            financial_data['employees'] = value
                            break
                        except:
                            continue
                    if 'employees' in financial_data:
                        break
            
            # Fallback: regex patterns if XBRL tags don't work (especially for turnover)
            if 'turnover' not in financial_data:
                regex_data = self._extract_financial_data_regex(content)
                if 'turnover' in regex_data and 'turnover' not in financial_data:
                    financial_data['turnover'] = regex_data['turnover']
                    print(f"[IXBRL] Extracted turnover via regex: £{regex_data['turnover']:,.0f}")
                # Merge other regex-extracted fields if not already found
                for key, value in regex_data.items():
                    if key not in financial_data:
                        financial_data[key] = value
            
            # Log what was extracted
            if financial_data:
                extracted_fields = list(financial_data.keys())
                print(f"[IXBRL] Extracted fields: {extracted_fields}")
                if 'turnover' not in extracted_fields:
                    print(f"[IXBRL] WARNING: Turnover not found in document")
            
            return financial_data
            
        except Exception as e:
            print(f"Error parsing iXBRL: {e}")
            return {}
    
    def _extract_financial_data_regex(self, content: str) -> Dict[str, Any]:
        """Extract financial data using regex patterns as fallback"""
        try:
            financial_data = {}
            import re
            
            # Look for financial figures in the content using regex
            # More comprehensive patterns for turnover - including XBRL format
            patterns = {
                'turnover': [
                    # XBRL format: look for turnover in ix:nonFraction elements
                    r'name="[^"]*[Tt]urnover[^"]*"[^>]*>([\d,]+(?:\.\d+)?)',
                    r'name="[^"]*[Rr]evenue[^"]*"[^>]*>([\d,]+(?:\.\d+)?)',
                    # Pattern for "Turnover" followed immediately by numbers (no space/colon)
                    # This handles formats like "Turnover21,638,153" or "Turnover321,638,15319,864,471"
                    # Match large numbers (at least 6 digits) to avoid catching note numbers like "3"
                    r'Turnover(\d{6,}(?:,\d{3})*(?:\.\d+)?)',
                    r'Turnover\s+(\d{6,}(?:,\d{3})*(?:\.\d+)?)',
                    r'Revenue(\d{6,}(?:,\d{3})*(?:\.\d+)?)',
                    r'Revenue\s+(\d{6,}(?:,\d{3})*(?:\.\d+)?)',
                    # Fallback: any turnover followed by numbers (but filter small values later)
                    r'Turnover\s*([\d,]+(?:\.\d+)?)',
                    r'Revenue\s*([\d,]+(?:\.\d+)?)',
                    # Standard text patterns with separators
                    r'Turnover[:\s]+£?\s*([\d,]+(?:\.\d+)?)',
                    r'Revenue[:\s]+£?\s*([\d,]+(?:\.\d+)?)',
                    r'Total\s+[Tt]urnover[:\s]+£?\s*([\d,]+(?:\.\d+)?)',
                    r'Total\s+[Rr]evenue[:\s]+£?\s*([\d,]+(?:\.\d+)?)',
                    r'Turnover\s+and\s+other\s+income[:\s]+£?\s*([\d,]+(?:\.\d+)?)',
                    # Look for turnover in table structures
                    r'<td[^>]*>Turnover[^<]*</td>\s*<td[^>]*>£?\s*([\d,]+(?:\.\d+)?)',
                    r'<td[^>]*>Revenue[^<]*</td>\s*<td[^>]*>£?\s*([\d,]+(?:\.\d+)?)',
                    # Look for turnover in div structures (common in iXBRL)
                    r'<div[^>]*>Turnover[^<]*</div>\s*<div[^>]*>£?\s*([\d,]+(?:\.\d+)?)',
                    r'<div[^>]*>Revenue[^<]*</div>\s*<div[^>]*>£?\s*([\d,]+(?:\.\d+)?)',
                ],
                'net_assets': [
                    r'Net\s+assets[:\s]+£?\s*([\d,]+(?:\.\d+)?)',
                    r'Shareholders[^\']*?\s+funds[:\s]+£?\s*([\d,]+(?:\.\d+)?)',
                    r'Total\s+equity[:\s]+£?\s*([\d,]+(?:\.\d+)?)'
                ],
                'cash_at_bank': [
                    r'Cash\s+at\s+bank[:\s]+£?\s*([\d,]+(?:\.\d+)?)',
                    r'Cash\s+and\s+bank[:\s]+£?\s*([\d,]+(?:\.\d+)?)',
                    r'Cash\s+and\s+cash\s+equivalents[:\s]+£?\s*([\d,]+(?:\.\d+)?)'
                ],
                'profit_before_tax': [
                    r'Profit\s+before\s+tax[:\s]+£?\s*([\d,]+(?:\.\d+)?)',
                    r'Profit\s+\(loss\)\s+before\s+tax[:\s]+£?\s*([\d,]+(?:\.\d+)?)'
                ]
            }
            
            for key, pattern_list in patterns.items():
                for pattern in pattern_list:
                    matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                    if matches:
                        try:
                            if key in financial_data:
                                continue
                            # Take the first match, but prefer larger numbers (likely the main figure)
                            values = [float(m.replace(',', '')) for m in matches]
                            if values:
                                # For turnover, filter out obviously wrong values (too small, negative, etc.)
                                # Minimum reasonable turnover is £10,000 (to avoid catching note numbers like "3")
                                valid_values = [v for v in values if v >= 10000]  # Minimum reasonable turnover
                                if valid_values:
                                    if key == 'turnover' and len(valid_values) > 1:
                                        # Take the largest value (likely the most recent year or total)
                                        financial_data[key] = max(valid_values)
                                        print(f"[REGEX] Extracted {key} = £{max(valid_values):,.0f} (from {len(valid_values)} matches, took max)")
                                    else:
                                        financial_data[key] = valid_values[0]
                                        print(f"[REGEX] Extracted {key} = £{valid_values[0]:,.0f}")
                                else:
                                    # If no valid values above threshold, try with lower threshold but log warning
                                    fallback_values = [v for v in values if v > 1000]
                                    if fallback_values:
                                        financial_data[key] = max(fallback_values) if key == 'turnover' else fallback_values[0]
                                        print(f"[REGEX] WARNING: Extracted {key} = £{financial_data[key]:,.0f} (below normal threshold, may be incorrect)")
                                    else:
                                        print(f"[REGEX] WARNING: No valid {key} values found (all values too small: {values})")
                            break
                        except Exception as e:
                            print(f"[REGEX] Error parsing {key} from pattern {pattern}: {e}")
                            continue
            
            return financial_data
            
        except Exception as e:
            print(f"Error in regex extraction: {e}")
            return {}
    
    async def _build_accounts_detail(self, company_number: str, company_data: dict, officers_data: list, 
                                     filing_history: list, financial_data: List[Dict[str, Any]], client: httpx.AsyncClient, 
                                     headers: dict) -> Dict[str, Any]:
        """Build v1-compatible accounts_detail structure with financial data and active directors"""
        try:
            accounts_detail = {
                'filing_date': None,
                'made_up_date': None,
                'shareholders_funds': None,
                'cash_at_bank': None,
                'turnover': None,
                'profit_before_tax': None,
                'operating_profit': None,
                'gross_profit': None,
                'employees': None,
                'company_size': None,
                'detailed_financials': [],
                'active_directors': [],
                'total_active_directors': 0,
                'years_of_data': 0
            }
            
            # Process multiple years of financial data
            if financial_data and len(financial_data) > 0:
                accounts_detail['years_of_data'] = len(financial_data)
                
                # Current year (most recent) data
                current_year = financial_data[0]
                accounts_detail['filing_date'] = current_year.get('filing_date')
                accounts_detail['made_up_date'] = current_year.get('made_up_date')
                
                if current_year.get('net_assets'):
                    accounts_detail['shareholders_funds'] = f"£{current_year['net_assets']:,.0f}"
                    accounts_detail['shareholders_funds_current'] = current_year['net_assets']
                
                if current_year.get('cash_at_bank'):
                    accounts_detail['cash_at_bank'] = f"£{current_year['cash_at_bank']:,.0f}"
                    accounts_detail['cash_at_bank_current'] = current_year['cash_at_bank']
                
                if current_year.get('turnover'):
                    accounts_detail['turnover'] = f"£{current_year['turnover']:,.0f}"
                    accounts_detail['turnover_current'] = current_year['turnover']
                
                if current_year.get('profit_before_tax'):
                    accounts_detail['profit_before_tax'] = f"£{current_year['profit_before_tax']:,.0f}"
                
                if current_year.get('operating_profit'):
                    accounts_detail['operating_profit'] = f"£{current_year['operating_profit']:,.0f}"
                
                if current_year.get('gross_profit'):
                    accounts_detail['gross_profit'] = f"£{current_year['gross_profit']:,.0f}"
                
                if current_year.get('employees'):
                    accounts_detail['employees'] = current_year['employees']
                    accounts_detail['employee_count'] = current_year['employees']
                
                # Previous year data for comparison
                if len(financial_data) >= 2:
                    previous_year = financial_data[1]
                    if previous_year.get('net_assets'):
                        accounts_detail['shareholders_funds_previous'] = previous_year['net_assets']
                    if previous_year.get('cash_at_bank'):
                        accounts_detail['cash_at_bank_previous'] = previous_year['cash_at_bank']
                    if previous_year.get('turnover'):
                        accounts_detail['turnover_previous'] = previous_year['turnover']
                
                # Build detailed_financials array with calculated financial_year
                for i, year_data in enumerate(financial_data):
                    financial_year = None
                    
                    # Calculate financial year from made_up_date
                    if year_data.get('made_up_date'):
                        try:
                            financial_year = year_data['made_up_date'].split('-')[0]
                        except:
                            pass
                    
                    # Fallback: calculate from filing date
                    if not financial_year and year_data.get('filing_date'):
                        try:
                            filing_year = int(year_data['filing_date'].split('-')[0])
                            financial_year = str(filing_year - 1)  # UK companies typically file previous year
                        except:
                            pass
                    
                    detailed_year = {
                        'filing_date': year_data.get('filing_date'),
                        'made_up_date': year_data.get('made_up_date'),
                        'turnover': year_data.get('turnover'),
                        'shareholders_funds': year_data.get('net_assets'),
                        'cash_at_bank': year_data.get('cash_at_bank'),
                        'profit_before_tax': year_data.get('profit_before_tax'),
                        'employees': year_data.get('employees'),
                        'financial_year': financial_year
                    }
                    accounts_detail['detailed_financials'].append(detailed_year)
                
                # Calculate trends (v1-style)
                if len(financial_data) >= 2:
                    current = financial_data[0]
                    previous = financial_data[1]
                    
                    # Revenue growth
                    if current.get('turnover') and previous.get('turnover'):
                        try:
                            current_rev = float(current['turnover'])
                            previous_rev = float(previous['turnover'])
                            if previous_rev > 0:
                                growth = ((current_rev - previous_rev) / previous_rev) * 100
                                accounts_detail['revenue_growth'] = f"{growth:+.1f}%"
                        except:
                            pass
                    
                    # Profitability trend
                    if current.get('net_assets') and previous.get('net_assets'):
                        try:
                            current_funds = float(current['net_assets'])
                            previous_funds = float(previous['net_assets'])
                            if current_funds > previous_funds:
                                accounts_detail['profitability_trend'] = 'Growing'
                            elif current_funds < previous_funds:
                                accounts_detail['profitability_trend'] = 'Declining'
                            else:
                                accounts_detail['profitability_trend'] = 'Stable'
                        except:
                            pass
                    
                    # Financial health score (simple scoring system matching v1)
                    health_score = 50  # Base score
                    
                    # Revenue growth bonus/penalty
                    if accounts_detail.get('revenue_growth'):
                        try:
                            growth_pct = float(accounts_detail['revenue_growth'].replace('%', '').replace('+', ''))
                            if growth_pct > 10:
                                health_score += 20
                            elif growth_pct > 0:
                                health_score += 10
                            elif growth_pct < -10:
                                health_score -= 20
                            elif growth_pct < 0:
                                health_score -= 10
                        except:
                            pass
                    
                    # Profitability bonus/penalty
                    if accounts_detail.get('profitability_trend') == 'Growing':
                        health_score += 15
                    elif accounts_detail.get('profitability_trend') == 'Declining':
                        health_score -= 15
                    
                    accounts_detail['financial_health_score'] = min(100, max(0, health_score))
            
            # Process active directors from officers data
            active_directors = []
            for officer in officers_data[:10]:  # Limit to top 10
                # Skip resigned officers
                if officer.get('resigned_on'):
                    continue
                
                officer_info = {
                    'name': officer.get('name', '').title(),
                    'role': officer.get('officer_role', '').title().replace('_', ' '),
                    'appointed_on': officer.get('appointed_on'),
                    'nationality': officer.get('nationality'),
                    'country_of_residence': officer.get('country_of_residence'),
                    'occupation': officer.get('occupation'),
                    'date_of_birth': None
                }
                
                # Extract date of birth if available
                if officer.get('date_of_birth'):
                    dob = officer['date_of_birth']
                    if isinstance(dob, dict):
                        month = dob.get('month', '')
                        year = dob.get('year', '')
                        if month and year:
                            officer_info['date_of_birth'] = f"{month}/{year}"
                
                # Extract address if available
                if officer.get('address'):
                    addr = officer['address']
                    address_parts = []
                    for key in ['premises', 'address_line_1', 'address_line_2', 'locality', 'postal_code']:
                        if addr.get(key):
                            address_parts.append(str(addr[key]))
                    if address_parts:
                        officer_info['address'] = ', '.join(address_parts)
                
                active_directors.append(officer_info)
            
            accounts_detail['active_directors'] = active_directors
            accounts_detail['total_active_directors'] = len(active_directors)
            
            return accounts_detail
            
        except Exception as e:
            print(f"Error building accounts_detail: {e}")
            return {}
