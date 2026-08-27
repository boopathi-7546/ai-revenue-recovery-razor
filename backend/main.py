"""
FastAPI backend for AI Revenue Recovery.

Run locally:
    cd backend
    pip install -r requirements.txt
    cp .env.example .env   # then fill in your real Supabase values
    uvicorn main:app --reload --port 8000

Docs will be at http://localhost:8000/docs
"""

from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.db import get_client
from backend.schemas import (
    MerchantCreate,
    FailedPaymentIn,
    ProcessPaymentRequest,
    RazorpayWebhookPayload,
)
from backend.service import process_failed_payment

app = FastAPI(title="AI Revenue Recovery API", version="0.1.0")

# Wide open for local dev; tighten this to your real frontend origin in Phase 3.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


# ── Merchants ──────────────────────────────────────────────────────────────

@app.post("/merchants")
def create_merchant(payload: MerchantCreate):
    sb = get_client()
    res = sb.table("merchants").insert(payload.model_dump()).execute()
    return res.data[0]


@app.get("/merchants/{merchant_id}")
def get_merchant(merchant_id: str):
    sb = get_client()
    res = sb.table("merchants").select("*").eq("id", merchant_id).single().execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Merchant not found")
    return res.data


# ── Failed payments ─────────────────────────────────────────────────────────

@app.post("/failed-payments")
def create_failed_payment(payload: FailedPaymentIn):
    """Manually register a failed payment (used by 'Try It Live' single-record flow)."""
    sb = get_client()
    row = payload.model_dump()
    row.setdefault("failed_at", datetime.now(timezone.utc).isoformat())
    res = sb.table("failed_payments").insert(row).execute()
    return res.data[0]


@app.get("/merchants/{merchant_id}/failed-payments")
def list_failed_payments(merchant_id: str, status: str | None = None):
    sb = get_client()
    q = sb.table("failed_payments").select("*").eq("merchant_id", merchant_id)
    if status:
        q = q.eq("status", status)
    res = q.order("created_at", desc=True).execute()
    return res.data


# ── Core pipeline trigger ───────────────────────────────────────────────────

@app.post("/process-payment")
def process_payment(payload: ProcessPaymentRequest):
    """
    Runs your agent's detect->diagnose->decide->execute->log pipeline
    for a single failed_payment row already in the database.
    """
    try:
        result = process_failed_payment(payload.failed_payment_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return result


# ── Razorpay webhook (mocked signature check for now) ───────────────────────

@app.post("/webhooks/razorpay")
def razorpay_webhook(payload: RazorpayWebhookPayload):
    """
    Mock webhook receiver for Razorpay 'payment.failed' events.
    Real signature verification (HMAC against RAZORPAY_WEBHOOK_SECRET)
    plugs in here once you're off test-mode — matches your existing
    'mocked, no real API keys' approach from the hackathon build.
    """
    sb = get_client()
    row = {
        "merchant_id": payload.merchant_id,
        "customer_name": payload.customer_name,
        "customer_email": payload.customer_email,
        "customer_id": payload.customer_id,
        "customer_tier": payload.customer_tier,
        "amount": payload.amount,
        "failure_reason": payload.failure_reason,
        "failed_at": datetime.now(timezone.utc).isoformat(),
    }
    inserted = sb.table("failed_payments").insert(row).execute().data[0]

    # Immediately run it through the agent, same as a real-time recovery flow would
    result = process_failed_payment(inserted["id"])
    return {"received": True, "failed_payment_id": inserted["id"], "result": result}


# ── Dashboard read endpoints ─────────────────────────────────────────────────

@app.get("/merchants/{merchant_id}/audit-log")
def get_audit_log(merchant_id: str, limit: int = 100):
    sb = get_client()
    res = (
        sb.table("audit_log")
        .select("*")
        .eq("merchant_id", merchant_id)
        .order("timestamp", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data


@app.get("/merchants/{merchant_id}/exceptions")
def get_exceptions(merchant_id: str):
    """Rows the agent skipped — matches your dashboard's Exceptions tab."""
    sb = get_client()
    res = (
        sb.table("audit_log")
        .select("*, failed_payments!inner(customer_name, amount, failure_reason, merchant_id)")
        .eq("failed_payments.merchant_id", merchant_id)
        .eq("outcome", "skipped")
        .order("timestamp", desc=True)
        .execute()
    )
    return res.data
