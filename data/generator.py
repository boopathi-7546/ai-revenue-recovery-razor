"""
Synthetic failed-payment dataset generator.
Produces 80 records (72 normal + 8 edge cases) saved as CSV and JSON.
"""

import csv
import json
import random
import os
from datetime import datetime, timedelta

random.seed(42)

# ── Constants ──────────────────────────────────────────────────────────────────
OUTPUT_DIR = os.path.join(os.path.dirname(__file__))
CSV_PATH   = os.path.join(OUTPUT_DIR, "failed_payments.csv")
JSON_PATH  = os.path.join(OUTPUT_DIR, "failed_payments.json")

FAILURE_REASONS = [
    "card_declined",
    "insufficient_funds",
    "expired_card",
    "bank_timeout",
    "already_refunded",
    "duplicate_charge",
]

NORMAL_REASONS = ["card_declined", "insufficient_funds", "expired_card", "bank_timeout"]

FIRST_NAMES = [
    "Aarav", "Priya", "Rahul", "Sneha", "Vikram", "Ananya", "Rohit",
    "Meera", "Karan", "Divya", "Aditya", "Pooja", "Nikhil", "Riya",
    "Siddharth", "Kavya", "Arjun", "Ishaan", "Naina", "Yash",
    "Aishwarya", "Rohan", "Sanya", "Manav", "Tanya", "Kunal",
    "Shreya", "Varun", "Roshni", "Aman", "Simran", "Akash",
    "Bhavna", "Dev", "Falak", "Gaurav", "Hema", "Ishan",
    "Jaya", "Krish", "Lakshmi", "Mohit", "Nisha", "Om",
    "Poonam", "Qasim", "Rajat", "Sarita", "Tarun", "Uma",
]

LAST_NAMES = [
    "Sharma", "Verma", "Patel", "Singh", "Kumar", "Gupta", "Joshi",
    "Mehta", "Nair", "Reddy", "Rao", "Iyer", "Agarwal", "Shah",
    "Chaudhary", "Malhotra", "Kapoor", "Bhat", "Pillai", "Tiwari",
]

BASE_DATE = datetime(2026, 7, 1, 0, 0, 0)


def random_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def random_timestamp(start=BASE_DATE, days_range=55):
    offset = timedelta(
        days=random.randint(0, days_range),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )
    return (start + offset).strftime("%Y-%m-%dT%H:%M:%S")


def derive_tier(amount: float) -> str:
    return "high" if amount >= 5000 else "low"


def build_normal_record(idx: int) -> dict:
    reason = random.choice(NORMAL_REASONS)
    # Amount spread: ₹100–₹25000, weighted toward ₹500–₹8000
    amount = round(random.triangular(100, 25000, 3500), 2)
    retry_count = random.choices([0, 1, 2, 3], weights=[40, 30, 20, 10])[0]
    ts = random_timestamp()
    return {
        "customer_id": f"CUST{1000 + idx:04d}",
        "customer_name": random_name(),
        "amount": amount,
        "failure_reason": reason,
        "failed_at": ts,
        "retry_count": retry_count,
        "customer_tier": derive_tier(amount),
    }


def build_edge_cases() -> list[dict]:
    """8 deliberate edge cases for the agent to handle as exceptions."""
    base_idx = 9000

    cases = [
        # 1. Already refunded — must be skipped, logged
        {
            "customer_id": f"CUST{base_idx + 1:04d}",
            "customer_name": random_name(),
            "amount": 2499.00,
            "failure_reason": "already_refunded",
            "failed_at": random_timestamp(),
            "retry_count": 0,
            "customer_tier": "low",
        },
        # 2. Already refunded (high tier)
        {
            "customer_id": f"CUST{base_idx + 2:04d}",
            "customer_name": random_name(),
            "amount": 7999.00,
            "failure_reason": "already_refunded",
            "failed_at": random_timestamp(),
            "retry_count": 1,
            "customer_tier": "high",
        },
        # 3. Already refunded (tiny amount)
        {
            "customer_id": f"CUST{base_idx + 3:04d}",
            "customer_name": random_name(),
            "amount": 99.00,
            "failure_reason": "already_refunded",
            "failed_at": random_timestamp(),
            "retry_count": 0,
            "customer_tier": "low",
        },
        # 4. Duplicate charge — must be skipped
        {
            "customer_id": f"CUST{base_idx + 4:04d}",
            "customer_name": random_name(),
            "amount": 4999.00,
            "failure_reason": "duplicate_charge",
            "failed_at": random_timestamp(),
            "retry_count": 0,
            "customer_tier": "low",
        },
        # 5. Duplicate charge (high tier)
        {
            "customer_id": f"CUST{base_idx + 5:04d}",
            "customer_name": random_name(),
            "amount": 12000.00,
            "failure_reason": "duplicate_charge",
            "failed_at": random_timestamp(),
            "retry_count": 0,
            "customer_tier": "high",
        },
        # 6. Zero amount — cost-guard catch
        {
            "customer_id": f"CUST{base_idx + 6:04d}",
            "customer_name": random_name(),
            "amount": 0.00,
            "failure_reason": "card_declined",
            "failed_at": random_timestamp(),
            "retry_count": 2,
            "customer_tier": "low",
        },
        # 7. Negative amount — invalid data, hard skip
        {
            "customer_id": f"CUST{base_idx + 7:04d}",
            "customer_name": random_name(),
            "amount": -500.00,
            "failure_reason": "bank_timeout",
            "failed_at": random_timestamp(),
            "retry_count": 1,
            "customer_tier": "low",
        },
        # 8. Tiny amount + high retry_count → cost not worth it
        {
            "customer_id": f"CUST{base_idx + 8:04d}",
            "customer_name": random_name(),
            "amount": 120.00,
            "failure_reason": "insufficient_funds",
            "failed_at": random_timestamp(),
            "retry_count": 2,
            "customer_tier": "low",
        },
    ]
    for c in cases:
        c["customer_tier"] = derive_tier(c["amount"])
    return cases


def generate_dataset() -> list[dict]:
    normal_records = [build_normal_record(i) for i in range(1, 73)]
    edge_cases     = build_edge_cases()
    all_records    = normal_records + edge_cases
    random.shuffle(all_records)
    return all_records


def save_dataset(records: list[dict]):
    # CSV
    fieldnames = [
        "customer_id", "customer_name", "amount", "failure_reason",
        "failed_at", "retry_count", "customer_tier",
    ]
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    # JSON
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    print(f"[DataGen] Generated {len(records)} records → {CSV_PATH}")
    print(f"[DataGen] JSON copy  → {JSON_PATH}")
    return records


def load_dataset() -> list[dict]:
    """Load existing dataset, or generate if absent."""
    if not os.path.exists(CSV_PATH):
        records = generate_dataset()
        save_dataset(records)
        return records

    records = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["amount"]      = float(row["amount"])
            row["retry_count"] = int(row["retry_count"])
            records.append(row)
    return records


if __name__ == "__main__":
    recs = generate_dataset()
    save_dataset(recs)
    print(f"\nSample record:\n{json.dumps(recs[0], indent=2)}")
