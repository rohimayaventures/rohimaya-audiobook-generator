"""
Authentication and Authorization
JWT token verification for Supabase Auth

Security features:
- JWT token verification with HS256
- Token expiration validation
- Audience claim verification
"""

import os
import time
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
from fastapi import Header, HTTPException, status
from jose import jwt, JWTError, ExpiredSignatureError

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
        jwt_secret_raw = os.getenv("SUPABASE_JWT_SECRET")

        if not self.supabase_url or not jwt_secret_raw:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_JWT_SECRET")

        # Supabase JWT secret - use as-is (the base64 string IS the secret)
        # Supabase signs tokens with the raw secret string, not decoded bytes
        self.jwt_secret = jwt_secret_raw

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
                options={
                    "verify_exp": True,  # Verify expiration
                    "verify_aud": True,  # Verify audience
                    "verify_iat": True,  # Verify issued at
                }
            )

            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: missing user ID",
                )

            # Additional security: Check if token is about to expire (within 5 minutes)
            exp = payload.get("exp")
            if exp and (exp - time.time()) < 300:
                # Token expires in less than 5 minutes - still valid but client should refresh
                pass  # Could add a response header to indicate token refresh needed

            return user_id

        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )
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


# Global auth service (lazy initialization)
_auth_instance: AuthService = None


def get_auth_service() -> AuthService:
    """Get or create auth service instance (lazy initialization)"""
    global _auth_instance
    if _auth_instance is None:
        _auth_instance = AuthService()
    return _auth_instance


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
    return get_auth_service().verify_token(authorization)


def get_current_user_optional(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """
    FastAPI dependency to get current user (optional)

    Args:
        authorization: Optional authorization header

    Returns:
        User ID or None
    """
    return get_auth_service().verify_token_optional(authorization)
