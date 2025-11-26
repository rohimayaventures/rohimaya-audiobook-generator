"""
Supabase Database Integration
Handles all database and storage operations
"""

import os
from typing import Dict, Any, List, Optional
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
env_path = Path(__file__).parent.parent.parent.parent / "env" / ".env"
load_dotenv(dotenv_path=env_path)


class SupabaseDB:
    """Wrapper for Supabase database and storage operations"""

    def __init__(self):
        """Initialize Supabase client"""
        self.url = os.getenv("SUPABASE_URL")
        self.service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not self.url or not self.service_role_key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in environment")

        # Use service role key for backend operations (bypasses RLS)
        self.client: Client = create_client(self.url, self.service_role_key)

        self.manuscripts_bucket = os.getenv("SUPABASE_BUCKET_MANUSCRIPTS", "manuscripts")
        self.audiobooks_bucket = os.getenv("SUPABASE_BUCKET_AUDIOBOOKS", "audiobooks")

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
    # STORAGE OPERATIONS
    # ========================================================================

    def upload_manuscript(self, user_id: str, filename: str, file_content: bytes) -> str:
        """
        Upload manuscript to Supabase Storage

        Args:
            user_id: User UUID
            filename: Original filename
            file_content: File bytes

        Returns:
            Storage path (e.g., "user123/my-book.txt")
        """
        storage_path = f"{user_id}/{filename}"

        self.client.storage.from_(self.manuscripts_bucket).upload(
            path=storage_path,
            file=file_content,
            file_options={"content-type": "text/plain"}
        )

        return storage_path

    def download_manuscript(self, storage_path: str) -> bytes:
        """
        Download manuscript from Supabase Storage

        Args:
            storage_path: Path in storage (e.g., "user123/my-book.txt")

        Returns:
            File content as bytes
        """
        return self.client.storage.from_(self.manuscripts_bucket).download(storage_path)

    def upload_audiobook(self, user_id: str, job_id: str, filename: str, file_content: bytes) -> str:
        """
        Upload generated audiobook to Supabase Storage

        Args:
            user_id: User UUID
            job_id: Job UUID
            filename: Audio filename
            file_content: Audio file bytes

        Returns:
            Storage path
        """
        storage_path = f"{user_id}/{job_id}/{filename}"

        self.client.storage.from_(self.audiobooks_bucket).upload(
            path=storage_path,
            file=file_content,
            file_options={"content-type": "audio/mpeg"}
        )

        return storage_path

    def get_download_url(self, storage_path: str, expires_in: int = 3600) -> str:
        """
        Get signed download URL for audiobook

        Args:
            storage_path: Path in storage
            expires_in: URL expiration time in seconds (default 1 hour)

        Returns:
            Signed download URL
        """
        result = self.client.storage.from_(self.audiobooks_bucket).create_signed_url(
            path=storage_path,
            expires_in=expires_in
        )
        return result['signedURL']

    def delete_storage_file(self, bucket: str, storage_path: str) -> bool:
        """
        Delete file from storage

        Args:
            bucket: Bucket name (manuscripts or audiobooks)
            storage_path: Path in storage

        Returns:
            True if deleted successfully
        """
        try:
            self.client.storage.from_(bucket).remove([storage_path])
            return True
        except Exception as e:
            print(f"Error deleting {storage_path}: {e}")
            return False


# Global database instance
db = SupabaseDB()
