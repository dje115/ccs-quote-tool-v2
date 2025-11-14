#!/usr/bin/env python3
"""
Web Pricing Scraper Service
Migrated from v1 with multi-tenant support
Scrapes real-time pricing from supplier websites
"""

import re
import logging
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class WebPricingScraper:
    """Scraper for getting real-time pricing from supplier websites"""
    
    def __init__(self):
        self.session = httpx.AsyncClient(
            timeout=30.0,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        
        # Define scraping rules for different suppliers
        self.scraping_rules = {
            'ubiquiti': {
                'base_url': 'https://www.ui.com',
                'search_url': 'https://www.ui.com/products/search',
                'price_selectors': [
                    '.price',
                    '.price-value',
                    '[data-testid="price"]',
                    '.product-price',
                    '.price-current'
                ],
                'product_selectors': [
                    '.product-card',
                    '.product-item',
                    '.search-result-item'
                ],
                'name_selectors': [
                    '.product-title',
                    '.product-name',
                    'h3',
                    'h4'
                ]
            },
            'cisco': {
                'base_url': 'https://www.cisco.com',
                'search_url': 'https://www.cisco.com/c/en_uk/products/wireless/index.html',
                'price_selectors': [
                    '.price',
                    '.product-price',
                    '.price-value'
                ],
                'product_selectors': [
                    '.product-item',
                    '.product-card'
                ],
                'name_selectors': [
                    '.product-title',
                    '.product-name'
                ]
            },
            'connectix': {
                'base_url': 'https://www.connectixcables.com',
                'search_url': 'https://www.connectixcables.com/products',
                'price_selectors': [
                    '.price',
                    '.product-price',
                    '.woocommerce-Price-amount'
                ],
                'product_selectors': [
                    '.product',
                    '.woocommerce-loop-product__link'
                ],
                'name_selectors': [
                    '.product-title',
                    '.woocommerce-loop-product__title'
                ]
            }
        }
        
        # Known pricing for common products (fallback)
        self.known_prices = {
            'u6-pro': 125.00,
            'u6-lite': 89.00,
            'u6-lr': 179.00,
            'u6-enterprise': 279.00,
            'u7-pro': 167.62,
            'u7-pro-max': 279.00,
            'g5-bullet': 179.00,
            'g5-dome': 179.00,
            'g5-flex': 89.00,
            'dream-machine': 279.00,
            'dream-machine-pro': 379.00,
            'nvr-pro': 399.00
        }
    
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
    
    async def scrape_ubiquiti_pricing(self, product_name: str) -> Optional[Dict[str, Any]]:
        """Scrape pricing from Ubiquiti website"""
        try:
            # Clean product name for search
            search_terms = product_name.lower().replace('ubiquiti', '').replace('unifi', '').strip()
            
            # Try direct product URL first (common products)
            direct_urls = {
                'u6-pro': 'https://www.ui.com/products/u6-pro',
                'u6-lite': 'https://www.ui.com/products/u6-lite',
                'u6-lr': 'https://www.ui.com/products/u6-lr',
                'u6-enterprise': 'https://www.ui.com/products/u6-enterprise',
                'dream-machine': 'https://www.ui.com/products/dream-machine',
                'dream-machine-pro': 'https://www.ui.com/products/dream-machine-pro'
            }
            
            for key, url in direct_urls.items():
                if key in search_terms:
                    price = await self._scrape_product_page(url)
                    if price:
                        return {
                            'price': price,
                            'url': url,
                            'source': 'ubiquiti_direct'
                        }
            
            # Use known pricing for common UniFi products
            for key, known_price in self.known_prices.items():
                if key in search_terms:
                    return {
                        'price': known_price,
                        'url': None,
                        'source': 'known_pricing'
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error scraping Ubiquiti pricing: {e}")
            return None
    
    async def _scrape_product_page(self, url: str) -> Optional[float]:
        """Scrape price from a product page"""
        try:
            response = await self.session.get(url)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try multiple price selectors
            price_selectors = [
                '.price',
                '.price-value',
                '[data-testid="price"]',
                '.product-price',
                '.price-current',
                '[class*="price"]'
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
            logger.error(f"Error scraping product page {url}: {e}")
            return None
    
    async def scrape_supplier_pricing(self, supplier_name: str, product_name: str) -> Optional[Dict[str, Any]]:
        """Main method to scrape pricing from any supplier"""
        supplier_name_lower = supplier_name.lower()
        
        if 'ubiquiti' in supplier_name_lower or 'unifi' in supplier_name_lower:
            return await self.scrape_ubiquiti_pricing(product_name)
        elif 'cisco' in supplier_name_lower:
            # TODO: Implement Cisco scraping
            return None
        elif 'connectix' in supplier_name_lower:
            # TODO: Implement Connectix scraping
            return None
        else:
            logger.warning(f"No scraping rules defined for supplier: {supplier_name}")
            return None
    
    async def get_product_pricing(
        self,
        supplier_name: str,
        product_name: str,
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
            supplier_name = supplier_name.strip()
            product_name = product_name.strip()
            
            # Try to scrape pricing
            pricing_result = await self.scrape_supplier_pricing(supplier_name, product_name)
            
            if pricing_result and pricing_result.get('price'):
                return {
                    'success': True,
                    'price': pricing_result['price'],
                    'currency': 'GBP',
                    'source': pricing_result.get('source', 'web_scraper'),
                    'product_name': product_name,
                    'supplier': supplier_name,
                    'url': pricing_result.get('url')
                }
            else:
                return {
                    'success': False,
                    'error': 'Pricing not found',
                    'product_name': product_name,
                    'supplier': supplier_name
                }
                
        except Exception as e:
            logger.error(f"Error getting product price: {e}")
            return {
                'success': False,
                'error': str(e),
                'product_name': product_name,
                'supplier': supplier_name
            }
    
    async def close(self):
        """Close the HTTP session"""
        await self.session.aclose()


