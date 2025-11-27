"""
AuthorFlow Studios - Billing Module

Stripe subscription integration for the AuthorFlow platform.

Components:
- entitlements.py: Plan definitions and entitlements mapping
- stripe_client.py: Stripe SDK wrapper and helpers
- routes.py: FastAPI billing endpoints
- webhook.py: Stripe webhook handler
"""

from .entitlements import (
    PLAN_ENTITLEMENTS,
    get_plan_entitlements,
    PlanId,
    Entitlements,
)
from .stripe_client import (
    get_stripe_client,
    get_or_create_stripe_customer,
    create_checkout_session,
    create_billing_portal_session,
)
from .routes import router as billing_router

__all__ = [
    # Entitlements
    "PLAN_ENTITLEMENTS",
    "get_plan_entitlements",
    "PlanId",
    "Entitlements",
    # Stripe client
    "get_stripe_client",
    "get_or_create_stripe_customer",
    "create_checkout_session",
    "create_billing_portal_session",
    # Router
    "billing_router",
]
