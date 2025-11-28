# AuthorFlow Studios - Billing Integration Guide

This document explains how to set up and configure Stripe billing for AuthorFlow Studios.

## Table of Contents

1. [Overview](#overview)
2. [Environment Variables](#environment-variables)
3. [Stripe Dashboard Setup](#stripe-dashboard-setup)
4. [Plan ID Mapping](#plan-id-mapping)
5. [Webhook Configuration](#webhook-configuration)
6. [Admin Users](#admin-users)
7. [Database Tables](#database-tables)
8. [API Endpoints](#api-endpoints)
9. [Troubleshooting](#troubleshooting)

---

## Overview

AuthorFlow Studios uses Stripe for subscription billing with monthly and yearly intervals. Free trials are configured per-plan and applied via the Stripe Checkout API.

### Subscription Plans

| Plan | Monthly | Yearly | Trial | Projects/Month | Max Minutes/Book |
|------|---------|--------|-------|----------------|------------------|
| Free | $0 | - | - | 1 | 5 |
| Creator | $29/mo | $290/yr | 7 days | 3 | 60 |
| Author Pro | $79/mo | $790/yr | 14 days | Unlimited | 360 |
| Publisher | $249/mo | $2,490/yr | 14 days | Unlimited | Unlimited |

### Yearly Savings
- **Creator**: Save $58/year (~2 months free)
- **Author Pro**: Save $158/year (~2 months free)
- **Publisher**: Save $498/year (~2 months free)

---

## Environment Variables

### Required (Backend - Railway)

```bash
# Stripe API Keys
STRIPE_SECRET_KEY=sk_live_...  # or sk_test_... for development

# Stripe Price IDs (get these after creating products)
# NOTE: Use AUTHOR_PRO with underscore, not AUTHORPRO
STRIPE_PRICE_CREATOR_MONTHLY=price_...
STRIPE_PRICE_AUTHOR_PRO_MONTHLY=price_...
STRIPE_PRICE_PUBLISHER_MONTHLY=price_...

# Yearly Price IDs (required for yearly billing)
STRIPE_PRICE_CREATOR_YEARLY=price_...
STRIPE_PRICE_AUTHOR_PRO_YEARLY=price_...
STRIPE_PRICE_PUBLISHER_YEARLY=price_...

# Webhook Secret (get this after creating webhook endpoint)
STRIPE_WEBHOOK_SECRET=whsec_...
```

### Frontend (Vercel)

```bash
NEXT_PUBLIC_API_URL=https://your-engine.railway.app
```

---

## Free Trials

### Configuration

Free trials are set via `subscription_data.trial_period_days` in the Stripe Checkout session (NOT on the Stripe price object):

```python
# apps/engine/api/billing/routes.py
PLAN_TRIAL_DAYS = {
    "creator": 7,       # 7-day trial
    "author_pro": 14,   # 14-day trial
    "publisher": 14,    # 14-day trial
}
```

### Trial Rules

1. **New subscribers only** - Users who previously had a subscription don't get another trial
2. **Full access** - Users on trial have full plan entitlements
3. **Automatic billing** - Stripe charges the card when trial ends
4. **Trial badge** - Dashboard shows trial days remaining

### Webhook Events

| Event | When It Fires |
|-------|--------------|
| `customer.subscription.created` | When trial starts (status="trialing") |
| `customer.subscription.trial_will_end` | 3 days before trial ends |
| `customer.subscription.updated` | When trial ends (status changes to "active" or "past_due") |

---

## Stripe Dashboard Setup

### Step 1: Create Products

Go to **Stripe Dashboard → Products** and create 3 products:

#### Creator Plan
- **Name**: Creator
- **Description**: Perfect for indie authors
- **Metadata**: Add key `plan_id` with value `creator`

#### Author Pro Plan
- **Name**: Author Pro
- **Description**: For serious authors
- **Metadata**: Add key `plan_id` with value `author_pro`

#### Publisher Plan
- **Name**: Publisher
- **Description**: For publishers & production houses
- **Metadata**: Add key `plan_id` with value `publisher`

### Step 2: Create Prices

For each product, create a recurring price:

| Product | Monthly Price | Billing Period |
|---------|--------------|----------------|
| Creator | $29.00 | Monthly |
| Author Pro | $79.00 | Monthly |
| Publisher | $249.00 | Monthly |

**Important**: Each price also needs the `plan_id` metadata matching its product.

### Step 3: Copy Price IDs

After creating prices, copy the Price ID (starts with `price_`) for each and add to your environment variables.

---

## Plan ID Mapping

The system uses `plan_id` metadata on Stripe prices to map to internal plans:

| Stripe Metadata `plan_id` | Internal Plan | Features |
|---------------------------|---------------|----------|
| `creator` | Creator | 3 projects, 60 min, Findaway |
| `author_pro` | Author Pro | Unlimited, 6 hrs, dual voice |
| `publisher` | Publisher | Unlimited, team access |

### How It Works

1. User clicks "Subscribe" on pricing page
2. Frontend calls `/billing/create-checkout-session` with `plan_id`
3. Backend looks up Price ID from environment variable
4. User completes Stripe Checkout
5. Webhook receives `checkout.session.completed`
6. Webhook reads `plan_id` from subscription's price metadata
7. User's `user_billing.plan_id` is updated

---

## Webhook Configuration

### Step 1: Create Webhook Endpoint

Go to **Stripe Dashboard → Developers → Webhooks** and add endpoint:

- **URL**: `https://your-engine.railway.app/billing/webhook`
- **Events to listen for**:
  - `checkout.session.completed`
  - `customer.subscription.created`
  - `customer.subscription.updated`
  - `customer.subscription.deleted`
  - `invoice.payment_failed`
  - `invoice.paid`

### Step 2: Copy Webhook Secret

After creating the endpoint, click on it and reveal the **Signing secret** (starts with `whsec_`). Add this to your environment as `STRIPE_WEBHOOK_SECRET`.

### Step 3: Test Webhooks

Use Stripe CLI for local testing:

```bash
stripe listen --forward-to localhost:8000/billing/webhook
```

Or trigger test events from the Dashboard:
1. Go to your webhook endpoint
2. Click "Send test webhook"
3. Select an event type and send

---

## Admin Users

Admin users bypass all billing restrictions and have full access to all features.

### Setting Up an Admin User

1. Go to **Supabase Dashboard → Authentication → Users**
2. Find the user you want to make admin
3. Click on the user to view details
4. Edit the **User Metadata** (raw_user_meta_data) to add:

```json
{
  "role": "admin"
}
```

### How Admin Detection Works

The billing routes check for admin status:

```python
# In routes.py
user_metadata = user.user_metadata or {}
if user_metadata.get("role") == "admin":
    # Return admin entitlements, skip billing checks
```

Admin users:
- See "Admin" as their plan on the dashboard
- Have unlimited projects and minutes
- Can access all features
- Don't need a Stripe subscription

---

## Database Tables

### user_billing

Tracks subscription status for each user.

```sql
CREATE TABLE user_billing (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    stripe_customer_id TEXT UNIQUE,
    stripe_subscription_id TEXT,
    plan_id TEXT DEFAULT 'free',
    status TEXT DEFAULT 'inactive',
    current_period_start TIMESTAMP WITH TIME ZONE,
    current_period_end TIMESTAMP WITH TIME ZONE,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### user_usage

Tracks usage for limit enforcement.

```sql
CREATE TABLE user_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    projects_created INTEGER DEFAULT 0,
    minutes_generated INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Running Migrations

Apply the billing schema to your Supabase database:

```bash
# Using Supabase CLI
supabase db push

# Or run the SQL directly in Supabase Dashboard → SQL Editor
# Copy contents of supabase-billing-schema.sql
```

---

## API Endpoints

### Public Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/billing/plans` | GET | List available plans |
| `/billing/webhook` | POST | Stripe webhook handler |

### Authenticated Endpoints

All require `Authorization: Bearer <access_token>` header.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/billing/me` | GET | Get current user's billing info |
| `/billing/create-checkout-session` | POST | Start Stripe Checkout |
| `/billing/create-portal-session` | POST | Access Billing Portal |

### Request/Response Examples

#### Create Checkout Session

```bash
POST /billing/create-checkout-session
Authorization: Bearer eyJhbGc...

{
  "plan_id": "author_pro",
  "billing_period": "monthly"
}
```

Response:
```json
{
  "checkout_url": "https://checkout.stripe.com/..."
}
```

#### Get Billing Info

```bash
GET /billing/me
Authorization: Bearer eyJhbGc...
```

Response:
```json
{
  "plan_id": "author_pro",
  "plan_name": "Author Pro",
  "status": "active",
  "current_period_end": "2024-02-15T00:00:00Z",
  "cancel_at_period_end": false,
  "entitlements": {
    "max_projects_per_month": null,
    "max_minutes_per_book": 360,
    "findaway_package": true,
    "dual_voice": true,
    ...
  }
}
```

---

## Troubleshooting

### "STRIPE_SECRET_KEY not set"

Ensure the environment variable is set in Railway:
1. Go to Railway Dashboard → your service
2. Click Variables
3. Add `STRIPE_SECRET_KEY` with your Stripe secret key

### "No Stripe Price ID configured for plan"

You haven't set the price ID environment variable:
1. Get the Price ID from Stripe Dashboard → Products → (your product) → Pricing
2. Add to Railway as `STRIPE_PRICE_{PLAN}_MONTHLY` (e.g., `STRIPE_PRICE_CREATOR_MONTHLY`)

### Webhooks Not Working

1. Check the webhook endpoint URL is correct
2. Verify `STRIPE_WEBHOOK_SECRET` is set correctly
3. Check Railway logs for webhook errors
4. Use Stripe Dashboard → Webhooks → (your endpoint) → View logs

### User Stuck on Free Tier

1. Check Stripe Dashboard for their subscription status
2. Verify the price has `plan_id` metadata set
3. Check `user_billing` table in Supabase for their record
4. Review webhook logs for errors

### Testing in Development

Use Stripe test mode:
1. Toggle to "Test mode" in Stripe Dashboard
2. Use test API keys (start with `sk_test_`)
3. Use test card numbers: `4242 4242 4242 4242`

---

## Security Notes

1. **Never expose `STRIPE_SECRET_KEY`** in frontend code
2. **Always verify webhook signatures** before processing
3. **Check subscription status** before granting access to features
4. **Use Stripe's test mode** for development
5. **Regularly audit** the `user_billing` table for anomalies
