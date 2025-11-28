-- =============================================================================
-- Migration: Add billing_interval column to user_billing
-- =============================================================================
-- This migration adds support for tracking monthly vs yearly billing intervals
--
-- Run this SQL in your Supabase Dashboard > SQL Editor BEFORE deploying
-- =============================================================================

-- Add billing_interval column (defaults to 'monthly' for existing users)
ALTER TABLE user_billing
ADD COLUMN IF NOT EXISTS billing_interval TEXT DEFAULT 'monthly';

-- Add a check constraint for valid values
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'user_billing_interval_check'
    ) THEN
        ALTER TABLE user_billing
        ADD CONSTRAINT user_billing_interval_check
        CHECK (billing_interval IN ('monthly', 'yearly'));
    END IF;
END
$$;

-- Update comment on the table
COMMENT ON COLUMN user_billing.billing_interval IS 'Billing interval: monthly or yearly';

-- =============================================================================
-- END OF MIGRATION
-- =============================================================================
