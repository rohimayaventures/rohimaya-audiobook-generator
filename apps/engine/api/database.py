"""
Supabase Database Integration
Handles database operations (jobs, job_files)
Storage is handled by Cloudflare R2 (see storage_r2.py)
"""

import os
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client

# Import R2 storage client
from .storage_r2 import r2

logger = logging.getLogger(__name__)

# Load environment variables (only for local development)
# In production (Railway), env vars are set directly
env_path = Path(__file__).parent.parent.parent.parent / "env" / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)


class SupabaseDB:
    """Wrapper for Supabase database operations (storage moved to R2)"""

    def __init__(self):
        """Initialize Supabase client for database only"""
        self.url = os.getenv("SUPABASE_URL")
        self.service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not self.url or not self.service_role_key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in environment")

        # Use service role key for backend operations (bypasses RLS)
        self.client: Client = create_client(self.url, self.service_role_key)

        # Storage now handled by R2 (imported above)
        self.storage = r2

    # ========================================================================
    # JOB OPERATIONS
    # ========================================================================

    def create_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new job in the database

        Args:
            job_data: Job metadata (user_id, title, mode, etc.)

        Returns:
            Created job record with ID

        Raises:
            Exception: If database operation fails
        """
        try:
            result = self.client.table("jobs").insert(job_data).execute()
            if not result.data:
                logger.error(f"create_job: No data returned from insert")
                raise Exception("Failed to create job: no data returned")
            return result.data[0]
        except Exception as e:
            logger.error(f"create_job failed: {e}")
            raise

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job by ID

        Args:
            job_id: Job UUID

        Returns:
            Job record or None if not found
        """
        try:
            result = self.client.table("jobs").select("*").eq("id", job_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"get_job({job_id}) failed: {e}")
            raise

    def get_user_jobs(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get all jobs for a user

        Args:
            user_id: User UUID
            status: Optional status filter (pending, processing, completed, failed)
            limit: Number of jobs to return
            offset: Pagination offset

        Returns:
            List of job records
        """
        try:
            query = self.client.table("jobs").select("*").eq("user_id", user_id)

            if status:
                query = query.eq("status", status)

            query = query.order("created_at", desc=True).limit(limit).offset(offset)

            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"get_user_jobs({user_id}) failed: {e}")
            raise

    def update_job(self, job_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update job fields

        Args:
            job_id: Job UUID
            updates: Dictionary of fields to update

        Returns:
            Updated job record

        Raises:
            Exception: If database operation fails
        """
        try:
            result = self.client.table("jobs").update(updates).eq("id", job_id).execute()
            if not result.data:
                logger.warning(f"update_job({job_id}): No data returned from update")
                return None
            return result.data[0]
        except Exception as e:
            logger.error(f"update_job({job_id}) failed: {e}")
            raise

    def delete_job(self, job_id: str) -> bool:
        """
        Delete job (also deletes job_files via CASCADE)

        Args:
            job_id: Job UUID

        Returns:
            True if deleted successfully
        """
        result = self.client.table("jobs").delete().eq("id", job_id).execute()
        return len(result.data) > 0

    # ========================================================================
    # JOB FILE OPERATIONS
    # ========================================================================

    def create_job_file(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a job_file record (for chunk/chapter tracking)

        Args:
            file_data: File metadata (job_id, file_type, audio_path, etc.)

        Returns:
            Created file record
        """
        result = self.client.table("job_files").insert(file_data).execute()
        return result.data[0] if result.data else None

    def get_job_files(self, job_id: str) -> List[Dict[str, Any]]:
        """
        Get all files for a job

        Args:
            job_id: Job UUID

        Returns:
            List of job_file records
        """
        result = self.client.table("job_files").select("*").eq("job_id", job_id).order("part_number").execute()
        return result.data if result.data else []

    # ========================================================================
    # STORAGE OPERATIONS (Delegated to R2)
    # ========================================================================

    def upload_manuscript(
        self,
        user_id: str,
        filename: str,
        file_content: bytes,
        job_id: Optional[str] = None
    ) -> str:
        """
        Upload manuscript to R2 storage

        Args:
            user_id: User UUID
            filename: Original filename
            file_content: File bytes
            job_id: Optional job ID for organization

        Returns:
            R2 object key (e.g., "manuscripts/user123/book.txt")
        """
        return self.storage.upload_manuscript(user_id, filename, file_content, job_id)

    def download_manuscript(self, object_key: str) -> bytes:
        """
        Download manuscript from R2 storage

        Args:
            object_key: R2 object key

        Returns:
            File content as bytes
        """
        return self.storage.download_manuscript(object_key)

    def upload_audiobook(
        self,
        user_id: str,
        job_id: str,
        filename: str,
        file_content: bytes
    ) -> str:
        """
        Upload generated audiobook to R2 storage

        Args:
            user_id: User UUID
            job_id: Job UUID
            filename: Audio filename
            file_content: Audio file bytes

        Returns:
            R2 object key (e.g., "audiobooks/user123/job456/final.mp3")
        """
        return self.storage.upload_audiobook(user_id, job_id, filename, file_content)

    def get_download_url(self, object_key: str, expires_in: int = 3600) -> str:
        """
        Get presigned download URL for audiobook from R2

        Args:
            object_key: R2 object key
            expires_in: URL expiration time in seconds (default 1 hour)

        Returns:
            Presigned download URL
        """
        return self.storage.generate_presigned_url(object_key, expires_in)

    def delete_storage_file(self, bucket_type: str, object_key: str) -> bool:
        """
        Delete file from R2 storage

        Args:
            bucket_type: "manuscripts" or "audiobooks"
            object_key: R2 object key

        Returns:
            True if deleted successfully
        """
        if bucket_type == "manuscripts":
            return self.storage.delete_manuscript(object_key)
        elif bucket_type == "audiobooks":
            return self.storage.delete_audiobook(object_key)
        else:
            logger.error(f"delete_storage_file: Unknown bucket type: {bucket_type}")
            return False

    # ========================================================================
    # USER OPERATIONS
    # ========================================================================

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user info from Supabase Auth

        Args:
            user_id: User UUID

        Returns:
            User data including email, display_name, user_metadata
        """
        try:
            response = self.client.auth.admin.get_user_by_id(user_id)
            if response and response.user:
                user = response.user
                return {
                    "id": user.id,
                    "email": user.email,
                    "display_name": user.user_metadata.get("display_name") if user.user_metadata else None,
                    "user_metadata": user.user_metadata,
                    "created_at": str(user.created_at) if user.created_at else None,
                }
            return None
        except Exception as e:
            logger.error(f"get_user({user_id}) failed: {e}")
            return None

    # ========================================================================
    # USER BILLING OPERATIONS
    # ========================================================================

    def get_user_billing(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user billing record

        Args:
            user_id: User UUID

        Returns:
            Billing record or None if not found
        """
        result = self.client.table("user_billing").select("*").eq("user_id", user_id).execute()
        return result.data[0] if result.data else None

    def get_user_billing_by_customer(self, stripe_customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user billing record by Stripe customer ID

        Args:
            stripe_customer_id: Stripe customer ID

        Returns:
            Billing record or None if not found
        """
        result = self.client.table("user_billing").select("*").eq("stripe_customer_id", stripe_customer_id).execute()
        return result.data[0] if result.data else None

    def get_user_billing_by_subscription(self, stripe_subscription_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user billing record by Stripe subscription ID

        Args:
            stripe_subscription_id: Stripe subscription ID

        Returns:
            Billing record or None if not found
        """
        result = self.client.table("user_billing").select("*").eq("stripe_subscription_id", stripe_subscription_id).execute()
        return result.data[0] if result.data else None

    def upsert_user_billing(self, user_id: str, billing_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create or update user billing record

        Args:
            user_id: User UUID
            billing_data: Billing data to upsert

        Returns:
            Upserted billing record
        """
        # Add user_id to data
        billing_data["user_id"] = user_id

        # Check if record exists
        existing = self.get_user_billing(user_id)

        if existing:
            # Update existing record
            result = self.client.table("user_billing").update(billing_data).eq("user_id", user_id).execute()
        else:
            # Insert new record
            result = self.client.table("user_billing").insert(billing_data).execute()

        return result.data[0] if result.data else None

    # ========================================================================
    # USER USAGE OPERATIONS (for limit enforcement)
    # ========================================================================

    def get_user_usage_current_period(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user's usage for the current billing period

        Args:
            user_id: User UUID

        Returns:
            Usage record for current month or None
        """
        from datetime import datetime, timedelta

        # Current month boundaries
        now = datetime.utcnow()
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        result = self.client.table("user_usage").select("*").eq(
            "user_id", user_id
        ).gte(
            "period_start", period_start.isoformat()
        ).execute()

        return result.data[0] if result.data else None

    def increment_user_usage(self, user_id: str, projects: int = 0, minutes: int = 0) -> Dict[str, Any]:
        """
        Increment user's usage counters

        Args:
            user_id: User UUID
            projects: Number of projects to add
            minutes: Number of minutes to add

        Returns:
            Updated usage record
        """
        from datetime import datetime

        # Get or create current period usage
        usage = self.get_user_usage_current_period(user_id)

        now = datetime.utcnow()
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Calculate period end (last day of month at 23:59:59)
        if now.month == 12:
            period_end = period_start.replace(year=now.year + 1, month=1) - timedelta(seconds=1)
        else:
            period_end = period_start.replace(month=now.month + 1) - timedelta(seconds=1)

        if usage:
            # Update existing
            new_projects = usage.get("projects_created", 0) + projects
            new_minutes = usage.get("total_minutes_generated", 0) + minutes

            result = self.client.table("user_usage").update({
                "projects_created": new_projects,
                "total_minutes_generated": new_minutes,
                "updated_at": datetime.utcnow().isoformat(),
            }).eq("id", usage["id"]).execute()
        else:
            # Create new
            result = self.client.table("user_usage").insert({
                "user_id": user_id,
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "projects_created": projects,
                "total_minutes_generated": minutes,
            }).execute()

        return result.data[0] if result.data else None

    # ========================================================================
    # GOOGLE DRIVE TOKEN OPERATIONS
    # ========================================================================

    def get_google_drive_tokens(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user's Google Drive OAuth tokens

        Args:
            user_id: User UUID

        Returns:
            Token data or None if not found
        """
        try:
            result = self.client.table("google_drive_tokens").select("*").eq("user_id", user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"get_google_drive_tokens({user_id}) failed: {e}")
            return None

    def store_google_drive_tokens(self, user_id: str, tokens: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Store or update user's Google Drive OAuth tokens

        Args:
            user_id: User UUID
            tokens: Token data (access_token, refresh_token, expires_in, token_type)

        Returns:
            Stored token record
        """
        try:
            from datetime import datetime

            token_data = {
                "user_id": user_id,
                "access_token": tokens.get("access_token"),
                "refresh_token": tokens.get("refresh_token"),
                "token_type": tokens.get("token_type", "Bearer"),
                "expires_in": tokens.get("expires_in"),
                "updated_at": datetime.utcnow().isoformat(),
            }

            # Check if exists
            existing = self.get_google_drive_tokens(user_id)

            if existing:
                # Update existing - preserve refresh_token if not provided
                if not token_data.get("refresh_token") and existing.get("refresh_token"):
                    token_data["refresh_token"] = existing["refresh_token"]

                result = self.client.table("google_drive_tokens").update(token_data).eq("user_id", user_id).execute()
            else:
                result = self.client.table("google_drive_tokens").insert(token_data).execute()

            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"store_google_drive_tokens({user_id}) failed: {e}")
            return None

    def clear_google_drive_tokens(self, user_id: str) -> bool:
        """
        Delete user's Google Drive OAuth tokens

        Args:
            user_id: User UUID

        Returns:
            True if deleted successfully
        """
        try:
            self.client.table("google_drive_tokens").delete().eq("user_id", user_id).execute()
            return True
        except Exception as e:
            logger.error(f"clear_google_drive_tokens({user_id}) failed: {e}")
            return False


# Global database instance (lazy initialization)
_db_instance: SupabaseDB = None


def get_db() -> SupabaseDB:
    """Get or create database instance (lazy initialization)"""
    global _db_instance
    if _db_instance is None:
        _db_instance = SupabaseDB()
    return _db_instance


# Backwards compatible alias
class _LazyDB:
    """Lazy proxy for SupabaseDB to maintain backwards compatibility"""
    def __getattr__(self, name):
        return getattr(get_db(), name)


db = _LazyDB()
