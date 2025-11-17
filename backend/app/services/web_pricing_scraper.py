#!/usr/bin/env python3
"""
Web Pricing Scraper Service
Migrated from v1 with multi-tenant support
Scrapes real-time pricing from supplier websites
"""

import re
import logging
import asyncio
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class WebPricingScraper:
    """
    Generic scraper for getting real-time pricing from supplier websites
    Uses supplier-specific configuration from database instead of hardcoded rules
    """
    
    def __init__(self):
        self.session: Optional[httpx.AsyncClient] = None
    
    async def _get_session(self) -> httpx.AsyncClient:
        """Get or create HTTP client session"""
        if self.session is None:
            self.session = httpx.AsyncClient(
                timeout=30.0,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            )
        return self.session
    
    async def close(self):
        """Close HTTP client session and cleanup resources"""
        if self.session:
            await self.close()
            self.session = None
    
    def extract_price(self, text: str) -> Optional[float]:
        """Extract numeric price from text"""
        if not text:
            return None
        
        # Remove currency symbols and clean text
        price_text = re.sub(r'[^\d.,]', '', str(text))
        
        # Handle different decimal formats
        if ',' in price_text and '.' in price_text:
            # Format like 1,234.56
            price_text = price_text.replace(',', '')
        elif ',' in price_text:
            # Could be 1,234 or 1,23 (European format)
            if len(price_text.split(',')[-1]) <= 2:
                # Likely decimal separator
                price_text = price_text.replace(',', '.')
            else:
                # Likely thousands separator
                price_text = price_text.replace(',', '')
        
        try:
            price = float(price_text)
            return price if price > 0 else None
        except (ValueError, TypeError):
            return None
    
    def _calculate_confidence(self, source: str, method: str, price: Optional[float] = None) -> float:
        """
        Calculate confidence score based on scraping method and source
        
        Returns:
            Confidence score 0.0-1.0
        """
        confidence_map = {
            'direct_url': 0.95,  # High confidence - direct product page
            'known_pricing': 0.9,  # High confidence - manually verified known prices
            'api': 0.95,  # High confidence - official API
            'search': 0.7,  # Medium confidence - search results
            'list': 0.6,  # Lower confidence - list view prices
            'cached': 0.8  # Medium-high confidence - previously scraped
        }
        
        base_confidence = confidence_map.get(method, 0.5)
        
        # Adjust based on source
        if source == 'known_pricing':
            base_confidence = 0.9
        elif source == 'pricing_url':
            base_confidence = 0.95  # High confidence for direct pricing URLs
        
        # Sanity check: if price seems unreasonable, lower confidence
        if price:
            if price < 0.01 or price > 100000:
                base_confidence *= 0.5  # Halve confidence for suspicious prices
        
        return min(1.0, max(0.0, base_confidence))
    
    async def _scrape_product_page(
        self, 
        url: str, 
        price_selectors: Optional[List[str]] = None,
        custom_headers: Optional[Dict[str, str]] = None,
        retry_count: int = 0, 
        max_retries: int = 2
    ) -> Optional[float]:
        """Scrape price from a product page with retry logic"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            if custom_headers:
                headers.update(custom_headers)
            
            session = await self._get_session()
            response = await session.get(url, headers=headers, follow_redirects=True)
            if response.status_code != 200:
                if retry_count < max_retries:
                    logger.warning(f"Retrying {url} (attempt {retry_count + 1}/{max_retries})")
                    await asyncio.sleep(1)  # Wait 1 second before retry
                    return await self._scrape_product_page(url, price_selectors, custom_headers, retry_count + 1, max_retries)
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Use provided selectors or fallback to defaults
            if not price_selectors:
                price_selectors = [
                    '.price',
                    '.price-value',
                    '[data-testid="price"]',
                    '.product-price',
                    '.price-current',
                    '.woocommerce-Price-amount',
                    '[class*="price"]',
                    '[id*="price"]',
                    'span[class*="price"]',
                    'div[class*="price"]'
                ]
            
            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    price = self.extract_price(price_text)
                    if price:
                        return price
            
            return None
            
        except Exception as e:
            if retry_count < max_retries:
                logger.warning(f"Error scraping {url}, retrying: {e}")
                await asyncio.sleep(1)
                return await self._scrape_product_page(url, price_selectors, custom_headers, retry_count + 1, max_retries)
            logger.error(f"Error scraping product page {url}: {e}")
            return None
    
    async def scrape_supplier_pricing(
        self, 
        supplier_config: Dict[str, Any],
        product_name: str,
        supplier_name: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Generic method to scrape pricing from any supplier using their configuration
        
        Args:
            supplier_config: Supplier scraping configuration from database
            product_name: Name of the product to search for
            supplier_name: Optional supplier name for logging
        
        Returns:
            Dict with price, url, source, confidence, etc.
        """
        if not supplier_config:
            logger.warning(f"No scraping configuration for supplier: {supplier_name}")
            return None
        
        try:
            # Parse configuration
            import json
            if isinstance(supplier_config, str):
                config = json.loads(supplier_config)
            else:
                config = supplier_config
            
            base_url = config.get('base_url', '')
            search_url_template = config.get('search_url_template', '')
            product_url_template = config.get('product_url_template', '')
            price_selectors = config.get('price_selectors', ['.price', '.price-value', '[class*="price"]'])
            product_selectors = config.get('product_selectors', ['.product-item', '.product-card'])
            name_selectors = config.get('name_selectors', ['.product-title', 'h3', 'h4'])
            search_result_selector = config.get('search_result_selector', None)
            rate_limit_ms = config.get('rate_limit_ms', 1000)
            custom_headers = config.get('custom_headers', {})
            currency = config.get('currency', 'GBP')
            
            # Apply rate limiting
            if rate_limit_ms > 0:
                await asyncio.sleep(rate_limit_ms / 1000.0)
            
            # Try direct product URL first if template provided
            if product_url_template and '{product_code}' in product_url_template:
                # Extract product code from product name (basic heuristic)
                product_code = self._extract_product_code(product_name)
                if product_code:
                    product_url = product_url_template.replace('{product_code}', product_code)
                    price = await self._scrape_product_page(product_url, price_selectors, custom_headers)
                    if price:
                        return {
                            'price': price,
                            'url': product_url,
                            'source': 'direct_url',
                            'scraping_method': 'direct_url',
                            'confidence': self._calculate_confidence('direct_url', 'direct_url', price),
                            'currency': currency
                        }
            
            # Try search if search URL template provided
            if search_url_template and '{query}' in search_url_template:
                search_url = search_url_template.replace('{query}', product_name.replace(' ', '+'))
                result = await self._scrape_search_results(
                    search_url, 
                    product_name,
                    price_selectors,
                    product_selectors,
                    name_selectors,
                    search_result_selector,
                    custom_headers
                )
                if result:
                    result['currency'] = currency
                    return result
            
            # Try pricing_url if provided (fallback)
            # This would be handled by the caller if pricing_url is set
            
            return None
            
        except Exception as e:
            logger.error(f"Error scraping pricing with config: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_product_code(self, product_name: str) -> Optional[str]:
        """Extract product code from product name (basic heuristic)"""
        # Look for patterns like "U6-Pro", "G5-Bullet", etc.
        import re
        # Match alphanumeric codes like "U6-Pro", "G5-Bullet", "CAT6-305M"
        match = re.search(r'([A-Z0-9]+[-_]?[A-Z0-9]+)', product_name.upper())
        if match:
            return match.group(1).replace('_', '-')
        return None
    
    async def _scrape_search_results(
        self,
        search_url: str,
        product_name: str,
        price_selectors: List[str],
        product_selectors: List[str],
        name_selectors: List[str],
        search_result_selector: Optional[str],
        custom_headers: Dict[str, str]
    ) -> Optional[Dict[str, Any]]:
        """Scrape pricing from search results page"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            headers.update(custom_headers)
            
            response = await self.session.get(search_url, headers=headers, follow_redirects=True)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find product items
            product_items = []
            if search_result_selector:
                product_items = soup.select(search_result_selector)
            else:
                # Try all product selectors
                for selector in product_selectors:
                    items = soup.select(selector)
                    if items:
                        product_items = items
                        break
            
            # Search through results for matching product
            product_name_lower = product_name.lower()
            for item in product_items[:5]:  # Check first 5 results
                # Try to find product name
                name_match = False
                for name_selector in name_selectors:
                    name_elem = item.select_one(name_selector)
                    if name_elem:
                        item_name = name_elem.get_text(strip=True).lower()
                        # Check if product name matches (fuzzy match)
                        if any(term in item_name for term in product_name_lower.split()):
                            name_match = True
                            break
                
                if name_match or len(product_items) == 1:  # If only one result, use it
                    # Try to get price from item
                    for price_selector in price_selectors:
                        price_elem = item.select_one(price_selector)
                        if price_elem:
                            price_text = price_elem.get_text(strip=True)
                            price = self.extract_price(price_text)
                            if price:
                                # Try to get product URL
                                link_elem = item.select_one('a[href]')
                                product_url = None
                                if link_elem:
                                    href = link_elem.get('href')
                                    if href:
                                        if href.startswith('http'):
                                            product_url = href
                                        elif href.startswith('/'):
                                            # Extract base URL from search_url
                                            from urllib.parse import urlparse
                                            parsed = urlparse(search_url)
                                            product_url = f"{parsed.scheme}://{parsed.netloc}{href}"
                                
                                return {
                                    'price': price,
                                    'url': product_url,
                                    'source': 'search',
                                    'scraping_method': 'search',
                                    'confidence': self._calculate_confidence('search', 'search', price)
                                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error scraping search results: {e}")
            return None
    
    async def get_product_pricing(
        self,
        supplier_config: Dict[str, Any],
        product_name: str,
        supplier_name: str = None,
        pricing_url: Optional[str] = None,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Get product pricing from supplier
        
        Returns:
            {
                'success': bool,
                'price': float,
                'currency': str,
                'source': str,  # 'web_scraper', 'known_pricing', 'cached'
                'product_name': str,
                'supplier': str
            }
        """
        try:
            product_name = product_name.strip()
            
            # If pricing_url is provided, try direct scraping first
            if pricing_url:
                price = await self._scrape_product_page(pricing_url)
                if price:
                    import json
                    config = supplier_config if isinstance(supplier_config, dict) else json.loads(supplier_config) if supplier_config else {}
                    currency = config.get('currency', 'GBP')
                    return {
                        'success': True,
                        'price': price,
                        'currency': currency,
                        'source': 'pricing_url',
                        'product_name': product_name,
                        'supplier': supplier_name or 'Unknown',
                        'url': pricing_url,
                        'scraping_method': 'direct_url',
                        'confidence': self._calculate_confidence('pricing_url', 'direct_url', price),
                        'scraping_metadata': {}
                    }
            
            # Try to scrape pricing using supplier configuration
            pricing_result = await self.scrape_supplier_pricing(supplier_config, product_name, supplier_name)
            
            if pricing_result and pricing_result.get('price'):
                return {
                    'success': True,
                    'price': pricing_result['price'],
                    'currency': pricing_result.get('currency', 'GBP'),
                    'source': pricing_result.get('source', 'web_scraper'),
                    'product_name': product_name,
                    'supplier': supplier_name,
                    'url': pricing_result.get('url'),
                    'scraping_method': pricing_result.get('scraping_method', 'search'),
                    'confidence': pricing_result.get('confidence', 0.7),
                    'scraping_metadata': pricing_result.get('scraping_metadata', {})
                }
            else:
                return {
                    'success': False,
                    'error': 'Pricing not found - no configuration or scraping failed',
                    'product_name': product_name,
                    'supplier': supplier_name or 'Unknown'
                }
                
        except Exception as e:
            logger.error(f"Error getting product price: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'product_name': product_name,
                'supplier': supplier_name or 'Unknown'
            }
    
    async def close(self):
        """Close the HTTP session"""
        await self.close()


