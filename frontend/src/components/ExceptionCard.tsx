import { AlertTriangle, XCircle, AlertCircle } from 'lucide-react';
import type { AuditRow } from '../api';

interface ExceptionCardProps {
  row: AuditRow;
}

const ACTION_META: Record<string, { label: string; color: string; icon: typeof AlertTriangle }> = {
  skip_non_retryable: { label: 'Non-retryable', color: '#ef4444', icon: XCircle },
  skip_invalid_data:  { label: 'Invalid Data',  color: '#f59e0b', icon: AlertCircle },
  skip_cost_floor:    { label: 'Cost Floor',    color: '#64748b', icon: AlertTriangle },
  skip_max_attempts:  { label: 'Max Attempts',  color: '#8b5cf6', icon: AlertTriangle },
};

const fmt = (a: number) => `₹${a.toLocaleString('en-IN')}`;

export function ExceptionCard({ row }: ExceptionCardProps) {
  const meta = ACTION_META[row.action_taken] || { label: row.action_taken, color: '#64748b', icon: AlertTriangle };
  const Icon = meta.icon;
  const fp = row.failed_payments;

  return (
    <div className="exception-card">
      <div className="exception-icon">
        <Icon size={18} style={{ color: meta.color }} />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div className="flex-between mb-2">
          <strong style={{ fontSize: 14 }}>{fp?.customer_name || 'Unknown Customer'}</strong>
          <span className="badge badge-danger" style={{ flexShrink: 0 }}>{meta.label}</span>
        </div>
        <div className="flex gap-2 mb-2" style={{ flexWrap: 'wrap' }}>
          {fp?.amount != null && (
            <span className="badge badge-gray">{fmt(fp.amount)}</span>
          )}
          {fp?.failure_reason && (
            <span className="badge badge-gray">{fp.failure_reason.replace(/_/g, ' ')}</span>
          )}
          {fp?.customer_tier && (
            <span className={`badge ${fp.customer_tier === 'high' ? 'badge-blue' : 'badge-gray'}`}>
              {fp.customer_tier} tier
            </span>
          )}
        </div>
        <p className="text-sm text-secondary" style={{ fontStyle: 'italic' }}>{row.reasoning}</p>
      </div>
    </div>
  );
}

interface ExceptionsListProps {
  rows: AuditRow[];
}

export function ExceptionsList({ rows }: ExceptionsListProps) {
  if (rows.length === 0) {
    return (
      <div className="empty-state">
        <AlertTriangle size={32} />
        <p>No exceptions recorded yet</p>
      </div>
    );
  }
  return (
    <div className="exceptions-grid">
      {rows.map((row) => <ExceptionCard key={row.id} row={row} />)}
    </div>
  );
}
