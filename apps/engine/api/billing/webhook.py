"""
Stripe Webhook Handler - AuthorFlow Studios

Handles incoming Stripe webhook events to sync subscription state.

IMPORTANT - Stripe Product/Price Metadata Setup:
------------------------------------------------
When creating Products and Prices in Stripe Dashboard, add this metadata:

Product metadata:
  - plan_id: "creator" | "author_pro" | "publisher"

Price metadata:
  - plan_id: "creator" | "author_pro" | "publisher"
  - billing_period: "monthly" | "yearly"

The webhook uses price.metadata.plan_id to determine which plan the user subscribed to.

Handled Events:
- checkout.session.completed - User completed checkout
- customer.subscription.created - New subscription created
- customer.subscription.updated - Subscription changed (upgrade/downgrade/renewal)
- customer.subscription.deleted - Subscription canceled/ended
- customer.subscription.trial_will_end - Trial ending in 3 days (for notifications)
- invoice.payment_failed - Payment failed
- invoice.paid - Invoice paid (for tracking)
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, status, Request, Header
import stripe

from api.database import db
from .stripe_client import verify_webhook_signature

# Structured logging for billing events
# Log tags: [BILLING], [WEBHOOK]
logger = logging.getLogger("billing")

router = APIRouter(prefix="/billing", tags=["Billing Webhooks"])


# =============================================================================
# WEBHOOK ENDPOINT
# =============================================================================

@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
    summary="Stripe Webhook Handler",
)
async def handle_stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
):
    """
    Handle incoming Stripe webhook events.

    This endpoint receives events from Stripe and updates our database accordingly.
    It must return 200 OK quickly to prevent Stripe from retrying.

    Security:
    - Verifies webhook signature using STRIPE_WEBHOOK_SECRET
    - Only processes events with valid signatures
    """
    if not stripe_signature:
        logger.warning("Webhook received without Stripe-Signature header")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe-Signature header"
        )

    # Get raw payload
    payload = await request.body()

    # Verify signature
    try:
        event = verify_webhook_signature(payload, stripe_signature)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Webhook signature verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature"
        )
    except ValueError as e:
        logger.error(f"Webhook configuration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook configuration error"
        )

    # Log event type (don't log full payload for security)
    event_type = event["type"]
    event_id = event["id"]
    logger.info(f"Received Stripe webhook: {event_type} (event_id: {event_id})")

    # Route to appropriate handler
    try:
        if event_type == "checkout.session.completed":
            await handle_checkout_completed(event["data"]["object"])
        elif event_type == "customer.subscription.created":
            await handle_subscription_created(event["data"]["object"])
        elif event_type == "customer.subscription.updated":
            await handle_subscription_updated(event["data"]["object"])
        elif event_type == "customer.subscription.deleted":
            await handle_subscription_deleted(event["data"]["object"])
        elif event_type == "customer.subscription.trial_will_end":
            await handle_trial_will_end(event["data"]["object"])
        elif event_type == "invoice.payment_failed":
            await handle_payment_failed(event["data"]["object"])
        elif event_type == "invoice.paid":
            await handle_invoice_paid(event["data"]["object"])
        else:
            logger.info(f"Unhandled webhook event type: {event_type}")
    except Exception as e:
        logger.error(f"Error handling webhook {event_type}: {e}", exc_info=True)
        # Still return 200 to prevent Stripe retries for our errors
        # Log and alert on these errors for manual review

    return {"status": "ok"}


# =============================================================================
# EVENT HANDLERS
# =============================================================================

async def handle_checkout_completed(session: Dict[str, Any]):
    """
    Handle checkout.session.completed event.

    This fires when a user completes the Stripe Checkout flow.
    The subscription may or may not be active yet (depends on payment).
    """
    logger.info(f"Checkout completed: {session['id']}")

    # Get user ID from metadata
    supabase_user_id = session.get("metadata", {}).get("supabase_user_id")
    if not supabase_user_id:
        # Try from subscription metadata
        subscription_id = session.get("subscription")
        if subscription_id:
            subscription = stripe.Subscription.retrieve(subscription_id)
            supabase_user_id = subscription.metadata.get("supabase_user_id")

    if not supabase_user_id:
        logger.error(f"No supabase_user_id found in checkout session {session['id']}")
        return

    # Get customer ID
    customer_id = session.get("customer")

    # Update user_billing with customer ID
    db.upsert_user_billing(supabase_user_id, {
        "stripe_customer_id": customer_id,
        "updated_at": datetime.utcnow(),
    })

    logger.info(f"Linked Stripe customer {customer_id} to user {supabase_user_id}")


async def handle_subscription_created(subscription: Dict[str, Any]):
    """
    Handle customer.subscription.created event.

    This fires when a new subscription is created.
    We extract the plan_id from price metadata and update user_billing.
    """
    subscription_id = subscription["id"]
    customer_id = subscription["customer"]
    status_value = subscription["status"]

    logger.info(f"Subscription created: {subscription_id} (status: {status_value})")

    # Get user ID from subscription metadata
    supabase_user_id = subscription.get("metadata", {}).get("supabase_user_id")

    if not supabase_user_id:
        # Try to find by customer ID in our database
        billing = db.get_user_billing_by_customer(customer_id)
        if billing:
            supabase_user_id = billing.get("user_id")

    if not supabase_user_id:
        logger.error(
            f"Cannot link subscription {subscription_id}: no supabase_user_id found. "
            f"Customer: {customer_id}"
        )
        return

    # Extract plan_id from price metadata
    # subscription.items.data[0].price.metadata.plan_id
    plan_id = extract_plan_id_from_subscription(subscription)

    # Extract billing interval from price
    billing_interval = extract_billing_interval_from_subscription(subscription)

    # Get billing period dates
    current_period_start = datetime.fromtimestamp(subscription["current_period_start"])
    current_period_end = datetime.fromtimestamp(subscription["current_period_end"])

    # Check for trial
    trial_start = None
    trial_end = None
    if subscription.get("trial_start"):
        trial_start = datetime.fromtimestamp(subscription["trial_start"])
    if subscription.get("trial_end"):
        trial_end = datetime.fromtimestamp(subscription["trial_end"])

    # Update user_billing
    db.upsert_user_billing(supabase_user_id, {
        "stripe_customer_id": customer_id,
        "stripe_subscription_id": subscription_id,
        "plan_id": plan_id,
        "billing_interval": billing_interval,
        "status": map_subscription_status(status_value),
        "current_period_start": current_period_start,
        "current_period_end": current_period_end,
        "trial_start": trial_start,
        "trial_end": trial_end,
        "cancel_at_period_end": subscription.get("cancel_at_period_end", False),
        "updated_at": datetime.utcnow(),
    })

    logger.info(
        f"User {supabase_user_id} subscribed to {plan_id} ({billing_interval}) "
        f"(subscription: {subscription_id})"
    )


async def handle_subscription_updated(subscription: Dict[str, Any]):
    """
    Handle customer.subscription.updated event.

    This fires on:
    - Plan changes (upgrade/downgrade)
    - Billing period renewal
    - Trial ending
    - Cancellation scheduled
    """
    subscription_id = subscription["id"]
    customer_id = subscription["customer"]
    status_value = subscription["status"]

    logger.info(f"Subscription updated: {subscription_id} (status: {status_value})")

    # Find user by subscription ID or customer ID
    billing = db.get_user_billing_by_subscription(subscription_id)
    if not billing:
        billing = db.get_user_billing_by_customer(customer_id)

    if not billing:
        logger.error(f"Cannot find user for subscription {subscription_id}")
        return

    supabase_user_id = billing.get("user_id")

    # Extract updated plan_id and billing interval
    plan_id = extract_plan_id_from_subscription(subscription)
    billing_interval = extract_billing_interval_from_subscription(subscription)

    # Get billing period dates
    current_period_start = datetime.fromtimestamp(subscription["current_period_start"])
    current_period_end = datetime.fromtimestamp(subscription["current_period_end"])

    # Check for cancellation
    canceled_at = None
    if subscription.get("canceled_at"):
        canceled_at = datetime.fromtimestamp(subscription["canceled_at"])

    # Update user_billing
    db.upsert_user_billing(supabase_user_id, {
        "plan_id": plan_id,
        "billing_interval": billing_interval,
        "status": map_subscription_status(status_value),
        "current_period_start": current_period_start,
        "current_period_end": current_period_end,
        "cancel_at_period_end": subscription.get("cancel_at_period_end", False),
        "canceled_at": canceled_at,
        "updated_at": datetime.utcnow(),
    })

    logger.info(f"Updated subscription for user {supabase_user_id}: {plan_id} ({billing_interval})")


async def handle_subscription_deleted(subscription: Dict[str, Any]):
    """
    Handle customer.subscription.deleted event.

    This fires when a subscription is fully canceled (not just scheduled).
    We downgrade the user to the free plan.
    """
    subscription_id = subscription["id"]
    customer_id = subscription["customer"]

    logger.info(f"Subscription deleted: {subscription_id}")

    # Find user
    billing = db.get_user_billing_by_subscription(subscription_id)
    if not billing:
        billing = db.get_user_billing_by_customer(customer_id)

    if not billing:
        logger.error(f"Cannot find user for deleted subscription {subscription_id}")
        return

    supabase_user_id = billing.get("user_id")

    # Downgrade to free plan
    db.upsert_user_billing(supabase_user_id, {
        "plan_id": "free",
        "status": "canceled",
        "stripe_subscription_id": None,
        "cancel_at_period_end": False,
        "canceled_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    })

    logger.info(f"User {supabase_user_id} downgraded to free plan (subscription deleted)")


async def handle_trial_will_end(subscription: Dict[str, Any]):
    """
    Handle customer.subscription.trial_will_end event.

    This fires 3 days before a trial ends.
    Use this to send reminder emails to users.
    """
    subscription_id = subscription["id"]
    customer_id = subscription["customer"]
    trial_end = subscription.get("trial_end")

    trial_end_date = None
    if trial_end:
        trial_end_date = datetime.fromtimestamp(trial_end)

    logger.info(
        f"Trial ending soon for subscription {subscription_id}. "
        f"Trial ends: {trial_end_date}"
    )

    # Find user
    billing = db.get_user_billing_by_subscription(subscription_id)
    if not billing:
        billing = db.get_user_billing_by_customer(customer_id)

    if not billing:
        logger.warning(f"Cannot find user for trial_will_end: subscription {subscription_id}")
        return

    supabase_user_id = billing.get("user_id")

    # Update trial_end in database (in case it changed)
    if trial_end_date:
        db.upsert_user_billing(supabase_user_id, {
            "trial_end": trial_end_date,
            "updated_at": datetime.utcnow(),
        })

    logger.info(f"Trial ending soon for user {supabase_user_id}")

    # TODO: Send email notification about trial ending
    # This could integrate with Brevo/SendGrid to notify the user


async def handle_payment_failed(invoice: Dict[str, Any]):
    """
    Handle invoice.payment_failed event.

    This fires when a payment fails (card declined, expired, etc.).
    We update the status to 'past_due' but don't immediately cancel.
    """
    subscription_id = invoice.get("subscription")
    customer_id = invoice.get("customer")

    if not subscription_id:
        logger.info("Payment failed for non-subscription invoice, ignoring")
        return

    logger.warning(f"Payment failed for subscription {subscription_id}")

    # Find user
    billing = db.get_user_billing_by_subscription(subscription_id)
    if not billing:
        billing = db.get_user_billing_by_customer(customer_id)

    if not billing:
        logger.error(f"Cannot find user for failed payment: subscription {subscription_id}")
        return

    supabase_user_id = billing.get("user_id")

    # Update status to past_due
    db.upsert_user_billing(supabase_user_id, {
        "status": "past_due",
        "updated_at": datetime.utcnow(),
    })

    logger.warning(f"User {supabase_user_id} marked as past_due due to payment failure")

    # TODO: Consider sending an email notification to the user


async def handle_invoice_paid(invoice: Dict[str, Any]):
    """
    Handle invoice.paid event.

    This fires when an invoice is successfully paid.
    Useful for tracking and confirming subscription renewals.
    """
    subscription_id = invoice.get("subscription")
    customer_id = invoice.get("customer")
    amount_paid = invoice.get("amount_paid", 0) / 100  # Convert cents to dollars

    logger.info(
        f"Invoice paid: ${amount_paid} for subscription {subscription_id}"
    )

    if not subscription_id:
        return

    # Find user and ensure status is active
    billing = db.get_user_billing_by_subscription(subscription_id)
    if not billing:
        billing = db.get_user_billing_by_customer(customer_id)

    if billing and billing.get("status") != "active":
        supabase_user_id = billing.get("user_id")
        db.upsert_user_billing(supabase_user_id, {
            "status": "active",
            "updated_at": datetime.utcnow(),
        })
        logger.info(f"User {supabase_user_id} status updated to active after payment")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def extract_plan_id_from_subscription(subscription: Dict[str, Any]) -> str:
    """
    Extract plan_id from subscription price metadata.

    Looks at: subscription.items.data[0].price.metadata.plan_id

    Returns:
        Plan ID string, or 'free' if not found
    """
    try:
        items = subscription.get("items", {}).get("data", [])
        if items:
            price = items[0].get("price", {})
            metadata = price.get("metadata", {})
            plan_id = metadata.get("plan_id")
            if plan_id:
                return plan_id

            # Fallback: try product metadata
            product_id = price.get("product")
            if product_id and isinstance(product_id, str):
                try:
                    product = stripe.Product.retrieve(product_id)
                    plan_id = product.metadata.get("plan_id")
                    if plan_id:
                        return plan_id
                except:
                    pass

    except Exception as e:
        logger.error(f"Error extracting plan_id from subscription: {e}")

    logger.warning("Could not extract plan_id from subscription, defaulting to 'free'")
    return "free"


def extract_billing_interval_from_subscription(subscription: Dict[str, Any]) -> str:
    """
    Extract billing interval from subscription price.

    Looks at: subscription.items.data[0].price.recurring.interval

    Returns:
        'monthly' or 'yearly' (maps Stripe's 'month'/'year' to our terms)
    """
    try:
        items = subscription.get("items", {}).get("data", [])
        if items:
            price = items[0].get("price", {})
            recurring = price.get("recurring", {})
            interval = recurring.get("interval")

            if interval == "year":
                return "yearly"
            elif interval == "month":
                return "monthly"

    except Exception as e:
        logger.error(f"Error extracting billing_interval from subscription: {e}")

    # Default to monthly if we can't determine
    return "monthly"


def map_subscription_status(stripe_status: str) -> str:
    """
    Map Stripe subscription status to our internal status.

    Stripe statuses: incomplete, incomplete_expired, trialing, active,
                     past_due, canceled, unpaid, paused

    Our statuses: inactive, active, trialing, past_due, canceled, unpaid
    """
    status_map = {
        "incomplete": "inactive",
        "incomplete_expired": "inactive",
        "trialing": "trialing",
        "active": "active",
        "past_due": "past_due",
        "canceled": "canceled",
        "unpaid": "unpaid",
        "paused": "inactive",
    }
    return status_map.get(stripe_status, "inactive")
