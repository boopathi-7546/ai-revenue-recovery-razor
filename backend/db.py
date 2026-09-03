"""
Supabase client setup.

Uses the SECRET (service_role) key — this must only ever run on the backend.
Never expose this key to any frontend code.
"""

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client, Client

_ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(_ENV_PATH, override=True)   # loads ALL keys from backend/.env into os.environ

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise RuntimeError(
        "Missing SUPABASE_URL or SUPABASE_SERVICE_KEY. "
        "Copy backend/.env.example to backend/.env and fill in your project values."
    )


@lru_cache
def get_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
