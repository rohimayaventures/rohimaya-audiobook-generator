"""
Google Drive Integration for AuthorFlow Studios

Handles:
- OAuth 2.0 flow for Google Drive access
- File picker integration
- Google Doc to text conversion
- Direct file download from Drive

Environment variables required:
- GOOGLE_DRIVE_CLIENT_ID
- GOOGLE_DRIVE_CLIENT_SECRET
- GOOGLE_DRIVE_REDIRECT_URI
"""

import os
import json
import logging
import tempfile
from typing import Dict, Any, Optional, List
from pathlib import Path
from urllib.parse import urlencode, parse_qs, urlparse

import httpx

logger = logging.getLogger(__name__)

# Google OAuth endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_DRIVE_API = "https://www.googleapis.com/drive/v3"
GOOGLE_DOCS_API = "https://docs.googleapis.com/v1"

# Required scopes
SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/documents.readonly",
]


class GoogleDriveClient:
    """
    Client for Google Drive API operations.

    Usage:
        client = GoogleDriveClient(access_token="...")
        content = client.get_document_text(file_id="...")
    """

    def __init__(self, access_token: str):
        """
        Initialize with an access token.

        Args:
            access_token: OAuth2 access token from Google
        """
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }

    async def get_file_metadata(self, file_id: str) -> Dict[str, Any]:
        """
        Get file metadata from Google Drive.

        Args:
            file_id: Google Drive file ID

        Returns:
            File metadata including name, mimeType, size
        """
        url = f"{GOOGLE_DRIVE_API}/files/{file_id}"
        params = {"fields": "id,name,mimeType,size,createdTime,modifiedTime"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()

    async def get_document_text(self, file_id: str) -> str:
        """
        Get text content from a Google Doc.

        Args:
            file_id: Google Doc file ID

        Returns:
            Plain text content of the document
        """
        url = f"{GOOGLE_DOCS_API}/documents/{file_id}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            doc = response.json()

        # Extract text from document structure
        return self._extract_text_from_doc(doc)

    def _extract_text_from_doc(self, doc: Dict[str, Any]) -> str:
        """
        Extract plain text from Google Docs JSON structure.

        Args:
            doc: Google Docs API document response

        Returns:
            Plain text content
        """
        text_parts = []

        content = doc.get("body", {}).get("content", [])

        for element in content:
            if "paragraph" in element:
                paragraph = element["paragraph"]
                for para_element in paragraph.get("elements", []):
                    if "textRun" in para_element:
                        text_parts.append(para_element["textRun"].get("content", ""))

        return "".join(text_parts)

    async def download_file_as_text(self, file_id: str, mime_type: str) -> str:
        """
        Download a file and convert to text.

        Handles:
        - Google Docs (application/vnd.google-apps.document)
        - Plain text files
        - DOCX files (basic support)
        - PDF files (basic support)

        Args:
            file_id: Google Drive file ID
            mime_type: MIME type of the file

        Returns:
            Text content of the file
        """
        # Google Docs - use Docs API
        if mime_type == "application/vnd.google-apps.document":
            return await self.get_document_text(file_id)

        # Export Google Docs to plain text
        if mime_type.startswith("application/vnd.google-apps."):
            return await self._export_google_file(file_id, "text/plain")

        # Download regular files
        return await self._download_and_convert(file_id, mime_type)

    async def _export_google_file(self, file_id: str, export_mime_type: str) -> str:
        """
        Export a Google Workspace file to specified format.

        Args:
            file_id: File ID
            export_mime_type: MIME type to export as

        Returns:
            Exported content as text
        """
        url = f"{GOOGLE_DRIVE_API}/files/{file_id}/export"
        params = {"mimeType": export_mime_type}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.text

    async def _download_and_convert(self, file_id: str, mime_type: str) -> str:
        """
        Download a file and convert to text based on MIME type.

        Args:
            file_id: File ID
            mime_type: File MIME type

        Returns:
            Text content
        """
        url = f"{GOOGLE_DRIVE_API}/files/{file_id}"
        params = {"alt": "media"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            content = response.content

        # Plain text
        if mime_type in ["text/plain", "text/markdown", "text/html"]:
            return content.decode("utf-8")

        # DOCX - basic extraction
        if mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return self._extract_text_from_docx(content)

        # PDF - basic extraction
        if mime_type == "application/pdf":
            return self._extract_text_from_pdf(content)

        # RTF - treat as plain text (rough approximation)
        if mime_type == "application/rtf":
            return self._extract_text_from_rtf(content)

        # Unknown - try as plain text
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError(f"Cannot convert file with MIME type {mime_type} to text")

    def _extract_text_from_docx(self, content: bytes) -> str:
        """
        Extract text from DOCX file.

        Args:
            content: DOCX file bytes

        Returns:
            Extracted text
        """
        import zipfile
        import io
        import xml.etree.ElementTree as ET

        text_parts = []

        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            # Read document.xml
            with zf.open("word/document.xml") as doc_xml:
                tree = ET.parse(doc_xml)
                root = tree.getroot()

                # Define namespace
                ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

                # Find all text elements
                for t in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"):
                    if t.text:
                        text_parts.append(t.text)

                # Add paragraph breaks
                for p in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
                    text_parts.append("\n")

        return "".join(text_parts)

    def _extract_text_from_pdf(self, content: bytes) -> str:
        """
        Extract text from PDF file.

        Note: This is a basic implementation. For better results,
        consider using a dedicated PDF library.

        Args:
            content: PDF file bytes

        Returns:
            Extracted text (best effort)
        """
        try:
            # Try using PyPDF2 if available
            import PyPDF2
            import io

            reader = PyPDF2.PdfReader(io.BytesIO(content))
            text_parts = []

            for page in reader.pages:
                text_parts.append(page.extract_text())

            return "\n".join(text_parts)
        except ImportError:
            logger.warning("PyPDF2 not available for PDF extraction")
            raise ValueError(
                "PDF extraction requires PyPDF2. "
                "Please convert your PDF to a text file or Google Doc."
            )

    def _extract_text_from_rtf(self, content: bytes) -> str:
        """
        Extract text from RTF file (basic).

        Args:
            content: RTF file bytes

        Returns:
            Extracted text (rough)
        """
        import re

        text = content.decode("latin-1", errors="ignore")

        # Remove RTF control words and groups
        text = re.sub(r'\{[^}]*\}', '', text)
        text = re.sub(r'\\[a-z]+\d*\s*', '', text)
        text = re.sub(r'\\[^a-z]', '', text)

        return text.strip()

    async def list_files(
        self,
        folder_id: Optional[str] = None,
        query: Optional[str] = None,
        page_size: int = 20,
        page_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List files in Google Drive.

        Args:
            folder_id: Optional folder ID to list files from
            query: Optional search query
            page_size: Number of results per page
            page_token: Token for pagination

        Returns:
            List of files with pagination info
        """
        url = f"{GOOGLE_DRIVE_API}/files"

        # Build query
        q_parts = []
        if folder_id:
            q_parts.append(f"'{folder_id}' in parents")
        if query:
            q_parts.append(query)

        # Filter to supported file types
        supported_types = [
            "application/vnd.google-apps.document",
            "text/plain",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/pdf",
            "application/rtf",
        ]
        type_filter = " or ".join([f"mimeType='{t}'" for t in supported_types])
        q_parts.append(f"({type_filter})")

        params = {
            "q": " and ".join(q_parts) if q_parts else None,
            "pageSize": page_size,
            "pageToken": page_token,
            "fields": "nextPageToken,files(id,name,mimeType,size,createdTime,modifiedTime,iconLink,webViewLink)",
            "orderBy": "modifiedTime desc",
        }

        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()


def get_oauth_url(state: Optional[str] = None) -> str:
    """
    Generate Google OAuth authorization URL.

    Args:
        state: Optional state parameter for CSRF protection

    Returns:
        Authorization URL to redirect user to
    """
    client_id = os.getenv("GOOGLE_DRIVE_CLIENT_ID")
    redirect_uri = os.getenv("GOOGLE_DRIVE_REDIRECT_URI")

    if not client_id:
        raise ValueError("GOOGLE_DRIVE_CLIENT_ID not configured")
    if not redirect_uri:
        raise ValueError("GOOGLE_DRIVE_REDIRECT_URI not configured")

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
    }

    if state:
        params["state"] = state

    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


async def exchange_code_for_tokens(code: str) -> Dict[str, Any]:
    """
    Exchange authorization code for access and refresh tokens.

    Args:
        code: Authorization code from OAuth callback

    Returns:
        Token response with access_token, refresh_token, expires_in
    """
    client_id = os.getenv("GOOGLE_DRIVE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_DRIVE_CLIENT_SECRET")
    redirect_uri = os.getenv("GOOGLE_DRIVE_REDIRECT_URI")

    if not all([client_id, client_secret, redirect_uri]):
        raise ValueError("Google Drive OAuth not fully configured")

    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(GOOGLE_TOKEN_URL, data=data)
        response.raise_for_status()
        return response.json()


async def refresh_access_token(refresh_token: str) -> Dict[str, Any]:
    """
    Refresh an expired access token.

    Args:
        refresh_token: Refresh token from previous authorization

    Returns:
        New token response with access_token, expires_in
    """
    client_id = os.getenv("GOOGLE_DRIVE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_DRIVE_CLIENT_SECRET")

    if not all([client_id, client_secret]):
        raise ValueError("Google Drive OAuth not fully configured")

    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(GOOGLE_TOKEN_URL, data=data)
        response.raise_for_status()
        return response.json()


def is_google_drive_configured() -> bool:
    """
    Check if Google Drive integration is configured.

    Returns:
        True if all required environment variables are set
    """
    return all([
        os.getenv("GOOGLE_DRIVE_CLIENT_ID"),
        os.getenv("GOOGLE_DRIVE_CLIENT_SECRET"),
        os.getenv("GOOGLE_DRIVE_REDIRECT_URI"),
    ])
