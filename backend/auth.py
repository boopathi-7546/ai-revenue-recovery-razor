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
    FastAPI dependency — call as:  merchant = Depends(get_current_merchant)

    Returns the merchants row for the authenticated user.
    Raises 401 if token is missing/invalid, 404 if no merchant row exists yet.
    """
    payload = _decode_token(credentials.credentials)
    auth_user_id: str = payload.get("sub", "")
    if not auth_user_id:
        raise HTTPException(status_code=401, detail="Token missing 'sub' claim.")

    sb = get_client()
    res = (
        sb.table("merchants")
        .select("*")
        .eq("auth_user_id", auth_user_id)
        .single()
        .execute()
    )
    if not res.data:
        raise HTTPException(
            status_code=404,
            detail="No merchant record found for this user. Please complete signup.",
        )
    return res.data  # e.g. {"id": "...", "business_name": "...", "auth_user_id": "..."}
