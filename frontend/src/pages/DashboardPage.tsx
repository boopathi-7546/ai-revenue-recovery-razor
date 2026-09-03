import { useState } from 'react';
import {
  TrendingUp, DollarSign, CheckCircle2, XCircle, AlertTriangle,
  RefreshCw, BarChart2, FileText, Zap, Activity
} from 'lucide-react';
import { Navbar } from '../components/Navbar';
import { MetricCard } from '../components/MetricCard';
import { OutcomePieChart, ActionBarChart } from '../components/RecoveryChart';
import { AuditLogTable } from '../components/AuditLogTable';
import { ExceptionsList } from '../components/ExceptionCard';
import { TryItLiveForm } from '../components/TryItLiveForm';
import { useAuth } from '../hooks/useAuth';
import { useDashboard } from '../hooks/useDashboard';

type Tab = 'overview' | 'audit' | 'exceptions' | 'try';

export function DashboardPage() {
  const { merchant } = useAuth();
  const { metrics, auditLog, exceptions, loading, error, refresh } = useDashboard(merchant?.id ?? null);
  const [tab, setTab] = useState<Tab>('overview');

  const fmtINR = (v: number) =>
    v >= 100000 ? `₹${(v / 100000).toFixed(1)}L` :
    v >= 1000   ? `₹${(v / 1000).toFixed(1)}K`   :
    `₹${v.toFixed(0)}`;

  return (
    <div className="dashboard-layout">
      <div className="dashboard-main">
        <Navbar businessName={merchant?.business_name} />

        <div className="dashboard-content">
          {/* Page header */}
          <div className="flex-between mb-6">
            <div className="page-header" style={{ marginBottom: 0 }}>
              <h1 className="page-title">Dashboard</h1>
              <p className="page-sub">Real-time payment recovery analytics</p>
            </div>
            <button
              id="dashboard-refresh-btn"
              className="btn btn-secondary btn-sm"
              onClick={refresh}
              disabled={loading}
            >
              <RefreshCw size={14} className={loading ? 'spin-icon' : ''} />
              Refresh
            </button>
          </div>

          {error && <div className="alert alert-error mb-4">{error}</div>}

          {/* Tabs */}
          <div className="tabs">
            {([
              { key: 'overview',   label: 'Overview',    icon: <Activity size={14} /> },
              { key: 'audit',      label: 'Audit Log',   icon: <FileText size={14} /> },
              { key: 'exceptions', label: 'Exceptions',  icon: <AlertTriangle size={14} /> },
              { key: 'try',        label: 'Try It Live', icon: <Zap size={14} /> },
            ] as const).map((t) => (
              <button
                key={t.key}
                id={`tab-${t.key}`}
                className={`tab-btn ${tab === t.key ? 'active' : ''}`}
                onClick={() => setTab(t.key)}
              >
                {t.icon} {t.label}
                {t.key === 'exceptions' && exceptions.length > 0 && (
                  <span className="badge badge-danger" style={{ fontSize: 10, padding: '1px 6px' }}>
                    {exceptions.length}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Overview Tab */}
          {tab === 'overview' && (
            <>
              {/* Metric cards */}
              {loading && !metrics ? (
                <div className="metrics-grid">
                  {[...Array(6)].map((_, i) => (
                    <div key={i} className="metric-card">
                      <div className="skeleton" style={{ width: 40, height: 40, borderRadius: 8 }} />
                      <div>
                        <div className="skeleton mb-2" style={{ width: 80, height: 12 }} />
                        <div className="skeleton" style={{ width: 120, height: 32 }} />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="metrics-grid">
                  <MetricCard
                    label="Total Processed"
                    value={metrics?.total_processed ?? 0}
                    sub="All payment records"
                    icon={<BarChart2 size={20} style={{ color: 'var(--accent)' }} />}
                    accentColor="linear-gradient(90deg, #3b82f6, #60a5fa)"
                  />
                  <MetricCard
                    label="Recovered"
                    value={metrics?.recovered ?? 0}
                    sub="Successful interventions"
                    icon={<CheckCircle2 size={20} style={{ color: '#10b981' }} />}
                    iconBg="rgba(16,185,129,0.15)"
                    accentColor="linear-gradient(90deg, #10b981, #34d399)"
                  />
                  <MetricCard
                    label="Recovery Rate"
                    value={`${metrics?.recovery_rate ?? 0}%`}
                    sub={metrics && metrics.recovery_rate >= 70 ? '🎉 Above target!' : 'Target: 70%'}
                    icon={<TrendingUp size={20} style={{ color: '#8b5cf6' }} />}
                    iconBg="rgba(139,92,246,0.15)"
                    accentColor="linear-gradient(90deg, #8b5cf6, #a78bfa)"
                  />
                  <MetricCard
                    label="Amount Recovered"
                    value={metrics ? fmtINR(metrics.amount_recovered_inr) : '₹0'}
                    sub="INR recovered"
                    icon={<DollarSign size={20} style={{ color: '#f59e0b' }} />}
                    iconBg="rgba(245,158,11,0.15)"
                    accentColor="linear-gradient(90deg, #f59e0b, #fbbf24)"
                  />
                  <MetricCard
                    label="Skipped"
                    value={metrics?.skipped ?? 0}
                    sub="Non-retryable / guardrailed"
                    icon={<XCircle size={20} style={{ color: '#64748b' }} />}
                    iconBg="rgba(100,116,139,0.15)"
                    accentColor="linear-gradient(90deg, #475569, #64748b)"
                  />
                  <MetricCard
                    label="Exceptions"
                    value={exceptions.length}
                    sub="Requires review"
                    icon={<AlertTriangle size={20} style={{ color: '#ef4444' }} />}
                    iconBg="rgba(239,68,68,0.15)"
                    accentColor="linear-gradient(90deg, #ef4444, #f87171)"
                  />
                </div>
              )}

              {/* Charts */}
              {auditLog.length > 0 ? (
                <div className="charts-grid">
                  <OutcomePieChart auditLog={auditLog} />
                  <ActionBarChart auditLog={auditLog} />
                </div>
              ) : !loading ? (
                <div className="empty-state card">
                  <Activity size={40} />
                  <h3 style={{ fontSize: 18 }}>No data yet</h3>
                  <p>Use "Try It Live" to run your first payment through the agent pipeline.</p>
                  <button className="btn btn-primary" onClick={() => setTab('try')}>
                    <Zap size={14} /> Try It Live
                  </button>
                </div>
              ) : null}
            </>
          )}

          {/* Audit Log Tab */}
          {tab === 'audit' && (
            <div className="card">
              <div className="flex-between mb-6">
                <div>
                  <h2 style={{ fontSize: 18, fontWeight: 700 }}>Audit Log</h2>
                  <p className="text-sm text-muted">Every agent action with full reasoning</p>
                </div>
              </div>
              {loading && auditLog.length === 0 ? (
                <div className="flex-center" style={{ padding: 60 }}>
                  <div className="spinner" style={{ width: 32, height: 32 }} />
                </div>
              ) : (
                <AuditLogTable rows={auditLog} />
              )}
            </div>
          )}

          {/* Exceptions Tab */}
          {tab === 'exceptions' && (
            <div className="card">
              <div className="flex-between mb-6">
                <div>
                  <h2 style={{ fontSize: 18, fontWeight: 700 }}>Exceptions</h2>
                  <p className="text-sm text-muted">Payments the agent skipped — and why</p>
                </div>
                <span className="badge badge-danger">{exceptions.length} skipped</span>
              </div>
              {loading && exceptions.length === 0 ? (
                <div className="flex-center" style={{ padding: 60 }}>
                  <div className="spinner" style={{ width: 32, height: 32 }} />
                </div>
              ) : (
                <ExceptionsList rows={exceptions} />
              )}
            </div>
          )}

          {/* Try It Live Tab */}
          {tab === 'try' && (
            <div className="card">
              <div className="mb-6">
                <h2 style={{ fontSize: 18, fontWeight: 700 }}>Try It Live</h2>
                <p className="text-sm text-muted">Submit a failed payment and watch the agent decide in real time</p>
              </div>
              {!merchant?.id && (
                <div className="alert alert-info mb-4" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <div className="spinner" style={{ width: 16, height: 16 }} />
                  <span>Loading your account...</span>
                </div>
              )}
              <TryItLiveForm merchantId={merchant?.id} onSuccess={refresh} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
