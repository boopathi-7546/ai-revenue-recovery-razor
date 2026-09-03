"""
Decision engine — maps each classified failure to an intervention.

Intervention types:
  immediate_retry       – auto-retry right now
  retry_in_3_days       – schedule retry for 72 hours later
  send_payment_update   – send link to update expired card
  escalate_human        – hand off to human specialist
  skip_non_retryable    – log and skip (refunded / duplicate)
  skip_invalid_data     – zero/negative amount
  skip_cost_floor       – not worth the retry cost
  skip_max_attempts     – hard stop after 3 attempts
"""

import random
from agent.classifier import classify_failure, FailureClass
from agent.guardrails import check_guardrails, record_attempt, get_attempt_count

# A/B assignment pool (deterministic per run by seeding externally)
_ab_assignments: dict[str, str] = {}


def get_ab_variant(customer_id: str) -> str:
    """Randomly assign and cache A/B variant for a customer."""
    if customer_id not in _ab_assignments:
        _ab_assignments[customer_id] = random.choice(["A", "B"])
    return _ab_assignments[customer_id]


def decide_intervention(record: dict) -> dict:
    """
    Core decision function.

    Returns a decision dict:
    {
        "action":       str,   # intervention type
        "variant":      str,   # "A" | "B" | "N/A"
        "reasoning":    str,   # human-readable explanation
        "messages":     dict,  # {"english": ..., "hinglish": ...}
        "allowed":      bool,  # whether action should be executed
        "guardrail_msg":str,   # if not allowed, why
        "failure_class":str,
    }
    """
    # Late import to avoid circular; messaging is side-effect free
    from agent import messaging as M

    cid    = record["customer_id"]
    name   = record["customer_name"]
    amount = float(record.get("amount", 0))
    tier   = record.get("customer_tier", "low")
    retry  = int(record.get("retry_count", 0))
    reason = record.get("failure_reason", "")

    # Step 1: Classify
    fc: FailureClass = classify_failure(record)

    # Step 2: Guardrails (pre-check)
    allowed, guardrail_msg = check_guardrails(record, fc)

    if not allowed:
        # Determine skip action type
        if fc == "invalid_data":
            action = "skip_invalid_data"
            msgs   = M.msg_cost_skip(name, amount)
        elif fc == "non_retryable_skip":
            action = "skip_non_retryable"
            msgs   = (
                M.msg_skip_refunded(name, amount)
                if reason == "already_refunded"
                else M.msg_skip_duplicate(name, amount)
            )
        elif "Max attempts" in guardrail_msg:
            action = "skip_max_attempts"
            msgs   = M.msg_max_attempts(name, amount)
        elif "Cost-of-recovery" in guardrail_msg:
            action = "skip_cost_floor"
            msgs   = M.msg_cost_skip(name, amount)
        else:
            # Dedup guard fires here (and any future unnamed guardrail)
            action = "skip_guardrail"
            if "Dedup guard" in guardrail_msg:
                msgs = M.msg_dedup_skip(name, amount)
            else:
                msgs = M.msg_cost_skip(name, amount)  # safe fallback for unknowns

        return {
            "action":        action,
            "variant":       "N/A",
            "reasoning":     guardrail_msg,
            "messages":      msgs,
            "allowed":       False,
            "guardrail_msg": guardrail_msg,
            "failure_class": fc,
        }

    # Step 3: Intervention logic
    attempts = get_attempt_count(cid)

    if fc == "non_retryable_send_link":
        # Expired card → send update link regardless of tier
        action    = "send_payment_update"
        variant   = "N/A"
        reasoning = (
            f"Card expired → sending payment-update link "
            f"(tier={tier}, retry_count={retry})"
        )
        msgs = M.msg_payment_update_link(name, amount)

    elif fc == "retryable":
        variant = get_ab_variant(cid) if tier == "low" else "N/A"

        if tier == "high":
            if attempts == 0:
                # First attempt: immediate retry
                action    = "immediate_retry"
                reasoning = (
                    f"High-tier customer (₹{amount:,.2f}) — first auto-attempt, "
                    f"then escalate to human if it fails again"
                )
                msgs = M.msg_retry_immediate(name, amount, reason, variant)
            else:
                # Subsequent: escalate to human
                action    = "escalate_human"
                reasoning = (
                    f"High-tier customer — {attempts} auto-attempt(s) already done, "
                    f"escalating to human specialist"
                )
                msgs = M.msg_escalate_human(name, amount)

        else:  # low tier
            if retry == 0 or attempts == 0:
                action    = "immediate_retry"
                reasoning = (
                    f"Low-tier retryable — first attempt, variant={variant} "
                    f"({'urgency-framed' if variant == 'B' else 'standard'} message)"
                )
                msgs = M.msg_retry_immediate(name, amount, reason, variant)
            elif retry == 1 or attempts == 1:
                action    = "retry_in_3_days"
                reasoning = (
                    f"Low-tier retryable — {retry} prior retry(ies), "
                    f"scheduling retry in 3 days, variant={variant}"
                )
                msgs = M.msg_retry_3days(name, amount)
            else:
                # 3rd attempt — escalate
                action    = "escalate_human"
                reasoning = (
                    f"Low-tier — {retry} retries exhausted, escalating to human "
                    f"and flagging for review"
                )
                msgs = M.msg_escalate_human(name, amount)
    else:
        # Fallback
        action    = "escalate_human"
        variant   = "N/A"
        reasoning = f"Unknown failure class '{fc}' — escalating for safety"
        msgs      = M.msg_escalate_human(name, amount)

    # Step 4: Record attempt AFTER decision (only for allowed actions)
    record_attempt(record)

    return {
        "action":        action,
        "variant":       variant,
        "reasoning":     reasoning,
        "messages":      msgs,
        "allowed":       True,
        "guardrail_msg": "All guardrails passed",
        "failure_class": fc,
    }
