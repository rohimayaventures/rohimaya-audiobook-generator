"""
Billing API Routes - AuthorFlow Studios

REST endpoints for subscription management.

Endpoints:
- POST /billing/create-checkout-session - Create Stripe Checkout
- POST /billing/create-portal-session - Create Stripe Billing Portal
- GET /billing/me - Get current user's billing info
- GET /billing/plans - Get available plans info
"""

import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Depends, Request
from pydantic import BaseModel, Field

from api.auth import get_current_user
from api.database import db
from .entitlements import (
    get_plan_entitlements,
    get_all_plans_display_info,
    get_plan_display_info,
    PlanId,
)
from .stripe_client import (
    get_or_create_stripe_customer,
    create_checkout_session,
    create_billing_portal_session,
    get_price_id_for_plan,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["Billing"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class CreateCheckoutSessionRequest(BaseModel):
    """Request to create a Stripe Checkout session"""
    plan_id: str = Field(
        ...,
        description="Plan to subscribe to: 'creator', 'author_pro', or 'publisher'"
    )
    billing_period: str = Field(
        default="monthly",
        description="Billing period: 'monthly' or 'yearly'"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "plan_id": "author_pro",
                "billing_period": "monthly"
            }
        }


# =============================================================================
# FREE TRIAL CONFIGURATION
# =============================================================================
# Trial days per plan (for new subscribers only, not returning users)
# These are applied via subscription_data.trial_period_days in checkout session
PLAN_TRIAL_DAYS = {
    "creator": 7,       # Creator: 7-day free trial
    "author_pro": 14,   # Author Pro: 14-day free trial
    "publisher": 14,    # Publisher: 14-day free trial
}


def get_trial_days_for_plan(plan_id: str) -> int:
    """Get the trial period in days for a given plan."""
    return PLAN_TRIAL_DAYS.get(plan_id, 7)  # Default 7 days if plan not found


class CheckoutSessionResponse(BaseModel):
    """Response containing Stripe Checkout URL"""
    url: str
    session_id: str


class PortalSessionResponse(BaseModel):
    """Response containing Stripe Billing Portal URL"""
    url: str


class UsageInfo(BaseModel):
    """User's usage for the current billing period"""
    projects_created: int = 0
    minutes_generated: int = 0
    period_start: Optional[str] = None
    period_end: Optional[str] = None


class TrialInfo(BaseModel):
    """Trial information for a subscription"""
    is_trialing: bool = False
    trial_start: Optional[str] = None
    trial_end: Optional[str] = None
    trial_days_remaining: Optional[int] = None


class BillingInfoResponse(BaseModel):
    """Current user's billing information"""
    plan_id: str
    plan_name: Optional[str] = None
    status: str
    billing_interval: str = "monthly"  # "monthly" or "yearly"
    current_period_end: Optional[str] = None
    cancel_at_period_end: bool = False
    entitlements: Dict[str, Any]
    is_admin: bool = False
    stripe_customer_id: Optional[str] = None
    usage: Optional[UsageInfo] = None
    trial: Optional[TrialInfo] = None


class PlansResponse(BaseModel):
    """Available subscription plans"""
    plans: Dict[str, Dict[str, Any]]


# =============================================================================
# BILLING ENDPOINTS
# =============================================================================

@router.post(
    "/create-checkout-session",
    response_model=CheckoutSessionResponse,
    summary="Create Stripe Checkout Session",
)
async def create_checkout(
    request: CreateCheckoutSessionRequest,
    user_id: str = Depends(get_current_user),
) -> CheckoutSessionResponse:
    """
    Create a Stripe Checkout session for subscription signup.

    The user will be redirected to Stripe's hosted checkout page.
    On successful payment, they'll be redirected back to the success URL.

    Requires authentication.
    """
    # Validate plan_id
    valid_plans = ["creator", "author_pro", "publisher"]
    if request.plan_id not in valid_plans:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid plan_id. Must be one of: {valid_plans}"
        )

    # Get user info from database
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    email = user.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has no email address"
        )

    # Get or create Stripe customer
    billing = db.get_user_billing(user_id)
    existing_customer_id = billing.get("stripe_customer_id") if billing else None

    try:
        customer_id = get_or_create_stripe_customer(
            supabase_user_id=user_id,
            email=email,
            name=user.get("display_name"),
            existing_customer_id=existing_customer_id,
        )
    except Exception as e:
        logger.error(f"Failed to create Stripe customer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create payment customer"
        )

    # Save customer ID to database
    db.upsert_user_billing(user_id, {"stripe_customer_id": customer_id})

    # Get price ID for the plan
    try:
        price_id = get_price_id_for_plan(request.plan_id, request.billing_period)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

    # Build URLs
    base_url = os.getenv(
        "FRONTEND_URL",
        "https://authorflowstudios.rohimayapublishing.com"
    )
    success_url = f"{base_url}/billing/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{base_url}/billing/cancel"

    # Check if user has ever had a subscription (no trial for returning users)
    has_previous_subscription = billing and billing.get("stripe_subscription_id")
    trial_days = get_trial_days_for_plan(request.plan_id) if not has_previous_subscription else None

    # Create checkout session with free trial for new subscribers
    try:
        session = create_checkout_session(
            customer_id=customer_id,
            price_id=price_id,
            success_url=success_url,
            cancel_url=cancel_url,
            supabase_user_id=user_id,
            trial_days=trial_days,
        )
    except Exception as e:
        logger.error(f"Failed to create checkout session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )

    return CheckoutSessionResponse(
        url=session["url"],
        session_id=session["id"],
    )


@router.post(
    "/create-portal-session",
    response_model=PortalSessionResponse,
    summary="Create Stripe Billing Portal Session",
)
async def create_portal(
    user_id: str = Depends(get_current_user),
) -> PortalSessionResponse:
    """
    Create a Stripe Billing Portal session.

    The portal allows users to:
    - Update payment method
    - View invoices
    - Cancel subscription
    - Change plan

    Requires authentication and an existing Stripe customer.
    """
    # Get user's billing info
    billing = db.get_user_billing(user_id)

    if not billing or not billing.get("stripe_customer_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No billing account found. Please subscribe first."
        )

    customer_id = billing["stripe_customer_id"]

    # Build return URL
    base_url = os.getenv(
        "FRONTEND_URL",
        "https://authorflowstudios.rohimayapublishing.com"
    )
    return_url = f"{base_url}/billing"

    try:
        session = create_billing_portal_session(
            customer_id=customer_id,
            return_url=return_url,
        )
    except Exception as e:
        logger.error(f"Failed to create portal session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create billing portal session"
        )

    return PortalSessionResponse(url=session["url"])


@router.get(
    "/me",
    response_model=BillingInfoResponse,
    summary="Get Current Billing Info",
)
async def get_billing_info(
    user_id: str = Depends(get_current_user),
) -> BillingInfoResponse:
    """
    Get the current user's billing information and entitlements.

    Returns:
    - Current plan ID
    - Subscription status
    - Period end date
    - Feature entitlements
    - Admin status

    Requires authentication.
    """
    # Check if user is admin via Supabase metadata
    user = db.get_user(user_id)
    is_admin = False
    if user:
        user_metadata = user.get("user_metadata", {}) or {}
        is_admin = user_metadata.get("role") == "admin"

    # If admin, return admin entitlements
    if is_admin:
        entitlements = get_plan_entitlements(PlanId.ADMIN.value)
        return BillingInfoResponse(
            plan_id="admin",
            plan_name="Admin",
            status="active",
            current_period_end=None,
            cancel_at_period_end=False,
            entitlements=entitlements.to_dict(),
            is_admin=True,
            stripe_customer_id=None,
            usage=None,  # Admins have no limits
        )

    # Get billing info from database
    billing = db.get_user_billing(user_id)

    # Get user's usage for the current period
    usage_record = db.get_user_usage_current_period(user_id)
    usage_info = None
    if usage_record:
        usage_info = UsageInfo(
            projects_created=usage_record.get("projects_created", 0),
            minutes_generated=usage_record.get("minutes_generated", 0),
            period_start=str(usage_record.get("period_start")) if usage_record.get("period_start") else None,
            period_end=str(usage_record.get("period_end")) if usage_record.get("period_end") else None,
        )

    if not billing:
        # No billing record - user is on free plan
        entitlements = get_plan_entitlements(PlanId.FREE.value)
        return BillingInfoResponse(
            plan_id="free",
            plan_name="Free",
            status="inactive",
            current_period_end=None,
            cancel_at_period_end=False,
            entitlements=entitlements.to_dict(),
            is_admin=False,
            stripe_customer_id=None,
            usage=usage_info,
        )

    # Get entitlements for their plan
    plan_id = billing.get("plan_id", "free")
    entitlements = get_plan_entitlements(plan_id)

    # Get plan display name
    plan_display = get_plan_display_info(plan_id)
    plan_name = plan_display.get("name", plan_id.title()) if plan_display else plan_id.title()

    # Format period end date
    period_end = billing.get("current_period_end")
    period_end_str = None
    if period_end:
        if isinstance(period_end, datetime):
            period_end_str = period_end.isoformat()
        else:
            period_end_str = str(period_end)

    # Build trial info
    trial_info = None
    status_value = billing.get("status", "inactive")
    trial_end = billing.get("trial_end")
    trial_start = billing.get("trial_start")

    if status_value == "trialing" or trial_end:
        trial_end_dt = None
        trial_start_dt = None

        # Parse trial_end
        if trial_end:
            if isinstance(trial_end, datetime):
                trial_end_dt = trial_end
            else:
                try:
                    trial_end_dt = datetime.fromisoformat(str(trial_end).replace("Z", "+00:00"))
                except:
                    pass

        # Parse trial_start
        if trial_start:
            if isinstance(trial_start, datetime):
                trial_start_dt = trial_start
            else:
                try:
                    trial_start_dt = datetime.fromisoformat(str(trial_start).replace("Z", "+00:00"))
                except:
                    pass

        # Calculate days remaining
        days_remaining = None
        if trial_end_dt:
            now = datetime.utcnow()
            if trial_end_dt.tzinfo:
                # Make now timezone-aware to match
                from datetime import timezone
                now = now.replace(tzinfo=timezone.utc)
            delta = trial_end_dt - now
            days_remaining = max(0, delta.days)

        trial_info = TrialInfo(
            is_trialing=status_value == "trialing",
            trial_start=trial_start_dt.isoformat() if trial_start_dt else None,
            trial_end=trial_end_dt.isoformat() if trial_end_dt else None,
            trial_days_remaining=days_remaining,
        )

    return BillingInfoResponse(
        plan_id=plan_id,
        plan_name=plan_name,
        status=billing.get("status", "inactive"),
        billing_interval=billing.get("billing_interval", "monthly"),
        current_period_end=period_end_str,
        cancel_at_period_end=billing.get("cancel_at_period_end", False),
        entitlements=entitlements.to_dict(),
        is_admin=False,
        stripe_customer_id=billing.get("stripe_customer_id"),
        usage=usage_info,
        trial=trial_info,
    )


@router.get(
    "/plans",
    response_model=PlansResponse,
    summary="Get Available Plans",
)
async def get_plans() -> PlansResponse:
    """
    Get information about available subscription plans.

    This endpoint is public (no authentication required).
    Returns plan names, prices, and feature lists for display.
    """
    plans = get_all_plans_display_info()
    return PlansResponse(plans=plans)
