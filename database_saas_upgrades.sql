-- SaaS Database Upgrades (Run these on top of the original schema)

-- 1. Ensure businesses link to Supabase Auth Users for Multi-Tenancy Protection
-- Replace the old businesses id column definition if initializing fresh:
-- id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,

-- 2. Enable Row Level Security (RLS) for SaaS Safety
ALTER TABLE businesses ENABLE ROW LEVEL SECURITY;
ALTER TABLE appointments ENABLE ROW LEVEL SECURITY;
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;

-- 3. RLS Policies
-- A business can only select and update its own settings row
CREATE POLICY "Business row visibility" ON businesses 
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Business row update" ON businesses 
    FOR UPDATE USING (auth.uid() = id);

-- A business can only view and manage appointments linked to its ID
CREATE POLICY "Appointment isolation" ON appointments 
    FOR ALL USING (auth.uid() = business_id);

-- 4. Analytics Data Warehouse Table
CREATE TABLE analytics_daily (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID REFERENCES businesses(id) ON DELETE CASCADE,
    metric_date DATE NOT NULL,
    total_conversations INT DEFAULT 0,
    appointments_booked INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(business_id, metric_date) -- Prevent duplicate aggregations per day
);

-- Protect Analytics with RLS too
ALTER TABLE analytics_daily ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Analytics isolation" ON analytics_daily
    FOR SELECT USING (auth.uid() = business_id);

-- Add Index for fast Dashboard queries
CREATE INDEX idx_analytics_business_date ON analytics_daily(business_id, metric_date DESC);
