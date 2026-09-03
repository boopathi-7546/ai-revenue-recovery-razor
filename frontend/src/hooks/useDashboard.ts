import { useState, useEffect, useCallback } from 'react';
import { getMetrics, getAuditLog, getExceptions, type Metrics, type AuditRow } from '../api';

export function useDashboard(merchantId: string | null) {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [auditLog, setAuditLog] = useState<AuditRow[]>([]);
  const [exceptions, setExceptions] = useState<AuditRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!merchantId) return;
    setLoading(true);
    setError(null);
    try {
      const [m, al, ex] = await Promise.all([
        getMetrics(merchantId),
        getAuditLog(merchantId),
        getExceptions(merchantId),
      ]);
      setMetrics(m);
      setAuditLog(al);
      setExceptions(ex);
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  }, [merchantId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { metrics, auditLog, exceptions, loading, error, refresh };
}
