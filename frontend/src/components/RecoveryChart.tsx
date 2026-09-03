import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
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
