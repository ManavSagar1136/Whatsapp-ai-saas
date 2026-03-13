-- Iteration 3: Relational Migrations & Analytics Expansion

-- 1. Create relational table for services (moving away from businesses JSONB)
CREATE TABLE business_services (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID REFERENCES businesses(id) ON DELETE CASCADE,
    service_name VARCHAR NOT NULL,
    duration_minutes INT NOT NULL DEFAULT 60,
    price NUMERIC DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS for multi-tenant safety
ALTER TABLE business_services ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tenant Isolation: Services" ON business_services
    FOR ALL USING (auth.uid() = business_id);

-- Add Index for fast lookups during LLM context building
CREATE INDEX idx_business_services_bid ON business_services(business_id);

-- 2. Expand Analytics Warehouse with new metrics
ALTER TABLE analytics_daily
ADD COLUMN new_customers INT DEFAULT 0,
ADD COLUMN repeat_customers INT DEFAULT 0,
ADD COLUMN conversion_rate NUMERIC DEFAULT 0.00;
