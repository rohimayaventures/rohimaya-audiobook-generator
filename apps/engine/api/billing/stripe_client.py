"""
Stripe Client - AuthorFlow Studios

Wrapper around Stripe SDK for subscription management.

Environment Variables Required:
- STRIPE_SECRET_KEY: Stripe secret key (sk_live_... or sk_test_...)
- STRIPE_PRICE_CREATOR_MONTHLY: Price ID for Creator plan
- STRIPE_PRICE_AUTHORPRO_MONTHLY: Price ID for Author Pro plan
- STRIPE_PRICE_PUBLISHER_MONTHLY: Price ID for Publisher plan

Optional:
- STRIPE_PRICE_CREATOR_YEARLY: Yearly price for Creator
- STRIPE_PRICE_AUTHORPRO_YEARLY: Yearly price for Author Pro
- STRIPE_PRICE_PUBLISHER_YEARLY: Yearly price for Publisher
"""

import os
import logging
from typing import Optional, Dict, Any

import stripe

logger = logging.getLogger(__name__)

# =============================================================================
# STRIPE CLIENT SETUP
# =============================================================================

def get_stripe_client() -> stripe:
    """
    Initialize and return the Stripe client.

    The client is configured with the STRIPE_SECRET_KEY environment variable.
    This function is idempotent - it's safe to call multiple times.
    """
    api_key = os.getenv("STRIPE_SECRET_KEY")
    if not api_key:
        raise ValueError(
            "STRIPE_SECRET_KEY environment variable is not set. "
            "Please configure it in Railway environment variables."
        )

    stripe.api_key = api_key
    return stripe


# =============================================================================
# PRICE ID MAPPING
# =============================================================================

def get_price_id_for_plan(plan_id: str, billing_period: str = "monthly") -> str:
    """
    Get the Stripe Price ID for a plan.

    Args:
        plan_id: Plan identifier ("creator", "author_pro", "publisher")
        billing_period: "monthly" or "yearly"

    Returns:
        Stripe Price ID

    Raises:
        ValueError: If plan_id is invalid or price not configured
    """
    # Build environment variable name
    plan_key = plan_id.upper().replace("-", "_")
    period_suffix = billing_period.upper()

    env_var = f"STRIPE_PRICE_{plan_key}_{period_suffix}"
    price_id = os.getenv(env_var)

    if not price_id:
        # Try without period suffix for backwards compatibility
        env_var_legacy = f"STRIPE_PRICE_{plan_key}_MONTHLY"
        price_id = os.getenv(env_var_legacy)

    if not price_id:
        raise ValueError(
            f"No Stripe Price ID configured for plan '{plan_id}' ({billing_period}). "
            f"Please set {env_var} in environment variables."
        )

    return price_id


# Mapping of plan IDs to env var names (for documentation)
PRICE_ENV_VARS = {
    "creator": "STRIPE_PRICE_CREATOR_MONTHLY",
    "author_pro": "STRIPE_PRICE_AUTHORPRO_MONTHLY",
    "publisher": "STRIPE_PRICE_PUBLISHER_MONTHLY",
}


# =============================================================================
# CUSTOMER MANAGEMENT
# =============================================================================

def get_or_create_stripe_customer(
    supabase_user_id: str,
    email: str,
    name: Optional[str] = None,
    existing_customer_id: Optional[str] = None,
) -> str:
    """
    Get existing Stripe customer or create a new one.

    Args:
        supabase_user_id: Supabase user UUID (stored in customer metadata)
        email: User's email address
        name: User's display name (optional)
        existing_customer_id: If we already have a customer ID, verify it exists

    Returns:
        Stripe customer ID (cus_...)

    The supabase_user_id is stored in the customer's metadata so we can
    link webhook events back to the correct user.
    """
    client = get_stripe_client()

    # If we have an existing customer ID, verify it exists
    if existing_customer_id:
        try:
            customer = client.Customer.retrieve(existing_customer_id)
            if not customer.deleted:
                logger.info(f"Found existing Stripe customer: {existing_customer_id}")
                return existing_customer_id
        except stripe.error.InvalidRequestError:
            logger.warning(f"Existing customer {existing_customer_id} not found, creating new")

    # Search for existing customer by metadata
    try:
        customers = client.Customer.search(
            query=f'metadata["supabase_user_id"]:"{supabase_user_id}"',
            limit=1
        )
        if customers.data:
            customer = customers.data[0]
            logger.info(f"Found Stripe customer by metadata: {customer.id}")
            return customer.id
    except Exception as e:
        logger.warning(f"Customer search failed: {e}")

    # Search by email as fallback
    try:
        customers = client.Customer.list(email=email, limit=1)
        if customers.data:
            customer = customers.data[0]
            # Update metadata if missing
            if not customer.metadata.get("supabase_user_id"):
                client.Customer.modify(
                    customer.id,
                    metadata={"supabase_user_id": supabase_user_id}
                )
            logger.info(f"Found Stripe customer by email: {customer.id}")
            return customer.id
    except Exception as e:
        logger.warning(f"Customer search by email failed: {e}")

    # Create new customer
    customer = client.Customer.create(
        email=email,
        name=name,
        metadata={
            "supabase_user_id": supabase_user_id,
            "platform": "authorflow_studios",
        }
    )

    logger.info(f"Created new Stripe customer: {customer.id}")
    return customer.id


# =============================================================================
# CHECKOUT SESSION
# =============================================================================

def create_checkout_session(
    customer_id: str,
    price_id: str,
    success_url: str,
    cancel_url: str,
    supabase_user_id: str,
    trial_days: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Create a Stripe Checkout session for subscription signup.

    Args:
        customer_id: Stripe customer ID
        price_id: Stripe Price ID
        success_url: URL to redirect on successful payment
        cancel_url: URL to redirect if user cancels
        supabase_user_id: User ID for metadata
        trial_days: Optional trial period in days

    Returns:
        Dict with 'id' (session ID) and 'url' (checkout URL)
    """
    client = get_stripe_client()

    session_params = {
        "customer": customer_id,
        "mode": "subscription",
        "line_items": [
            {
                "price": price_id,
                "quantity": 1,
            }
        ],
        "success_url": success_url,
        "cancel_url": cancel_url,
        "metadata": {
            "supabase_user_id": supabase_user_id,
        },
        "subscription_data": {
            "metadata": {
                "supabase_user_id": supabase_user_id,
            }
        },
        # Allow promotion codes
        "allow_promotion_codes": True,
        # Collect billing address
        "billing_address_collection": "auto",
    }

    # Add trial if specified
    if trial_days and trial_days > 0:
        session_params["subscription_data"]["trial_period_days"] = trial_days

    session = client.checkout.Session.create(**session_params)

    logger.info(f"Created checkout session: {session.id} for customer {customer_id}")

    return {
        "id": session.id,
        "url": session.url,
    }


# =============================================================================
# BILLING PORTAL
# =============================================================================

def create_billing_portal_session(
    customer_id: str,
    return_url: str,
) -> Dict[str, Any]:
    """
    Create a Stripe Billing Portal session.

    The billing portal allows users to:
    - Update payment method
    - View invoices
    - Cancel subscription
    - Change plan (if configured in Stripe Dashboard)

    Args:
        customer_id: Stripe customer ID
        return_url: URL to return to after portal session

    Returns:
        Dict with 'id' and 'url'
    """
    client = get_stripe_client()

    session = client.billing_portal.Session.create(
        customer=customer_id,
        return_url=return_url,
    )

    logger.info(f"Created portal session for customer {customer_id}")

    return {
        "id": session.id,
        "url": session.url,
    }


# =============================================================================
# SUBSCRIPTION HELPERS
# =============================================================================

def get_subscription(subscription_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a subscription by ID.

    Args:
        subscription_id: Stripe subscription ID

    Returns:
        Subscription object or None if not found
    """
    client = get_stripe_client()

    try:
        subscription = client.Subscription.retrieve(subscription_id)
        return subscription
    except stripe.error.InvalidRequestError:
        return None


def cancel_subscription(
    subscription_id: str,
    at_period_end: bool = True
) -> Dict[str, Any]:
    """
    Cancel a subscription.

    Args:
        subscription_id: Stripe subscription ID
        at_period_end: If True, cancel at end of billing period.
                       If False, cancel immediately.

    Returns:
        Updated subscription object
    """
    client = get_stripe_client()

    if at_period_end:
        subscription = client.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True
        )
    else:
        subscription = client.Subscription.cancel(subscription_id)

    logger.info(
        f"Canceled subscription {subscription_id} "
        f"(at_period_end={at_period_end})"
    )

    return subscription


def get_customer_subscriptions(customer_id: str) -> list:
    """
    Get all subscriptions for a customer.

    Args:
        customer_id: Stripe customer ID

    Returns:
        List of subscription objects
    """
    client = get_stripe_client()

    subscriptions = client.Subscription.list(
        customer=customer_id,
        status="all",
        limit=10
    )

    return subscriptions.data


# =============================================================================
# WEBHOOK SIGNATURE VERIFICATION
# =============================================================================

def verify_webhook_signature(
    payload: bytes,
    sig_header: str,
) -> stripe.Event:
    """
    Verify a Stripe webhook signature and construct the event.

    Args:
        payload: Raw request body bytes
        sig_header: Stripe-Signature header value

    Returns:
        Verified Stripe Event object

    Raises:
        stripe.error.SignatureVerificationError: If signature is invalid
    """
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    if not webhook_secret:
        raise ValueError(
            "STRIPE_WEBHOOK_SECRET environment variable is not set. "
            "Please configure it in Railway environment variables."
        )

    event = stripe.Webhook.construct_event(
        payload, sig_header, webhook_secret
    )

    return event
