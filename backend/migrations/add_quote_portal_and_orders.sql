-- Add show_in_customer_portal field to quotes table
ALTER TABLE quotes 
ADD COLUMN IF NOT EXISTS show_in_customer_portal BOOLEAN NOT NULL DEFAULT FALSE;

-- Create orders table for customer orders
CREATE TABLE IF NOT EXISTS orders (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    customer_id VARCHAR(36) NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    quote_id VARCHAR(36) REFERENCES quotes(id) ON DELETE SET NULL,
    
    -- Order identification
    order_number VARCHAR(100) UNIQUE NOT NULL,
    order_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Order details
    status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- pending, confirmed, processing, shipped, delivered, cancelled
    priority VARCHAR(50) DEFAULT 'normal',  -- low, normal, high, urgent
    
    -- Pricing
    subtotal NUMERIC(12, 2) NOT NULL DEFAULT 0,
    tax_rate NUMERIC(5, 4) DEFAULT 0.20,
    tax_amount NUMERIC(12, 2) NOT NULL DEFAULT 0,
    discount_amount NUMERIC(12, 2) DEFAULT 0,
    total_amount NUMERIC(12, 2) NOT NULL DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'GBP',
    
    -- Shipping
    shipping_address TEXT,
    shipping_postcode VARCHAR(20),
    shipping_method VARCHAR(100),
    shipping_cost NUMERIC(12, 2) DEFAULT 0,
    estimated_delivery_date TIMESTAMP WITH TIME ZONE,
    
    -- Payment
    payment_status VARCHAR(50) DEFAULT 'pending',  -- pending, paid, partial, refunded
    payment_method VARCHAR(100),
    payment_reference VARCHAR(255),
    paid_at TIMESTAMP WITH TIME ZONE,
    
    -- Order items (stored as JSON for flexibility)
    items JSONB,
    
    -- Notes and metadata
    notes TEXT,
    internal_notes TEXT,  -- Internal notes not visible to customer
    order_metadata JSONB,
    
    -- Tracking
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Created by
    created_by VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_orders_tenant_customer ON orders(tenant_id, customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_quote ON orders(quote_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_order_number ON orders(order_number);
CREATE INDEX IF NOT EXISTS idx_orders_order_date ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_orders_is_deleted ON orders(is_deleted) WHERE is_deleted = FALSE;

-- Add comments
COMMENT ON TABLE orders IS 'Customer orders placed from quotes';
COMMENT ON COLUMN orders.status IS 'Order status: pending, confirmed, processing, shipped, delivered, cancelled';
COMMENT ON COLUMN orders.payment_status IS 'Payment status: pending, paid, partial, refunded';
COMMENT ON COLUMN orders.items IS 'JSON array of order items with product details, quantities, and prices';

