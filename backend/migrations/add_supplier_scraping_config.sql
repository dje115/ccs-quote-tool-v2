-- Migration: Add supplier scraping configuration
-- Date: 2025-11-16
-- Description: Adds scraping configuration fields to suppliers table for flexible, tenant-specific scraping rules

-- Add scraping configuration fields to suppliers table
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS scraping_config JSONB DEFAULT '{}'::jsonb;
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS scraping_enabled BOOLEAN DEFAULT TRUE;
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS scraping_method VARCHAR(50) DEFAULT 'generic'; -- 'generic', 'api', 'custom'

-- Scraping config JSON structure:
-- {
--   "base_url": "https://example.com",
--   "search_url_template": "https://example.com/search?q={query}",
--   "product_url_template": "https://example.com/products/{product_code}",
--   "price_selectors": [".price", ".price-value", "[data-price]"],
--   "product_selectors": [".product-item", ".product-card"],
--   "name_selectors": [".product-title", "h3"],
--   "search_result_selector": ".search-result",
--   "pagination_selector": ".pagination a",
--   "requires_auth": false,
--   "auth_config": {},
--   "rate_limit_ms": 1000,
--   "custom_headers": {},
--   "price_extraction_regex": null,
--   "currency": "GBP"
-- }

CREATE INDEX IF NOT EXISTS idx_suppliers_scraping_enabled ON suppliers(scraping_enabled) WHERE scraping_enabled = TRUE;

COMMENT ON COLUMN suppliers.scraping_config IS 'JSON configuration for web scraping: selectors, URLs, authentication, etc.';
COMMENT ON COLUMN suppliers.scraping_method IS 'Scraping method: generic (web scraping), api (API-based), custom (custom implementation)';
COMMENT ON COLUMN suppliers.scraping_enabled IS 'Whether web scraping is enabled for this supplier';


