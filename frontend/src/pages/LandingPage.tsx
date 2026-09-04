import { Link } from 'react-router-dom';
import { Zap, ShieldCheck, BarChart2, Repeat, ArrowRight, GitBranch, Bot, Bell } from 'lucide-react';

export function LandingPage() {
  return (
    <div className="page-wrapper">
      {/* Navbar */}
      <nav className="navbar">
        <div className="navbar-inner">
          <div className="navbar-logo">
            <Zap size={20} style={{ color: 'var(--accent)' }} />
            Revenue<span>Recovery</span>
          </div>
          <div className="navbar-actions">
            <Link to="/login" className="btn btn-ghost btn-sm">Log in</Link>
            <Link to="/signup" className="btn btn-primary btn-sm">Get Started</Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="hero">
        <div className="hero-grid" />
        <div className="container">
          <div className="hero-content">
            <div className="hero-badge">
              <Zap size={11} /> AI-powered · Razorpay Integration
            </div>
            <h1 className="hero-title">
              Stop losing revenue to <span className="accent">failed payments</span>
            </h1>
            <p className="hero-desc">
              An autonomous AI agent that detects failed subscription payments, diagnoses root causes,
              chooses the optimal recovery intervention, and executes it — all in real time.
            </p>
            <div className="hero-actions">
              <Link to="/signup" id="hero-cta-signup" className="btn btn-primary btn-lg pulse-glow">
                Start recovering revenue <ArrowRight size={16} />
              </Link>
              <a href="#features" className="btn btn-secondary btn-lg">See how it works</a>
            </div>

            {/* Illustrative stats strip — sample figures, not live counters */}
            <div style={{ display: 'flex', gap: 32, marginTop: 48 }}>
              {[
                { val: '₹2.4L+', label: 'Recovered (sample)' },
                { val: '83%',    label: 'Recovery rate (sample)' },
                { val: '80',     label: 'Payments processed (sample)' },
              ].map((s) => (
                <div key={s.label}>
                  <div style={{ fontSize: 24, fontWeight: 700, fontFamily: "'Fraunces', serif", color: 'var(--accent)' }}>{s.val}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{s.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="features-section" id="features">
        <div className="container">
          <div className="section-header">
            <h2 className="section-title">How it works</h2>
            <p className="section-sub">5 steps from failure to recovery, fully automated</p>
          </div>
          <div className="features-grid">
            {[
              { icon: <Bot size={22} style={{ color: 'var(--accent)' }} />, title: 'Detect', desc: 'Real-time Razorpay webhook ingestion. Every payment.failed event is captured instantly.' },
              { icon: <GitBranch size={22} style={{ color: 'var(--accent-2)' }} />, title: 'Diagnose', desc: 'AI classifies failure reason — retryable, non-retryable, or edge case — with full auditability.' },
              { icon: <ShieldCheck size={22} style={{ color: 'var(--success)' }} />, title: 'Guardrails', desc: 'Hard limits enforced: max 3 attempts, 24h dedup, cost floor, invalid data skip.' },
              { icon: <Repeat size={22} style={{ color: 'var(--warning)' }} />, title: 'Decide', desc: 'Optimal intervention chosen per customer tier and A/B variant — immediate retry, 3-day retry, payment link, or escalate.' },
              { icon: <Bell size={22} style={{ color: 'var(--danger)' }} />, title: 'Execute', desc: 'Outreach messages generated in English & Hinglish. Every action logged with full reasoning.' },
              { icon: <BarChart2 size={22} style={{ color: 'var(--accent)' }} />, title: 'Measure', desc: 'Real-time dashboard tracks recovery rate, A/B results, action distribution, and exceptions.' },
            ].map((f) => (
              <div key={f.title} className="feature-card">
                <div className="feature-icon-wrap">{f.icon}</div>
                <h3 className="feature-title">{f.title}</h3>
                <p className="feature-desc">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="cta-section">
        <div className="container">
          <h2 className="section-title" style={{ marginBottom: 12 }}>Ready to recover lost revenue?</h2>
          <p className="section-sub" style={{ marginBottom: 36 }}>Sign up free and run the agent on your own failed payments in minutes.</p>
          <Link to="/signup" id="cta-signup-btn" className="btn btn-primary btn-lg">
            Get started for free <ArrowRight size={16} />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer style={{ borderTop: '1px solid var(--border)', padding: '24px 0', textAlign: 'center' }}>
        <div className="container">
          <p className="text-muted text-sm">
            Built for Razorpay Buildathon 2026 · <a href="https://github.com/boopathi-7546/ai-revenue-recovery-razor" target="_blank" rel="noreferrer">GitHub</a>
          </p>
        </div>
      </footer>
    </div>
  );
}
