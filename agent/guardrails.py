"""
Guardrails module — enforces hard limits on recovery attempts.

Rules:
  1. MAX_ATTEMPTS = 3 per customer (across all time)
  2. No duplicate intervention within 24 hours (simulated via timestamps)
  3. Hard-stop + flag-for-human-review after 3 failed attempts
  4. Never act on already_refunded / duplicate_charge / invalid_data
"""

from datetime import datetime, timedelta
from typing import Optional

MAX_ATTEMPTS       = 3
DEDUP_WINDOW_HOURS = 24
COST_FLOOR_INR     = 150.0   # Skip if amount < this AND retry_count >= 2

# In-memory state for this run
_attempt_tracker: dict[str, int]       = {}   # customer_id → attempts this run
_last_action_ts:  dict[str, datetime]  = {}   # customer_id → last intervention time


def reset_state():
    """Reset tracker between test runs."""
    global _attempt_tracker, _last_action_ts
    _attempt_tracker = {}
    _last_action_ts  = {}


def _parse_ts(ts_str: str) -> datetime:
    try:
        return datetime.fromisoformat(ts_str)
    except (ValueError, TypeError):
        return datetime.now()


def check_guardrails(record: dict, failure_class: str) -> tuple[bool, str]:
    """
    Return (allowed: bool, reason: str).
    If allowed is False, the agent must NOT take action — log and skip.
    """
    cid    = record["customer_id"]
    amount = float(record.get("amount", 0))
    retry  = int(record.get("retry_count", 0))

    # ── Guardrail 0: invalid data ──────────────────────────────────────────────
    if failure_class == "invalid_data":
        return False, "Invalid data: zero or negative amount — hard skip"

    # ── Guardrail 1: never act on already-resolved cases ──────────────────────
    if failure_class == "non_retryable_skip":
        reason = record.get("failure_reason", "")
        return False, f"Non-retryable ({reason}) — logged and skipped per policy"

    # ── Guardrail 2: cost-of-recovery floor ───────────────────────────────────
    if amount < COST_FLOOR_INR and retry >= 2:
        return False, (
            f"Cost-of-recovery skip: amount ₹{amount:.2f} < floor ₹{COST_FLOOR_INR} "
            f"and retry_count={retry} ≥ 2"
        )

    # ── Guardrail 3: max attempts per customer ─────────────────────────────────
    attempts_so_far = _attempt_tracker.get(cid, 0)
    if attempts_so_far >= MAX_ATTEMPTS:
        return False, (
            f"Max attempts ({MAX_ATTEMPTS}) reached for {cid} — flagged for human review"
        )

    # ── Guardrail 4: 24-hour dedup window ─────────────────────────────────────
    if cid in _last_action_ts:
        last_ts = _last_action_ts[cid]
        # Simulate: use failed_at as "now" to allow deterministic testing
        now = _parse_ts(record.get("failed_at", ""))
        if (now - last_ts) < timedelta(hours=DEDUP_WINDOW_HOURS):
            delta_h = ((now - last_ts).total_seconds() / 3600)
            return False, (
                f"Dedup guard: last action was {delta_h:.1f}h ago "
                f"(< {DEDUP_WINDOW_HOURS}h window) — skipping"
            )

    return True, "All guardrails passed"


def record_attempt(record: dict):
    """Call this after a successful attempt is dispatched."""
    cid = record["customer_id"]
    _attempt_tracker[cid] = _attempt_tracker.get(cid, 0) + 1
    _last_action_ts[cid]  = _parse_ts(record.get("failed_at", ""))


def get_attempt_count(customer_id: str) -> int:
    return _attempt_tracker.get(customer_id, 0)


def is_flagged_for_human(customer_id: str) -> bool:
    return _attempt_tracker.get(customer_id, 0) >= MAX_ATTEMPTS
