"""
main.py — One-command runner.

Usage:
    python main.py

Regenerates data + runs the full agent pipeline + writes audit + metrics.
"""

import os
import sys
import random

# Seed for reproducibility
random.seed(99)

# Ensure project root is on path
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from data.generator import generate_dataset, save_dataset
from agent.loop import run_pipeline

if __name__ == "__main__":
    print("=" * 60)
    print("  AI REVENUE RECOVERY — MAIN RUNNER")
    print("=" * 60)

    # Step 1: Generate (or regenerate) synthetic dataset
    print("\n[Step 1] Generating synthetic dataset...")
    records = generate_dataset()
    save_dataset(records)

    # Step 2: Run agent pipeline
    print("\n[Step 2] Running agent pipeline...")
    audit_records, metrics = run_pipeline(records)

    print("\n" + "=" * 60)
    print("  ✓ Pipeline complete.")
    print(f"  ✓ Audit trail: logs/audit_trail.csv ({len(audit_records)} rows)")
    print(f"  ✓ Metrics:     logs/metrics.json")
    print("=" * 60)
    print("\nNow launch the dashboard with:")
    print("  streamlit run app.py")
    print()
