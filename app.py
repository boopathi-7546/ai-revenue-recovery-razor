"""
AI Revenue Recovery Dashboard — Streamlit app.

Sections:
  1. Metric cards (animated count-up)
  2. Plotly line chart: recovery rate over time
  3. Plotly bar chart: by failure reason
  4. Plotly bar chart: A/B variant comparison
  5. Filterable audit log table
  6. Lottie animations (success / alert)
  7. Custom dark fintech CSS
  8. Sidebar: English / Hinglish message preview
  9. 3D bar visualization (Three.js via st.components)
"""

import os
import sys
import json
import time
import random
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from streamlit.components.v1 import html as st_html

# ── Path setup ─────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

AUDIT_CSV    = os.path.join(ROOT, "logs", "audit_trail.csv")
METRICS_JSON = os.path.join(ROOT, "logs", "metrics.json")

# ── Streamlit page config ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Revenue Recovery | Razorpay",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
#  DARK FINTECH CSS
# ══════════════════════════════════════════════════════════════════════════════
DARK_CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

  /* ── Design Tokens ───────────────────────────────────────────────── */
  :root {
    --bg-dark:        #0a0e1a;
    --bg-card:        #0f1623;
    --bg-card-hover:  #141e30;
    --bg-glass:       rgba(15, 22, 35, 0.72);
    --accent-green:   #00d4aa;
    --accent-red:     #ff4d6d;
    --accent-blue:    #4f8ef7;
    --accent-purple:  #a855f7;
    --accent-amber:   #f59e0b;
    --text-primary:   #f1f5f9;
    --text-secondary: #cbd5e1;
    --text-muted:     #64748b;
    --text-dim:       #475569;
    --border:         #1e293b;
    --border-subtle:  #0f1929;
    --gradient-hero:  linear-gradient(135deg, #080c18 0%, #0f1623 55%, #0b1525 100%);
    --gradient-green: linear-gradient(135deg, #00d4aa, #00b4d8);
    --gradient-red:   linear-gradient(135deg, #ff4d6d, #f72585);
    --gradient-blue:  linear-gradient(135deg, #4f8ef7, #a855f7);
    --gradient-amber: linear-gradient(135deg, #f59e0b, #ef4444);
    --glow-green:     0 0 24px rgba(0,212,170,0.22), 0 8px 32px rgba(0,0,0,0.5);
    --glow-red:       0 0 24px rgba(255,77,109,0.22), 0 8px 32px rgba(0,0,0,0.5);
    --glow-blue:      0 0 24px rgba(79,142,247,0.22),  0 8px 32px rgba(0,0,0,0.5);
    --glow-amber:     0 0 24px rgba(245,158,11,0.22),  0 8px 32px rgba(0,0,0,0.5);
    --transition-fast:   0.18s ease;
    --transition-smooth: 0.28s cubic-bezier(0.4, 0, 0.2, 1);
    --transition-spring: 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
    --radius-sm:  8px;
    --radius-md:  12px;
    --radius-lg:  18px;
    --radius-xl:  24px;
  }

  /* ── Keyframe animations ─────────────────────────────────────────── */
  @keyframes page-fade-in {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0);    }
  }
  @keyframes fade-in {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: translateY(0);   }
  }
  @keyframes slide-up {
    from { opacity: 0; transform: translateY(14px); }
    to   { opacity: 1; transform: translateY(0);    }
  }

  /* Page-load animation on the main content block */
  .main .block-container {
    animation: page-fade-in 0.55s ease both;
    padding-top: 2rem !important;
    padding-bottom: 3rem !important;
  }

  /* ── Base ────────────────────────────────────────────────────────── */
  html, body, [class*="css"], .stApp {
    font-family: 'Inter', sans-serif !important;
    background-color: var(--bg-dark) !important;
    color: var(--text-primary) !important;
  }

  /* ── Sidebar ─────────────────────────────────────────────────────── */
  section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #090d1b 0%, #0d1220 50%, #111827 100%) !important;
    border-right: 1px solid var(--border-subtle) !important;
  }
  section[data-testid="stSidebar"] * { color: var(--text-primary) !important; }
  section[data-testid="stSidebar"] .stSelectbox > div > div {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    transition: border-color var(--transition-fast), box-shadow var(--transition-fast) !important;
  }
  section[data-testid="stSidebar"] .stSelectbox > div > div:hover {
    border-color: var(--accent-blue) !important;
    box-shadow: 0 0 0 3px rgba(79,142,247,0.1) !important;
  }

  /* ── Hero header ─────────────────────────────────────────────────── */
  .hero-header {
    background: var(--gradient-hero);
    border: 1px solid rgba(79,142,247,0.18);
    border-radius: var(--radius-xl);
    padding: 36px 48px;
    margin-bottom: 36px;
    position: relative;
    overflow: hidden;
    animation: slide-up 0.5s ease both;
  }
  .hero-header::before {
    content: '';
    position: absolute;
    top: -60%; left: -30%;
    width: 160%; height: 220%;
    background: radial-gradient(ellipse at 40% 40%, rgba(79,142,247,0.07) 0%, transparent 55%),
                radial-gradient(ellipse at 70% 70%, rgba(0,212,170,0.04) 0%, transparent 45%);
    pointer-events: none;
  }
  .hero-header::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent 0%, rgba(79,142,247,0.35) 30%, rgba(0,212,170,0.35) 70%, transparent 100%);
  }
  .hero-title {
    font-size: 2.6rem;
    font-weight: 800;
    line-height: 1.15;
    letter-spacing: -0.03em;
    background: linear-gradient(135deg, #f1f5f9 0%, #4f8ef7 50%, #00d4aa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 10px 0;
  }
  .hero-subtitle {
    color: var(--text-secondary);
    font-size: 0.95rem;
    font-weight: 400;
    line-height: 1.6;
    margin: 0;
    max-width: 680px;
  }
  .hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(0,212,170,0.1);
    border: 1px solid rgba(0,212,170,0.25);
    color: var(--accent-green);
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 16px;
    animation: fade-in 0.4s ease 0.2s both;
  }

  /* ── Metric Cards — glassmorphism + per-color glow on hover ──────── */
  .metric-card {
    background: var(--bg-glass);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 28px 32px;
    position: relative;
    overflow: hidden;
    transition:
      transform     var(--transition-spring),
      box-shadow    var(--transition-smooth),
      background    var(--transition-smooth),
      border-color  var(--transition-smooth);
    cursor: default;
    animation: slide-up 0.5s ease both;
    min-height: 140px;
  }
  .metric-card::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, rgba(255,255,255,0.03) 0%, transparent 60%);
    border-radius: inherit;
    pointer-events: none;
  }
  .metric-card::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 2px;
    border-radius: 0 0 var(--radius-lg) var(--radius-lg);
    opacity: 0.8;
    transition: height var(--transition-smooth), opacity var(--transition-smooth);
  }
  .metric-card.green::after  { background: var(--gradient-green); }
  .metric-card.red::after    { background: var(--gradient-red);   }
  .metric-card.blue::after   { background: var(--gradient-blue);  }
  .metric-card.amber::after  { background: var(--gradient-amber); }

  .metric-card:hover                { background: var(--bg-card-hover); transform: translateY(-6px) scale(1.01); }
  .metric-card:hover::after         { height: 3px; opacity: 1; }
  .metric-card.green:hover          { border-color: rgba(0,212,170,0.35);  box-shadow: var(--glow-green); }
  .metric-card.red:hover            { border-color: rgba(255,77,109,0.35); box-shadow: var(--glow-red);   }
  .metric-card.blue:hover           { border-color: rgba(79,142,247,0.35); box-shadow: var(--glow-blue);  }
  .metric-card.amber:hover          { border-color: rgba(245,158,11,0.35); box-shadow: var(--glow-amber); }

  /* Font hierarchy: label → value → sub */
  .metric-label {
    color: var(--text-muted);
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 10px;
  }
  .metric-value {
    font-size: 2.1rem;
    font-weight: 800;
    color: var(--text-primary);
    line-height: 1;
    letter-spacing: -0.02em;
    margin-bottom: 6px;
  }
  .metric-sub {
    color: var(--text-dim);
    font-size: 0.76rem;
    font-weight: 400;
    line-height: 1.4;
    margin-top: 8px;
  }
  .metric-icon {
    position: absolute;
    top: 22px; right: 26px;
    font-size: 1.8rem;
    opacity: 0.15;
    transition: opacity var(--transition-smooth), transform var(--transition-spring);
  }
  .metric-card:hover .metric-icon { opacity: 0.3; transform: scale(1.12) rotate(-5deg); }

  /* ── Section typography ──────────────────────────────────────────── */
  .section-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: -0.01em;
    margin-bottom: 3px;
  }
  .section-sub {
    font-size: 0.78rem;
    font-weight: 400;
    color: var(--text-muted);
    margin-bottom: 18px;
    line-height: 1.5;
  }

  /* ── Chart wrapper ───────────────────────────────────────────────── */
  .chart-section {
    background: var(--bg-glass);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 28px;
    margin-bottom: 24px;
    transition: border-color var(--transition-smooth);
  }
  .chart-section:hover { border-color: rgba(79,142,247,0.2); }

  /* ── Tab bar — glassmorphism + gradient active indicator ─────────── */
  .stTabs [data-baseweb="tab-list"] {
    background: rgba(15,22,35,0.8) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border-radius: var(--radius-md) !important;
    padding: 5px !important;
    border: 1px solid var(--border) !important;
    gap: 2px !important;
  }
  .stTabs [data-baseweb="tab"] {
    border-radius: var(--radius-sm) !important;
    color: var(--text-muted) !important;
    font-weight: 500 !important;
    font-size: 0.88rem !important;
    padding: 8px 18px !important;
    transition: color var(--transition-fast), background var(--transition-fast) !important;
  }
  .stTabs [data-baseweb="tab"]:hover {
    color: var(--text-secondary) !important;
    background: rgba(255,255,255,0.04) !important;
  }
  .stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(79,142,247,0.18), rgba(0,212,170,0.10)) !important;
    color: var(--text-primary) !important;
    font-weight: 600 !important;
    box-shadow: 0 0 0 1px rgba(79,142,247,0.25) !important;
  }

  /* Tab panel fade-in — triggers each time a tab is selected */
  .stTabs [data-baseweb="tab-panel"] {
    animation: fade-in 0.32s ease both;
  }

  /* ── Form inputs ─────────────────────────────────────────────────── */
  .stSelectbox > div > div,
  .stTextInput > div > div > input,
  .stMultiSelect > div {
    background: rgba(15,22,35,0.9) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-primary) !important;
    border-radius: var(--radius-md) !important;
    transition: border-color var(--transition-fast), box-shadow var(--transition-fast) !important;
  }
  .stSelectbox > div > div:hover,
  .stTextInput > div > div > input:hover,
  .stMultiSelect > div:hover {
    border-color: rgba(79,142,247,0.4) !important;
    box-shadow: 0 0 0 3px rgba(79,142,247,0.08) !important;
  }
  .stSelectbox > div > div:focus-within,
  .stTextInput > div > div > input:focus,
  .stMultiSelect > div:focus-within {
    border-color: var(--accent-blue) !important;
    box-shadow: 0 0 0 3px rgba(79,142,247,0.15) !important;
    outline: none !important;
  }

  /* ── Buttons ─────────────────────────────────────────────────────── */
  .stButton > button {
    transition: transform var(--transition-fast), box-shadow var(--transition-smooth), background var(--transition-fast) !important;
  }
  .stButton > button:hover  { transform: translateY(-2px) !important; box-shadow: 0 6px 20px rgba(0,0,0,0.35) !important; }
  .stButton > button:active { transform: translateY(0) !important; }

  /* ── Dataframe ───────────────────────────────────────────────────── */
  .stDataFrame {
    border-radius: var(--radius-md) !important;
    overflow: hidden !important;
    border: 1px solid var(--border) !important;
  }
  [data-testid="stDataFrame"] tr { transition: background var(--transition-fast) !important; }
  [data-testid="stDataFrame"] tr:hover { background: rgba(79,142,247,0.07) !important; }

  /* ── Exception cards (inline hover) ─────────────────────────────── */
  .exception-card {
    transition: transform var(--transition-smooth), box-shadow var(--transition-smooth), border-color var(--transition-smooth);
  }
  .exception-card:hover {
    transform: translateX(4px);
    border-color: rgba(245,158,11,0.4) !important;
    box-shadow: -4px 0 16px rgba(245,158,11,0.1);
  }

  /* ── Exception badge ─────────────────────────────────────────────── */
  .exception-badge {
    display: inline-flex;
    align-items: center;
    background: rgba(255,77,109,0.12);
    border: 1px solid rgba(255,77,109,0.25);
    color: var(--accent-red);
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 700;
    margin-left: 8px;
    letter-spacing: 0.03em;
  }

  /* ── Pill tags ───────────────────────────────────────────────────── */
  .pill { display:inline-block; padding:3px 11px; border-radius:20px; font-size:0.71rem; font-weight:600; letter-spacing:0.02em; transition:opacity var(--transition-fast); }
  .pill:hover { opacity: 0.85; }
  .pill-green { background:rgba(0,212,170,0.13); color:#00d4aa; border:1px solid rgba(0,212,170,0.22); }
  .pill-red   { background:rgba(255,77,109,0.13); color:#ff4d6d; border:1px solid rgba(255,77,109,0.22); }
  .pill-amber { background:rgba(245,158,11,0.13); color:#f59e0b; border:1px solid rgba(245,158,11,0.22); }
  .pill-blue  { background:rgba(79,142,247,0.13); color:#4f8ef7; border:1px solid rgba(79,142,247,0.22); }

  /* ── Divider ─────────────────────────────────────────────────────── */
  hr { border:none !important; border-top:1px solid var(--border-subtle) !important; margin:24px 0 !important; }

  /* ── Scrollbar ───────────────────────────────────────────────────── */
  ::-webkit-scrollbar { width:5px; height:5px; }
  ::-webkit-scrollbar-track { background: var(--bg-dark); }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius:3px; }
  ::-webkit-scrollbar-thumb:hover { background: #2d3f55; }

  /* ── Column spacing ──────────────────────────────────────────────── */
  [data-testid="column"] { padding:0 6px !important; }
  [data-testid="column"]:first-child { padding-left:0 !important; }
  [data-testid="column"]:last-child  { padding-right:0 !important; }

  /* ── Alert boxes ─────────────────────────────────────────────────── */
  .stAlert {
    border-radius: var(--radius-md) !important;
    border: 1px solid var(--border) !important;
    background: rgba(15,22,35,0.8) !important;
  }

  /* ── Download button ─────────────────────────────────────────────── */
  [data-testid="stDownloadButton"] button {
    background: rgba(79,142,247,0.1) !important;
    border: 1px solid rgba(79,142,247,0.25) !important;
    color: var(--accent-blue) !important;
    border-radius: var(--radius-md) !important;
    font-weight: 600 !important;
    transition: background var(--transition-fast), border-color var(--transition-fast), transform var(--transition-fast) !important;
  }
  [data-testid="stDownloadButton"] button:hover {
    background: rgba(79,142,247,0.18) !important;
    border-color: rgba(79,142,247,0.45) !important;
    transform: translateY(-1px) !important;
  }

  /* ── Hide streamlit chrome ───────────────────────────────────────── */
  footer { display: none !important; }
  #MainMenu { visibility: hidden !important; }
</style>
"""

st.markdown(DARK_CSS, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  LOAD DATA
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=30)
def load_data():
    if not os.path.exists(AUDIT_CSV):
        return None, None
    df = pd.read_csv(AUDIT_CSV)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    with open(METRICS_JSON, "r", encoding="utf-8") as f:
        metrics = json.load(f)
    return df, metrics


df, metrics = load_data()

# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:16px 0 8px;">
      <div style="font-size:2.5rem;">💳</div>
      <div style="font-weight:800;font-size:1.1rem;color:#f1f5f9;">AI Recovery Agent</div>
      <div style="font-size:0.75rem;color:#64748b;margin-top:2px;">Hackathon Edition</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    st.markdown("### ⚙️ Controls")
    lang_choice = st.selectbox(
        "Message Language",
        ["English", "Hinglish"],
        help="Preview outreach messages in English or Hinglish"
    )
    st.divider()

    if df is not None:
        st.markdown("### 🔍 Customer Lookup")
        customer_ids = sorted(df["customer_id"].unique().tolist())
        selected_cid = st.selectbox("Select Customer ID", customer_ids)
        row = df[df["customer_id"] == selected_cid].iloc[0]

        with st.container():
            st.markdown(f"""
            <div style="background:#111827;border:1px solid #1e293b;border-radius:12px;padding:16px;margin-top:8px;">
              <div style="color:#94a3b8;font-size:0.72rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;">Customer</div>
              <div style="font-weight:700;font-size:1rem;color:#f1f5f9;margin:4px 0;">{row['customer_name']}</div>
              <div style="color:#64748b;font-size:0.78rem;">{row['customer_id']} · {row['customer_tier'].upper()} TIER</div>
              <hr style="border-color:#1e293b;margin:12px 0;">
              <div style="color:#94a3b8;font-size:0.72rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;">Amount</div>
              <div style="color:#00d4aa;font-weight:800;font-size:1.2rem;margin:4px 0;">₹{float(row['amount']):,.2f}</div>
              <div style="color:#94a3b8;font-size:0.72rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;margin-top:10px;">Failure</div>
              <div style="color:#ff4d6d;font-size:0.85rem;font-weight:500;margin:4px 0;">{row['failure_reason'].replace('_',' ').title()}</div>
              <div style="color:#94a3b8;font-size:0.72rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;margin-top:10px;">Action Taken</div>
              <div style="color:#4f8ef7;font-size:0.85rem;font-weight:500;margin:4px 0;">{row['action_taken'].replace('_',' ').title()}</div>
              <div style="color:#94a3b8;font-size:0.72rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;margin-top:10px;">Outcome</div>
              <div style="color:{'#00d4aa' if row['outcome']=='success' else '#ff4d6d' if row['outcome']=='failed' else '#f59e0b'};font-size:0.85rem;font-weight:700;margin:4px 0;">{row['outcome'].upper()}</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("**📩 Outreach Message:**")
            msg_col = "msg_english" if lang_choice == "English" else "msg_hinglish"
            msg_text = str(row.get(msg_col, "No message available."))
            st.info(msg_text)
    st.divider()
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  HERO HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="hero-header">
  <div class="hero-badge">🤖 Hackathon Submission</div>
  <div class="hero-title">AI Revenue Recovery</div>
  <p class="hero-subtitle">
    Autonomous agent that detects failed payments · diagnoses root causes · executes bounded recovery workflows
    · presents measurable results with full audit rigour.
  </p>
</div>
""", unsafe_allow_html=True)

# ── Handle no data ─────────────────────────────────────────────────────────────
if df is None or metrics is None:
    st.error("⚠️ No data found. Run `python main.py` first to generate data and run the agent.")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
#  LOTTIE ANIMATIONS
# ══════════════════════════════════════════════════════════════════════════════
try:
    from streamlit_lottie import st_lottie
    import requests

    @st.cache_data(show_spinner=False)
    def load_lottie(url: str):
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return None

    LOTTIE_SUCCESS = load_lottie("https://assets9.lottiefiles.com/packages/lf20_attqquof.json")
    LOTTIE_ALERT   = load_lottie("https://assets4.lottiefiles.com/packages/lf20_qpwbiyxf.json")
    LOTTIE_MONEY   = load_lottie("https://assets1.lottiefiles.com/packages/lf20_06a6pf9i.json")
    LOTTIE_LOADED  = True
except Exception:
    LOTTIE_LOADED = False

# ══════════════════════════════════════════════════════════════════════════════
#  ANIMATED METRIC CARDS  (count-up effect)
# ══════════════════════════════════════════════════════════════════════════════
recovery_rate = float(metrics.get("recovery_rate_pct", 0))
total_at_risk = float(metrics.get("total_at_risk", 0))
total_recovered = float(metrics.get("total_recovered", 0))
exception_count = int(metrics.get("exception_count", 0))

STEPS    = 40
DELAY_S  = 0.025

col1, col2, col3, col4 = st.columns(4)

ph_risk   = col1.empty()
ph_rec    = col2.empty()
ph_rate   = col3.empty()
ph_exc    = col4.empty()

def render_metric(placeholder, label, value, sub, color_class, icon, prefix="", suffix=""):
    placeholder.markdown(f"""
    <div class="metric-card {color_class}" style="min-height:130px;">
      <div class="metric-icon">{icon}</div>
      <div class="metric-label">{label}</div>
      <div class="metric-value">{prefix}{value}{suffix}</div>
      <div class="metric-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

# Animate count-up
for step in range(1, STEPS + 1):
    frac = step / STEPS
    cur_risk  = total_at_risk  * frac
    cur_rec   = total_recovered * frac
    cur_rate  = recovery_rate  * frac
    cur_exc   = int(exception_count * frac)

    render_metric(ph_risk,  "Total at Risk",    f"{cur_risk:,.0f}",  "INR · all failed payments attempted", "red",   "⚠️", prefix="₹")
    render_metric(ph_rec,   "Total Recovered",  f"{cur_rec:,.0f}",   "INR · successfully collected",         "green", "✅", prefix="₹")
    render_metric(ph_rate,  "Recovery Rate",    f"{cur_rate:.1f}",   f"Target: 70% · {'🔥 Exceeded!' if recovery_rate>=70 else '⬆ Near target'}", "blue" if recovery_rate < 70 else "green", "📈", suffix="%")
    render_metric(ph_exc,   "Exceptions",       str(cur_exc),        "Skipped (refunded/duplicate/invalid)",  "amber", "🚨")
    time.sleep(DELAY_S)

# ── Balloons if > 70% ─────────────────────────────────────────────────────────
if recovery_rate >= 70:
    st.balloons()

# ── Lottie animations ─────────────────────────────────────────────────────────
if LOTTIE_LOADED:
    la, lb, lc = st.columns([1, 2, 1])
    with la:
        if LOTTIE_ALERT and exception_count > 0:
            st_lottie(LOTTIE_ALERT, height=90, key="alert_lottie", loop=False)
    with lb:
        if LOTTIE_MONEY:
            st_lottie(LOTTIE_MONEY, height=90, key="money_lottie", loop=True)
    with lc:
        if LOTTIE_SUCCESS and recovery_rate >= 60:
            st_lottie(LOTTIE_SUCCESS, height=90, key="success_lottie", loop=False)

st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  TABS: Charts / Audit Log / Exceptions / 3D View
# ══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs(["📊 Analytics", "📋 Audit Log", "⚠️ Exceptions", "🌐 3D View"])

# ─────────────────────────────────────────────────────────────────────────────
#  TAB 1: Analytics
# ─────────────────────────────────────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color="#94a3b8"),
    margin=dict(l=20, r=20, t=40, b=20),
    colorway=["#4f8ef7", "#00d4aa", "#ff4d6d", "#a855f7", "#f59e0b"],
    xaxis=dict(gridcolor="#1e293b", linecolor="#1e293b", zerolinecolor="#1e293b"),
    yaxis=dict(gridcolor="#1e293b", linecolor="#1e293b", zerolinecolor="#1e293b"),
)

with tab1:
    # ── Row 1: Recovery Over Time + A/B Test ──────────────────────────────────
    c1, c2 = st.columns([3, 2])

    with c1:
        st.markdown('<div class="section-title">📈 Recovery Rate Over Time</div><div class="section-sub">Cumulative recovery percentage as interventions execute</div>', unsafe_allow_html=True)
        ts = metrics.get("time_series", [])
        if ts:
            ts_df = pd.DataFrame(ts)
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(
                x=ts_df["date"], y=ts_df["cumulative_rate"],
                mode="lines+markers",
                name="Recovery Rate %",
                line=dict(color="#4f8ef7", width=3, shape="spline"),
                marker=dict(size=7, color="#4f8ef7", line=dict(width=2, color="#0a0e1a")),
                fill="tozeroy", fillcolor="rgba(79,142,247,0.08)",
                hovertemplate="<b>%{x}</b><br>Rate: %{y:.1f}%<extra></extra>",
            ))
            fig_line.add_hline(y=70, line_dash="dash", line_color="#f59e0b", annotation_text="70% Target",
                               annotation_font_color="#f59e0b", annotation_position="top right")
            _line_layout = {**PLOTLY_LAYOUT, "height": 320,
                            "yaxis": {**PLOTLY_LAYOUT["yaxis"], "range": [0, 105], "ticksuffix": "%"}}
            fig_line.update_layout(**_line_layout)
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("No time series data available.")

    with c2:
        st.markdown('<div class="section-title">🧪 A/B Variant Comparison</div><div class="section-sub">Plain reminder (A) vs urgency-framed (B)</div>', unsafe_allow_html=True)
        ab = metrics.get("ab_stats", {})
        if ab:
            ab_df = pd.DataFrame([
                {"Variant": f"A — Standard", "Recovery Rate": ab["A"].get("recovery_rate", 0),
                 "Recovered": ab["A"].get("recovered", 0), "Attempts": ab["A"].get("attempts", 0)},
                {"Variant": f"B — Urgency",  "Recovery Rate": ab["B"].get("recovery_rate", 0),
                 "Recovered": ab["B"].get("recovered", 0), "Attempts": ab["B"].get("attempts", 0)},
            ])
            fig_ab = go.Figure()
            colors = ["#4f8ef7", "#00d4aa"]
            for i, row_ab in ab_df.iterrows():
                fig_ab.add_trace(go.Bar(
                    x=[row_ab["Variant"]], y=[row_ab["Recovery Rate"]],
                    name=row_ab["Variant"],
                    marker=dict(color=colors[i], opacity=0.9,
                                line=dict(color=colors[i], width=1)),
                    text=[f"{row_ab['Recovery Rate']:.1f}%"],
                    textposition="outside", textfont=dict(color="#f1f5f9", size=14, family="Inter"),
                    hovertemplate=(f"<b>{row_ab['Variant']}</b><br>"
                                   f"Rate: {row_ab['Recovery Rate']:.1f}%<br>"
                                   f"Recovered: {row_ab['Recovered']}/{row_ab['Attempts']}<extra></extra>"),
                ))
            _ab_layout = {**PLOTLY_LAYOUT, "height": 320, "showlegend": False,
                          "yaxis": {**PLOTLY_LAYOUT["yaxis"], "range": [0, 115], "ticksuffix": "%"}}
            fig_ab.update_layout(**_ab_layout)
            st.plotly_chart(fig_ab, use_container_width=True)

    # ── Row 2: By Failure Reason ──────────────────────────────────────────────
    st.markdown('<div class="section-title">🔍 Recovery by Failure Reason</div><div class="section-sub">Success vs. attempt counts per failure category</div>', unsafe_allow_html=True)
    rs = metrics.get("reason_stats", {})
    if rs:
        reasons = list(rs.keys())
        attempts_vals  = [rs[r]["attempts"]   for r in reasons]
        recovered_vals = [rs[r]["recovered"]  for r in reasons]
        failed_vals    = [a - rec for a, rec in zip(attempts_vals, recovered_vals)]
        rate_vals      = [rs[r].get("recovery_rate", 0) for r in reasons]

        fig_reason = go.Figure()
        fig_reason.add_trace(go.Bar(
            name="Recovered", x=reasons, y=recovered_vals,
            marker=dict(color="#00d4aa", opacity=0.9, line=dict(color="#00d4aa", width=1)),
            text=[f"₹{rs[r]['amount_recovered']:,.0f}" for r in reasons],
            textposition="inside", textfont=dict(color="#0a0e1a", size=11, family="Inter"),
            hovertemplate="<b>%{x}</b><br>Recovered: %{y}<extra></extra>",
        ))
        fig_reason.add_trace(go.Bar(
            name="Failed", x=reasons, y=failed_vals,
            marker=dict(color="#ff4d6d", opacity=0.7, line=dict(color="#ff4d6d", width=1)),
            hovertemplate="<b>%{x}</b><br>Failed: %{y}<extra></extra>",
        ))
        fig_reason.update_layout(
            **PLOTLY_LAYOUT, height=360, barmode="stack",
            legend=dict(orientation="h", y=1.05, x=0.5, xanchor="center",
                        font=dict(color="#94a3b8")),
        )
        fig_reason.update_xaxes(ticktext=[r.replace("_", " ").title() for r in reasons],
                                tickvals=reasons)
        st.plotly_chart(fig_reason, use_container_width=True)

    # ── Row 3: Action distribution + Tier breakdown ───────────────────────────
    c3, c4 = st.columns(2)

    with c3:
        st.markdown('<div class="section-title">⚡ Action Distribution</div><div class="section-sub">Breakdown of interventions chosen by the agent</div>', unsafe_allow_html=True)
        action_counts = df[df["outcome"] != "skipped"]["action_taken"].value_counts().reset_index()
        action_counts.columns = ["Action", "Count"]
        action_counts["Action"] = action_counts["Action"].str.replace("_", " ").str.title()
        fig_pie = go.Figure(go.Pie(
            labels=action_counts["Action"], values=action_counts["Count"],
            hole=0.55,
            marker=dict(colors=["#4f8ef7","#00d4aa","#a855f7","#f59e0b","#ff4d6d"],
                        line=dict(color="#0a0e1a", width=2)),
            textfont=dict(color="#f1f5f9", size=11),
            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>",
        ))
        fig_pie.update_layout(**PLOTLY_LAYOUT, height=320,
                              annotations=[dict(text="Actions", x=0.5, y=0.5, font_size=14,
                                               font_color="#f1f5f9", showarrow=False)])
        st.plotly_chart(fig_pie, use_container_width=True)

    with c4:
        st.markdown('<div class="section-title">🏆 Recovery by Tier</div><div class="section-sub">High-value vs. low-value customer outcomes</div>', unsafe_allow_html=True)
        tier_df = df[df["outcome"] != "skipped"].groupby("customer_tier").apply(
            lambda g: pd.Series({
                "At Risk":   g["amount"].sum(),
                "Recovered": g[g["outcome"] == "success"]["amount"].sum(),
            })
        ).reset_index()

        fig_tier = go.Figure()
        fig_tier.add_trace(go.Bar(
            x=tier_df["customer_tier"].str.upper(), y=tier_df["At Risk"],
            name="At Risk", marker_color="#ff4d6d", opacity=0.8,
        ))
        fig_tier.add_trace(go.Bar(
            x=tier_df["customer_tier"].str.upper(), y=tier_df["Recovered"],
            name="Recovered", marker_color="#00d4aa", opacity=0.9,
        ))
        _tier_layout = {**PLOTLY_LAYOUT, "height": 320, "barmode": "group",
                        "legend": dict(orientation="h", y=1.05, x=0.5, xanchor="center",
                                       font=dict(color="#94a3b8")),
                        "yaxis": {**PLOTLY_LAYOUT["yaxis"], "tickprefix": "₹"}}
        fig_tier.update_layout(**_tier_layout)
        st.plotly_chart(fig_tier, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
#  TAB 2: Audit Log
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown('<div class="section-title">📋 Full Audit Trail</div><div class="section-sub">Every agent decision, timestamped and reasoned — filterable</div>', unsafe_allow_html=True)

    # Filter controls
    f1, f2, f3, f4 = st.columns([2, 2, 2, 1])
    with f1:
        outcome_filter = st.multiselect("Outcome", df["outcome"].unique().tolist(),
                                         default=df["outcome"].unique().tolist(), key="oc_filter")
    with f2:
        reason_filter = st.multiselect("Failure Reason",
                                        df["failure_reason"].unique().tolist(),
                                        default=df["failure_reason"].unique().tolist(), key="fr_filter")
    with f3:
        tier_filter = st.multiselect("Customer Tier",
                                      df["customer_tier"].unique().tolist(),
                                      default=df["customer_tier"].unique().tolist(), key="ct_filter")
    with f4:
        search_term = st.text_input("Search name/ID", placeholder="🔍 search...", key="search")

    display_df = df[
        df["outcome"].isin(outcome_filter) &
        df["failure_reason"].isin(reason_filter) &
        df["customer_tier"].isin(tier_filter)
    ]
    if search_term:
        mask = (
            display_df["customer_id"].str.contains(search_term, case=False, na=False) |
            display_df["customer_name"].str.contains(search_term, case=False, na=False)
        )
        display_df = display_df[mask]

    show_cols = ["customer_id", "customer_name", "amount", "failure_reason",
                 "customer_tier", "action_taken", "variant", "outcome", "reasoning"]
    styled = display_df[show_cols].copy()
    styled["amount"] = styled["amount"].apply(lambda x: f"₹{float(x):,.2f}")

    st.dataframe(
        styled,
        use_container_width=True,
        height=480,
        column_config={
            "customer_id":    st.column_config.TextColumn("Customer ID"),
            "customer_name":  st.column_config.TextColumn("Name"),
            "amount":         st.column_config.TextColumn("Amount"),
            "failure_reason": st.column_config.TextColumn("Failure Reason"),
            "customer_tier":  st.column_config.TextColumn("Tier"),
            "action_taken":   st.column_config.TextColumn("Action"),
            "variant":        st.column_config.TextColumn("Variant"),
            "outcome":        st.column_config.TextColumn("Outcome"),
            "reasoning":      st.column_config.TextColumn("Reasoning", width="large"),
        },
    )
    st.caption(f"Showing {len(display_df)} of {len(df)} records")

    csv_bytes = display_df.to_csv(index=False).encode()
    st.download_button("⬇️ Download filtered CSV", csv_bytes, "filtered_audit.csv", "text/csv")


# ─────────────────────────────────────────────────────────────────────────────
#  TAB 3: Exceptions
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    exceptions_list = metrics.get("exceptions", [])
    st.markdown(f"""
    <div class="section-title">⚠️ Unresolved Exceptions
      <span class="exception-badge">{len(exceptions_list)} cases</span>
    </div>
    <div class="section-sub">Cases the agent intentionally skipped — with documented reasoning</div>
    """, unsafe_allow_html=True)

    ACTION_LABELS = {
        "skip_non_retryable": ("Already Resolved", "🔵", "pill-blue"),
        "skip_invalid_data":  ("Invalid Data",      "🔴", "pill-red"),
        "skip_cost_floor":    ("Cost Floor",         "🟡", "pill-amber"),
        "skip_max_attempts":  ("Max Attempts",       "🔴", "pill-red"),
        "skip_guardrail":     ("Guardrail Block",    "🟡", "pill-amber"),
    }

    if exceptions_list:
        for ex in exceptions_list:
            action_key = ex.get("action", "")
            label, icon, pill_class = ACTION_LABELS.get(action_key, ("Skipped", "⚪", "pill-amber"))
            st.markdown(f"""
            <div class="exception-card" style="background:#0f1623;border:1px solid #1e293b;border-left:4px solid #f59e0b;
                        border-radius:14px;padding:18px 22px;margin-bottom:12px;">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div>
                  <span style="font-weight:700;font-size:0.97rem;color:#f1f5f9;">{ex.get('customer_name','')}</span>
                  <span style="color:#475569;font-size:0.78rem;margin-left:9px;font-weight:500;">{ex.get('customer_id','')}</span>
                  <span class="pill {pill_class}" style="margin-left:9px;">{icon} {label}</span>
                </div>
                <div style="color:#00d4aa;font-weight:800;font-size:1.05rem;letter-spacing:-0.01em;">&#8377;{float(ex.get('amount',0)):,.2f}</div>
              </div>
              <div style="color:#64748b;font-size:0.8rem;margin-top:10px;line-height:1.5;">
                <strong style="color:#94a3b8;font-weight:600;">Failure:</strong>&nbsp;
                {ex.get('reason','').replace('_',' ').title()}
              </div>
              <div style="color:#64748b;font-size:0.8rem;margin-top:4px;line-height:1.5;">
                <strong style="color:#94a3b8;font-weight:600;">Reason skipped:</strong>&nbsp;
                {ex.get('explanation','')}
              </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("No exceptions — all cases processed successfully!")

# ─────────────────────────────────────────────────────────────────────────────
#  TAB 4: 3D Visualization (Three.js)
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    st.markdown('<div class="section-title">🌐 3D Risk vs Recovery Visualization</div><div class="section-sub">Interactive Three.js scene — drag to orbit, scroll to zoom</div>', unsafe_allow_html=True)

    # Compute per-reason data for 3D
    reason_3d = []
    rs = metrics.get("reason_stats", {})
    for r, s in rs.items():
        reason_3d.append({
            "reason":    r.replace("_", " ").title(),
            "at_risk":   s.get("amount_at_risk", 0),
            "recovered": s.get("amount_recovered", 0),
        })
    # Add totals as first entry
    reason_3d.insert(0, {
        "reason": "TOTAL",
        "at_risk":   total_at_risk,
        "recovered": total_recovered,
    })

    max_val = max((x["at_risk"] for x in reason_3d), default=1)
    bars_json = json.dumps(reason_3d)

    THREE_JS_HTML = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:#0a0e1a; overflow:hidden; font-family:Inter,sans-serif; }}
  canvas {{ display:block; }}
  #tooltip {{
    position:absolute; background:rgba(17,24,39,0.95);
    border:1px solid #1e293b; border-radius:8px;
    padding:10px 14px; color:#f1f5f9; font-size:12px;
    pointer-events:none; display:none;
    box-shadow: 0 8px 24px rgba(0,0,0,0.4);
  }}
  #legend {{
    position:absolute; top:16px; right:16px;
    background:rgba(17,24,39,0.9); border:1px solid #1e293b;
    border-radius:10px; padding:14px; font-size:11px; color:#94a3b8;
  }}
  .leg-item {{ display:flex; align-items:center; gap:8px; margin-bottom:6px; }}
  .leg-dot   {{ width:12px; height:12px; border-radius:3px; flex-shrink:0; }}
  #info {{
    position:absolute; bottom:12px; left:50%; transform:translateX(-50%);
    color:#475569; font-size:11px; letter-spacing:.04em;
  }}
</style>
</head>
<body>
<div id="tooltip"></div>
<div id="legend">
  <div style="font-weight:700;color:#f1f5f9;margin-bottom:10px;">Legend</div>
  <div class="leg-item"><div class="leg-dot" style="background:#ff4d6d;"></div> At Risk</div>
  <div class="leg-item"><div class="leg-dot" style="background:#00d4aa;"></div> Recovered</div>
</div>
<div id="info">🖱 Drag to orbit · Scroll to zoom · Hover bars for details</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r134/three.min.js"></script>
<script>
const DATA    = {bars_json};
const MAX_VAL = {max_val};
const MAX_H   = 4.5;
const BAR_W   = 0.55;
const GAP     = 0.2;
const PAIR_W  = BAR_W * 2 + GAP;
const SPACING = PAIR_W + 0.6;

// Scene
const scene    = new THREE.Scene();
scene.background= new THREE.Color(0x0a0e1a);
scene.fog       = new THREE.FogExp2(0x0a0e1a, 0.04);

const W = window.innerWidth, H = window.innerHeight;
const camera   = new THREE.PerspectiveCamera(50, W/H, 0.1, 200);
camera.position.set(0, 7, 18);
camera.lookAt(0, 0, 0);

const renderer = new THREE.WebGLRenderer({{ antialias:true }});
renderer.setSize(W, H);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
document.body.appendChild(renderer.domElement);

// Lighting
const ambient = new THREE.AmbientLight(0xffffff, 0.35);
scene.add(ambient);
const dirLight = new THREE.DirectionalLight(0xffffff, 0.9);
dirLight.position.set(10, 18, 8);
dirLight.castShadow = true;
scene.add(dirLight);
const fill = new THREE.PointLight(0x4f8ef7, 0.6, 40);
fill.position.set(-8, 6, -4);
scene.add(fill);
const rimLight = new THREE.PointLight(0x00d4aa, 0.5, 30);
rimLight.position.set(8, 3, 6);
scene.add(rimLight);

// Grid floor
const gridHelper = new THREE.GridHelper(32, 32, 0x1e293b, 0x1e293b);
scene.add(gridHelper);

// Materials
const matRisk = new THREE.MeshPhongMaterial({{
  color:0xff4d6d, emissive:0x3d0010, shininess:60,
  transparent:true, opacity:0.92
}});
const matRec  = new THREE.MeshPhongMaterial({{
  color:0x00d4aa, emissive:0x003326, shininess:80,
  transparent:true, opacity:0.92
}});
const matBase = new THREE.MeshPhongMaterial({{ color:0x1e293b, shininess:20 }});

// Build bars
const barMeshes = [];
const totalWidth = DATA.length * SPACING;
const startX     = -(totalWidth - SPACING) / 2;

DATA.forEach((d, i) => {{
  const x = startX + i * SPACING;

  const hRisk = (d.at_risk / MAX_VAL) * MAX_H || 0.05;
  const hRec  = (d.recovered / MAX_VAL) * MAX_H || 0.05;

  // At-risk bar
  const geoR = new THREE.BoxGeometry(BAR_W, 1, BAR_W);
  const meshR = new THREE.Mesh(geoR, matRisk.clone());
  meshR.scale.y = 0.001;
  meshR.position.set(x - (BAR_W + GAP) / 2, 0, 0);
  meshR.castShadow = meshR.receiveShadow = true;
  meshR.userData = {{ label:d.reason, type:'At Risk',   val:d.at_risk,   targetH:hRisk }};
  scene.add(meshR);
  barMeshes.push(meshR);

  // Recovered bar
  const geoG = new THREE.BoxGeometry(BAR_W, 1, BAR_W);
  const meshG = new THREE.Mesh(geoG, matRec.clone());
  meshG.scale.y = 0.001;
  meshG.position.set(x + (BAR_W + GAP) / 2, 0, 0);
  meshG.castShadow = meshG.receiveShadow = true;
  meshG.userData = {{ label:d.reason, type:'Recovered', val:d.recovered, targetH:hRec }};
  scene.add(meshG);
  barMeshes.push(meshG);

  // Base plate
  const geoB  = new THREE.BoxGeometry(PAIR_W + 0.1, 0.08, BAR_W + 0.1);
  const meshB = new THREE.Mesh(geoB, matBase);
  meshB.position.set(x, -0.04, 0);
  scene.add(meshB);

  // Text label (canvas texture)
  const canvas2d = document.createElement('canvas');
  canvas2d.width=256; canvas2d.height=64;
  const ctx = canvas2d.getContext('2d');
  ctx.fillStyle='rgba(0,0,0,0)';
  ctx.fillRect(0,0,256,64);
  ctx.fillStyle='#94a3b8';
  ctx.font='bold 18px Inter,sans-serif';
  ctx.textAlign='center';
  const short = d.reason.length > 12 ? d.reason.slice(0,12)+'…' : d.reason;
  ctx.fillText(short, 128, 36);
  const tex  = new THREE.CanvasTexture(canvas2d);
  const spGeo = new THREE.PlaneGeometry(1.4, 0.35);
  const spMat = new THREE.MeshBasicMaterial({{ map:tex, transparent:true, depthWrite:false }});
  const sp    = new THREE.Mesh(spGeo, spMat);
  sp.position.set(x, -0.35, BAR_W/2 + 0.1);
  scene.add(sp);
}});

// Orbit controls (manual)
let isDown=false, lastX=0, lastY=0;
let theta=0.2, phi=0.45, radius=18;

renderer.domElement.addEventListener('mousedown', e=>{{ isDown=true; lastX=e.clientX; lastY=e.clientY; }});
renderer.domElement.addEventListener('mouseup',   ()=>isDown=false);
renderer.domElement.addEventListener('mousemove', e=>{{
  if (!isDown) return;
  const dx=(e.clientX-lastX)*0.008, dy=(e.clientY-lastY)*0.008;
  theta -= dx; phi = Math.max(0.1, Math.min(1.4, phi+dy));
  lastX=e.clientX; lastY=e.clientY;
}});
renderer.domElement.addEventListener('wheel', e=>{{
  radius = Math.max(6, Math.min(35, radius + e.deltaY*0.04));
}});

// Raycaster for hover tooltip
const raycaster = new THREE.Raycaster();
const mouse     = new THREE.Vector2();
const tooltip   = document.getElementById('tooltip');

renderer.domElement.addEventListener('mousemove', e=>{{
  mouse.x = (e.clientX/W)*2-1;
  mouse.y = -(e.clientY/H)*2+1;
  raycaster.setFromCamera(mouse, camera);
  const hits = raycaster.intersectObjects(barMeshes);
  if (hits.length) {{
    const d = hits[0].object.userData;
    tooltip.style.display = 'block';
    tooltip.style.left    = (e.clientX+14)+'px';
    tooltip.style.top     = (e.clientY-10)+'px';
    tooltip.innerHTML = `<strong>${{d.label}}</strong><br>
      <span style="color:#94a3b8">${{d.type}}:</span>
      <span style="color:${{d.type==='At Risk'?'#ff4d6d':'#00d4aa'}};font-weight:700;">
        ₹${{d.val.toLocaleString('en-IN',{{minimumFractionDigits:0}})}}</span>`;
  }} else {{
    tooltip.style.display='none';
  }}
}});

// Particle field (stars)
const pGeo = new THREE.BufferGeometry();
const pCount = 300;
const pPos  = new Float32Array(pCount*3);
for(let i=0;i<pCount*3;i++) pPos[i]=(Math.random()-0.5)*60;
pGeo.setAttribute('position', new THREE.BufferAttribute(pPos,3));
const pMat  = new THREE.PointsMaterial({{color:0x334155,size:0.15}});
scene.add(new THREE.Points(pGeo, pMat));

// Animation
let t = 0;
const clock = new THREE.Clock();
function animate(){{
  requestAnimationFrame(animate);
  const dt = clock.getDelta();
  t += dt;

  // Grow bars
  barMeshes.forEach(m=>{{
    const target = m.userData.targetH || 0.05;
    if(m.scale.y < target) {{
      m.scale.y = Math.min(target, m.scale.y + dt * 2.5);
      m.position.y = m.scale.y / 2;
    }}
  }});

  // Slow auto-orbit
  if(!isDown) theta += dt * 0.08;

  camera.position.x = radius * Math.sin(theta) * Math.cos(phi);
  camera.position.y = radius * Math.sin(phi);
  camera.position.z = radius * Math.cos(theta) * Math.cos(phi);
  camera.lookAt(0, MAX_H/2, 0);

  renderer.render(scene, camera);
}}
animate();

window.addEventListener('resize',()=>{{
  camera.aspect=window.innerWidth/window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth,window.innerHeight);
}});
</script>
</body>
</html>
"""

    st_html(THREE_JS_HTML, height=560, scrolling=False)

    # Stats below 3D view
    st.markdown("---")
    cols = st.columns(len(reason_3d))
    for i, r in enumerate(reason_3d):
        with cols[i]:
            rate = (r["recovered"] / r["at_risk"] * 100) if r["at_risk"] > 0 else 0
            st.metric(
                label=r["reason"],
                value=f"₹{r['recovered']:,.0f}",
                delta=f"{rate:.1f}% of ₹{r['at_risk']:,.0f}",
            )

# ══════════════════════════════════════════════════════════════════════════════
#  FOOTER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("""
<div style="text-align:center;color:#334155;font-size:0.75rem;padding:16px 0 8px;">
  <strong style="color:#475569;">AI Revenue Recovery Agent</strong> ·
  Built for Hackathon · Powered by Python, Streamlit &amp; Plotly ·
  All external actions are <strong>mocked/simulated</strong> — no real API keys required
</div>
""", unsafe_allow_html=True)
