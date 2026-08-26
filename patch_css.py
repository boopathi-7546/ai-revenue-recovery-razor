"""
Patch script: replaces the DARK_CSS block in app.py with the polished version.
Run: python patch_css.py
"""
import re

APPPY = "app.py"

NEW_CSS = r'''DARK_CSS = """
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
'''

with open(APPPY, "r", encoding="utf-8") as f:
    content = f.read()

# Match from DARK_CSS = """ to the closing """  (the first triple-quote after it)
pattern = r'DARK_CSS = """.*?"""'
new_content = re.sub(pattern, NEW_CSS.strip(), content, count=1, flags=re.DOTALL)

if new_content == content:
    print("ERROR: pattern not found — no substitution made")
else:
    with open(APPPY, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("SUCCESS: DARK_CSS block replaced")
