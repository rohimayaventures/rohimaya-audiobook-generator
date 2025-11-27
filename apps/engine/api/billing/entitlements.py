"""
Plan Entitlements - AuthorFlow Studios

Defines the entitlements for each subscription plan.
Used throughout the application to check feature access and enforce limits.

Plan IDs (must match Stripe product/price metadata):
- free: Free tier (default for new users)
- creator: Creator plan ($29/mo)
- author_pro: Author Pro plan ($79/mo)
- publisher: Publisher plan ($249/mo)
- admin: Internal admin (full access, no subscription required)
"""

from typing import Dict, Any, Optional, Literal, Union
from dataclasses import dataclass
from enum import Enum


class PlanId(str, Enum):
    """Valid plan identifiers"""
    FREE = "free"
    CREATOR = "creator"
    AUTHOR_PRO = "author_pro"
    PUBLISHER = "publisher"
    ADMIN = "admin"


@dataclass
class Entitlements:
    """Entitlements for a subscription plan"""
    # Project limits
    max_projects_per_month: Union[int, None]  # None = unlimited
    max_minutes_per_book: Union[int, None]  # None = unlimited

    # Feature flags
    findaway_package: bool
    retail_sample: Union[bool, str]  # True, False, "advanced", or "spicy"
    cover_generation: Union[bool, str]  # True, False, "premium", or "banana"
    dual_voice: bool

    # Phase 3 features
    multi_character_voice: bool  # Multi-character voice with auto-detection
    emotional_tts: bool  # Emotional TTS instructions
    google_drive_import: bool  # Import from Google Drive

    # Queue priority
    faster_queue: bool

    # Team features (Publisher+)
    team_members: Union[int, None]  # None = unlimited
    team_access: bool

    # Support level
    support_level: str  # "community", "email", "priority", "dedicated"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "max_projects_per_month": self.max_projects_per_month,
            "max_minutes_per_book": self.max_minutes_per_book,
            "findaway_package": self.findaway_package,
            "retail_sample": self.retail_sample,
            "cover_generation": self.cover_generation,
            "dual_voice": self.dual_voice,
            "multi_character_voice": self.multi_character_voice,
            "emotional_tts": self.emotional_tts,
            "google_drive_import": self.google_drive_import,
            "faster_queue": self.faster_queue,
            "team_members": self.team_members,
            "team_access": self.team_access,
            "support_level": self.support_level,
        }


# =============================================================================
# PLAN ENTITLEMENTS MAPPING
# =============================================================================
# This is the single source of truth for what each plan gets.
# Update this when changing plan features.
# =============================================================================

PLAN_ENTITLEMENTS: Dict[str, Entitlements] = {
    # -------------------------------------------------------------------------
    # FREE TIER
    # - Limited usage for testing the platform
    # - 1 project per month, max 5 minutes
    # -------------------------------------------------------------------------
    PlanId.FREE.value: Entitlements(
        max_projects_per_month=1,
        max_minutes_per_book=5,
        findaway_package=False,
        retail_sample=True,  # Basic retail sample
        cover_generation=False,
        dual_voice=False,
        multi_character_voice=False,
        emotional_tts=False,
        google_drive_import=False,
        faster_queue=False,
        team_members=0,
        team_access=False,
        support_level="community",
    ),

    # -------------------------------------------------------------------------
    # CREATOR TIER ($29/month)
    # - For indie authors getting started
    # - 3 projects per month, up to 60 min each
    # -------------------------------------------------------------------------
    PlanId.CREATOR.value: Entitlements(
        max_projects_per_month=3,
        max_minutes_per_book=60,  # ~1 hour audiobook
        findaway_package=True,
        retail_sample=True,
        cover_generation=True,
        dual_voice=False,
        multi_character_voice=False,
        emotional_tts=True,  # Basic emotional TTS
        google_drive_import=True,
        faster_queue=False,
        team_members=0,
        team_access=False,
        support_level="email",
    ),

    # -------------------------------------------------------------------------
    # AUTHOR PRO TIER ($79/month)
    # - For serious authors with multiple books
    # - Unlimited projects, up to 6 hours each
    # - Dual voice + multi-character support
    # -------------------------------------------------------------------------
    PlanId.AUTHOR_PRO.value: Entitlements(
        max_projects_per_month=None,  # Unlimited
        max_minutes_per_book=360,  # 6 hours
        findaway_package=True,
        retail_sample="spicy",  # AI-powered + spicy sample selection
        cover_generation="premium",  # Higher quality covers
        dual_voice=True,
        multi_character_voice=True,
        emotional_tts=True,
        google_drive_import=True,
        faster_queue=True,
        team_members=0,
        team_access=False,
        support_level="priority",
    ),

    # -------------------------------------------------------------------------
    # PUBLISHER TIER ($249/month)
    # - For publishers and production houses
    # - Unlimited everything + team features
    # -------------------------------------------------------------------------
    PlanId.PUBLISHER.value: Entitlements(
        max_projects_per_month=None,  # Unlimited
        max_minutes_per_book=None,  # Unlimited
        findaway_package=True,
        retail_sample="spicy",  # Full spicy sample features
        cover_generation="banana",  # Premium covers with Banana.dev option
        dual_voice=True,
        multi_character_voice=True,
        emotional_tts=True,
        google_drive_import=True,
        faster_queue=True,
        team_members=5,  # Up to 5 team members
        team_access=True,
        support_level="dedicated",
    ),

    # -------------------------------------------------------------------------
    # ADMIN (Internal use only)
    # - Full access to everything
    # - No subscription required
    # - Set via Supabase user metadata: { "role": "admin" }
    # -------------------------------------------------------------------------
    PlanId.ADMIN.value: Entitlements(
        max_projects_per_month=None,  # Unlimited
        max_minutes_per_book=None,  # Unlimited
        findaway_package=True,
        retail_sample="spicy",
        cover_generation="banana",
        dual_voice=True,
        multi_character_voice=True,
        emotional_tts=True,
        google_drive_import=True,
        faster_queue=True,
        team_members=None,  # Unlimited
        team_access=True,
        support_level="dedicated",
    ),
}


def get_plan_entitlements(plan_id: str) -> Entitlements:
    """
    Get entitlements for a plan ID.

    Args:
        plan_id: Plan identifier (free, creator, author_pro, publisher, admin)

    Returns:
        Entitlements object for the plan

    If plan_id is not recognized, returns FREE tier entitlements.
    """
    return PLAN_ENTITLEMENTS.get(plan_id, PLAN_ENTITLEMENTS[PlanId.FREE.value])


def check_feature_access(plan_id: str, feature: str) -> bool:
    """
    Check if a plan has access to a specific feature.

    Args:
        plan_id: Plan identifier
        feature: Feature name (e.g., "dual_voice", "findaway_package")

    Returns:
        True if the plan has access to the feature
    """
    entitlements = get_plan_entitlements(plan_id)
    value = getattr(entitlements, feature, False)

    # Handle special cases
    if value is None:  # Unlimited
        return True
    if isinstance(value, str):  # "advanced", "premium", etc.
        return True
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value > 0

    return False


def check_limit(plan_id: str, limit_name: str, current_usage: int) -> bool:
    """
    Check if current usage is within plan limits.

    Args:
        plan_id: Plan identifier
        limit_name: Limit attribute name (e.g., "max_projects_per_month")
        current_usage: Current usage count

    Returns:
        True if within limits, False if limit exceeded
    """
    entitlements = get_plan_entitlements(plan_id)
    limit_value = getattr(entitlements, limit_name, 0)

    # None means unlimited
    if limit_value is None:
        return True

    return current_usage < limit_value


# =============================================================================
# PLAN DISPLAY INFO (for frontend)
# =============================================================================

PLAN_DISPLAY_INFO = {
    PlanId.FREE.value: {
        "name": "Free",
        "price_monthly": 0,
        "description": "Try AuthorFlow with limited features",
        "highlight": False,
        "features": [
            "1 audiobook per month",
            "Up to 5 minutes per book",
            "Basic retail sample",
            "Community support",
        ],
    },
    PlanId.CREATOR.value: {
        "name": "Creator",
        "price_monthly": 29,
        "description": "Perfect for indie authors",
        "highlight": False,
        "features": [
            "3 audiobooks per month",
            "Up to 1 hour per book",
            "Findaway-ready packages",
            "AI cover generation",
            "Retail sample selection",
            "Emotional TTS",
            "Google Drive import",
            "Email support",
        ],
    },
    PlanId.AUTHOR_PRO.value: {
        "name": "Author Pro",
        "price_monthly": 79,
        "description": "For serious authors",
        "highlight": True,  # Recommended plan
        "features": [
            "Unlimited audiobooks",
            "Up to 6 hours per book",
            "Dual-voice narration",
            "Multi-character voices",
            "Spicy retail samples",
            "Premium cover generation",
            "Emotional TTS",
            "Priority queue",
            "Priority support",
        ],
    },
    PlanId.PUBLISHER.value: {
        "name": "Publisher",
        "price_monthly": 249,
        "description": "For publishers & production houses",
        "highlight": False,
        "features": [
            "Everything in Author Pro",
            "Unlimited book length",
            "Banana.dev cover generation",
            "Team access (5 members)",
            "Dedicated support",
            "Custom branding options",
            "API access",
        ],
    },
}


def get_plan_display_info(plan_id: str) -> Optional[Dict[str, Any]]:
    """Get display info for a plan (for frontend)"""
    return PLAN_DISPLAY_INFO.get(plan_id)


def get_all_plans_display_info() -> Dict[str, Dict[str, Any]]:
    """Get display info for all plans"""
    return PLAN_DISPLAY_INFO
