"""
FastAPI backend for AI Revenue Recovery.

Run locally:
    cd backend
    pip install -r requirements.txt
    cp .env.example .env   # then fill in your real Supabase values
    uvicorn main:app --reload --port 8000

Docs will be at http://localhost:8000/docs
"""

import hashlib
import hmac
import os
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from backend.auth import get_current_merchant
from backend.db import get_client
from backend.schemas import (
    MerchantCreate,
    FailedPaymentIn,
    MerchantSignup,
    ProcessPaymentRequest,
    RazorpayWebhookPayload,
)
from backend.service import process_failed_payment

app = FastAPI(title="AI Revenue Recovery API", version="0.1.0")

# Allow configured frontend origin (defaults to * for local dev)
_FRONTEND_URL = os.environ.get("FRONTEND_URL", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[_FRONTEND_URL] if _FRONTEND_URL != "*" else ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


# ── Auth / Merchants ───────────────────────────────────────────────────────

@app.post("/auth/signup", status_code=201)
def signup(payload: MerchantSignup):
    """
    Called immediately after Supabase Auth signup completes on the frontend.
    Creates the merchant row linked to the new Supabase user UUID.
    """
    sb = get_client()
    # Idempotent — if the merchant already exists (e.g. double-click), just return it
    existing = (
        sb.table("merchants")
        .select("*")
        .eq("auth_user_id", payload.auth_user_id)
        .execute()
    )
    if existing.data:
        return existing.data[0]
    res = sb.table("merchants").insert({
        "business_name": payload.business_name,
        "auth_user_id": payload.auth_user_id,
        "cost_floor": payload.cost_floor,
        "max_retry_attempts": payload.max_retry_attempts,
    }).execute()
    return res.data[0]


@app.get("/merchants/me")
def get_my_merchant(merchant: dict = Depends(get_current_merchant)):
    """Return the merchant row for the currently logged-in user."""
    return merchant


@app.get("/merchants/{merchant_id}")
def get_merchant(
    merchant_id: str,
    merchant: dict = Depends(get_current_merchant),
):
    if merchant["id"] != merchant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return merchant


# ── Failed payments ─────────────────────────────────────────────────────────

@app.post("/failed-payments", status_code=201)
def create_failed_payment(
    payload: FailedPaymentIn,
    merchant: dict = Depends(get_current_merchant),
):
    """Manually register a failed payment (used by 'Try It Live' single-record flow)."""
    if payload.merchant_id != merchant["id"]:
        raise HTTPException(status_code=403, detail="merchant_id mismatch")
    sb = get_client()
    row = payload.model_dump()
    row.setdefault("failed_at", datetime.now(timezone.utc).isoformat())
    res = sb.table("failed_payments").insert(row).execute()
    return res.data[0]


@app.get("/merchants/{merchant_id}/failed-payments")
def list_failed_payments(
    merchant_id: str,
    status: str | None = None,
    merchant: dict = Depends(get_current_merchant),
):
    if merchant["id"] != merchant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    sb = get_client()
    q = sb.table("failed_payments").select("*").eq("merchant_id", merchant_id)
    if status:
        q = q.eq("status", status)
    res = q.order("created_at", desc=True).execute()
    return res.data


# ── Core pipeline trigger ───────────────────────────────────────────────────

@app.post("/process-payment")
def process_payment(
    payload: ProcessPaymentRequest,
    merchant: dict = Depends(get_current_merchant),
):
    """
    Runs your agent's detect->diagnose->decide->execute->log pipeline
    for a single failed_payment row already in the database.
    """
    try:
        result = process_failed_payment(payload.failed_payment_id, merchant["id"])
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return result


# ── Razorpay webhook (real HMAC-SHA256 signature check) ────────────────────

_RAZORPAY_SECRET = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "mock_secret_for_now")


async def _verify_razorpay_signature(request: Request) -> bytes:
    """
    Razorpay signs the raw request body with HMAC-SHA256 using your webhook secret.
    Header: X-Razorpay-Signature
    Docs: https://razorpay.com/docs/webhooks/validate-test/
    """
    body = await request.body()
    sig_header = request.headers.get("X-Razorpay-Signature", "")

    # Skip real verification when using the mock secret (local dev / test mode)
    if _RAZORPAY_SECRET != "mock_secret_for_now" and sig_header:
        expected = hmac.new(
            _RAZORPAY_SECRET.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, sig_header):
            raise HTTPException(status_code=400, detail="Invalid Razorpay signature")
    return body


@app.post("/webhooks/razorpay")
async def razorpay_webhook(
    request: Request,
    payload: RazorpayWebhookPayload,
    _body: bytes = Depends(_verify_razorpay_signature),
):
    """
    Webhook receiver for Razorpay 'payment.failed' events.
    Signature is verified via HMAC-SHA256 (real key required for production;
    falls back to skip-verify when RAZORPAY_WEBHOOK_SECRET=mock_secret_for_now).
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

    # Immediately run through the agent pipeline
    result = process_failed_payment(inserted["id"], payload.merchant_id)
    return {"received": True, "failed_payment_id": inserted["id"], "result": result}


# ── Dashboard read endpoints ─────────────────────────────────────────────────

@app.get("/merchants/{merchant_id}/audit-log")
def get_audit_log(
    merchant_id: str,
    limit: int = 100,
    merchant: dict = Depends(get_current_merchant),
):
    if merchant["id"] != merchant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    sb = get_client()
    res = (
        sb.table("audit_log")
        .select("*, failed_payments(customer_name, amount, failure_reason, customer_tier, customer_id)")
        .eq("merchant_id", merchant_id)
        .order("timestamp", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data


@app.get("/merchants/{merchant_id}/metrics")
def get_metrics(
    merchant_id: str,
    merchant: dict = Depends(get_current_merchant),
):
    """Aggregate metrics for the dashboard headline cards."""
    if merchant["id"] != merchant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    sb = get_client()
    logs = (
        sb.table("audit_log")
        .select("outcome, action_taken, failed_payments(amount)")
        .eq("merchant_id", merchant_id)
        .execute()
    ).data or []

    total = len(logs)
    recovered = sum(1 for r in logs if r["outcome"] == "success")
    skipped = sum(1 for r in logs if r["outcome"] == "skipped")
    failed_attempts = sum(1 for r in logs if r["outcome"] == "failed")
    recovery_rate = round(recovered / total * 100, 1) if total else 0
    amount_recovered = sum(
        float(r["failed_payments"]["amount"])
        for r in logs
        if r["outcome"] == "success" and r.get("failed_payments")
    )
    return {
        "total_processed": total,
        "recovered": recovered,
        "skipped": skipped,
        "failed_attempts": failed_attempts,
        "recovery_rate": recovery_rate,
        "amount_recovered_inr": round(amount_recovered, 2),
    }


@app.get("/merchants/{merchant_id}/exceptions")
def get_exceptions(
    merchant_id: str,
    merchant: dict = Depends(get_current_merchant),
):
    """Rows the agent skipped — matches your dashboard's Exceptions tab."""
    if merchant["id"] != merchant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    sb = get_client()
    res = (
        sb.table("audit_log")
        .select("*, failed_payments(customer_name, amount, failure_reason, merchant_id)")
        .eq("merchant_id", merchant_id)
        .eq("outcome", "skipped")
        .order("timestamp", desc=True)
        .execute()
    )
    return res.data
