# AI Revenue Recovery Agent 💳

> **Hackathon submission** — An autonomous Python agent that detects failed subscription payments, diagnoses root causes, chooses bounded recovery interventions, executes them (mocked), and presents results in a polished Streamlit dashboard with 3D visuals.
>    🔗 **Live Demo:** https://ai-revenue-recovery-razor-jjrmeywxyr3lanfs7r34nh.streamlit.app
   📂 **Repository:** https://github.com/boopathi-7546/ai-revenue-recovery-razor

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate data + run agent (one command)
python main.py

# 3. Launch dashboard
streamlit run app.py
```

No API keys required — all external actions (SMS, payment retries, CRM tickets) are **mocked/simulated**.

---

## Problem Statement

Subscription businesses lose significant revenue to failed payments. Most systems simply retry blindly or abandon the charge. This project shows how an AI agent can:

1. **Detect** which payments failed and why
2. **Diagnose** whether the failure is retryable or unrecoverable
3. **Decide** the optimal recovery intervention per customer segment
4. **Execute** the intervention within hard guardrails
5. **Measure** results with full audit rigour and A/B testing

---

## Data Model

**`data/failed_payments.csv`** — 80 records (72 realistic + 8 deliberate edge cases)

| Field | Type | Description |
|---|---|---|
| `customer_id` | string | Unique customer identifier |
| `customer_name` | string | Full name (synthetic) |
| `amount` | float (INR) | Payment amount |
| `failure_reason` | enum | See failure reasons below |
| `failed_at` | ISO 8601 | Timestamp of failure |
| `retry_count` | int | Prior retry attempts |
| `customer_tier` | derived | `high` (≥ ₹5,000) or `low` |

**Failure reasons:**

| Reason | Class | Default Intervention |
|---|---|---|
| `card_declined` | Retryable | Immediate retry |
| `insufficient_funds` | Retryable | Immediate retry / 3-day retry |
| `bank_timeout` | Retryable | Immediate retry |
| `expired_card` | Non-retryable | Send payment-update link |
| `already_refunded` | Non-retryable | **Hard skip** |
| `duplicate_charge` | Non-retryable | **Hard skip** |

---

## Decision Logic

```
For each failed payment:
  1. Classify failure reason → retryable / non-retryable-link / non-retryable-skip / invalid
  2. Apply guardrails (see below)
  3. Choose intervention:
     - high-tier + retryable + 0 attempts  → immediate_retry
     - high-tier + retryable + 1+ attempts → escalate_human
     - low-tier  + retryable + 0 retries   → immediate_retry (A/B variant)
     - low-tier  + retryable + 1 retry     → retry_in_3_days (A/B variant)
     - low-tier  + retryable + 2+ retries  → escalate_human
     - expired_card                         → send_payment_update
     - already_refunded / duplicate_charge  → skip_non_retryable
     - zero / negative amount               → skip_invalid_data
     - amount < ₹150 AND retry_count ≥ 2   → skip_cost_floor
```

---

## Guardrails

| Guardrail | Rule |
|---|---|
| **Max attempts** | Never exceed 3 recovery attempts per customer |
| **24h dedup** | No duplicate intervention within 24 hours (simulated via timestamps) |
| **Hard stop** | After 3 failed attempts → flag for human review |
| **Never act on** | `already_refunded`, `duplicate_charge` — log and skip |
| **Cost floor** | If `amount < ₹150` AND `retry_count ≥ 2` → skip (not worth the cost) |
| **Invalid data** | If `amount ≤ 0` → skip immediately |

---

## Exception List — Correctly Skipped Cases

| Customer | Amount | Reason | Action | Why Skipped |
|---|---|---|---|---|
| CUST9001 | ₹2,499 | `already_refunded` | `skip_non_retryable` | Payment was already refunded — intervening could cause a double-refund |
| CUST9002 | ₹7,999 | `already_refunded` | `skip_non_retryable` | Same — high-tier but same policy applies |
| CUST9003 | ₹99 | `already_refunded` | `skip_non_retryable` | Tiny refunded amount — no action warranted |
| CUST9004 | ₹4,999 | `duplicate_charge` | `skip_non_retryable` | Duplicate charge detected — retrying would double-bill the customer |
| CUST9005 | ₹12,000 | `duplicate_charge` | `skip_non_retryable` | High-value duplicate — escalate for review, never auto-retry |
| CUST9006 | ₹0 | `card_declined` | `skip_invalid_data` | Zero amount — invalid record, likely a data error |
| CUST9007 | ₹−500 | `bank_timeout` | `skip_invalid_data` | Negative amount — invalid data, must not be processed |
| CUST9008 | ₹120 | `insufficient_funds` | `skip_cost_floor` | Below ₹150 cost floor with retry_count=2 — recovery cost exceeds amount |

---

## A/B Test Design

For **low-tier retryable** failures, customers are randomly split 50/50:

| Variant | Message Style | Retry Window |
|---|---|---|
| **A** | Plain English reminder, neutral tone | Standard (3 days) |
| **B** | Urgency-framed, shorter window, emoji | 2-hour urgency window |

Results tracked by: attempts, recoveries, recovery rate %, amount recovered.

---

## Audit Trail

Every agent action is logged to `logs/audit_trail.csv` and `logs/audit_trail.json`:

| Field | Description |
|---|---|
| `timestamp` | When the agent processed this record |
| `customer_id` | Customer identifier |
| `customer_name` | Customer name |
| `amount` | Payment amount (INR) |
| `failure_reason` | Original failure reason |
| `customer_tier` | High or low |
| `failure_class` | Retryable / non-retryable classification |
| `action_taken` | Intervention chosen |
| `variant` | A/B variant (or N/A) |
| `reasoning` | Detailed human-readable explanation |
| `outcome` | `success` / `failed` / `skipped` |
| `exec_log` | Mock execution log line |
| `executed_at` | Execution timestamp |
| `msg_english` | English outreach message |
| `msg_hinglish` | Hinglish outreach message |

---

## Project Structure

```
d:\Razorpay\
├── data/
│   ├── generator.py        # Synthetic dataset generator
│   ├── failed_payments.csv # Generated dataset (auto-created)
│   └── failed_payments.json
├── agent/
│   ├── __init__.py
│   ├── classifier.py       # Retryable vs non-retryable classification
│   ├── decision.py         # Intervention chooser + tier logic
│   ├── guardrails.py       # Hard limits: max attempts, dedup, cost floor
│   ├── messaging.py        # EN + Hinglish message variants
│   ├── executor.py         # Mocked executor (prints/logs actions)
│   ├── loop.py             # Orchestrated pipeline
│   └── metrics.py          # Headline metrics + A/B analysis
├── logs/
│   ├── audit_trail.csv     # Structured audit log (auto-generated)
│   ├── audit_trail.json
│   └── metrics.json        # Computed metrics (auto-generated)
├── app.py                  # Streamlit dashboard
├── main.py                 # One-command runner
├── requirements.txt
└── README.md
```

---

## Dashboard Features

| Feature | Implementation |
|---|---|
| Animated metric cards | `st.empty()` count-up loop |
| Recovery rate line chart | Plotly animated line (spline, fill) |
| Recovery by failure reason | Plotly stacked bar |
| A/B variant comparison | Plotly grouped bar |
| Action distribution | Plotly donut chart |
| Recovery by tier | Plotly grouped bar |
| Filterable audit log | `st.dataframe` with multi-select filters |
| Exception viewer | Custom HTML cards with pill tags |
| 3D visualization | Three.js via `st.components.v1.html()` |
| Success animation | streamlit-lottie |
| Balloons | `st.balloons()` if recovery rate ≥ 70% |
| Language toggle | EN / Hinglish message sidebar preview |
| Dark fintech theme | Custom CSS injected via `st.markdown` |

---

## Design Decisions

- **No external framework**: Plain Python classes/functions — easier to audit, debug, and judge
- **Mocked execution**: All "API calls" are `print()` statements with simulated success rates
- **Seed-controlled randomness**: `random.seed(99)` in `main.py` ensures reproducible results
- **Priority order built**: Part A (accuracy/rigour) → Part B core → Part B visual → 3D stretch goal
