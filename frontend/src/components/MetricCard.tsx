import type { ReactNode } from 'react';

interface MetricCardProps {
  label: string;
  value: string | number;
  sub?: string;
  icon: ReactNode;
  iconBg?: string;
  accentColor?: string;
}

export function MetricCard({ label, value, sub, icon, iconBg = 'rgba(59,130,246,0.15)', accentColor }: MetricCardProps) {
  return (
    <div
      className="metric-card"
      style={{ '--accent-gradient': accentColor } as React.CSSProperties}
    >
      <div className="metric-icon" style={{ background: iconBg }}>
        {icon}
      </div>
      <div>
        <div className="metric-label">{label}</div>
        <div className="metric-value">{value}</div>
        {sub && <div className="metric-sub">{sub}</div>}
      </div>
    </div>
  );
}
