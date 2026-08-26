"""
Mock executor — simulates external actions without real API calls.
All actions are logged to console and return a simulated outcome.
"""

import random
from datetime import datetime

# Simulated success rates per action type (for realism in mock data)
MOCK_SUCCESS_RATES = {
    "immediate_retry":     0.62,
    "retry_in_3_days":     0.48,
    "send_payment_update": 0.71,
    "escalate_human":      0.85,
    "skip_non_retryable":  None,  # Not an action — always "skipped"
    "skip_invalid_data":   None,
    "skip_cost_floor":     None,
    "skip_max_attempts":   None,
    "skip_guardrail":      None,
}

_SKIP_ACTIONS = {
    "skip_non_retryable", "skip_invalid_data",
    "skip_cost_floor", "skip_max_attempts", "skip_guardrail",
}


def execute_intervention(record: dict, decision: dict) -> dict:
    """
    Mock-execute the decided intervention.

    Returns:
    {
        "outcome":     "success" | "failed" | "skipped",
        "exec_log":    str,       # human-readable execution note
        "executed_at": str,       # ISO timestamp
    }
    """
    action  = decision["action"]
    cid     = record["customer_id"]
    name    = record["customer_name"]
    amount  = float(record.get("amount", 0))
    now_str = datetime.now().isoformat(timespec="seconds")

    if action in _SKIP_ACTIONS:
        msg = f"[SKIP]    {cid} ({name}) — {decision['guardrail_msg']}"
        print(msg)
        return {
            "outcome":     "skipped",
            "exec_log":    msg,
            "executed_at": now_str,
        }

    success_rate = MOCK_SUCCESS_RATES.get(action, 0.5)
    succeeded    = random.random() < success_rate
    outcome      = "success" if succeeded else "failed"

    if action == "immediate_retry":
        exec_log = (
            f"[MOCK API] Retry payment for {cid} ({name}) ₹{amount:,.2f} — "
            f"{'✓ APPROVED' if succeeded else '✗ DECLINED again'}"
        )
    elif action == "retry_in_3_days":
        exec_log = (
            f"[MOCK JOB] Scheduled 3-day retry for {cid} ({name}) ₹{amount:,.2f} — "
            f"job_id=JOB_{cid}_72H queued {'successfully' if succeeded else '(queue error)'}"
        )
    elif action == "send_payment_update":
        exec_log = (
            f"[MOCK SMS] Payment-update link sent to {cid} ({name}) ₹{amount:,.2f} — "
            f"delivery {'confirmed' if succeeded else 'failed (invalid number)'}"
        )
    elif action == "escalate_human":
        exec_log = (
            f"[MOCK CRM] Escalation ticket created for {cid} ({name}) ₹{amount:,.2f} — "
            f"ticket_id=TKT_{cid} {'assigned to agent' if succeeded else '(queue full, retry later)'}"
        )
    else:
        exec_log = f"[MOCK] Unknown action '{action}' for {cid} — no-op"

    print(exec_log)
    return {
        "outcome":     outcome,
        "exec_log":    exec_log,
        "executed_at": now_str,
    }
