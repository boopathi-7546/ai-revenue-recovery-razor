import axios from 'axios';
import { supabase } from './supabase';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
});

// Attach Supabase JWT to every request automatically
api.interceptors.request.use(async (config) => {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Types
export interface Metrics {
  total_processed: number;
  recovered: number;
  skipped: number;
  failed_attempts: number;
  recovery_rate: number;
  amount_recovered_inr: number;
}

export interface AuditRow {
  id: string;
  merchant_id: string;
  payment_id: string;
  action_taken: string;
  variant: string | null;
  outcome: string;
  reasoning: string;
  message_en: string;
  message_hi: string;
  timestamp: string;
  failed_payments?: {
    customer_name: string;
    amount: number;
    failure_reason: string;
    customer_tier: string;
    customer_id: string;
  };
}

export interface FailedPaymentIn {
  merchant_id: string;
  customer_name: string;
  customer_email?: string;
  customer_id: string;
  customer_tier: 'low' | 'high';
  amount: number;
  failure_reason: string;
  retry_count?: number;
}

// API calls
export const getMetrics = (merchantId: string) =>
  api.get<Metrics>(`/merchants/${merchantId}/metrics`).then((r) => r.data);

export const getAuditLog = (merchantId: string, limit = 100) =>
  api.get<AuditRow[]>(`/merchants/${merchantId}/audit-log`, { params: { limit } }).then((r) => r.data);

export const getExceptions = (merchantId: string) =>
  api.get<AuditRow[]>(`/merchants/${merchantId}/exceptions`).then((r) => r.data);

export const getMyMerchant = () =>
  api.get('/merchants/me').then((r) => r.data);

export const createMerchant = (payload: {
  auth_user_id: string;
  business_name: string;
}) => api.post('/auth/signup', payload).then((r) => r.data);

export const submitFailedPayment = (payload: FailedPaymentIn) =>
  api.post('/failed-payments', payload).then((r) => r.data);

export const processPayment = (failedPaymentId: string) =>
  api.post('/process-payment', { failed_payment_id: failedPaymentId }).then((r) => r.data);

export default api;
