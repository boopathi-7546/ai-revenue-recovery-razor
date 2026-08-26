"""Integration test for the Try It Live tab agent calls."""
import sys
sys.path.insert(0, '.')
import io, csv as _csv, pandas as pd
from agent.guardrails import reset_state
from agent.decision import decide_intervention
from agent.executor import execute_intervention

# ── Part 1: single record ────────────────────────────────────────────
print("=== PART 1: Single record ===")
reset_state()
rec = {
    'customer_id': 'DEMO1234', 'customer_name': 'Priya Sharma',
    'amount': 1000.0, 'failure_reason': 'card_declined',
    'failed_at': '2026-08-26T21:00:00', 'retry_count': 0, 'customer_tier': 'low',
}
dec = decide_intervention(rec)
exr = execute_intervention(rec, dec)
print(f"  Action  : {dec['action']}")
print(f"  Outcome : {exr['outcome']}")
print(f"  Variant : {dec['variant']}")
print(f"  English : {dec['messages'].get('english','')[:70]}")
print(f"  Hinglish: {dec['messages'].get('hinglish','')[:70]}")
print()

# ── Edge: already_refunded → should skip ────────────────────────────
print("=== Edge: already_refunded ===")
reset_state()
rec2 = {**rec, 'failure_reason': 'already_refunded', 'amount': 7999.0, 'customer_tier': 'high'}
dec2 = decide_intervention(rec2)
exr2 = execute_intervention(rec2, dec2)
print(f"  Action  : {dec2['action']}")
print(f"  Outcome : {exr2['outcome']}")
assert exr2['outcome'] == 'skipped', "Expected skipped!"
print()

# ── Part 2: batch of 5 (mirrors sample CSV) ──────────────────────────
print("=== PART 2: Batch 5 rows ===")
SAMPLE = [
    ['customer_name', 'amount', 'failure_reason'],
    ['Aarav Sharma',   6500.0,  'card_declined'],
    ['Priya Verma',     850.0,  'insufficient_funds'],
    ['Rohit Patel',   12000.0,  'bank_timeout'],
    ['Sneha Singh',     120.0,  'insufficient_funds'],
    ['Vikram Gupta',   8750.0,  'expired_card'],
]
buf = io.StringIO()
_csv.writer(buf).writerows(SAMPLE)
df = pd.read_csv(io.StringIO(buf.getvalue()))
df.columns = df.columns.str.strip().str.lower()
df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)

reset_state()
batch = []
for i in range(len(df)):
    row = df.iloc[i]
    amt = float(row['amount'])
    r = {
        'customer_id': f'BATCH{i+1:04d}',
        'customer_name': str(row['customer_name']),
        'amount': amt,
        'failure_reason': str(row['failure_reason']).strip().lower(),
        'failed_at': '2026-08-26T21:00:00',
        'retry_count': 0,
        'customer_tier': 'high' if amt >= 5000 else 'low',
    }
    d = decide_intervention(r)
    e = execute_intervention(r, d)
    batch.append({'name': r['customer_name'], 'action': d['action'], 'outcome': e['outcome']})

for b in batch:
    print(f"  {b['name']:<18s}  {b['action']:<26s}  {b['outcome']}")

at_risk = sum(df['amount'].tolist())
print(f"\n  5 rows processed, total amount: INR {at_risk:,.2f}")
print()
print("ALL TESTS PASSED")
