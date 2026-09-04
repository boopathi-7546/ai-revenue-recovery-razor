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
  success: '#5B8C5A',
  failed:  '#C1442E',
  skipped: '#6B6355',
  immediate_retry:       '#E4A62F',
  retry_in_3_days:       '#B1502F',
  send_payment_update:   '#D99A3D',
  escalate_human:        '#8C6A3A',
  skip_non_retryable:    '#6B6355',
  skip_invalid_data:     '#55493E',
  skip_cost_floor:       '#3E342B',
  skip_max_attempts:     '#2B231D',
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
    <div style={{ background: '#141A21', border: '1px solid rgba(228,166,47,0.2)', borderRadius: 8, padding: '10px 14px' }}>
      {label && <p style={{ fontSize: 12, color: '#A69A88', marginBottom: 6 }}>{label}</p>}
      {payload.map((p: any, i: number) => (
        <p key={i} style={{ fontSize: 13, color: p.color || '#F5F1E8', margin: '2px 0' }}>
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
              <Cell key={entry.name} fill={(COLORS as any)[entry.name] || '#E4A62F'} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend formatter={(v) => <span style={{ fontSize: 12, color: '#A69A88' }}>{v}</span>} />
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
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(228,166,47,0.07)" horizontal={false} />
          <XAxis type="number" tick={{ fontSize: 11, fill: '#6B6355' }} />
          <YAxis type="category" dataKey="name" tick={{ fontSize: 10, fill: '#A69A88' }} width={130} />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="value" radius={[0, 4, 4, 0]}>
            {data.map((entry) => (
              <Cell key={entry.name} fill={(COLORS as any)[entry.name] || '#E4A62F'} />
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
              <stop offset="5%" stopColor="#E4A62F" stopOpacity={0.35} />
              <stop offset="95%" stopColor="#E4A62F" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(228,166,47,0.07)" />
          <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#6B6355' }} />
          <YAxis domain={[0, 105]} tickFormatter={(v) => `${v}%`} tick={{ fontSize: 10, fill: '#6B6355' }} />
          <Tooltip content={<CustomTooltip />} formatter={(v: any) => [`${v}%`, 'Recovery Rate']} />
          <ReferenceLine y={70} stroke="#D99A3D" strokeDasharray="4 3" label={{ value: '70% Target', fill: '#D99A3D', fontSize: 10 }} />
          <Area
            type="monotone"
            dataKey="rate"
            name="Recovery Rate %"
            stroke="#E4A62F"
            strokeWidth={2.5}
            fill="url(#rateGrad)"
            dot={{ r: 4, fill: '#E4A62F', stroke: '#0B0E13', strokeWidth: 2 }}
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
  const AB_COLORS = ['#E4A62F', '#5B8C5A'];
  return (
    <div className="card" style={{ height: 300 }}>
      <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 4 }}>
        🧪 A/B Variant Comparison
      </h3>
      <p style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 12 }}>Plain reminder (A) vs urgency-framed (B)</p>
      <ResponsiveContainer width="100%" height={210}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(228,166,47,0.07)" vertical={false} />
          <XAxis dataKey="variant" tick={{ fontSize: 11, fill: '#A69A88' }} />
          <YAxis domain={[0, 115]} tickFormatter={(v) => `${v}%`} tick={{ fontSize: 10, fill: '#6B6355' }} />
          <Tooltip content={<CustomTooltip />} formatter={(v: any, _name: any, props: any) => [
            `${v}% (${props.payload.recovered}/${props.payload.attempts})`, 'Recovery Rate',
          ]} />
          <Bar
            dataKey="rate"
            name="Recovery Rate %"
            radius={[6, 6, 0, 0]}
            label={{ position: 'top', fill: '#F5F1E8', fontSize: 13, formatter: (v: any) => `${v}%` }}
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
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(228,166,47,0.07)" vertical={false} />
          <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#A69A88' }} />
          <YAxis tick={{ fontSize: 10, fill: '#6B6355' }} allowDecimals={false} />
          <Tooltip content={<CustomTooltip />} />
          <Legend formatter={(v) => <span style={{ fontSize: 12, color: '#A69A88' }}>{v}</span>} />
          <Bar dataKey="recovered" name="Recovered" stackId="a" fill="#5B8C5A" opacity={0.9} />
          <Bar dataKey="failed"    name="Failed"    stackId="a" fill="#C1442E" opacity={0.75} radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
