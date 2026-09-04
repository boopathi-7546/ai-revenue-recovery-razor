"""
Direct seed — bypasses HTTP, calls process_failed_payment() from service layer directly.
No uvicorn needed. Run from repo root: python scripts/direct_seed.py
"""
import os, sys
sys.path.insert(0, 'd:/Razorpay')

# Force DISABLE_DEDUP=true before importing anything
os.environ['DISABLE_DEDUP'] = 'true'

from datetime import datetime, timedelta, timezone
from backend.db import get_client
from backend.service import process_failed_payment

MID = os.environ.get('SEED_MERCHANT_ID', 'd5c1e368-3f0e-4310-9e1e-57beaaa1a785')
NOW = datetime.now(timezone.utc)

def ts(h): return (NOW - timedelta(hours=h)).isoformat()

RECORDS = [
    ('Meera Krishnamurthy',  'meera.k@ex.in',   'CUST-MEERA-001', 'high', 2499.0, 'card_declined',      0, ts(72)),
    ('Arjun Venkataraman',   'arjun.v@ex.in',   'CUST-ARJUN-002', 'high', 1850.0, 'bank_timeout',       0, ts(68)),
    ('Priya Subramaniam',    'priya.s@ex.in',   'CUST-PRIYA-003', 'high', 3200.0, 'insufficient_funds', 0, ts(60)),
    ('Ravi Shankar Gupta',   'ravi.g@ex.in',    'CUST-RAVI-004',  'low',   499.0, 'card_declined',      0, ts(55)),
    ('Divya Nambiar',        'divya.n@ex.in',   'CUST-DIVYA-005', 'low',   799.0, 'bank_timeout',       0, ts(50)),
    ('Sanjay Mehrotra',      'sanjay.m@ex.in',  'CUST-SANJAY-006','high', 1200.0, 'card_declined',      0, ts(48)),
    ('Ananya Bhattacharya',  'ananya.b@ex.in',  'CUST-ANANYA-007','low',   299.0, 'insufficient_funds', 0, ts(45)),
    ('Vikram Malhotra',      'vikram.m@ex.in',  'CUST-VIKRAM-008','high', 4500.0, 'bank_timeout',       0, ts(42)),
    ('Sunita Pillai',        'sunita.p@ex.in',  'CUST-SUNITA-009','low',   650.0, 'card_declined',      0, ts(38)),
    ('Rohit Agarwal',        'rohit.a@ex.in',   'CUST-ROHIT-010', 'high', 2100.0, 'card_declined',      0, ts(35)),
    ('Kavitha Rajan',        'kavitha.r@ex.in', 'CUST-KAVITHA-011','low',  399.0, 'bank_timeout',       0, ts(30)),
    ('Amrit Singh Sandhu',   'amrit.s@ex.in',   'CUST-AMRIT-012', 'high', 1750.0, 'insufficient_funds', 0, ts(28)),
    ('Neha Joshi',           'neha.j@ex.in',    'CUST-NEHA-013',  'low',   550.0, 'card_declined',      0, ts(24)),
    ('Karthik Balakrishnan', 'karthik.b@ex.in', 'CUST-KARTHIK-014','high',3800.0, 'card_declined',      0, ts(20)),
    # Non-retryable: expired card -> send_payment_update
    ('Pooja Desai',          'pooja.d@ex.in',   'CUST-POOJA-015', 'low',   899.0, 'expired_card',       0, ts(18)),
    ('Suresh Iyer',          'suresh.i@ex.in',  'CUST-SURESH-016','high', 2750.0, 'expired_card',       0, ts(15)),
    # Hard skips
    ('Fatima Sheikh',        'fatima.s@ex.in',  'CUST-FATIMA-017','low',   600.0, 'already_refunded',   0, ts(12)),
    ('Gaurav Tiwari',        'gaurav.t@ex.in',  'CUST-GAURAV-018','low',   350.0, 'duplicate_charge',   0, ts(10)),
    # Below cost floor at retry 2
    ('Mani Chandrasekaran',  'mani.c@ex.in',    'CUST-MANI-019',  'low',    90.0, 'card_declined',      2, ts(6)),
    # Zero amount
    ('Leena Fernandes',      'leena.f@ex.in',   'CUST-LEENA-020', 'low',     0.0, 'card_declined',      0, ts(2)),
]

sb = get_client()
N = len(RECORDS)
counts = {'success': 0, 'skipped': 0, 'failed': 0, 'error': 0}

print('\n' + '='*65)
print('  DIRECT SEED ->  Supabase (no HTTP layer)')
print('  Merchant:', MID)
print('  Records :', N)
print('='*65 + '\n')

for i, (name, email, cid, tier, amt, reason, retry, failed_at) in enumerate(RECORDS, 1):
    try:
        row = {
            'merchant_id': MID,
            'customer_name': name,
            'customer_email': email,
            'customer_id': cid,
            'customer_tier': tier,
            'amount': amt,
            'failure_reason': reason,
            'retry_count': retry,
            'failed_at': failed_at,
        }
        inserted = sb.table('failed_payments').insert(row).execute().data[0]
        result = process_failed_payment(inserted['id'], MID)
        outcome = result['execution']['outcome']
        action  = result['decision']['action']
        icon = {'success': 'OK', 'skipped': '--', 'failed': '!!'}.get(outcome, '??')
        counts[outcome if outcome in counts else 'error'] += 1
        print('  [%02d/%d] [%s] %-26s %-22s Rs%8.2f  ->  %-30s (%s)' % (
            i, N, icon, name, reason, amt, action, outcome))
    except Exception as exc:
        counts['error'] += 1
        print('  [%02d/%d] [ERR] %s -- %s' % (i, N, name, exc))

eligible = counts['success'] + counts['failed']
rate = round(counts['success'] / max(eligible, 1) * 100, 1)
print('\n' + '='*65)
print('  Recovered :', counts['success'])
print('  Skipped   :', counts['skipped'])
print('  Failed    :', counts['failed'])
print('  Errors    :', counts['error'])
print('  Recovery rate (excl. skips): %s%%' % rate)
print('='*65 + '\n')
