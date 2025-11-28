-- Migration: Add product image support
-- Date: 2025-11-16
-- Description: Adds image fields to products table for MinIO-hosted product galleries

-- Add image fields to products table
ALTER TABLE products ADD COLUMN IF NOT EXISTS image_url VARCHAR(500);
ALTER TABLE products ADD COLUMN IF NOT EXISTS image_path VARCHAR(500);  -- MinIO object path
ALTER TABLE products ADD COLUMN IF NOT EXISTS image_bucket VARCHAR(100) DEFAULT 'ccs-quote-tool';
ALTER TABLE products ADD COLUMN IF NOT EXISTS gallery_images JSONB DEFAULT '[]'::jsonb;  -- Array of image paths for gallery

-- Add index for image_path for faster lookups
CREATE INDEX IF NOT EXISTS idx_products_image_path ON products(image_path) WHERE image_path IS NOT NULL;

-- Comments
COMMENT ON COLUMN products.image_url IS 'Public URL or presigned URL for primary product image';
COMMENT ON COLUMN products.image_path IS 'MinIO object path for primary product image';
COMMENT ON COLUMN products.image_bucket IS 'MinIO bucket name where images are stored';
COMMENT ON COLUMN products.gallery_images IS 'JSON array of additional image paths for product gallery';






