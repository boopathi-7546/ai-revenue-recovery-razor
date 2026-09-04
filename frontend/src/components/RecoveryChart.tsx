import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import type { AuditRow } from '../api';

interface RecoveryChartProps {
  auditLog: AuditRow[];
}

const COLORS = {
  success: '#10b981',
  failed:  '#ef4444',
  skipped: '#64748b',
  immediate_retry:       '#3b82f6',
  retry_in_3_days:       '#8b5cf6',
  send_payment_update:   '#f59e0b',
  escalate_human:        '#ec4899',
  skip_non_retryable:    '#64748b',
  skip_invalid_data:     '#475569',
  skip_cost_floor:       '#334155',
  skip_max_attempts:     '#1e293b',
};

function buildActionDist(auditLog: AuditRow[]) {
  const counts: Record<string, number> = {};
  auditLog.forEach((r) => {
    counts[r.action_taken] = (counts[r.action_taken] || 0) + 1;
  });
  return Object.entries(counts).map(([name, value]) => ({ name, value }));
}

function buildOutcomeDist(auditLog: AuditRow[]) {
  const c: Record<string, number> = { success: 0, failed: 0, skipped: 0 };
  auditLog.forEach((r) => { c[r.outcome] = (c[r.outcome] || 0) + 1; });
  return Object.entries(c).map(([name, value]) => ({ name, value }));
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: '#0d1526', border: '1px solid rgba(99,179,237,0.2)', borderRadius: 8, padding: '10px 14px' }}>
      {label && <p style={{ fontSize: 12, color: '#94a3b8', marginBottom: 6 }}>{label}</p>}
      {payload.map((p: any, i: number) => (
        <p key={i} style={{ fontSize: 13, color: p.color || '#f0f6ff', margin: '2px 0' }}>
          {p.name}: <strong>{p.value}</strong>
        </p>
      ))}
    </div>
  );
};

export function OutcomePieChart({ auditLog }: RecoveryChartProps) {
  const data = buildOutcomeDist(auditLog);
  return (
    <div className="card" style={{ height: 280 }}>
      <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 16 }}>Outcome Distribution</h3>
      <ResponsiveContainer width="100%" height={200}>
        <PieChart>
          <Pie data={data} cx="50%" cy="50%" innerRadius={55} outerRadius={85} paddingAngle={3} dataKey="value">
            {data.map((entry) => (
              <Cell key={entry.name} fill={(COLORS as any)[entry.name] || '#3b82f6'} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend formatter={(v) => <span style={{ fontSize: 12, color: '#94a3b8' }}>{v}</span>} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

export function ActionBarChart({ auditLog }: RecoveryChartProps) {
  const data = buildActionDist(auditLog);
  return (
    <div className="card" style={{ height: 280 }}>
      <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 16 }}>Actions Taken</h3>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} layout="vertical">
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,179,237,0.07)" horizontal={false} />
          <XAxis type="number" tick={{ fontSize: 11, fill: '#4b5c7a' }} />
          <YAxis type="category" dataKey="name" tick={{ fontSize: 10, fill: '#94a3b8' }} width={130} />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="value" radius={[0, 4, 4, 0]}>
            {data.map((entry) => (
              <Cell key={entry.name} fill={(COLORS as any)[entry.name] || '#3b82f6'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

/** Bucket audit log rows by calendar day and compute recovery rate per day */
function buildTrendData(auditLog: AuditRow[]) {
  const byDay: Record<string, { total: number; recovered: number }> = {};
  auditLog.forEach((r) => {
    const day = r.timestamp.slice(0, 10); // YYYY-MM-DD
    if (!byDay[day]) byDay[day] = { total: 0, recovered: 0 };
    byDay[day].total += 1;
    if (r.outcome === 'success') byDay[day].recovered += 1;
  });
  return Object.entries(byDay)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, { total, recovered }]) => ({
      date,
      rate: total > 0 ? Math.round((recovered / total) * 100) : 0,
      recovered,
      total,
    }));
}

/** Compare variant A vs B success rates */
function buildABData(auditLog: AuditRow[]) {
  const ab: Record<string, { attempts: number; recovered: number }> = {
    A: { attempts: 0, recovered: 0 },
    B: { attempts: 0, recovered: 0 },
  };
  auditLog.forEach((r) => {
    const v = r.variant?.toUpperCase();
    if (v === 'A' || v === 'B') {
      ab[v].attempts += 1;
      if (r.outcome === 'success') ab[v].recovered += 1;
    }
  });
  return [
    {
      variant: 'A — Standard',
      rate: ab.A.attempts > 0 ? Math.round((ab.A.recovered / ab.A.attempts) * 100) : 0,
      recovered: ab.A.recovered,
      attempts: ab.A.attempts,
    },
    {
      variant: 'B — Urgency',
      rate: ab.B.attempts > 0 ? Math.round((ab.B.recovered / ab.B.attempts) * 100) : 0,
      recovered: ab.B.recovered,
      attempts: ab.B.attempts,
    },
  ];
}

/** Failure reason frequency breakdown (recovered vs failed counts, stacked) */
function buildFailureReasonData(auditLog: AuditRow[]) {
  const rs: Record<string, { recovered: number; failed: number }> = {};
  auditLog.forEach((r) => {
    const reason = r.failed_payments?.failure_reason || 'unknown';
    if (!rs[reason]) rs[reason] = { recovered: 0, failed: 0 };
    if (r.outcome === 'success') rs[reason].recovered += 1;
    else if (r.outcome !== 'skipped') rs[reason].failed += 1;
  });
  return Object.entries(rs).map(([name, { recovered, failed }]) => ({
    name: name.replace(/_/g, ' '),
    recovered,
    failed,
  }));
}

/** Recovery Rate Over Time — area chart bucketed by day */
export function RecoveryTrendChart({ auditLog }: RecoveryChartProps) {
  const data = buildTrendData(auditLog);
  if (data.length === 0) return null;
  return (
    <div className="card" style={{ height: 300 }}>
      <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 16 }}>
        📈 Recovery Rate Over Time
      </h3>
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="rateGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#4f8ef7" stopOpacity={0.35} />
              <stop offset="95%" stopColor="#4f8ef7" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,179,237,0.07)" />
          <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#4b5c7a' }} />
          <YAxis domain={[0, 105]} tickFormatter={(v) => `${v}%`} tick={{ fontSize: 10, fill: '#4b5c7a' }} />
          <Tooltip content={<CustomTooltip />} formatter={(v: any) => [`${v}%`, 'Recovery Rate']} />
          <ReferenceLine y={70} stroke="#f59e0b" strokeDasharray="4 3" label={{ value: '70% Target', fill: '#f59e0b', fontSize: 10 }} />
          <Area
            type="monotone"
            dataKey="rate"
            name="Recovery Rate %"
            stroke="#4f8ef7"
            strokeWidth={2.5}
            fill="url(#rateGrad)"
            dot={{ r: 4, fill: '#4f8ef7', stroke: '#0a0e1a', strokeWidth: 2 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

/** A/B Variant Comparison — bar chart comparing variant A vs B success rates */
export function ABVariantChart({ auditLog }: RecoveryChartProps) {
  const data = buildABData(auditLog);
  const hasData = data.some((d) => d.attempts > 0);
  if (!hasData) return null;
  const AB_COLORS = ['#4f8ef7', '#00d4aa'];
  return (
    <div className="card" style={{ height: 300 }}>
      <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 4 }}>
        🧪 A/B Variant Comparison
      </h3>
      <p style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 12 }}>Plain reminder (A) vs urgency-framed (B)</p>
      <ResponsiveContainer width="100%" height={210}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,179,237,0.07)" vertical={false} />
          <XAxis dataKey="variant" tick={{ fontSize: 11, fill: '#94a3b8' }} />
          <YAxis domain={[0, 115]} tickFormatter={(v) => `${v}%`} tick={{ fontSize: 10, fill: '#4b5c7a' }} />
          <Tooltip content={<CustomTooltip />} formatter={(v: any, _name: any, props: any) => [
            `${v}% (${props.payload.recovered}/${props.payload.attempts})`, 'Recovery Rate',
          ]} />
          <Bar
            dataKey="rate"
            name="Recovery Rate %"
            radius={[6, 6, 0, 0]}
            label={{ position: 'top', fill: '#f1f5f9', fontSize: 13, formatter: (v: any) => `${v}%` }}
          >
            {data.map((_, i) => (
              <Cell key={i} fill={AB_COLORS[i % AB_COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

/** Failure Reason Breakdown — stacked bar: recovered vs failed per failure reason */
export function FailureReasonChart({ auditLog }: RecoveryChartProps) {
  const data = buildFailureReasonData(auditLog);
  if (data.length === 0) return null;
  return (
    <div className="card" style={{ height: 320 }}>
      <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 4 }}>
        🔍 Recovery by Failure Reason
      </h3>
      <p style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 12 }}>Success vs attempt counts per failure category</p>
      <ResponsiveContainer width="100%" height={230}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,179,237,0.07)" vertical={false} />
          <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#94a3b8' }} />
          <YAxis tick={{ fontSize: 10, fill: '#4b5c7a' }} allowDecimals={false} />
          <Tooltip content={<CustomTooltip />} />
          <Legend formatter={(v) => <span style={{ fontSize: 12, color: '#94a3b8' }}>{v}</span>} />
          <Bar dataKey="recovered" name="Recovered" stackId="a" fill="#00d4aa" opacity={0.9} />
          <Bar dataKey="failed"    name="Failed"    stackId="a" fill="#ff4d6d" opacity={0.75} radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
