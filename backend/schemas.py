from typing import Optional
from pydantic import BaseModel, Field


class MerchantCreate(BaseModel):
    business_name: str
    auth_user_id: Optional[str] = None
    cost_floor: float = 150.0
    max_retry_attempts: int = 3


class FailedPaymentIn(BaseModel):
    """Mirrors a row your agent/ pipeline expects, plus merchant_id for multi-tenancy."""
    merchant_id: str
    customer_name: str
    customer_email: Optional[str] = None
    customer_id: str = Field(..., description="Stable identifier used for guardrail tracking")
    customer_tier: str = "low"  # "low" | "high"
    amount: float
    failure_reason: str
    retry_count: int = 0
    failed_at: Optional[str] = None  # ISO timestamp; defaults to now if omitted


class ProcessPaymentRequest(BaseModel):
    failed_payment_id: str


class RazorpayWebhookPayload(BaseModel):
    """
    Simplified mock of a Razorpay 'payment.failed' webhook event.
    Real signature verification will replace the mock check in Phase 2b.
    """
    merchant_id: str
    customer_name: str
    customer_email: Optional[str] = None
    customer_id: str
    customer_tier: str = "low"
    amount: float
    failure_reason: str
    razorpay_payment_id: Optional[str] = None
