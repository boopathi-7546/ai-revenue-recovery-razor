import { useState } from 'react';
import { Zap, Upload, Loader } from 'lucide-react';
import { submitFailedPayment, processPayment } from '../api';
import toast from 'react-hot-toast';

interface TryItLiveFormProps {
  merchantId: string;
  onSuccess?: () => void;
}

const FAILURE_REASONS = [
  'card_declined',
  'insufficient_funds',
  'bank_timeout',
  'expired_card',
  'already_refunded',
  'duplicate_charge',
];

export function TryItLiveForm({ merchantId, onSuccess }: TryItLiveFormProps) {
  const [form, setForm] = useState({
    customer_name: '',
    customer_email: '',
    customer_id: '',
    customer_tier: 'low' as 'low' | 'high',
    amount: '',
    failure_reason: 'card_declined',
    retry_count: '0',
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.customer_name || !form.customer_id || !form.amount) {
      toast.error('Please fill in all required fields');
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      // 1. Register the failed payment
      const fp = await submitFailedPayment({
        merchant_id: merchantId,
        customer_name: form.customer_name,
        customer_email: form.customer_email || undefined,
        customer_id: form.customer_id,
        customer_tier: form.customer_tier,
        amount: parseFloat(form.amount),
        failure_reason: form.failure_reason,
        retry_count: parseInt(form.retry_count) || 0,
      });
      // 2. Run it through the agent pipeline
      const res = await processPayment(fp.id);
      setResult(res);
      toast.success('Agent processed the payment!');
      onSuccess?.();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  const outcomeBadge = result?.execution?.outcome;
  const outcomeClass =
    outcomeBadge === 'success' ? 'badge-success' :
    outcomeBadge === 'skipped' ? 'badge-gray' : 'badge-danger';

  return (
    <div>
      <form className="try-form" onSubmit={handleSubmit} id="try-it-live-form">
        <div className="try-form-grid">
          <div className="form-group">
            <label className="form-label">Customer Name *</label>
            <input id="try-customer-name" className="form-input" placeholder="e.g. Priya Sharma" value={form.customer_name} onChange={(e) => set('customer_name', e.target.value)} required />
          </div>
          <div className="form-group">
            <label className="form-label">Customer Email</label>
            <input id="try-customer-email" className="form-input" type="email" placeholder="priya@example.com" value={form.customer_email} onChange={(e) => set('customer_email', e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Customer ID *</label>
            <input id="try-customer-id" className="form-input" placeholder="e.g. CUST001" value={form.customer_id} onChange={(e) => set('customer_id', e.target.value)} required />
          </div>
          <div className="form-group">
            <label className="form-label">Customer Tier</label>
            <select id="try-customer-tier" className="form-input" value={form.customer_tier} onChange={(e) => set('customer_tier', e.target.value)}>
              <option value="low">Low (below ₹5,000)</option>
              <option value="high">High (₹5,000+)</option>
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Amount (₹) *</label>
            <input id="try-amount" className="form-input" type="number" placeholder="e.g. 2499" value={form.amount} onChange={(e) => set('amount', e.target.value)} required min="0" />
          </div>
          <div className="form-group">
            <label className="form-label">Failure Reason</label>
            <select id="try-failure-reason" className="form-input" value={form.failure_reason} onChange={(e) => set('failure_reason', e.target.value)}>
              {FAILURE_REASONS.map((r) => <option key={r} value={r}>{r.replace(/_/g, ' ')}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Prior Retry Count</label>
            <select id="try-retry-count" className="form-input" value={form.retry_count} onChange={(e) => set('retry_count', e.target.value)}>
              <option value="0">0 (first attempt)</option>
              <option value="1">1</option>
              <option value="2">2</option>
              <option value="3">3+</option>
            </select>
          </div>
        </div>

        <button id="try-submit-btn" type="submit" className="btn btn-primary btn-lg" disabled={loading} style={{ alignSelf: 'flex-start' }}>
          {loading ? <><div className="spinner" /> Processing...</> : <><Zap size={16} /> Run Agent Pipeline</>}
        </button>
      </form>

      {/* Result */}
      {result && (
        <div className="result-card">
          <div className="flex-between mb-4">
            <div className="result-action">{result.decision?.action?.replace(/_/g, ' ')}</div>
            <span className={`badge ${outcomeClass}`}>{outcomeBadge}</span>
          </div>
          <p className="result-reasoning">{result.decision?.reasoning}</p>
          {result.decision?.messages && (
            <div className="result-messages">
              {result.decision.messages.english && (
                <div className="result-msg">
                  <strong>English</strong>
                  {result.decision.messages.english}
                </div>
              )}
              {result.decision.messages.hinglish && (
                <div className="result-msg">
                  <strong>Hinglish</strong>
                  {result.decision.messages.hinglish}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
