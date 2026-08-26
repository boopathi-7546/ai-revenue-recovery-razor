"""
Metrics computation:
  - Headline metrics: total at risk, recovered, recovery rate
  - A/B test analysis: variant A vs B recovery rates
  - Unresolved exception list
"""

import json
from collections import defaultdict


def compute_metrics(audit_records: list[dict]) -> dict:
    """
    Compute headline and A/B metrics from the audit trail.

    audit_records fields expected:
        customer_id, customer_name, amount, action_taken,
        reasoning, outcome, variant, failure_reason, customer_tier,
        executed_at, failure_class
    """
    total_at_risk  = 0.0
    total_recovered = 0.0
    exceptions     = []

    # A/B tracking
    ab_stats = {
        "A": {"attempts": 0, "recovered": 0, "amount_recovered": 0.0},
        "B": {"attempts": 0, "recovered": 0, "amount_recovered": 0.0},
    }

    # Recovery by failure reason
    reason_stats: dict[str, dict] = defaultdict(lambda: {
        "attempts": 0, "recovered": 0, "amount_at_risk": 0.0, "amount_recovered": 0.0
    })

    # Recovery over time (by date)
    time_stats: dict[str, dict] = defaultdict(lambda: {
        "attempts": 0, "recovered": 0, "amount_recovered": 0.0
    })

    skipped_actions = {
        "skip_non_retryable", "skip_invalid_data",
        "skip_cost_floor", "skip_max_attempts", "skip_guardrail",
    }

    for rec in audit_records:
        amount       = float(rec.get("amount", 0))
        action       = rec.get("action_taken", "")
        outcome      = rec.get("outcome", "")
        variant      = rec.get("variant", "N/A")
        reason       = rec.get("failure_reason", "unknown")
        exec_at      = rec.get("failed_at", rec.get("executed_at", ""))[:10]  # use original failure date for spread

        # Edge: log exceptions (skipped / non-retryable / flagged)
        if action in skipped_actions or outcome == "skipped":
            exceptions.append({
                "customer_id":   rec.get("customer_id"),
                "customer_name": rec.get("customer_name"),
                "amount":        amount,
                "reason":        reason,
                "action":        action,
                "explanation":   rec.get("reasoning", ""),
            })
            continue

        # All attempted (non-skipped) contribute to "at risk"
        total_at_risk += amount
        reason_stats[reason]["attempts"]     += 1
        reason_stats[reason]["amount_at_risk"] += amount
        time_stats[exec_at]["attempts"]      += 1

        if outcome == "success":
            total_recovered += amount
            reason_stats[reason]["recovered"]        += 1
            reason_stats[reason]["amount_recovered"]  += amount
            time_stats[exec_at]["recovered"]          += 1
            time_stats[exec_at]["amount_recovered"]   += amount

        # A/B stats (only low-tier retryable with variant A or B)
        if variant in ("A", "B"):
            ab_stats[variant]["attempts"]        += 1
            ab_stats[variant]["amount_recovered"] += amount if outcome == "success" else 0
            if outcome == "success":
                ab_stats[variant]["recovered"] += 1

    # Compute rates
    recovery_rate = (total_recovered / total_at_risk * 100) if total_at_risk > 0 else 0.0

    for v in ("A", "B"):
        att = ab_stats[v]["attempts"]
        ab_stats[v]["recovery_rate"] = (
            ab_stats[v]["recovered"] / att * 100 if att > 0 else 0.0
        )

    for r in reason_stats:
        att = reason_stats[r]["attempts"]
        reason_stats[r]["recovery_rate"] = (
            reason_stats[r]["recovered"] / att * 100 if att > 0 else 0.0
        )

    # Build time series (sorted by date)
    time_series = []
    cumulative_recovered = 0.0
    for date in sorted(time_stats.keys()):
        if not date:
            continue
        cumulative_recovered += time_stats[date]["amount_recovered"]
        cum_rate = (
            cumulative_recovered / total_at_risk * 100
            if total_at_risk > 0 else 0.0
        )
        time_series.append({
            "date":                date,
            "daily_recovered":     time_stats[date]["amount_recovered"],
            "cumulative_recovered": cumulative_recovered,
            "cumulative_rate":     round(cum_rate, 2),
        })

    return {
        "total_at_risk":      round(total_at_risk, 2),
        "total_recovered":    round(total_recovered, 2),
        "recovery_rate_pct":  round(recovery_rate, 2),
        "ab_stats":           ab_stats,
        "reason_stats":       dict(reason_stats),
        "exceptions":         exceptions,
        "exception_count":    len(exceptions),
        "time_series":        time_series,
    }


def save_metrics(metrics: dict, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    print(f"[Metrics] Saved to {path}")


def print_summary(metrics: dict):
    print("\n" + "═" * 60)
    print("  RECOVERY METRICS SUMMARY")
    print("═" * 60)
    print(f"  Total at risk:      ₹{metrics['total_at_risk']:>12,.2f}")
    print(f"  Total recovered:    ₹{metrics['total_recovered']:>12,.2f}")
    print(f"  Recovery rate:       {metrics['recovery_rate_pct']:>8.1f}%")
    print(f"  Exception count:     {metrics['exception_count']:>8d}")
    print()
    print("  A/B Test Results:")
    for v in ("A", "B"):
        s = metrics["ab_stats"][v]
        print(
            f"    Variant {v}: {s['attempts']} attempts, "
            f"{s['recovered']} recovered, "
            f"{s['recovery_rate']:.1f}% rate, "
            f"₹{s['amount_recovered']:,.2f} recovered"
        )
    print()
    print("  Recovery by Failure Reason:")
    for reason, s in metrics["reason_stats"].items():
        print(
            f"    {reason:<25s}: {s['recovered']}/{s['attempts']} "
            f"({s['recovery_rate']:.1f}%)"
        )
    print()
    print("  Unresolved Exceptions:")
    for ex in metrics["exceptions"]:
        print(
            f"    [{ex['action']:<25s}] {ex['customer_id']} "
            f"₹{ex['amount']:,.2f} — {ex['reason']}"
        )
    print("═" * 60)
