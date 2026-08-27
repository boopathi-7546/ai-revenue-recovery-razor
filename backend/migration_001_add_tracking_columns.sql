-- Additive migration — safe to run, does not touch existing data or tables.
-- Adds 2 columns needed so the FastAPI layer can reconstruct guardrail state
-- (attempt counts, 24h dedup) per customer per merchant from audit_log.

-- 1. A stable per-customer key on failed_payments (falls back to customer_email
--    if you don't have a separate customer_id concept yet).
alter table failed_payments
  add column if not exists customer_id text;

-- Backfill: use email as the tracking key for any existing rows
update failed_payments
  set customer_id = customer_email
  where customer_id is null;

-- 2. A status column so the dashboard/API can query recovery state directly
--    instead of re-deriving it from audit_log every time.
alter table failed_payments
  add column if not exists status text not null default 'pending';
  -- expected values: pending | retrying | recovered | skipped | escalated

create index if not exists idx_failed_payments_customer
  on failed_payments(merchant_id, customer_id);

create index if not exists idx_failed_payments_status
  on failed_payments(status);
