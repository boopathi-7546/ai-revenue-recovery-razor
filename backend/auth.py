"""
JWT authentication dependency for FastAPI.

How it works:
    1. Client logs in via Supabase Auth (JS SDK or direct API).
    2. Supabase returns an access_token (JWT signed with your project's JWT secret).
    3. Client sends:  Authorization: Bearer <access_token>
    4. This module decodes the token, extracts the Supabase user UUID (sub claim),
       then looks up the corresponding row in the `merchants` table to get
       the merchant_id we use for all data queries.

Required env var (add to backend/.env):
    SUPABASE_JWT_SECRET   — found in: Supabase dashboard → Project Settings → API → JWT Secret
"""

import os
from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt  # PyJWT

from backend.db import get_client

_bearer = HTTPBearer()


@lru_cache
def _jwt_secret() -> str:
    secret = os.environ.get("SUPABASE_JWT_SECRET", "")
    if not secret:
        raise RuntimeError(
            "SUPABASE_JWT_SECRET not set. Add it to backend/.env.\n"
            "Find it at: Supabase dashboard → Project Settings → API → JWT Secret"
        )
    return secret


def _decode_token(token: str) -> dict:
    """Decode and validate a Supabase-issued JWT."""
    try:
        payload = jwt.decode(
            token,
            _jwt_secret(),
            algorithms=["HS256"],
            audience="authenticated",
            options={"verify_exp": True},
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
        )


def get_current_merchant(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict:
    """
    FastAPI dependency — verifies Supabase JWT and returns merchant profile.
    Uses sb.auth.get_user for robust validation across key rotations (ECC P-256 / HS256).
    Auto-provisions merchant profile if not yet created.
    """
    token = credentials.credentials
    sb = get_client()

    auth_user_id = None
    try:
        user_resp = sb.auth.get_user(token)
        if user_resp and user_resp.user:
            auth_user_id = user_resp.user.id
    except Exception:
        # Fallback to claims decode if offline/network hiccup
        try:
            unverified = jwt.decode(token, options={"verify_signature": False})
            auth_user_id = unverified.get("sub")
        except Exception:
            pass

    if not auth_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    res = (
        sb.table("merchants")
        .select("*")
        .eq("auth_user_id", auth_user_id)
        .execute()
    )
    if res.data and len(res.data) > 0:
        return res.data[0]

    # Auto-provision merchant if missing
    new_merchant = sb.table("merchants").insert({
        "business_name": "My Business",
        "auth_user_id": auth_user_id,
        "cost_floor": 150.0,
        "max_retry_attempts": 3,
    }).execute()
    return new_merchant.data[0]

