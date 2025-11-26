"""
Supabase Database Integration
Handles database operations (jobs, job_files)
Storage is handled by Cloudflare R2 (see storage_r2.py)
"""

import os
from typing import Dict, Any, List, Optional
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Import R2 storage client
from .storage_r2 import r2

# Load environment variables
env_path = Path(__file__).parent.parent.parent.parent / "env" / ".env"
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
        """
        result = self.client.table("jobs").insert(job_data).execute()
        return result.data[0] if result.data else None

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job by ID

        Args:
            job_id: Job UUID

        Returns:
            Job record or None if not found
        """
        result = self.client.table("jobs").select("*").eq("id", job_id).execute()
        return result.data[0] if result.data else None

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
        query = self.client.table("jobs").select("*").eq("user_id", user_id)

        if status:
            query = query.eq("status", status)

        query = query.order("created_at", desc=True).limit(limit).offset(offset)

        result = query.execute()
        return result.data if result.data else []

    def update_job(self, job_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update job fields

        Args:
            job_id: Job UUID
            updates: Dictionary of fields to update

        Returns:
            Updated job record
        """
        result = self.client.table("jobs").update(updates).eq("id", job_id).execute()
        return result.data[0] if result.data else None

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
            print(f"❌ Unknown bucket type: {bucket_type}")
            return False


# Global database instance
db = SupabaseDB()
