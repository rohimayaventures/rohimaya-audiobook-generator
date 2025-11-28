# AuthorFlow Studios - Billing Testing Guide

This document provides test procedures for the billing system.

## Prerequisites

1. Stripe test mode enabled (Dashboard toggle to "Test")
2. Test API keys configured (`sk_test_...`)
3. Test price IDs configured for all plans
4. Webhook endpoint configured and receiving events

## Test Cards

Use these Stripe test card numbers:

| Card Number | Description |
|-------------|-------------|
| `4242 4242 4242 4242` | Succeeds |
| `4000 0000 0000 0341` | Attaching fails |
| `4000 0000 0000 9995` | Charge is declined |
| `4000 0027 6000 3184` | Requires authentication (3DS) |

- Expiry: Any future date (e.g., 12/25)
- CVC: Any 3 digits (e.g., 123)
- ZIP: Any 5 digits (e.g., 12345)

## Test Scenarios

### 1. Monthly Creator Trial

**Steps:**
1. Create a new account or use one that never had a subscription
2. Go to `/pricing`
3. Ensure "Monthly" is selected (default)
4. Click "Start 7-day free trial" on Creator plan
5. Complete Stripe Checkout with test card `4242 4242 4242 4242`

**Expected Results:**
- Redirected to `/billing/success`
- Dashboard shows:
  - Plan badge: "Creator"
  - Trial badge: "Trial: 7 days left"
- `/billing` page shows:
  - Status: "You are on a free trial with 7 days remaining"
  - Interval badge: "Monthly"
- Database `user_billing`:
  - `plan_id`: "creator"
  - `billing_interval`: "monthly"
  - `status`: "trialing"
  - `trial_start` and `trial_end` populated

**Webhook Events:**
- `checkout.session.completed`
- `customer.subscription.created` (status: "trialing")

---

### 2. Yearly Author Pro Trial

**Steps:**
1. Create a new account
2. Go to `/pricing`
3. Toggle to "Yearly"
4. Verify "2 months free" badge appears
5. Click "Start 14-day free trial" on Author Pro plan
6. Complete Stripe Checkout

**Expected Results:**
- Dashboard shows:
  - Plan badge: "Author Pro"
  - Trial badge: "Trial: 14 days left"
  - Interval badge: "Annual"
- `/billing` page shows yearly pricing info
- Database:
  - `billing_interval`: "yearly"
  - `status`: "trialing"

---

### 3. Returning User (No Trial)

**Steps:**
1. Use an account that previously had a subscription
2. Go to `/pricing`
3. Select any plan
4. Complete checkout

**Expected Results:**
- NO trial period
- Charged immediately
- Status: "active" (not "trialing")

---

### 4. Trial Expiration Blocking

**Steps:**
1. In Supabase, manually set a user's `trial_end` to past date
2. Set `status` to "past_due" or "canceled"
3. Try to create a new audiobook job

**Expected Results:**
- Job creation blocked with 403 error
- Error message: "Your subscription is {status}. Please update your payment method..."

---

### 5. Upgrade from Monthly to Yearly

**Steps:**
1. Subscribe to Creator monthly
2. Wait for subscription to be active
3. Click "Manage Subscription" on `/billing`
4. In Stripe Portal, upgrade to yearly

**Expected Results:**
- `billing_interval` updates to "yearly"
- Prorated charge applied
- `/billing` shows "Annual" badge

---

### 6. Cancel Subscription

**Steps:**
1. Subscribe to any plan
2. Go to `/billing`
3. Click "Manage Subscription"
4. Cancel in Stripe Portal

**Expected Results:**
- `cancel_at_period_end`: true
- Dashboard shows "Your subscription will end on {date}"
- User keeps access until period end
- After period ends:
  - `status`: "canceled"
  - `plan_id`: "free"

---

### 7. Payment Failure

**Steps:**
1. Subscribe with card `4000 0000 0000 0341` (card that fails to attach)
2. Or use `4000 0000 0000 9995` (charge declined)

**Expected Results:**
- Checkout fails or subscription goes to `past_due`
- Webhook `invoice.payment_failed` fires
- User marked as `past_due` in database
- Job creation blocked

---

### 8. Trial Will End Notification

**Note:** This event fires 3 days before trial ends. For testing:

1. In Stripe Dashboard → Developers → Webhooks
2. Click your webhook endpoint
3. Click "Send test webhook"
4. Select `customer.subscription.trial_will_end`
5. Send

**Expected Results:**
- Webhook logs show event processed
- `trial_end` updated in database (if changed)
- TODO: Email notification sent (not yet implemented)

---

## Database Verification

Check `user_billing` table in Supabase:

```sql
SELECT
  user_id,
  plan_id,
  billing_interval,
  status,
  trial_start,
  trial_end,
  current_period_end,
  cancel_at_period_end
FROM user_billing
WHERE user_id = '<USER_UUID>';
```

## Webhook Testing with Stripe CLI

```bash
# Install Stripe CLI
# Mac: brew install stripe/stripe-cli/stripe
# Windows: scoop install stripe

# Login
stripe login

# Forward webhooks to local server
stripe listen --forward-to localhost:8000/billing/webhook

# Trigger specific events
stripe trigger checkout.session.completed
stripe trigger customer.subscription.created
stripe trigger customer.subscription.updated
stripe trigger invoice.payment_failed
```

## Troubleshooting

### Webhook not received
1. Check endpoint URL is correct in Stripe Dashboard
2. Verify `STRIPE_WEBHOOK_SECRET` matches
3. Check Railway logs for 400/500 errors

### Trial not applied
1. Verify user never had a previous subscription
2. Check `trial_period_days` in checkout session logs
3. Verify PLAN_TRIAL_DAYS configuration

### Wrong billing interval
1. Check price's `recurring.interval` in Stripe
2. Verify webhook handler extracts interval correctly
3. Check database `billing_interval` column exists

### User stuck on free
1. Check webhook logs for errors
2. Verify price has `plan_id` metadata
3. Check `user_billing` row exists
