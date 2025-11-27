"""
Cloudflare R2 Storage Client
S3-compatible object storage for manuscripts and audiobooks
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError
from botocore.client import Config

# Load environment variables (only for local development)
# In production (Railway), env vars are set directly
env_path = Path(__file__).parent.parent.parent.parent / "env" / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)


class R2Storage:
    """Cloudflare R2 storage client using S3-compatible API"""

    def __init__(self):
        """Initialize R2 client with credentials from environment"""
        self.account_id = os.getenv("R2_ACCOUNT_ID")
        self.access_key_id = os.getenv("R2_ACCESS_KEY_ID")
        self.secret_access_key = os.getenv("R2_SECRET_ACCESS_KEY")
        self.endpoint = os.getenv("R2_ENDPOINT")
        self.public_url = os.getenv("R2_PUBLIC_URL", "")

        # Bucket names
        self.manuscripts_bucket = os.getenv("R2_BUCKET_MANUSCRIPTS", "manuscripts")
        self.audiobooks_bucket = os.getenv("R2_BUCKET_AUDIOBOOKS", "audiobooks")

        # Validate required config
        if not all([self.account_id, self.access_key_id, self.secret_access_key]):
            raise ValueError(
                "Missing R2 configuration. Required: R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY"
            )

        # Construct endpoint if not provided
        if not self.endpoint:
            self.endpoint = f"https://{self.account_id}.r2.cloudflarestorage.com"

        # Initialize S3 client for R2
        self.client = boto3.client(
            's3',
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            region_name='auto',  # R2 uses 'auto' for region
            config=Config(
                signature_version='s3v4',
                s3={'addressing_style': 'path'}
            )
        )

        print(f"✅ R2 Storage initialized: {self.endpoint}")

    # ========================================================================
    # MANUSCRIPT OPERATIONS
    # ========================================================================

    def upload_manuscript(
        self,
        user_id: str,
        filename: str,
        file_content: bytes,
        job_id: Optional[str] = None
    ) -> str:
        """
        Upload manuscript to R2

        Args:
            user_id: User UUID
            filename: Original filename
            file_content: File bytes
            job_id: Optional job ID for better organization

        Returns:
            Object key (e.g., "manuscripts/user123/job456/book.txt")
        """
        # Construct object key
        if job_id:
            object_key = f"manuscripts/{user_id}/{job_id}/{filename}"
        else:
            object_key = f"manuscripts/{user_id}/{filename}"

        try:
            # Determine content type
            content_type = self._get_content_type(filename)

            # Upload to R2
            self.client.put_object(
                Bucket=self.manuscripts_bucket,
                Key=object_key,
                Body=file_content,
                ContentType=content_type,
                Metadata={
                    'user_id': user_id,
                    'original_filename': filename
                }
            )

            print(f"✅ Uploaded manuscript: {object_key}")
            return object_key

        except ClientError as e:
            print(f"❌ Failed to upload manuscript: {e}")
            raise

    def download_manuscript(self, object_key: str) -> bytes:
        """
        Download manuscript from R2

        Args:
            object_key: Full object key path

        Returns:
            File content as bytes
        """
        try:
            response = self.client.get_object(
                Bucket=self.manuscripts_bucket,
                Key=object_key
            )
            content = response['Body'].read()
            print(f"✅ Downloaded manuscript: {object_key} ({len(content)} bytes)")
            return content

        except ClientError as e:
            print(f"❌ Failed to download manuscript: {e}")
            raise

    # ========================================================================
    # AUDIOBOOK OPERATIONS
    # ========================================================================

    def upload_audiobook(
        self,
        user_id: str,
        job_id: str,
        filename: str,
        file_content: bytes
    ) -> str:
        """
        Upload generated audiobook to R2

        Args:
            user_id: User UUID
            job_id: Job UUID
            filename: Audio filename (e.g., "My_Book_COMPLETE.mp3")
            file_content: Audio file bytes

        Returns:
            Object key (e.g., "audiobooks/user123/job456/final.mp3")
        """
        # Construct object key with clear hierarchy
        object_key = f"audiobooks/{user_id}/{job_id}/{filename}"

        try:
            # Determine content type
            content_type = self._get_audio_content_type(filename)

            # Upload to R2
            self.client.put_object(
                Bucket=self.audiobooks_bucket,
                Key=object_key,
                Body=file_content,
                ContentType=content_type,
                Metadata={
                    'user_id': user_id,
                    'job_id': job_id,
                    'original_filename': filename
                }
            )

            print(f"✅ Uploaded audiobook: {object_key} ({len(file_content)} bytes)")
            return object_key

        except ClientError as e:
            print(f"❌ Failed to upload audiobook: {e}")
            raise

    def generate_presigned_url(
        self,
        object_key: str,
        expires_in: int = 3600,
        bucket: Optional[str] = None
    ) -> str:
        """
        Generate presigned URL for secure download

        Args:
            object_key: Full object key path
            expires_in: URL expiration in seconds (default 1 hour)
            bucket: Optional bucket name (defaults to audiobooks)

        Returns:
            Presigned download URL
        """
        if bucket is None:
            bucket = self.audiobooks_bucket

        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': bucket,
                    'Key': object_key
                },
                ExpiresIn=expires_in
            )
            print(f"✅ Generated presigned URL: {object_key} (expires in {expires_in}s)")
            return url

        except ClientError as e:
            print(f"❌ Failed to generate presigned URL: {e}")
            raise

    def get_public_url(self, object_key: str) -> str:
        """
        Get public URL for object (if R2 public URL is configured)

        Args:
            object_key: Full object key path

        Returns:
            Public URL or presigned URL as fallback
        """
        if self.public_url:
            # Use configured public URL
            return f"{self.public_url}/{object_key}"
        else:
            # Fallback to presigned URL (1 week expiry)
            return self.generate_presigned_url(object_key, expires_in=604800)

    # ========================================================================
    # FILE DELETION
    # ========================================================================

    def delete_object(self, bucket: str, object_key: str) -> bool:
        """
        Delete object from R2

        Args:
            bucket: Bucket name (manuscripts or audiobooks)
            object_key: Full object key path

        Returns:
            True if deleted successfully
        """
        try:
            self.client.delete_object(
                Bucket=bucket,
                Key=object_key
            )
            print(f"✅ Deleted: {bucket}/{object_key}")
            return True

        except ClientError as e:
            print(f"❌ Failed to delete {bucket}/{object_key}: {e}")
            return False

    def delete_manuscript(self, object_key: str) -> bool:
        """Delete manuscript from R2"""
        return self.delete_object(self.manuscripts_bucket, object_key)

    def delete_audiobook(self, object_key: str) -> bool:
        """Delete audiobook from R2"""
        return self.delete_object(self.audiobooks_bucket, object_key)

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _get_content_type(self, filename: str) -> str:
        """Determine content type from filename"""
        ext = Path(filename).suffix.lower()
        content_types = {
            '.txt': 'text/plain',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
        }
        return content_types.get(ext, 'application/octet-stream')

    def _get_audio_content_type(self, filename: str) -> str:
        """Determine audio content type from filename"""
        ext = Path(filename).suffix.lower()
        content_types = {
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.flac': 'audio/flac',
            '.m4a': 'audio/mp4',
            '.m4b': 'audio/mp4',
            '.ogg': 'audio/ogg',
        }
        return content_types.get(ext, 'audio/mpeg')

    def check_bucket_exists(self, bucket_name: str) -> bool:
        """
        Check if bucket exists (useful for setup validation)

        Args:
            bucket_name: Bucket name to check

        Returns:
            True if bucket exists and is accessible
        """
        try:
            self.client.head_bucket(Bucket=bucket_name)
            print(f"✅ Bucket exists: {bucket_name}")
            return True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == '404':
                print(f"❌ Bucket not found: {bucket_name}")
            else:
                print(f"❌ Error checking bucket {bucket_name}: {e}")
            return False


# Global R2 storage instance (lazy initialization)
_r2_instance: R2Storage = None


def get_r2() -> R2Storage:
    """Get or create R2 storage instance (lazy initialization)"""
    global _r2_instance
    if _r2_instance is None:
        _r2_instance = R2Storage()
    return _r2_instance


# Backwards compatible alias
class _LazyR2:
    """Lazy proxy for R2Storage to maintain backwards compatibility"""
    def __getattr__(self, name):
        return getattr(get_r2(), name)


r2 = _LazyR2()
