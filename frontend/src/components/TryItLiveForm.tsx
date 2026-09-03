import { useState } from 'react';
import { Zap, Copy, Check, Sparkles, Shield, Cpu, MessageSquare } from 'lucide-react';
import { submitFailedPayment, processPayment } from '../api';
import toast from 'react-hot-toast';

interface TryItLiveFormProps {
  merchantId?: string;
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

const PRESETS = [
  {
    label: '⚡ Card Declined',
    customer_name: 'Aarav Patel',
    customer_email: 'aarav@example.com',
    customer_id: 'CUST-001',
    customer_tier: 'low' as const,
    amount: '1850',
    failure_reason: 'card_declined',
    retry_count: '0',
  },
  {
    label: '⏳ Insufficient Funds',
    customer_name: 'Ananya Roy',
    customer_email: 'ananya@example.com',
    customer_id: 'CUST-002',
    customer_tier: 'low' as const,
    amount: '950',
    failure_reason: 'insufficient_funds',
    retry_count: '1',
  },
  {
    label: '🛡️ Duplicate Charge',
    customer_name: 'Rohan Verma',
    customer_email: 'rohan@example.com',
    customer_id: 'CUST-003',
    customer_tier: 'high' as const,
    amount: '6200',
    failure_reason: 'duplicate_charge',
    retry_count: '0',
  },
  {
    label: '💎 VIP High Value',
    customer_name: 'Vikram Mehta',
    customer_email: 'vikram@example.com',
    customer_id: 'CUST-004',
    customer_tier: 'high' as const,
    amount: '14500',
    failure_reason: 'bank_timeout',
    retry_count: '0',
  },
];

export function TryItLiveForm({ merchantId, onSuccess }: TryItLiveFormProps) {
  const [form, setForm] = useState({
    customer_name: 'Aarav Patel',
    customer_email: 'aarav@example.com',
    customer_id: 'CUST-001',
    customer_tier: 'low' as 'low' | 'high',
    amount: '1850',
    failure_reason: 'card_declined',
    retry_count: '0',
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [copiedField, setCopiedField] = useState<'english' | 'hinglish' | null>(null);

  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const applyPreset = (p: typeof PRESETS[0]) => {
    if (loading || !merchantId) return;
    setForm({
      customer_name: p.customer_name,
      customer_email: p.customer_email,
      customer_id: p.customer_id,
      customer_tier: p.customer_tier,
      amount: p.amount,
      failure_reason: p.failure_reason,
      retry_count: p.retry_count,
    });
    setResult(null);
  };

  const handleCopy = (field: 'english' | 'hinglish', text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(field);
    toast.success(`Copied ${field} message!`);
    setTimeout(() => setCopiedField(null), 2000);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!merchantId) {
      toast.error('Merchant account is loading. Please wait a moment.');
      return;
    }
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

  const isControlsDisabled = loading || !merchantId;

  return (
    <div className="try-live-container">
      {/* Left Column: Presets and Interactive Form */}
      <div className="try-live-left">
        <div style={{ marginBottom: 4 }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            ⚡ 1-Click Test Scenarios
          </div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {PRESETS.map((p) => (
              <button
                key={p.label}
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => applyPreset(p)}
                disabled={isControlsDisabled}
                style={{ fontSize: 12, padding: '6px 12px' }}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        <form className="try-form" onSubmit={handleSubmit} id="try-it-live-form">
          <div className="try-form-grid">
            <div className="form-group">
              <label className="form-label">Customer Name *</label>
              <input
                id="try-customer-name"
                className="form-input"
                placeholder="e.g. Priya Sharma"
                value={form.customer_name}
                onChange={(e) => set('customer_name', e.target.value)}
                disabled={isControlsDisabled}
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">Customer Email</label>
              <input
                id="try-customer-email"
                className="form-input"
                type="email"
                placeholder="priya@example.com"
                value={form.customer_email}
                onChange={(e) => set('customer_email', e.target.value)}
                disabled={isControlsDisabled}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Customer ID *</label>
              <input
                id="try-customer-id"
                className="form-input"
                placeholder="e.g. CUST001"
                value={form.customer_id}
                onChange={(e) => set('customer_id', e.target.value)}
                disabled={isControlsDisabled}
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">Customer Tier</label>
              <select
                id="try-customer-tier"
                className="form-input"
                value={form.customer_tier}
                onChange={(e) => set('customer_tier', e.target.value)}
                disabled={isControlsDisabled}
              >
                <option value="low">Low (below ₹5,000)</option>
                <option value="high">High (₹5,000+)</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Amount (₹) *</label>
              <input
                id="try-amount"
                className="form-input"
                type="number"
                placeholder="e.g. 2499"
                value={form.amount}
                onChange={(e) => set('amount', e.target.value)}
                disabled={isControlsDisabled}
                required
                min="0"
              />
            </div>
            <div className="form-group">
              <label className="form-label">Failure Reason</label>
              <select
                id="try-failure-reason"
                className="form-input"
                value={form.failure_reason}
                onChange={(e) => set('failure_reason', e.target.value)}
                disabled={isControlsDisabled}
              >
                {FAILURE_REASONS.map((r) => <option key={r} value={r}>{r.replace(/_/g, ' ')}</option>)}
              </select>
            </div>
            <div className="form-group" style={{ gridColumn: 'span 2' }}>
              <label className="form-label">Prior Retry Count</label>
              <select
                id="try-retry-count"
                className="form-input"
                value={form.retry_count}
                onChange={(e) => set('retry_count', e.target.value)}
                disabled={isControlsDisabled}
              >
                <option value="0">0 (first attempt)</option>
                <option value="1">1</option>
                <option value="2">2</option>
                <option value="3">3+ (Guardrail trigger limit)</option>
              </select>
            </div>
          </div>

          <button
            id="try-submit-btn"
            type="submit"
            className="btn btn-primary btn-lg"
            disabled={isControlsDisabled}
            style={{ alignSelf: 'flex-start', marginTop: 4 }}
          >
            {loading ? (
              <><div className="spinner" /> Running Agent Pipeline...</>
            ) : !merchantId ? (
              <><div className="spinner" /> Loading account...</>
            ) : (
              <><Zap size={16} /> Run Agent Pipeline</>
            )}
          </button>
        </form>
      </div>

      {/* Right Column: Real-time Output or Pipeline Architecture */}
      <div className="try-live-right">
        {result ? (
          <div className="result-card">
            <div className="flex-between mb-4">
              <div>
                <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 2 }}>
                  Selected Strategy
                </div>
                <div className="result-action">{result.decision?.action?.replace(/_/g, ' ')}</div>
              </div>
              <span className={`badge ${outcomeClass}`} style={{ fontSize: 12, padding: '4px 10px', textTransform: 'uppercase' }}>
                {outcomeBadge}
              </span>
            </div>

            <p className="result-reasoning">{result.decision?.reasoning}</p>

            {result.decision?.messages && (
              <div className="result-messages">
                {result.decision.messages.english && (
                  <div className="result-msg">
                    <strong>
                      <span>English Message</span>
                      <button
                        type="button"
                        className="btn btn-ghost btn-sm"
                        onClick={() => handleCopy('english', result.decision.messages.english)}
                        style={{ padding: '2px 6px', fontSize: 11, height: 'auto' }}
                      >
                        {copiedField === 'english' ? <Check size={12} color="#10b981" /> : <Copy size={12} />}
                        {copiedField === 'english' ? 'Copied' : 'Copy'}
                      </button>
                    </strong>
                    {result.decision.messages.english}
                  </div>
                )}
                {result.decision.messages.hinglish && (
                  <div className="result-msg">
                    <strong>
                      <span>Hinglish Message</span>
                      <button
                        type="button"
                        className="btn btn-ghost btn-sm"
                        onClick={() => handleCopy('hinglish', result.decision.messages.hinglish)}
                        style={{ padding: '2px 6px', fontSize: 11, height: 'auto' }}
                      >
                        {copiedField === 'hinglish' ? <Check size={12} color="#10b981" /> : <Copy size={12} />}
                        {copiedField === 'hinglish' ? 'Copied' : 'Copy'}
                      </button>
                    </strong>
                    {result.decision.messages.hinglish}
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="pipeline-explainer-card">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
              <Cpu size={18} style={{ color: 'var(--accent)' }} />
              <h3 style={{ fontSize: 15, fontWeight: 700, margin: 0 }}>Agent Decision Engine</h3>
            </div>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: 18 }}>
              Each failed payment is routed through a multi-stage autonomous pipeline before taking action:
            </p>

            <div className="pipeline-step">
              <div className="pipeline-step-badge">1</div>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>ML Failure Classifier</div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Classifies error codes into soft vs hard declines and customer fault.</div>
              </div>
            </div>

            <div className="pipeline-step">
              <div className="pipeline-step-badge">2</div>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>Autonomous Guardrails</div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Enforces cost floor (₹150) and prevents spamming past max retry limit.</div>
              </div>
            </div>

            <div className="pipeline-step">
              <div className="pipeline-step-badge">3</div>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>Multi-Armed Bandit Decision</div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Chooses optimal recovery route: smart retry, delayed retry, or pay link.</div>
              </div>
            </div>

            <div className="pipeline-step">
              <div className="pipeline-step-badge">4</div>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>Dual-Language Generator</div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Synthesizes targeted English and Hinglish recovery notifications.</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
