-- =============================================================================
-- AUTHORFLOW STUDIOS - BILLING SCHEMA (STRIPE INTEGRATION)
-- =============================================================================
-- Run this SQL in your Supabase Dashboard → SQL Editor
-- This creates the user_billing table for subscription management
-- =============================================================================

-- =============================================================================
-- USER_BILLING TABLE
-- Stores Stripe subscription info linked to Supabase users
-- =============================================================================
CREATE TABLE IF NOT EXISTS user_billing (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Stripe identifiers
    stripe_customer_id TEXT UNIQUE,
    stripe_subscription_id TEXT,

    -- Plan information
    -- "free", "creator", "author_pro", "publisher", or "admin" (admin is set via metadata)
    plan_id TEXT NOT NULL DEFAULT 'free',

    -- Subscription status
    -- "inactive", "active", "trialing", "past_due", "canceled", "unpaid"
    status TEXT NOT NULL DEFAULT 'inactive',

    -- Billing period
    current_period_start TIMESTAMP WITH TIME ZONE,
    current_period_end TIMESTAMP WITH TIME ZONE,

    -- Cancellation tracking
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    canceled_at TIMESTAMP WITH TIME ZONE,

    -- Trial tracking (optional)
    trial_start TIMESTAMP WITH TIME ZONE,
    trial_end TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_user_billing_user_id ON user_billing(user_id);
CREATE INDEX IF NOT EXISTS idx_user_billing_stripe_customer_id ON user_billing(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_user_billing_status ON user_billing(status);

-- =============================================================================
-- AUTO-UPDATE TRIGGER FOR updated_at
-- =============================================================================
DROP TRIGGER IF EXISTS update_user_billing_updated_at ON user_billing;
CREATE TRIGGER update_user_billing_updated_at
    BEFORE UPDATE ON user_billing
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- ROW LEVEL SECURITY (RLS)
-- =============================================================================
ALTER TABLE user_billing ENABLE ROW LEVEL SECURITY;

-- Users can only view their own billing info
CREATE POLICY "Users can view their own billing"
    ON user_billing FOR SELECT
    USING (auth.uid() = user_id);

-- Users can insert their own billing (for initial creation)
CREATE POLICY "Users can insert their own billing"
    ON user_billing FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Service role can do everything (for webhook updates)
-- Note: service_role bypasses RLS automatically

-- =============================================================================
-- GRANT PERMISSIONS
-- =============================================================================
GRANT ALL ON user_billing TO authenticated;
GRANT ALL ON user_billing TO service_role;

-- =============================================================================
-- USAGE TRACKING TABLE (Optional - for enforcing monthly limits)
-- =============================================================================
CREATE TABLE IF NOT EXISTS user_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Usage period (monthly)
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Usage counters
    projects_created INTEGER DEFAULT 0,
    total_minutes_generated INTEGER DEFAULT 0,
    total_characters_processed BIGINT DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Unique constraint per user per period
    UNIQUE(user_id, period_start)
);

CREATE INDEX IF NOT EXISTS idx_user_usage_user_id ON user_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_user_usage_period ON user_usage(period_start, period_end);

ALTER TABLE user_usage ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own usage"
    ON user_usage FOR SELECT
    USING (auth.uid() = user_id);

GRANT ALL ON user_usage TO authenticated;
GRANT ALL ON user_usage TO service_role;

-- =============================================================================
-- DONE!
-- =============================================================================
-- Next steps:
-- 1. Add Stripe env vars to Railway (backend)
-- 2. Add Stripe publishable key to Vercel (frontend)
-- 3. Create products/prices in Stripe Dashboard with proper metadata
-- 4. Configure webhook endpoint in Stripe Dashboard
-- =============================================================================
