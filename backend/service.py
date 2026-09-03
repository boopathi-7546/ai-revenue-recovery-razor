"""
Bridges Supabase (persistent, multi-tenant state) with the existing
agent/ pipeline (classifier, decision, executor) — without modifying
any agent/ files, so the hackathon demo stays untouched.

Why this exists:
    agent/guardrails.py tracks attempt counts + last-action timestamps
    in plain in-memory dicts that reset every pipeline run. That's fine
    for a batch demo script, but a real API is called once per payment
    event and must not "forget" a customer's history between calls.

    So before calling the agent's decision logic for a given record, we
    seed those in-memory trackers from Supabase (audit_log history for
    that specific customer, scoped to their merchant). After the agent
    makes its decision and mock-executes it, we write the result back
    to Supabase (audit_log insert + failed_payments update).

Schema assumptions (matches your live Supabase tables + migration_001):
    failed_payments: id, merchant_id, customer_name, customer_email,
        customer_id, amount, failure_reason, customer_tier, retry_count,
        status, failed_at, created_at
    audit_log: id, merchant_id, payment_id, action_taken, variant,
        outcome, reasoning, message_en, message_hi, timestamp
"""

from datetime import datetime, timezone

from agent import guardrails
from agent.decision import decide_intervention
from agent.executor import execute_intervention

from backend.db import get_client

_SKIP_ACTIONS = {
    "skip_non_retryable", "skip_invalid_data",
    "skip_cost_floor", "skip_max_attempts", "skip_guardrail",
}


def _seed_guardrail_state(merchant_id: str, customer_id: str):
    """
    Reset the agent's in-memory guardrail trackers, then seed them with
    this customer's real history pulled from audit_log, scoped by merchant.

    Requires joining audit_log -> failed_payments to filter by customer_id,
    since audit_log itself only stores payment_id.
    """
    guardrails.reset_state()
    sb = get_client()

    history = (
        sb.table("audit_log")
        .select("action_taken, timestamp, failed_payments!inner(customer_id)")
        .eq("merchant_id", merchant_id)
        .eq("failed_payments.customer_id", customer_id)
        .order("timestamp", desc=True)
        .execute()
    )

    rows = history.data or []
    if not rows:
        return  # first time we've seen this customer — trackers stay at 0

    attempts = sum(1 for r in rows if r["action_taken"] not in _SKIP_ACTIONS)
    guardrails._attempt_tracker[customer_id] = attempts

    last_ts_str = rows[0]["timestamp"]
    try:
        last_ts = datetime.fromisoformat(last_ts_str.replace("Z", "+00:00"))
    except ValueError:
        last_ts = datetime.now(timezone.utc)
    guardrails._last_action_ts[customer_id] = last_ts.replace(tzinfo=None)


def process_failed_payment(failed_payment_id: str, merchant_id: str | None = None) -> dict:
    """
    Runs one record through: seed state -> decide -> execute -> persist.
    Returns the full decision + execution result for the API response.
    """
    sb = get_client()

    fp_res = (
        sb.table("failed_payments")
        .select("*")
        .eq("id", failed_payment_id)
        .single()
        .execute()
    )
    fp = fp_res.data
    if not fp:
        raise ValueError(f"failed_payment {failed_payment_id} not found")
    if merchant_id and fp.get("merchant_id") != merchant_id:
        raise ValueError(f"failed_payment {failed_payment_id} does not belong to merchant {merchant_id}")

    customer_id = fp.get("customer_id") or fp.get("customer_email") or fp["id"]

    record = {
        "customer_id": customer_id,
        "customer_name": fp.get("customer_name", "Customer"),
        "customer_tier": fp.get("customer_tier", "low"),
        "amount": float(fp["amount"]),
        "failure_reason": fp["failure_reason"],
        "retry_count": fp.get("retry_count", 0),
        "failed_at": fp.get("failed_at") or fp.get("created_at"),
    }

    _seed_guardrail_state(fp["merchant_id"], customer_id)

    decision = decide_intervention(record)
    exec_result = execute_intervention(record, decision)

    sb.table("audit_log").insert({
        "merchant_id": fp["merchant_id"],
        "payment_id": fp["id"],
        "action_taken": decision["action"],
        "variant": decision["variant"],
        "outcome": exec_result["outcome"],
        "reasoning": decision["reasoning"],
        "message_en": decision["messages"].get("english", ""),
        "message_hi": decision["messages"].get("hinglish", ""),
    }).execute()

    new_status = (
        "recovered" if exec_result["outcome"] == "success"
        else "skipped" if exec_result["outcome"] == "skipped"
        else "retrying"
    )
    sb.table("failed_payments").update({
        "status": new_status,
        "retry_count": record["retry_count"] + (0 if exec_result["outcome"] == "skipped" else 1),
    }).eq("id", failed_payment_id).execute()

    return {
        "failed_payment_id": failed_payment_id,
        "decision": decision,
        "execution": exec_result,
        "new_status": new_status,
    }
