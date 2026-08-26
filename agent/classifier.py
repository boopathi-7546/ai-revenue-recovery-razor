"""
Failure reason classification: retryable vs non-retryable.
"""

from typing import Literal

# Failure reasons → classification
RETRYABLE_REASONS = {"card_declined", "insufficient_funds", "bank_timeout"}
NON_RETRYABLE_REASONS = {"expired_card", "already_refunded", "duplicate_charge"}

# Sub-classification for non-retryable
SEND_LINK_REASONS = {"expired_card"}          # → send payment-update link
SKIP_REASONS      = {"already_refunded", "duplicate_charge"}  # → hard skip

FailureClass = Literal["retryable", "non_retryable_send_link", "non_retryable_skip", "invalid_data"]


def classify_failure(record: dict) -> FailureClass:
    """
    Classify a payment record's failure reason.

    Returns one of:
        'retryable'              – safe to retry automatically
        'non_retryable_send_link' – expired card → send update link
        'non_retryable_skip'     – already refunded / duplicate charge → skip
        'invalid_data'           – zero/negative amount → skip immediately
    """
    amount = record.get("amount", 0)
    reason = record.get("failure_reason", "").strip().lower()

    # Guard: invalid amount
    if amount <= 0:
        return "invalid_data"

    if reason in RETRYABLE_REASONS:
        return "retryable"
    elif reason in SEND_LINK_REASONS:
        return "non_retryable_send_link"
    elif reason in SKIP_REASONS:
        return "non_retryable_skip"
    else:
        # Unknown reason — treat as non-retryable, escalate
        return "non_retryable_send_link"


def human_readable_class(cls: FailureClass) -> str:
    mapping = {
        "retryable":               "Retryable",
        "non_retryable_send_link": "Non-retryable (send payment-update link)",
        "non_retryable_skip":      "Non-retryable (skip — already resolved)",
        "invalid_data":            "Invalid data (zero/negative amount)",
    }
    return mapping.get(cls, cls)
