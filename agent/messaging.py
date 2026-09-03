"""
Outreach message generation in two variants:
  - English (plain, professional)
  - Hinglish (mixed Hindi-English, friendly)

Each function returns a dict: {"english": str, "hinglish": str}
Also generates A/B sub-variants for low-tier retryable customers.
"""

from typing import Literal

MsgLang = Literal["english", "hinglish"]


# ── Core message builders ──────────────────────────────────────────────────────

def msg_retry_immediate(name: str, amount: float, reason: str, variant: str = "A") -> dict:
    """For retryable failures — immediate retry message."""
    en_A = (
        f"Hi {name}, we noticed your payment of ₹{amount:,.2f} could not be processed "
        f"due to {reason.replace('_', ' ')}. We will automatically retry your payment "
        f"shortly. No action needed from your end."
    )
    en_B = (
        f"⚡ Urgent: {name}, your ₹{amount:,.2f} payment failed! We're retrying right now. "
        f"Please ensure your card/account is ready. Act within 2 hours to avoid service interruption."
    )
    hi_A = (
        f"Namaste {name}! Aapka ₹{amount:,.2f} ka payment {reason.replace('_', ' ')} ki wajah se "
        f"process nahi ho paya. Hum jaldi hi dobara try karenge — aapko kuch bhi karne ki zaroorat nahi."
    )
    hi_B = (
        f"⚡ Urgent! {name} ji, aapka ₹{amount:,.2f} ka payment fail ho gaya hai! "
        f"Hum abhi retry kar rahe hain — 2 ghante mein apna account check karein, "
        f"warna service band ho sakti hai."
    )
    return {
        "english": en_B if variant == "B" else en_A,
        "hinglish": hi_B if variant == "B" else hi_A,
    }


def msg_retry_3days(name: str, amount: float) -> dict:
    """For low-tier retryable after 1st fail — retry in 3 days."""
    return {
        "english": (
            f"Dear {name}, we were unable to process your payment of ₹{amount:,.2f}. "
            f"We will automatically retry in 3 days. Please ensure sufficient funds are available."
        ),
        "hinglish": (
            f"Hello {name}! Aapka ₹{amount:,.2f} ka payment abhi process nahi ho paya. "
            f"3 din baad hum phir se try karenge — tab tak apna balance check zaroor karein."
        ),
    }


def msg_payment_update_link(name: str, amount: float) -> dict:
    """For expired card — send a payment-update link."""
    link = f"https://pay.razorpay.com/update?cid=MOCK&amount={int(amount)}"
    return {
        "english": (
            f"Hi {name}, your saved card has expired and a payment of ₹{amount:,.2f} could not "
            f"be collected. Please update your payment method using this secure link: {link}"
        ),
        "hinglish": (
            f"Namaste {name}! Aapka card expire ho gaya hai aur ₹{amount:,.2f} ka payment "
            f"collect nahi ho paya. Apna payment method update karne ke liye yeh link use karein: {link}"
        ),
    }


def msg_escalate_human(name: str, amount: float) -> dict:
    """For high-tier customers after 1 auto-attempt — escalate to human."""
    return {
        "english": (
            f"Dear {name}, your payment of ₹{amount:,.2f} requires personal attention. "
            f"A Razorpay recovery specialist will contact you within 2 business hours."
        ),
        "hinglish": (
            f"{name} ji, aapka ₹{amount:,.2f} ka payment special attention maang raha hai. "
            f"Humare recovery expert 2 business hours mein aapko contact karenge."
        ),
    }


def msg_skip_refunded(name: str, amount: float) -> dict:
    return {
        "english": f"No action taken for {name} (₹{amount:,.2f}) — payment already refunded.",
        "hinglish": f"{name} ji ke liye koi action nahi liya — payment pehle se refund ho chuki hai.",
    }


def msg_skip_duplicate(name: str, amount: float) -> dict:
    return {
        "english": f"No action taken for {name} (₹{amount:,.2f}) — duplicate charge detected.",
        "hinglish": f"{name} ji ke liye koi action nahi liya — duplicate charge detect hua hai.",
    }


def msg_cost_skip(name: str, amount: float) -> dict:
    return {
        "english": (
            f"Recovery attempt skipped for {name} (₹{amount:,.2f}) — "
            f"amount below recovery cost threshold after multiple retries."
        ),
        "hinglish": (
            f"{name} ji ka recovery attempt skip kiya gaya — amount ₹{amount:,.2f} itna kam hai "
            f"ki retry ki cost justify nahi hoti."
        ),
    }


def msg_max_attempts(name: str, amount: float) -> dict:
    return {
        "english": (
            f"Maximum recovery attempts reached for {name} (₹{amount:,.2f}). "
            f"Case flagged for manual human review."
        ),
        "hinglish": (
            f"{name} ji ke liye maximum recovery attempts ho gaye hain (₹{amount:,.2f}). "
            f"Case manual review ke liye flag kiya gaya hai."
        ),
    }


def msg_dedup_skip(name: str, amount: float) -> dict:
    return {
        "english": (
            f"No action taken for {name} (₹{amount:,.2f}) — a recovery attempt "
            f"was already made within the last 24h. Skipping to avoid duplicate outreach."
        ),
        "hinglish": (
            f"{name} ji ke liye koi action nahi liya — pichhle 24 ghanton mein pehle se "
            f"ek attempt ho chuka hai. Duplicate outreach se bachne ke liye skip kiya gaya."
        ),
    }
