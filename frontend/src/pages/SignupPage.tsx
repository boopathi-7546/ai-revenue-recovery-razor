import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Zap, Mail, Lock, Building2, Eye, EyeOff } from 'lucide-react';
import { supabase } from '../supabase';
import { createMerchant } from '../api';
import toast from 'react-hot-toast';

export function SignupPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ businessName: '', email: '', password: '', confirmPassword: '' });
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (form.password !== form.confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    if (form.password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }
    setLoading(true);
    try {
      // 1. Create Supabase Auth user
      const { data, error: authError } = await supabase.auth.signUp({
        email: form.email,
        password: form.password,
      });
      if (authError) throw authError;
      if (!data.user) throw new Error('Signup failed — no user returned');

      // 2. Create merchant row via FastAPI (idempotent)
      await createMerchant({
        auth_user_id: data.user.id,
        business_name: form.businessName,
      });

      toast.success('Account created! Welcome aboard 🎉');
      navigate('/dashboard');
    } catch (e: any) {
      setError(e.message || 'Signup failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-header">
          <div className="auth-logo">
            <Zap size={20} style={{ color: 'var(--accent)', verticalAlign: 'middle', marginRight: 6 }} />
            Revenue<span>Recovery</span>
          </div>
          <p className="auth-subtitle">Create your merchant account</p>
        </div>

        <form className="auth-form" onSubmit={handleSignup} id="signup-form">
          {error && <div className="alert alert-error"><span>{error}</span></div>}

          <div className="form-group">
            <label className="form-label" htmlFor="signup-business">Business Name</label>
            <div style={{ position: 'relative' }}>
              <Building2 size={15} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input id="signup-business" type="text" className="form-input" placeholder="Acme Corp" style={{ paddingLeft: 36 }} value={form.businessName} onChange={(e) => set('businessName', e.target.value)} required />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="signup-email">Email address</label>
            <div style={{ position: 'relative' }}>
              <Mail size={15} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input id="signup-email" type="email" className="form-input" placeholder="you@company.com" style={{ paddingLeft: 36 }} value={form.email} onChange={(e) => set('email', e.target.value)} required autoComplete="email" />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="signup-password">Password</label>
            <div style={{ position: 'relative' }}>
              <Lock size={15} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input id="signup-password" type={showPw ? 'text' : 'password'} className="form-input" placeholder="Min 6 characters" style={{ paddingLeft: 36, paddingRight: 40 }} value={form.password} onChange={(e) => set('password', e.target.value)} required autoComplete="new-password" />
              <button type="button" id="signup-toggle-pw" onClick={() => setShowPw(!showPw)} style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: 0 }}>
                {showPw ? <EyeOff size={15} /> : <Eye size={15} />}
              </button>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="signup-confirm-password">Confirm Password</label>
            <div style={{ position: 'relative' }}>
              <Lock size={15} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input id="signup-confirm-password" type={showPw ? 'text' : 'password'} className="form-input" placeholder="Re-enter password" style={{ paddingLeft: 36 }} value={form.confirmPassword} onChange={(e) => set('confirmPassword', e.target.value)} required autoComplete="new-password" />
            </div>
          </div>

          <button id="signup-submit-btn" type="submit" className="btn btn-primary w-full" style={{ justifyContent: 'center' }} disabled={loading}>
            {loading ? <><div className="spinner" /> Creating account...</> : 'Create account'}
          </button>
        </form>

        <div className="auth-footer">
          Already have an account? <Link to="/login">Sign in</Link>
        </div>
      </div>
    </div>
  );
}
