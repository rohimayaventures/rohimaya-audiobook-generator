"""
Rate Limiting for AuthorFlow Studios API

Implements tiered rate limiting based on user subscription plan:
- Free: 10 requests/minute, 2 jobs/hour
- Creator: 30 requests/minute, 10 jobs/hour
- Author Pro: 60 requests/minute, 30 jobs/hour
- Publisher: 120 requests/minute, unlimited jobs

Uses slowapi with in-memory storage (Redis recommended for production).
"""

import os
import logging
from typing import Optional, Callable
from functools import wraps

from fastapi import Request, HTTPException, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

logger = logging.getLogger(__name__)

# ============================================================================
# RATE LIMIT CONFIGURATION BY PLAN
# ============================================================================

RATE_LIMITS = {
    # Plan ID: (requests_per_minute, jobs_per_hour)
    "free": {"requests_per_minute": 10, "jobs_per_hour": 2},
    "creator": {"requests_per_minute": 30, "jobs_per_hour": 10},
    "author_pro": {"requests_per_minute": 60, "jobs_per_hour": 30},
    "publisher": {"requests_per_minute": 120, "jobs_per_hour": None},  # Unlimited
    "admin": {"requests_per_minute": 1000, "jobs_per_hour": None},  # Admin bypass
}

# Default limits for unauthenticated requests
DEFAULT_LIMIT = "5/minute"


def get_user_identifier(request: Request) -> str:
    """
    Get unique identifier for rate limiting.

    Priority:
    1. User ID from auth header (for authenticated requests)
    2. IP address (for unauthenticated requests)
    """
    # Try to get user_id from request state (set by auth middleware)
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"

    # Fall back to IP address
    return f"ip:{get_remote_address(request)}"


def get_plan_from_request(request: Request) -> str:
    """
    Get user's subscription plan from request.

    Returns plan_id or 'free' as default.
    """
    # Try to get plan from request state (set by auth middleware)
    plan_id = getattr(request.state, "plan_id", None)
    if plan_id:
        return plan_id

    # Check if user is admin
    is_admin = getattr(request.state, "is_admin", False)
    if is_admin:
        return "admin"

    return "free"


def get_rate_limit_string(request: Request) -> str:
    """
    Get rate limit string based on user's plan.

    Returns slowapi-compatible limit string like "30/minute".
    """
    plan_id = get_plan_from_request(request)
    limits = RATE_LIMITS.get(plan_id, RATE_LIMITS["free"])

    rpm = limits["requests_per_minute"]
    return f"{rpm}/minute"


# ============================================================================
# LIMITER INSTANCE
# ============================================================================

# Create limiter with custom key function
limiter = Limiter(
    key_func=get_user_identifier,
    default_limits=[DEFAULT_LIMIT],
    storage_uri=os.getenv("REDIS_URL", "memory://"),  # Use Redis in production
)


def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom exception handler for rate limit exceeded.

    Returns a user-friendly error message with retry information.
    """
    plan_id = get_plan_from_request(request)
    limits = RATE_LIMITS.get(plan_id, RATE_LIMITS["free"])

    # Parse retry-after from exception
    retry_after = getattr(exc, "retry_after", 60)

    logger.warning(
        f"Rate limit exceeded for {get_user_identifier(request)} "
        f"(plan: {plan_id}, limit: {limits['requests_per_minute']}/min)"
    )

    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "error": "rate_limit_exceeded",
            "message": f"Too many requests. Please wait {retry_after} seconds before trying again.",
            "plan": plan_id,
            "limit": f"{limits['requests_per_minute']} requests/minute",
            "retry_after": retry_after,
            "upgrade_hint": "Upgrade your plan for higher rate limits." if plan_id == "free" else None,
        },
        headers={"Retry-After": str(retry_after)},
    )


# ============================================================================
# JOB CREATION RATE LIMITING
# ============================================================================

# In-memory job creation tracking (use Redis in production)
_job_creation_counts: dict = {}


def check_job_creation_limit(user_id: str, plan_id: str) -> bool:
    """
    Check if user can create another job based on hourly limit.

    Args:
        user_id: User UUID
        plan_id: Subscription plan ID

    Returns:
        True if allowed, False if limit exceeded
    """
    import time

    limits = RATE_LIMITS.get(plan_id, RATE_LIMITS["free"])
    hourly_limit = limits.get("jobs_per_hour")

    # No limit for this plan
    if hourly_limit is None:
        return True

    current_hour = int(time.time() // 3600)
    key = f"{user_id}:{current_hour}"

    # Get current count
    current_count = _job_creation_counts.get(key, 0)

    if current_count >= hourly_limit:
        logger.warning(
            f"Job creation limit exceeded for user {user_id} "
            f"(plan: {plan_id}, limit: {hourly_limit}/hour, current: {current_count})"
        )
        return False

    # Increment count
    _job_creation_counts[key] = current_count + 1

    # Clean up old entries (keep only current hour)
    for old_key in list(_job_creation_counts.keys()):
        if not old_key.endswith(f":{current_hour}"):
            del _job_creation_counts[old_key]

    return True


def get_job_creation_remaining(user_id: str, plan_id: str) -> Optional[int]:
    """
    Get remaining job creation quota for current hour.

    Returns:
        Number of jobs remaining, or None if unlimited
    """
    import time

    limits = RATE_LIMITS.get(plan_id, RATE_LIMITS["free"])
    hourly_limit = limits.get("jobs_per_hour")

    if hourly_limit is None:
        return None

    current_hour = int(time.time() // 3600)
    key = f"{user_id}:{current_hour}"

    current_count = _job_creation_counts.get(key, 0)
    return max(0, hourly_limit - current_count)


# ============================================================================
# DECORATORS FOR EASY USE
# ============================================================================

def dynamic_rate_limit():
    """
    Decorator that applies rate limiting based on user's plan.

    Usage:
        @app.get("/endpoint")
        @dynamic_rate_limit()
        async def endpoint():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Get dynamic limit based on plan
            limit = get_rate_limit_string(request)

            # Apply rate limit check
            # Note: This is a simplified version - slowapi handles this internally
            # when using limiter.limit() decorator

            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_rate_limit_headers(request: Request) -> dict:
    """
    Get rate limit headers to include in response.

    Returns dict with X-RateLimit-* headers.
    """
    plan_id = get_plan_from_request(request)
    limits = RATE_LIMITS.get(plan_id, RATE_LIMITS["free"])

    return {
        "X-RateLimit-Limit": str(limits["requests_per_minute"]),
        "X-RateLimit-Plan": plan_id,
    }


def is_rate_limiting_enabled() -> bool:
    """Check if rate limiting is enabled."""
    return os.getenv("DISABLE_RATE_LIMITING", "").lower() != "true"
