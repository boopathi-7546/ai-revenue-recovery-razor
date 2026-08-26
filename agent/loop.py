"""
Agent orchestration loop:
    detect → diagnose → decide → execute → log

Pipeline is entirely pure Python; no external frameworks.
"""

import csv
import os
import json
import sys
from datetime import datetime

# ── Path setup ─────────────────────────────────────────────────────────────────
ROOT_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR  = os.path.join(ROOT_DIR, "data")
LOGS_DIR  = os.path.join(ROOT_DIR, "logs")
AUDIT_CSV = os.path.join(LOGS_DIR, "audit_trail.csv")
AUDIT_JSON = os.path.join(LOGS_DIR, "audit_trail.json")
METRICS_JSON = os.path.join(LOGS_DIR, "metrics.json")

AUDIT_FIELDS = [
    "timestamp", "customer_id", "customer_name", "amount",
    "failure_reason", "customer_tier", "failure_class",
    "action_taken", "variant", "reasoning", "outcome",
    "exec_log", "executed_at", "failed_at", "msg_english", "msg_hinglish",
]


def _ensure_dirs():
    os.makedirs(LOGS_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)


# ── Stage 1: Detect ────────────────────────────────────────────────────────────
def detect(records: list[dict]) -> list[dict]:
    """Load all records as 'failed payments' needing triage."""
    print(f"\n[Detect] {len(records)} failed payment records loaded for processing.")
    return records


# ── Stage 2: Diagnose ─────────────────────────────────────────────────────────
def diagnose(records: list[dict]) -> list[tuple[dict, str]]:
    """Classify each record and pair (record, failure_class)."""
    from agent.classifier import classify_failure
    diagnosed = []
    for rec in records:
        fc = classify_failure(rec)
        diagnosed.append((rec, fc))
    print(f"[Diagnose] Classified {len(diagnosed)} records.")
    return diagnosed


# ── Stage 3: Decide ────────────────────────────────────────────────────────────
def decide(diagnosed: list[tuple[dict, str]]) -> list[tuple[dict, dict]]:
    """Choose intervention for each record."""
    from agent.decision import decide_intervention
    decisions = []
    for rec, _ in diagnosed:
        decision = decide_intervention(rec)
        decisions.append((rec, decision))
    print(f"[Decide] Interventions chosen for {len(decisions)} records.")
    return decisions


# ── Stage 4: Execute ───────────────────────────────────────────────────────────
def execute(decisions: list[tuple[dict, dict]]) -> list[dict]:
    """Mock-execute each intervention and collect audit records."""
    from agent.executor import execute_intervention
    audit_records = []
    now = datetime.now().isoformat(timespec="seconds")

    for rec, dec in decisions:
        exec_result = execute_intervention(rec, dec)

        audit_row = {
            "timestamp":      now,
            "customer_id":    rec["customer_id"],
            "customer_name":  rec["customer_name"],
            "amount":         rec["amount"],
            "failure_reason": rec["failure_reason"],
            "customer_tier":  rec["customer_tier"],
            "failure_class":  dec["failure_class"],
            "action_taken":   dec["action"],
            "variant":        dec["variant"],
            "reasoning":      dec["reasoning"],
            "outcome":        exec_result["outcome"],
            "exec_log":       exec_result["exec_log"],
            "executed_at":    exec_result["executed_at"],
            "failed_at":      rec.get("failed_at", ""),
            "msg_english":    dec["messages"].get("english", ""),
            "msg_hinglish":   dec["messages"].get("hinglish", ""),
        }
        audit_records.append(audit_row)

    print(f"[Execute] {len(audit_records)} actions executed/logged.")
    return audit_records


# ── Stage 5: Log ───────────────────────────────────────────────────────────────
def log_audit(audit_records: list[dict]):
    """Persist audit trail as CSV and JSON."""
    _ensure_dirs()

    with open(AUDIT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=AUDIT_FIELDS)
        writer.writeheader()
        writer.writerows(audit_records)

    with open(AUDIT_JSON, "w", encoding="utf-8") as f:
        json.dump(audit_records, f, indent=2, ensure_ascii=False)

    print(f"[Log] Audit trail → {AUDIT_CSV} ({len(audit_records)} rows)")
    print(f"[Log] Audit JSON  → {AUDIT_JSON}")


# ── Full pipeline ──────────────────────────────────────────────────────────────
def run_pipeline(records: list[dict]) -> tuple[list[dict], dict]:
    """
    Run the full agent loop and return (audit_records, metrics).
    """
    from agent.metrics import compute_metrics, save_metrics, print_summary
    from agent.guardrails import reset_state

    # Reset per-run state
    reset_state()

    print("\n" + "━" * 60)
    print("  AI REVENUE RECOVERY AGENT — STARTING PIPELINE")
    print("━" * 60)

    detected   = detect(records)
    diagnosed  = diagnose(detected)
    decisions  = decide(diagnosed)
    audit_recs = execute(decisions)

    log_audit(audit_recs)

    metrics = compute_metrics(audit_recs)
    save_metrics(metrics, METRICS_JSON)
    print_summary(metrics)

    return audit_recs, metrics


def load_audit_trail() -> list[dict]:
    """Load existing audit trail from CSV (for dashboard)."""
    if not os.path.exists(AUDIT_CSV):
        return []
    rows = []
    with open(AUDIT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["amount"] = float(row.get("amount", 0))
            rows.append(row)
    return rows


def load_metrics() -> dict:
    """Load metrics JSON (for dashboard)."""
    if not os.path.exists(METRICS_JSON):
        return {}
    with open(METRICS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)
