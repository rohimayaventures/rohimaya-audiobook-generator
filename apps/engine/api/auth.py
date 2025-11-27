"""
Authentication and Authorization
JWT token verification for Supabase Auth
"""

import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
from fastapi import Header, HTTPException, status
from jose import jwt, JWTError

# Load environment variables (only for local development)
# In production (Railway), env vars are set directly
env_path = Path(__file__).parent.parent.parent.parent / "env" / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)


class AuthService:
    """Handle JWT verification and user extraction"""

    def __init__(self):
        """Initialize with Supabase JWT secret"""
        self.supabase_url = os.getenv("SUPABASE_URL")
        # JWT Secret is used for verifying tokens (different from service role key)
        # Find this in Supabase Dashboard → Project Settings → API → JWT Secret
        self.jwt_secret = os.getenv("SUPABASE_JWT_SECRET")

        if not self.supabase_url or not self.jwt_secret:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_JWT_SECRET")

    def verify_token(self, authorization: Optional[str] = Header(None)) -> str:
        """
        Verify JWT token and extract user ID

        Args:
            authorization: Authorization header (Bearer token)

        Returns:
            User ID (UUID)

        Raises:
            HTTPException: 401 if token is invalid or missing
        """
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authorization header",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Extract token from "Bearer <token>"
        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify JWT token
        try:
            # Supabase uses HS256 algorithm
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
            )

            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: missing user ID",
                )

            return user_id

        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def verify_token_optional(self, authorization: Optional[str] = Header(None)) -> Optional[str]:
        """
        Verify JWT token but allow unauthenticated requests

        Args:
            authorization: Optional authorization header

        Returns:
            User ID if authenticated, None otherwise
        """
        if not authorization:
            return None

        try:
            return self.verify_token(authorization)
        except HTTPException:
            return None


# Global auth service
auth_service = AuthService()


def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    """
    FastAPI dependency to get current user from token

    Usage:
        @app.get("/protected")
        async def protected_route(user_id: str = Depends(get_current_user)):
            return {"user_id": user_id}

    Args:
        authorization: Authorization header

    Returns:
        User ID

    Raises:
        HTTPException: 401 if not authenticated
    """
    return auth_service.verify_token(authorization)


def get_current_user_optional(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """
    FastAPI dependency to get current user (optional)

    Args:
        authorization: Optional authorization header

    Returns:
        User ID or None
    """
    return auth_service.verify_token_optional(authorization)
