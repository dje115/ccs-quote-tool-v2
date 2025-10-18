#!/usr/bin/env python3
"""
Web scraping service for LinkedIn and website data extraction
"""

import re
import httpx
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup


class WebScrapingService:
    """Service for scraping LinkedIn and company websites"""
    
    def __init__(self):
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    async def scrape_linkedin(self, company_name: str, website: str = None) -> Dict[str, Any]:
        """
        Scrape LinkedIn company data
        Note: LinkedIn has anti-scraping measures, so this is basic implementation
        """
        try:
            linkedin_data = {
                'linkedin_url': None,
                'linkedin_followers': None,
                'linkedin_industry': None,
                'linkedin_company_size': None,
                'linkedin_description': None,
                'linkedin_website': None,
                'linkedin_headquarters': None,
                'linkedin_founded': None,
                'linkedin_specialties': None
            }
            
            # Try to find LinkedIn URL from website
            if website:
                try:
                    async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers, follow_redirects=True) as client:
                        response = await client.get(website)
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.text, 'html.parser')
                            linkedin_links = soup.find_all('a', href=re.compile(r'linkedin\.com/company'))
                            if linkedin_links:
                                linkedin_data['linkedin_url'] = linkedin_links[0]['href']
                                print(f"[LINKEDIN] Found LinkedIn URL from website: {linkedin_data['linkedin_url']}")
                except Exception as e:
                    print(f"[LINKEDIN] Error scraping website for LinkedIn link: {e}")
            
            # Construct likely LinkedIn URL
            if not linkedin_data['linkedin_url']:
                company_slug = re.sub(r'[^a-zA-Z0-9]+', '-', company_name.lower()).strip('-')
                linkedin_data['linkedin_url'] = f"https://www.linkedin.com/company/{company_slug}"
                print(f"[LINKEDIN] Constructed LinkedIn URL: {linkedin_data['linkedin_url']}")
            
            return {
                'success': True,
                'data': linkedin_data
            }
            
        except Exception as e:
            print(f"[LINKEDIN] Error: {e}")
            return {
                'success': False,
                'error': f'LinkedIn scraping failed: {str(e)}',
                'data': {}
            }
    
    async def scrape_website(self, company_name: str, website: str) -> Dict[str, Any]:
        """
        Scrape company website for additional data
        """
        try:
            web_data = {
                'website_title': None,
                'website_description': None,
                'contact_info': [],
                'social_media': [],
                'key_phrases': [],
                'locations': [],
                'addresses': [],
                'additional_sites': []
            }
            
            if not website:
                return {
                    'success': False,
                    'error': 'No website provided',
                    'data': web_data
                }
            
            # Ensure website has protocol
            if not website.startswith(('http://', 'https://')):
                website = f'https://{website}'
            
            print(f"[WEBSITE] Scraping {website}")
            
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers, follow_redirects=True) as client:
                response = await client.get(website)
                
                if response.status_code != 200:
                    return {
                        'success': False,
                        'error': f'Website returned status code {response.status_code}',
                        'data': web_data
                    }
                
                soup = BeautifulSoup(response.text, 'html.parser')
                text_content = soup.get_text()
                
                # Extract basic info
                if soup.title:
                    web_data['website_title'] = soup.title.string
                    print(f"[WEBSITE] Title: {web_data['website_title']}")
                
                # Extract meta description
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                if meta_desc:
                    web_data['website_description'] = meta_desc.get('content')
                    print(f"[WEBSITE] Description: {web_data['website_description'][:100]}...")
                
                # Extract contact information
                contact_patterns = [
                    (r'\b\d{2,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b', 'phone'),  # Phone numbers
                    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'email')  # Email addresses
                ]
                
                contacts = []
                for pattern, contact_type in contact_patterns:
                    matches = re.findall(pattern, text_content)
                    contacts.extend(matches)
                
                web_data['contact_info'] = list(set(contacts))[:10]  # Unique contacts, max 10
                print(f"[WEBSITE] Found {len(web_data['contact_info'])} contact items")
                
                # Extract social media links
                social_links = []
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if any(platform in href.lower() for platform in ['facebook', 'twitter', 'linkedin', 'instagram', 'youtube']):
                        social_links.append(href)
                
                web_data['social_media'] = social_links[:10]  # Max 10 social links
                print(f"[WEBSITE] Found {len(web_data['social_media'])} social media links")
                
                # Extract key phrases (simple keyword extraction)
                words = re.findall(r'\b[a-zA-Z]{4,}\b', text_content.lower())
                word_freq = {}
                stop_words = {'this', 'that', 'with', 'from', 'they', 'been', 'have', 'will', 'your', 'said', 'each', 'which', 'their', 'time', 'would', 'there', 'could', 'other', 'about', 'into', 'than', 'them', 'these', 'some', 'make', 'when', 'what', 'were', 'more'}
                for word in words:
                    if word not in stop_words:
                        word_freq[word] = word_freq.get(word, 0) + 1
                
                web_data['key_phrases'] = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]
                print(f"[WEBSITE] Extracted {len(web_data['key_phrases'])} key phrases")
                
                # Extract location and address information
                locations, addresses, additional_sites = await self._extract_location_info(soup, text_content)
                web_data['locations'] = locations
                web_data['addresses'] = addresses
                web_data['additional_sites'] = additional_sites
                print(f"[WEBSITE] Found {len(locations)} locations, {len(addresses)} addresses, {len(additional_sites)} additional sites")
            
            return {
                'success': True,
                'data': web_data
            }
            
        except httpx.TimeoutException:
            print(f"[WEBSITE] Timeout scraping {website}")
            return {
                'success': False,
                'error': 'Website request timed out',
                'data': {}
            }
        except Exception as e:
            print(f"[WEBSITE] Error scraping {website}: {e}")
            return {
                'success': False,
                'error': f'Website scraping failed: {str(e)}',
                'data': {}
            }
    
    async def _extract_location_info(self, soup, text_content: str) -> tuple:
        """Extract location, address, and additional site information from website"""
        locations = []
        addresses = []
        additional_sites = []
        
        try:
            # Extract addresses using regex patterns
            # UK postcode pattern
            postcode_pattern = r'\b[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}\b'
            postcodes = re.findall(postcode_pattern, text_content, re.IGNORECASE)
            addresses.extend(postcodes)
            
            # Look for address-like patterns
            address_patterns = [
                r'\d+\s+[A-Za-z\s]+(?:Street|Road|Avenue|Lane|Close|Drive|Way|Place|Court|Grove|Hill|Park|Gardens?|Square|Terrace|Crescent|Mews|Manor|House|Building|Centre|Center|Business Park|Industrial Estate|Trading Estate)\b',
                r'\b[A-Za-z\s]+(?:Street|Road|Avenue|Lane|Close|Drive|Way|Place|Court|Grove|Hill|Park|Gardens?|Square|Terrace|Crescent|Mews|Manor|House|Building|Centre|Center|Business Park|Industrial Estate|Trading Estate)\b'
            ]
            
            for pattern in address_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    cleaned = re.sub(r'\s+', ' ', match.strip())
                    if 10 < len(cleaned) < 100:  # Reasonable address length
                        addresses.append(cleaned)
            
            # Look for location mentions in specific contexts
            location_contexts = [
                r'office[s]?\s+in\s+([A-Za-z\s,]+)',
                r'located\s+in\s+([A-Za-z\s,]+)',
                r'based\s+in\s+([A-Za-z\s,]+)',
                r'serving\s+([A-Za-z\s,]+)',
                r'covering\s+([A-Za-z\s,]+)',
                r'operating\s+in\s+([A-Za-z\s,]+)'
            ]
            
            for pattern in location_contexts:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    cleaned = re.sub(r'\s+', ' ', match.strip())
                    if 2 < len(cleaned) < 50:
                        locations.append(cleaned)
            
            # Look for "Our Locations", "Contact Us", "Find Us" sections
            location_sections = soup.find_all(['div', 'section', 'p'], 
                                            string=re.compile(r'(?:our\s+)?locations?|contact\s+us|find\s+us|visit\s+us|office[s]?|address[es]?', re.IGNORECASE))
            for section in location_sections:
                parent = section.parent if section.parent else section
                for elem in parent.find_all(['p', 'div', 'span', 'li', 'td']):
                    text = elem.get_text().strip()
                    if any(keyword in text.lower() for keyword in ['street', 'road', 'avenue', 'lane', 'close', 'drive', 'way', 'place', 'point', 'barn', 'farm', 'industrial', 'estate']):
                        addresses.append(text)
            
            # Look for multiple office/site mentions
            site_patterns = [
                r'(?:office|site|location|branch|depot|facility|premises)\s+(?:in|at)\s+([A-Za-z\s,]+)',
                r'(?:our|the)\s+(?:office|site|location|branch|depot|facility|premises)\s+in\s+([A-Za-z\s,]+)',
                r'([A-Za-z\s]+)\s+(?:office|site|location|branch|depot|facility|premises)'
            ]
            
            for pattern in site_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    cleaned = re.sub(r'\s+', ' ', match.strip())
                    if 2 < len(cleaned) < 50:
                        additional_sites.append(cleaned)
            
            # Remove duplicates and clean up
            addresses = list(set([addr.strip() for addr in addresses if addr.strip()]))[:10]
            locations = list(set([loc.strip() for loc in locations if loc.strip()]))[:10]
            additional_sites = list(set([site.strip() for site in additional_sites if site.strip()]))[:10]
            
        except Exception as e:
            print(f"[WEBSITE] Error extracting location info: {e}")
        
        return locations, addresses, additional_sites
    
    async def scrape_comprehensive(self, company_name: str, website: str = None) -> Dict[str, Any]:
        """
        Get comprehensive data from both LinkedIn and website
        """
        try:
            results = {
                'linkedin': None,
                'website': None
            }
            
            # Scrape LinkedIn
            linkedin_result = await self.scrape_linkedin(company_name, website)
            if linkedin_result['success']:
                results['linkedin'] = linkedin_result['data']
            
            # Scrape website
            if website:
                website_result = await self.scrape_website(company_name, website)
                if website_result['success']:
                    results['website'] = website_result['data']
            
            return {
                'success': True,
                'data': results
            }
            
        except Exception as e:
            print(f"[WEB SCRAPING] Error in comprehensive scrape: {e}")
            return {
                'success': False,
                'error': f'Comprehensive scraping failed: {str(e)}',
                'data': {}
            }





