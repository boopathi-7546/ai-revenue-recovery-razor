import { useState, useMemo } from 'react';
import { Search, Filter, Download } from 'lucide-react';
import type { AuditRow } from '../api';

interface AuditLogTableProps {
  rows: AuditRow[];
}

const OUTCOME_BADGE: Record<string, string> = {
  success: 'badge-success',
  failed:  'badge-danger',
  skipped: 'badge-gray',
};

const ACTION_BADGE: Record<string, string> = {
  immediate_retry:     'badge-blue',
  retry_in_3_days:     'badge-purple',
  send_payment_update: 'badge-warning',
  escalate_human:      'badge-danger',
};

export function AuditLogTable({ rows }: AuditLogTableProps) {
  const [search, setSearch] = useState('');
  const [outcomeFilter, setOutcomeFilter] = useState('all');
  const [actionFilter, setActionFilter] = useState('all');

  const actions = useMemo(() => ['all', ...new Set(rows.map((r) => r.action_taken))], [rows]);

  const filtered = useMemo(() => {
    return rows.filter((r) => {
      const name = r.failed_payments?.customer_name?.toLowerCase() || '';
      const cid  = r.failed_payments?.customer_id?.toLowerCase() || '';
      const q = search.toLowerCase();
      const matchSearch = !search || name.includes(q) || cid.includes(q) || r.action_taken.includes(q);
      const matchOutcome = outcomeFilter === 'all' || r.outcome === outcomeFilter;
      const matchAction  = actionFilter  === 'all' || r.action_taken === actionFilter;
      return matchSearch && matchOutcome && matchAction;
    });
  }, [rows, search, outcomeFilter, actionFilter]);

  const fmt = (ts: string) => new Date(ts).toLocaleString('en-IN', { dateStyle: 'short', timeStyle: 'short' });
  const fmtAmount = (a?: number) => a != null ? `₹${a.toLocaleString('en-IN')}` : '—';

  const downloadCSV = () => {
    const headers = ['customer_name', 'customer_id', 'amount', 'failure_reason', 'action_taken', 'outcome', 'variant', 'timestamp'];
    const rows = filtered.map((r) => [
      r.failed_payments?.customer_name ?? '',
      r.failed_payments?.customer_id ?? '',
      r.failed_payments?.amount ?? '',
      r.failed_payments?.failure_reason ?? '',
      r.action_taken,
      r.outcome,
      r.variant ?? '',
      r.timestamp,
    ]);
    const csv = [headers, ...rows]
      .map((row) => row.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(','))
      .join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href = url;
    a.download = `audit_log_filtered_${new Date().toISOString().slice(0,10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div>
      {/* Filters */}
      <div className="flex gap-3 mb-4" style={{ flexWrap: 'wrap', alignItems: 'center' }}>
        <div style={{ position: 'relative', flex: 1, minWidth: 200 }}>
          <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input
            id="audit-search"
            className="form-input"
            placeholder="Search customer..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ paddingLeft: 32 }}
          />
        </div>
        <select id="audit-outcome-filter" className="form-input" style={{ width: 140 }} value={outcomeFilter} onChange={(e) => setOutcomeFilter(e.target.value)}>
          <option value="all">All outcomes</option>
          <option value="success">Success</option>
          <option value="failed">Failed</option>
          <option value="skipped">Skipped</option>
        </select>
        <select id="audit-action-filter" className="form-input" style={{ width: 180 }} value={actionFilter} onChange={(e) => setActionFilter(e.target.value)}>
          {actions.map((a) => <option key={a} value={a}>{a === 'all' ? 'All actions' : a.replace(/_/g, ' ')}</option>)}
        </select>
        <button
          id="audit-download-csv-btn"
          className="btn btn-secondary btn-sm"
          onClick={downloadCSV}
          disabled={filtered.length === 0}
          title={`Download ${filtered.length} filtered rows as CSV`}
          style={{ whiteSpace: 'nowrap' }}
        >
          <Download size={13} /> Download CSV ({filtered.length})
        </button>
      </div>

      <p className="text-sm text-muted mb-2">{filtered.length} records</p>

      {filtered.length === 0 ? (
        <div className="empty-state">
          <Filter size={32} />
          <p>No records match your filters</p>
        </div>
      ) : (
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Customer</th>
                <th>Amount</th>
                <th>Failure</th>
                <th>Action</th>
                <th>Outcome</th>
                <th>Variant</th>
                <th>When</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((row) => (
                <tr key={row.id}>
                  <td>
                    <strong>{row.failed_payments?.customer_name || '—'}</strong>
                    <div className="text-xs text-muted">{row.failed_payments?.customer_id}</div>
                  </td>
                  <td>{fmtAmount(row.failed_payments?.amount)}</td>
                  <td>
                    <span className="badge badge-gray">
                      {row.failed_payments?.failure_reason?.replace(/_/g, ' ') || '—'}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${ACTION_BADGE[row.action_taken] || 'badge-blue'}`}>
                      {row.action_taken.replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${OUTCOME_BADGE[row.outcome] || 'badge-gray'}`}>
                      {row.outcome}
                    </span>
                  </td>
                  <td>{row.variant ? <span className="badge badge-purple">{row.variant}</span> : <span className="text-muted">—</span>}</td>
                  <td className="text-muted">{fmt(row.timestamp)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
