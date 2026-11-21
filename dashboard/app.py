from pathlib import Path
import re

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ============================================================
# CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="GTM Intelligence | AI Education Market",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "processed"
REPORT_DIR = ROOT / "reports"

DATA_FILES = {
    "competitor_breadth": DATA_DIR / "competitor_skill_breadth.csv",
    "skill_coverage": DATA_DIR / "skill_market_coverage.csv",
    "category_coverage": DATA_DIR / "category_market_coverage.csv",
    "competitor_matrix": DATA_DIR / "competitor_skill_matrix.csv",
    "potential_gaps": DATA_DIR / "potential_skill_gaps.csv",
}
REPORT_FILE = REPORT_DIR / "gtm_recommendations_v3.md"

# Colour tokens (all tested for contrast on white and on the page canvas)
INK = "#162338"        # primary text
INK_SOFT = "#40536f"   # secondary text
MUTED = "#64748b"      # captions
GRID = "#e3e9f2"
BLUE = "#3b63c9"
TEAL = "#0b8f84"
VIOLET = "#7653c4"
AMBER = "#d9822b"
ROSE = "#d04e72"
CYAN = "#2e8798"

COMPETITOR_COLORS = {
    "upGrad": BLUE,
    "Great Learning": TEAL,
    "Simplilearn": AMBER,
    "Scaler": VIOLET,
    "Coursera": ROSE,
    "Emeritus": CYAN,
}
PALETTE = [BLUE, TEAL, AMBER, VIOLET, ROSE, CYAN, "#5b6b8a", "#9a7b2f", "#4c9a5f", "#a0527c"]
FONT_FAMILY = "DM Sans, Segoe UI, Arial, sans-serif"

PLOT_CONFIG = {"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d"]}


# ============================================================
# VISUAL DESIGN (forces a consistent light theme everywhere)
# ============================================================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@600;700;800&display=swap');

    :root {
        color-scheme: light;
        --ink: #162338;
        --ink-soft: #40536f;
        --muted: #64748b;
        --line: #e3e9f2;
        --blue: #3b63c9;
        --teal: #0b8f84;
        --canvas: #f3f6fb;
    }
    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        font-family: 'DM Sans', 'Segoe UI', Arial, sans-serif;
        background: var(--canvas) !important;
        color: var(--ink);
    }
    .block-container { max-width: 1560px; padding-top: 1.2rem; padding-bottom: 3rem; }

    /* Header kept (so the sidebar toggle still works) but made invisible */
    header[data-testid="stHeader"] { background: transparent !important; height: 2.4rem; }
    [data-testid="stDecoration"] { display: none !important; }
    footer { visibility: hidden; }

    /* ---------- Main-area text ---------- */
    .stApp h1, .stApp h2, .stApp h3, .stApp h4 { font-family: 'Manrope', sans-serif; color: var(--ink); }
    [data-testid="stMain"] p, [data-testid="stMain"] li, [data-testid="stMain"] label,
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] { color: var(--ink); }
    [data-testid="stMain"] [data-testid="stCaptionContainer"],
    [data-testid="stMain"] [data-testid="stCaptionContainer"] p { color: var(--muted) !important; }
    [data-testid="stMain"] code { background: #eaf0fa; color: #26407a; padding: 2px 6px; border-radius: 6px; }
    [data-testid="stMain"] hr { border-color: var(--line); }

    /* ---------- Widgets ---------- */
    [data-testid="stMain"] [data-testid="stWidgetLabel"] p {
        color: var(--ink-soft) !important; font-weight: 700; font-size: 12.5px;
    }
    [data-testid="stMain"] div[data-baseweb="select"] > div,
    [data-testid="stMain"] div[data-baseweb="select"] > div > div,
    [data-testid="stMain"] div[data-baseweb="input"],
    [data-testid="stMain"] div[data-baseweb="input"] > div,
    [data-testid="stMain"] div[data-baseweb="base-input"] {
        background: #ffffff !important; background-color: #ffffff !important;
        border-color: #d3dcea !important; color: var(--ink) !important;
    }
    [data-testid="stMain"] div[data-baseweb="select"] > div,
    [data-testid="stMain"] div[data-baseweb="input"] { border-radius: 10px !important; }
    [data-testid="stMain"] div[data-baseweb="select"] span,
    [data-testid="stMain"] div[data-baseweb="select"] div,
    [data-testid="stMain"] div[data-baseweb="input"] input,
    [data-testid="stMain"] div[data-baseweb="base-input"] input {
        color: var(--ink) !important; -webkit-text-fill-color: var(--ink) !important;
    }
    [data-testid="stMain"] div[data-baseweb="select"] svg { fill: var(--ink-soft) !important; color: var(--ink-soft) !important; }
    div[data-baseweb="input"] input::placeholder { color: #8a97ab !important; -webkit-text-fill-color: #8a97ab !important; }
    div[data-baseweb="popover"] ul, div[data-baseweb="menu"] { background: #ffffff !important; }
    div[data-baseweb="popover"] li, div[data-baseweb="popover"] li * { color: var(--ink) !important; }
    div[data-baseweb="popover"] li:hover { background: #eaf1ff !important; }
    span[data-baseweb="tag"] { background: #e4edff !important; }
    span[data-baseweb="tag"] span { color: #244f9e !important; }
    [data-testid="stSlider"] [data-testid="stTickBarMin"], [data-testid="stSlider"] [data-testid="stTickBarMax"],
    [data-testid="stSlider"] [data-testid="stThumbValue"] { color: var(--ink-soft) !important; }

    /* ---------- Navigation pills (horizontal radio) ---------- */
    div[role="radiogroup"] { gap: 8px; flex-wrap: wrap; }
    div[role="radiogroup"] label {
        background: #ffffff; border: 1px solid #d6dfec; border-radius: 999px;
        padding: 8px 18px; margin: 0; cursor: pointer;
        transition: all .15s ease;
    }
    /* Hide the radio circle so only the pill label shows */
    div[role="radiogroup"] label > div:not(:has([data-testid="stMarkdownContainer"])),
    div[role="radiogroup"] label > span { display: none !important; }
    div[role="radiogroup"] label p { color: var(--ink-soft) !important; font-size: 13px !important; font-weight: 700 !important; }
    div[role="radiogroup"] label:hover { border-color: var(--blue); background: #f4f8ff; }
    div[role="radiogroup"] label:has(input:checked) {
        background: linear-gradient(120deg, #3b63c9, #0b8f84); border-color: transparent;
        box-shadow: 0 6px 16px rgba(59, 99, 201, .28);
    }
    div[role="radiogroup"] label:has(input:checked) p { color: #ffffff !important; }

    /* ---------- Sidebar ---------- */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #111d31 0%, #162842 100%);
        border-right: 1px solid #263650;
    }
    /* Only fix the width while the sidebar is open, so a collapsed sidebar leaves no gap */
    [data-testid="stSidebar"][aria-expanded="true"] { min-width: 250px !important; max-width: 250px !important; }
    [data-testid="stSidebar"] * { color: #eaf0fa; }
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p { color: #a9bad2 !important; font-size: 12px; }
    [data-testid="stSidebar"] hr { border-color: #2b3b55; }
    [data-testid="stSidebar"] .stButton button {
        background: #213653; border: 1px solid #36507a; color: #ffffff; border-radius: 10px;
    }
    [data-testid="stSidebar"] .stButton button:hover { background: #2c4871; border-color: #5a82c4; }
    [data-testid="stSidebar"] .stButton button p { color: #ffffff !important; }
    .side-label { font-size: 10px; font-weight: 800; letter-spacing: 1.6px; color: #8fa3c0 !important; margin: 4px 0 6px; }

    .brand { padding: 6px 2px 18px; border-bottom: 1px solid #2b3b55; margin-bottom: 18px; }
    .brand-mark {
        display: inline-flex; align-items: center; justify-content: center;
        width: 40px; height: 40px; border-radius: 12px;
        background: linear-gradient(135deg, #3b63c9, #0b8f84);
        font-size: 20px; margin-right: 10px; vertical-align: middle;
    }
    .brand-name { font-family: 'Manrope', sans-serif; font-size: 17px; font-weight: 800; color: #ffffff !important; vertical-align: middle; }
    .brand-sub { color: #8fa3c0 !important; font-size: 10px; letter-spacing: 1.6px; margin: 10px 0 0 2px; }

    /* ---------- Hero ---------- */
    .hero {
        background: linear-gradient(115deg, #14243b 0%, #234a78 58%, #11837f 100%);
        padding: 28px 32px; border-radius: 20px;
        box-shadow: 0 14px 34px rgba(23, 49, 83, .16);
        margin-bottom: 14px; position: relative; overflow: hidden;
    }
    .hero:after {
        content: ""; position: absolute; right: -60px; top: -80px; width: 260px; height: 260px; border-radius: 50%;
        background: radial-gradient(circle, rgba(255,255,255,.14), rgba(255,255,255,0) 70%);
    }
    .hero-kicker { color: #bcd9f2 !important; font-size: 10.5px; font-weight: 800; letter-spacing: 2px; text-transform: uppercase; }
    .hero-title { color: #ffffff !important; font-family: 'Manrope', sans-serif; font-size: 30px; font-weight: 800; line-height: 1.2; margin-top: 8px; }
    .hero-copy { color: #dbe8f6 !important; font-size: 13.5px; margin-top: 9px; max-width: 860px; line-height: 1.55; }

    .caution {
        background: #fff8e8; border: 1px solid #f0dfb7; border-left: 4px solid #d9a21f; border-radius: 12px;
        padding: 11px 15px; color: #6b5220 !important; font-size: 12px; margin: 0 0 18px; line-height: 1.5;
    }
    .caution b { color: #5a4210; }

    .nav-label { font-size: 10px; font-weight: 800; letter-spacing: 1.6px; color: var(--muted); margin: 0 0 8px; }
    .page-heading { font-family: 'Manrope', sans-serif; font-size: 24px; font-weight: 800; color: var(--ink); margin: 4px 0 2px; }
    .page-description { color: var(--muted); font-size: 13.5px; margin-bottom: 18px; }

    /* ---------- Cards ---------- */
    .metric-card {
        background: #ffffff; border: 1px solid var(--line); border-top: 4px solid var(--accent, #3b63c9);
        border-radius: 15px; padding: 17px 19px; min-height: 120px;
        box-shadow: 0 6px 18px rgba(25, 48, 80, .05);
    }
    .metric-label { color: var(--muted); font-size: 10.5px; text-transform: uppercase; letter-spacing: 1.1px; font-weight: 800; }
    .metric-value { color: var(--ink); font-family: 'Manrope', sans-serif; font-size: 31px; font-weight: 800; margin-top: 8px; line-height: 1.1; }
    .metric-foot { color: #7b889b; font-size: 11.5px; margin-top: 8px; }

    [data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"] .section-title),
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: #ffffff; border-color: var(--line) !important; border-radius: 16px;
    }
    .section-title { font-family: 'Manrope', sans-serif; color: var(--ink); font-size: 16px; font-weight: 800; margin: 2px 0 3px; }
    .section-note { color: var(--muted); font-size: 12px; margin-bottom: 8px; }

    .callout {
        background: #eaf2ff; border-left: 4px solid #3b63c9; border-radius: 10px;
        padding: 12px 16px; color: #29406a !important; font-size: 12.5px; margin: 10px 0 16px; line-height: 1.55;
    }
    .callout b { color: #1d3566; }

    div[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 12px; overflow: hidden; background: #ffffff; }
    .stButton button, .stDownloadButton button { border-radius: 10px; font-weight: 700; }
    .stDownloadButton button { background: #ffffff; color: #244f9e; border: 1px solid #bcd0f3; }
    .stDownloadButton button:hover { background: #eaf2ff; border-color: #3b63c9; color: #1d3f85; }
    .stDownloadButton button p { color: inherit !important; }

    [data-testid="stExpander"] { background: #ffffff; border: 1px solid var(--line); border-radius: 12px; }
    [data-testid="stExpander"] summary p { color: var(--ink) !important; font-weight: 700; }

    /* ---------- Strategy report typography ---------- */
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] h3 { color: var(--ink); font-family: 'Manrope', sans-serif; }
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] h2 { border-bottom: 2px solid #e8eef8; padding-bottom: 6px; margin-top: 1.4rem; }
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] table { border-collapse: collapse; width: 100%; font-size: 13px; }
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] th { background: #eef3fb; color: var(--ink); }
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] th,
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] td { border: 1px solid var(--line); padding: 8px 10px; color: var(--ink); }
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] blockquote { border-left: 4px solid #3b63c9; background: #f3f7ff; color: var(--ink-soft); }

       /* ============================================================
       DARK-THEME PROOFING (buttons, chat, input bar)
       ============================================================ */

    [data-stale="true"] { opacity: 1 !important; }

    /* ---------- All buttons (Clear chat, example prompts, downloads) ---------- */
    .stApp .stButton > button,
    .stApp .stDownloadButton > button,
    .stApp button[data-testid^="stBaseButton"] {
        background: #ffffff !important;
        background-color: #ffffff !important;
        background-image: none !important;
        border: 1px solid #bcd0f3 !important;
        border-radius: 10px !important;
        box-shadow: none !important;
    }
    .stApp .stButton > button *,
    .stApp .stDownloadButton > button *,
    .stApp button[data-testid^="stBaseButton"] * {
        color: #244f9e !important;
        -webkit-text-fill-color: #244f9e !important;
        opacity: 1 !important;
        font-weight: 700;
    }
    .stApp .stButton > button:hover,
    .stApp .stDownloadButton > button:hover,
    .stApp button[data-testid^="stBaseButton"]:hover {
        background: #eaf2ff !important; border-color: #3b63c9 !important;
    }

    /* Sidebar buttons stay dark (higher specificity than the rules above) */
    .stApp [data-testid="stSidebar"] .stButton > button {
        background: #213653 !important; border: 1px solid #36507a !important;
    }
    .stApp [data-testid="stSidebar"] .stButton > button * {
        color: #ffffff !important; -webkit-text-fill-color: #ffffff !important;
    }

    /* ---------- Chat bubbles + answers ---------- */
    .stApp [data-testid="stChatMessage"] {
        background: #ffffff !important; border: 1px solid #e3e9f2;
        border-radius: 14px; padding: 14px 18px; margin-bottom: 10px;
    }
    .stApp [data-testid="stChatMessage"],
    .stApp [data-testid="stChatMessage"] *,
    .stApp [data-testid="stChatMessageContent"] *,
    .stApp [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] *,
    .stApp [data-testid="stChatMessage"] li::marker {
        color: #162338 !important;
        -webkit-text-fill-color: #162338 !important;
        opacity: 1 !important;
    }
    .stApp [data-testid="stChatMessage"] code { background: #eaf0fa !important; color: #26407a !important; }

    /* ---------- Bottom bar + chat input ---------- */
    [data-testid="stBottom"],
    [data-testid="stBottom"] *,
    [data-testid="stBottomBlockContainer"] { background-color: transparent !important; }
    [data-testid="stBottom"] { background: var(--canvas) !important; }
    [data-testid="stChatInput"],
    [data-testid="stChatInput"] > div,
    [data-testid="stChatInput"] div[data-baseweb] {
        background: #ffffff !important; background-color: #ffffff !important;
        border-color: #d3dcea !important; border-radius: 12px !important;
    }
    [data-testid="stChatInput"] textarea {
        background: #ffffff !important; color: #162338 !important;
        -webkit-text-fill-color: #162338 !important;
    }
    [data-testid="stChatInput"] textarea::placeholder {
        color: #8a97ab !important; -webkit-text-fill-color: #8a97ab !important;
    }
    [data-testid="stChatInput"] button {
        background: #3b63c9 !important; background-color: #3b63c9 !important;
        border: none !important; border-radius: 8px !important;
    }
    [data-testid="stChatInput"] button svg { fill: #ffffff !important; color: #ffffff !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# REUSABLE HELPERS
# ============================================================
def _wide(fn, *args, **kwargs):
    """Call a Streamlit widget at full width, across old and new Streamlit versions."""
    try:
        return fn(*args, width="stretch", **kwargs)
    except Exception:
        return fn(*args, use_container_width=True, **kwargs)


@st.cache_data(show_spinner=False)
def load_csv(path_string: str) -> pd.DataFrame:
    path = Path(path_string)
    if not path.exists():
        return pd.DataFrame()
    frame = pd.read_csv(path)
    frame = frame.loc[:, ~frame.columns.astype(str).str.startswith("Unnamed:")]
    return frame


def clean_numeric(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    frame = frame.copy()
    for col in columns:
        if col in frame.columns:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
    return frame


def fmt(value) -> str:
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return "—"


def pct(value, digits: int = 1) -> str:
    try:
        if pd.isna(value):
            return "—"
        return f"{float(value):.{digits}f}%"
    except (ValueError, TypeError):
        return "—"


def metric_card(label: str, value: str, foot: str, accent: str):
    st.markdown(
        f"""
        <div class="metric-card" style="--accent:{accent}">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-foot">{foot}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_title(title: str, note: str | None = None):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if note:
        st.markdown(f'<div class="section-note">{note}</div>', unsafe_allow_html=True)


def page_intro(title: str, description: str):
    st.markdown(f'<div class="page-heading">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-description">{description}</div>', unsafe_allow_html=True)


def chart_style(fig, height: int = 350):
    fig.update_layout(
        template="plotly_white",
        height=height,
        autosize=True,
        margin=dict(l=16, r=28, t=36, b=40),
        font=dict(family=FONT_FAMILY, color=INK, size=13),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        legend_title_text="",
        legend=dict(font=dict(color=INK, size=12), bgcolor="rgba(255,255,255,0.95)"),
        hoverlabel=dict(bgcolor=INK, font=dict(color="#ffffff", size=13, family=FONT_FAMILY)),
        uniformtext=dict(minsize=11, mode="show"),
    )
    fig.update_xaxes(
        showgrid=True, gridcolor=GRID, zeroline=False, showline=False,
        tickfont=dict(color=INK_SOFT, size=12), title_font=dict(color=INK, size=13), automargin=True,
    )
    fig.update_yaxes(
        showgrid=False, zeroline=False, showline=False,
        tickfont=dict(color=INK, size=12), title_font=dict(color=INK, size=13), automargin=True,
    )
    return fig


def plot(fig, height: int = 350):
    fig = chart_style(fig, height)
    try:
        st.plotly_chart(fig, width="stretch", config=PLOT_CONFIG)
    except Exception:
        st.plotly_chart(fig, use_container_width=True, config=PLOT_CONFIG)


def hbar(frame, x, y, text=None, color=None, color_map=None, height=360, x_title="", pad=1.18, **kwargs):
    """Horizontal bar chart with always-visible value labels."""
    fig = px.bar(
        frame, x=x, y=y, orientation="h", text=text or x,
        color=color, color_discrete_map=color_map, **kwargs,
    )
    max_val = pd.to_numeric(frame[x], errors="coerce").max()
    fig.update_traces(
        textposition="outside", cliponaxis=False,
        textfont=dict(color=INK, size=12, family=FONT_FAMILY),
        marker_line_width=0,
    )
    fig.update_layout(xaxis_title=x_title, yaxis_title="", bargap=0.32)
    if pd.notna(max_val) and max_val > 0:
        fig.update_xaxes(range=[0, max_val * pad])
    return fig


def table(frame: pd.DataFrame, height: int = 420):
    config = {}
    if "coverage_percentage" in frame.columns:
        config["coverage_percentage"] = st.column_config.ProgressColumn(
            "Coverage %", format="%.1f%%", min_value=0, max_value=100
        )
    for col, label in [("programme_count", "Programmes"), ("competitor_count", "Competitors"),
                       ("unique_skills", "Unique skills"), ("total_programmes", "Programmes")]:
        if col in frame.columns:
            config[col] = st.column_config.NumberColumn(label, format="%d")
    try:
        st.dataframe(frame, width="stretch", hide_index=True, height=height, column_config=config)
    except Exception:
        st.dataframe(frame, use_container_width=True, hide_index=True, height=height, column_config=config)


def show_data_table(frame: pd.DataFrame, height: int = 420):
    table(frame, height)


def render_markdown_report(report_text: str):
    cleaned = re.sub(r"^\s*#\s+.*?\n", "", report_text, count=1)
    st.markdown(cleaned)


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown(
        """
        <div class="brand">
            <span class="brand-mark">🎯</span>
            <span class="brand-name">GTM Intelligence</span>
            <div class="brand-sub">AI / ML EDUCATION MARKET</div>
        </div>
        <div class="side-label">DATA WORKSPACE</div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Source: collected competitor programme sample")
    st.caption("Analytics: Python + Pandas")
    st.caption("AI engine: Ollama / Llama 3.2")
    st.write("")
    if _wide(st.button, "↻  Refresh data"):
        st.cache_data.clear()
        st.rerun()
    st.markdown("---")
    st.caption("Portfolio project · Competitive intelligence")

pages = [
    "Overview", "Competitors", "Skill Explorer", "Skill Matrix",
    "Opportunity Lab", "GTM Strategy", "GTM Copilot", "Data & Methodology",
]


# ============================================================
# LOAD + VALIDATE DATA
# ============================================================
missing_files = [p for p in DATA_FILES.values() if not p.exists()]
if missing_files:
    st.error("The dashboard cannot find these required processed data files:")
    for path in missing_files:
        st.code(str(path.relative_to(ROOT)))
    st.info("Run the data-processing and analytics scripts, then refresh the dashboard.")
    st.stop()

data = {key: load_csv(str(path)) for key, path in DATA_FILES.items()}
breadth = clean_numeric(data["competitor_breadth"], ["total_programmes", "unique_skills", "skill_categories"])
skills = clean_numeric(data["skill_coverage"], ["programme_count", "competitor_count", "coverage_percentage"])
categories = clean_numeric(data["category_coverage"], ["unique_skills", "programme_count", "competitor_count", "coverage_percentage"])
matrix = data["competitor_matrix"].copy()
gaps = clean_numeric(data["potential_gaps"], ["programme_count", "competitor_count", "coverage_percentage"])

required_columns = {
    "competitor_breadth": (breadth, ["competitor_name", "total_programmes", "unique_skills", "skill_categories"]),
    "skill_market_coverage": (skills, ["canonical_skill", "skill_category", "programme_count", "competitor_count", "coverage_percentage"]),
    "category_market_coverage": (categories, ["skill_category", "unique_skills", "programme_count", "competitor_count", "coverage_percentage"]),
    "competitor_skill_matrix": (matrix, ["canonical_skill"]),
    "potential_skill_gaps": (gaps, ["canonical_skill", "skill_category", "competitor_count"]),
}
for dataset_name, (frame, columns) in required_columns.items():
    missing_columns = [col for col in columns if col not in frame.columns]
    if missing_columns:
        st.error(f"{dataset_name} is missing columns: {', '.join(missing_columns)}")
        st.stop()

competitor_columns = [col for col in matrix.columns if col != "canonical_skill"]
for col in competitor_columns:
    matrix[col] = pd.to_numeric(matrix[col], errors="coerce").fillna(0)


# ============================================================
# GLOBAL HEADER
# ============================================================
st.markdown(
    """
    <div class="hero">
        <div class="hero-kicker">Competitive intelligence workspace</div>
        <div class="hero-title">AI / ML Education Market</div>
        <div class="hero-copy">
            Benchmark sampled competitor curricula, explore skill coverage and identify
            programme themes worth validating before a go-to-market decision.
        </div>
    </div>
    <div class="caution"><b>Sample-based analysis:</b> these results describe only the programmes collected.
    Competitor coverage is not market share and does not prove learner demand, employer demand or teaching quality.</div>
    <div class="nav-label">WORKSPACE NAVIGATION</div>
    """,
    unsafe_allow_html=True,
)

page = st.radio("Choose dashboard section", pages, horizontal=True, label_visibility="collapsed")
st.write("")


# ============================================================
# PAGE 1 — OVERVIEW
# ============================================================
if page == "Overview":
    page_intro("Market overview", "A decision-focused snapshot of the AI/ML education competitor sample.")

    total_competitors = breadth["competitor_name"].nunique()
    total_programmes = breadth["total_programmes"].fillna(0).sum()
    total_skills = skills["canonical_skill"].nunique()
    total_categories = categories["skill_category"].nunique()

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        metric_card("Competitors", fmt(total_competitors), "Providers represented", BLUE)
    with k2:
        metric_card("Programmes", fmt(total_programmes), "Sampled programmes", TEAL)
    with k3:
        metric_card("Canonical skills", fmt(total_skills), "Standardized skills", VIOLET)
    with k4:
        metric_card("Skill categories", fmt(total_categories), "Taxonomy categories", AMBER)

    st.write("")
    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            section_title("Competitor sample size", "Number of programmes collected for each provider.")
            chart_data = breadth.sort_values("total_programmes", ascending=True)
            fig = hbar(chart_data, "total_programmes", "competitor_name", color="competitor_name",
                       color_map=COMPETITOR_COLORS, x_title="Sampled programmes")
            fig.update_layout(showlegend=False)
            plot(fig, 360)
    with right:
        with st.container(border=True):
            section_title("Observed curriculum breadth", "Unique canonical skills found in the collected programmes.")
            chart_data = breadth.sort_values("unique_skills", ascending=True)
            fig = hbar(chart_data, "unique_skills", "competitor_name", color="competitor_name",
                       color_map=COMPETITOR_COLORS, x_title="Unique skills")
            fig.update_layout(showlegend=False)
            plot(fig, 360)

    lower_left, lower_right = st.columns([1.25, 1])
    with lower_left:
        with st.container(border=True):
            section_title("Most represented skills", "Top 10 by competitor count, then programme count.")
            top = skills.sort_values(["competitor_count", "programme_count"], ascending=[False, False]).head(10)
            top = top.sort_values(["competitor_count", "programme_count"], ascending=[True, True])
            fig = hbar(
                top, "competitor_count", "canonical_skill", color="skill_category",
                x_title="Number of competitors", height=470,
                color_discrete_sequence=PALETTE,
                hover_data=["programme_count", "coverage_percentage"],
                labels={"competitor_count": "Competitors", "canonical_skill": "Skill", "skill_category": "Category"},
            )
            fig.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.16, xanchor="left", x=0))
            fig.update_xaxes(dtick=1)
            plot(fig, 480)
    with lower_right:
        with st.container(border=True):
            section_title("Category coverage", "Percentage of sampled competitors represented in each category.")
            cat = categories.sort_values("coverage_percentage", ascending=True).copy()
            cat["label"] = cat["coverage_percentage"].map(lambda v: f"{v:.0f}%" if pd.notna(v) else "")
            fig = px.bar(
                cat, x="coverage_percentage", y="skill_category", orientation="h", text="label",
                color="coverage_percentage", color_continuous_scale=["#e9b872", "#5fb9ab", TEAL],
                range_color=[0, 100],
                hover_data=["unique_skills", "programme_count", "competitor_count"],
                labels={"coverage_percentage": "Coverage (%)", "skill_category": "Category"},
            )
            fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0,
                              textfont=dict(color=INK, size=12, family=FONT_FAMILY))
            fig.update_layout(coloraxis_showscale=False, xaxis_title="Competitor coverage (%)",
                              yaxis_title="", bargap=0.3)
            fig.update_xaxes(range=[0, 118])
            plot(fig, 480)

    with st.expander("View the underlying competitor benchmark"):
        show_data_table(breadth)


# ============================================================
# PAGE 2 — COMPETITOR PROFILES
# ============================================================
elif page == "Competitors":
    page_intro("Competitor profiles", "Compare the providers represented in your sample and inspect each provider's observed curriculum.")

    names = sorted(breadth["competitor_name"].dropna().tolist())
    selected_competitor = st.selectbox("Select a competitor", names)
    selected_row = breadth[breadth["competitor_name"] == selected_competitor].iloc[0]

    st.write("")
    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card("Sampled programmes", fmt(selected_row["total_programmes"]), selected_competitor,
                    COMPETITOR_COLORS.get(selected_competitor, BLUE))
    with c2:
        metric_card("Unique skills", fmt(selected_row["unique_skills"]), "Skills identified in sample", TEAL)
    with c3:
        metric_card("Skill categories", fmt(selected_row["skill_categories"]), "Categories represented", VIOLET)

    st.write("")
    if selected_competitor in matrix.columns:
        observed = matrix.loc[matrix[selected_competitor] > 0, ["canonical_skill"]].copy()
        observed = observed.merge(
            skills[["canonical_skill", "skill_category", "programme_count", "competitor_count", "coverage_percentage"]],
            on="canonical_skill", how="left",
        )
        left, right = st.columns([1.1, 1])
        with left:
            with st.container(border=True):
                section_title(f"{selected_competitor}: observed skills",
                              "Skills marked as present in the competitor-skill matrix.")
                show_data_table(observed.sort_values(["skill_category", "canonical_skill"]), 450)
        with right:
            with st.container(border=True):
                section_title("Category mix", "Share of distinct observed skills in each category.")
                category_mix = (observed["skill_category"].fillna("Unclassified")
                                .value_counts().rename_axis("Category").reset_index(name="Skills"))
                if category_mix.empty:
                    st.info("No observed skills for this competitor.")
                else:
                    fig = px.pie(category_mix, names="Category", values="Skills", hole=0.55,
                                 color_discrete_sequence=PALETTE)
                    fig.update_traces(
                        textposition="inside", textinfo="percent",
                        insidetextfont=dict(color="#ffffff", size=13, family=FONT_FAMILY),
                        marker=dict(line=dict(color="#ffffff", width=2)),
                        hovertemplate="%{label}: %{value} skills (%{percent})<extra></extra>",
                    )
                    fig.update_layout(
                        showlegend=True,
                        legend=dict(orientation="h", yanchor="top", y=-0.04, xanchor="center", x=0.5),
                        annotations=[dict(text=f"<b>{len(observed)}</b><br>skills", x=0.5, y=0.5,
                                          showarrow=False, font=dict(size=18, color=INK))],
                    )
                    fig.update_layout(uniformtext=dict(minsize=10, mode="hide"))
                    plot(fig, 450)
    else:
        st.info("This competitor does not have a matching column in the competitor-skill matrix.")

    st.write("")
    with st.container(border=True):
        section_title("Side-by-side competitor benchmark", "All providers in the sample, ordered by unique skills.")
        show_data_table(breadth.sort_values("unique_skills", ascending=False), 300)


# ============================================================
# PAGE 3 — SKILL EXPLORER
# ============================================================
elif page == "Skill Explorer":
    page_intro("Skill intelligence", "Search, filter and inspect how individual skills are represented across sampled competitors.")

    f1, f2, f3 = st.columns([1.1, 1.5, 1])
    with f1:
        category_options = ["All categories"] + sorted(skills["skill_category"].dropna().unique().tolist())
        selected_category = st.selectbox("Category", category_options)
    with f2:
        skill_query = st.text_input("Search skill", placeholder="e.g. Prompt Engineering, RAG")
    with f3:
        coverage_filter = st.selectbox(
            "Observed coverage",
            ["Any coverage", "Low (≤ 33.33%)", "Medium (33.34–66.66%)", "High (≥ 66.67%)"],
        )

    filtered = skills.copy()
    if selected_category != "All categories":
        filtered = filtered[filtered["skill_category"] == selected_category]
    if skill_query:
        filtered = filtered[filtered["canonical_skill"].astype(str).str.contains(skill_query, case=False, na=False, regex=False)]
    if coverage_filter == "Low (≤ 33.33%)":
        filtered = filtered[filtered["coverage_percentage"] <= 33.33]
    elif coverage_filter == "Medium (33.34–66.66%)":
        filtered = filtered[filtered["coverage_percentage"].between(33.34, 66.66)]
    elif coverage_filter == "High (≥ 66.67%)":
        filtered = filtered[filtered["coverage_percentage"] >= 66.67]

    st.write("")
    m1, m2 = st.columns(2)
    with m1:
        metric_card("Skills matching filters", fmt(len(filtered)), "Current search and category filters", BLUE)
    with m2:
        avg_cov = filtered["coverage_percentage"].mean() if not filtered.empty else None
        metric_card("Average competitor coverage", pct(avg_cov), "Across matching skills; not market demand", TEAL)

    st.write("")
    with st.container(border=True):
        section_title("Matching skills", "Sorted by competitor count, then programme count.")
        table(filtered.sort_values(["competitor_count", "programme_count"], ascending=[False, False]), 380)

    if filtered.empty:
        st.info("No skills match these filters. Try clearing the search or widening the coverage range.")
    else:
        st.write("")
        with st.container(border=True):
            section_title("Inspect one skill", "See which sampled competitors were observed teaching it.")
            chosen_skill = st.selectbox("Choose a skill", filtered["canonical_skill"].dropna().tolist())
            skill_row = filtered[filtered["canonical_skill"] == chosen_skill].iloc[0]
            observed_row = matrix[matrix["canonical_skill"].astype(str) == str(chosen_skill)]

            a, b, c = st.columns(3)
            with a:
                metric_card("Programmes", fmt(skill_row["programme_count"]), chosen_skill, BLUE)
            with b:
                metric_card("Competitors", fmt(skill_row["competitor_count"]), "With observed presence", TEAL)
            with c:
                metric_card("Coverage", pct(skill_row["coverage_percentage"], 2),
                            f"Of {len(competitor_columns)} sampled competitors", VIOLET)

            if not observed_row.empty:
                values = observed_row.iloc[0][competitor_columns]
                presence_df = pd.DataFrame({"Competitor": competitor_columns, "Presence": values.values})
                presence_df["Status"] = presence_df["Presence"].map(lambda v: "Observed" if v > 0 else "Not observed")
                presence_df["Height"] = presence_df["Presence"].map(lambda v: 1.0 if v > 0 else 0.07)
                fig = px.bar(
                    presence_df, x="Competitor", y="Height", color="Status", text="Status",
                    color_discrete_map={"Observed": TEAL, "Not observed": "#cfd8e6"},
                    category_orders={"Competitor": competitor_columns, "Status": ["Observed", "Not observed"]},
                )
                fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0,
                                  textfont=dict(color=INK, size=12, family=FONT_FAMILY),
                                  hovertemplate="%{x}: %{text}<extra></extra>")
                fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="", bargap=0.35)
                fig.update_yaxes(range=[0, 1.3], showticklabels=False, showgrid=False)
                fig.update_xaxes(showgrid=False, tickfont=dict(color=INK, size=13))
                plot(fig, 300)


# ============================================================
# PAGE 4 — SKILL MATRIX HEATMAP
# ============================================================
elif page == "Skill Matrix":
    page_intro("Competitor skill matrix", "A visual view of which skills were observed for each provider in the collected sample.")

    fa, fb = st.columns([1.5, 1])
    with fa:
        chosen_competitors = st.multiselect("Competitors to display", competitor_columns, default=competitor_columns)
    with fb:
        matrix_search = st.text_input("Filter skill names", placeholder="Search skills...")

    heat = matrix[["canonical_skill"] + chosen_competitors].copy() if chosen_competitors else pd.DataFrame()
    if matrix_search and not heat.empty:
        heat = heat[heat["canonical_skill"].astype(str).str.contains(matrix_search, case=False, na=False, regex=False)]

    if heat.empty or not chosen_competitors:
        st.info("Choose at least one competitor and ensure the skill filter matches available skills.")
    else:
        # Sort skills so the most widely observed appear first
        heat["_total"] = heat[chosen_competitors].sum(axis=1)
        heat = heat.sort_values(["_total", "canonical_skill"], ascending=[False, True]).drop(columns="_total")

        z = (heat[chosen_competitors].astype(float).values > 0).astype(int)
        labels = [["✓" if v else "·" for v in row] for row in z]

        with st.container(border=True):
            section_title("Observed skills by competitor",
                          f"Showing {len(heat):,} skills across {len(chosen_competitors)} competitors, most widely observed first.")
            fig = go.Figure(
                data=go.Heatmap(
                    z=z, x=chosen_competitors, y=heat["canonical_skill"],
                    colorscale=[[0, "#eef2f8"], [0.4999, "#eef2f8"], [0.5, "#58c4b6"], [1, "#58c4b6"]],
                    zmin=0, zmax=1, showscale=False,
                    text=labels, texttemplate="%{text}",
                    textfont=dict(color=INK, size=13, family=FONT_FAMILY),
                    customdata=[["Observed" if v else "Not observed" for v in row] for row in z],
                    hovertemplate="Skill: %{y}<br>Competitor: %{x}<br>%{customdata}<extra></extra>",
                    xgap=3, ygap=3,
                )
            )
            fig.update_layout(
                height=max(480, min(1400, 28 * len(heat) + 150)),
                margin=dict(l=10, r=10, t=30, b=10),
                paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
                font=dict(family=FONT_FAMILY, color=INK, size=12),
                xaxis=dict(side="top", tickangle=0, tickfont=dict(size=13, color=INK), showgrid=False, automargin=True),
                yaxis=dict(autorange="reversed", tickfont=dict(size=11, color=INK), showgrid=False, automargin=True),
                hoverlabel=dict(bgcolor=INK, font=dict(color="#ffffff")),
            )
            try:
                st.plotly_chart(fig, width="stretch", config=PLOT_CONFIG)
            except Exception:
                st.plotly_chart(fig, use_container_width=True, config=PLOT_CONFIG)

        st.markdown(
            '<div class="callout"><b>How to read:</b> a teal <b>✓</b> means the skill was observed for that competitor in the collected sample. '
            'A grey <b>·</b> means it was not observed in the sample. This does not prove the provider does not teach it elsewhere.</div>',
            unsafe_allow_html=True,
        )
        _wide(st.download_button, "Download displayed matrix", heat.to_csv(index=False).encode("utf-8"),
              "competitor_skill_matrix_view.csv", "text/csv")


# ============================================================
# PAGE 5 — OPPORTUNITY LAB
# ============================================================
elif page == "Opportunity Lab":
    page_intro("Opportunity lab", "Investigate skills with lower observed competitor coverage. Treat these as research leads, not validated market gaps.")

    o1, o2 = st.columns([1, 1.2])
    with o1:
        max_coverage = st.slider("Maximum observed competitor coverage (%)", 0, 100, 33, 1)
    with o2:
        opportunity_search = st.text_input("Search opportunity skills", placeholder="e.g. AI Copilots, AI Security")

    opportunities = gaps.copy()
    if "coverage_percentage" in opportunities.columns:
        opportunities = opportunities[opportunities["coverage_percentage"] <= max_coverage]
    if opportunity_search:
        opportunities = opportunities[opportunities["canonical_skill"].astype(str).str.contains(opportunity_search, case=False, na=False, regex=False)]

    st.write("")
    a, b, c = st.columns(3)
    with a:
        metric_card("Matching skills", fmt(len(opportunities)), "After applying filters", VIOLET)
    with b:
        metric_card("Competitors in sample", fmt(breadth["competitor_name"].nunique()), "Coverage denominator", BLUE)
    with c:
        min_coverage = (opportunities["coverage_percentage"].min()
                        if not opportunities.empty and "coverage_percentage" in opportunities else None)
        metric_card("Lowest observed coverage", pct(min_coverage, 2), "Among filtered skills", AMBER)

    st.write("")
    if opportunities.empty:
        st.info("No skills match these filters. Increase the maximum coverage or clear the search.")
    else:
        sorted_opps = opportunities.sort_values(["competitor_count", "programme_count"], ascending=[True, True])

        with st.container(border=True):
            section_title("Low-coverage skills", "Sorted from least to most observed among sampled competitors.")
            table(sorted_opps, 360)

        st.write("")
        with st.container(border=True):
            section_title("Opportunity detail", "Pick a skill to see who was and wasn't observed teaching it.")
            chosen_opportunity = st.selectbox("Select a skill to inspect", sorted_opps["canonical_skill"].dropna().astype(str).tolist())
            gap_row = sorted_opps[sorted_opps["canonical_skill"].astype(str) == chosen_opportunity].iloc[0]
            matrix_row = matrix[matrix["canonical_skill"].astype(str) == chosen_opportunity]

            x1, x2, x3 = st.columns(3)
            with x1:
                metric_card("Observed competitors", fmt(gap_row["competitor_count"]), chosen_opportunity, BLUE)
            with x2:
                metric_card("Observed programmes", fmt(gap_row.get("programme_count", None)), "In the collected sample", TEAL)
            with x3:
                metric_card("Competitor coverage", pct(gap_row.get("coverage_percentage", None), 2), "Not a demand measure", VIOLET)

            if not matrix_row.empty:
                present = [n for n in competitor_columns if matrix_row.iloc[0][n] > 0]
                absent = [n for n in competitor_columns if matrix_row.iloc[0][n] <= 0]
                st.write("")
                left, right = st.columns(2)
                with left:
                    st.markdown("**Observed in sample**")
                    st.write(", ".join(present) if present else "No competitor presence recorded.")
                with right:
                    st.markdown("**Not observed in this sample**")
                    st.write(", ".join(absent) if absent else "All competitors represented.")

        st.markdown(
            '<div class="callout"><b>Validation before product decisions:</b> check source-page evidence, review taxonomy, '
            'interview target learners and employers, and test willingness to pay before treating this as a programme opportunity.</div>',
            unsafe_allow_html=True,
        )


# ============================================================
# PAGE 6 — GTM STRATEGY
# ============================================================
elif page == "GTM Strategy":
    page_intro("GTM strategy", "Read and export the V3 strategy generated from the collected competitor intelligence.")

    if REPORT_FILE.exists():
        report_text = REPORT_FILE.read_text(encoding="utf-8")
        st.download_button("Download GTM strategy", data=report_text,
                           file_name="gtm_recommendations_v3.md", mime="text/markdown")
        st.write("")
        with st.container(border=True):
            render_markdown_report(report_text)
    else:
        st.warning("The V3 report was not found.")
        st.code("reports/gtm_recommendations_v3.md")
        st.info("Run the V3 GTM recommendation engine and refresh this page.")


# ============================================================
# PAGE 7 — GTM COPILOT
# ============================================================
elif page == "GTM Copilot":
    page_intro(
        "GTM Copilot",
        "Ask questions about the collected AI/ML education market data and get answers grounded in your project datasets."
    )

    st.markdown(
        '<div class="callout"><b>How it works:</b> Python retrieves and calculates facts from your datasets; '
        'Ollama / Llama 3.2 interprets those facts. Results describe the collected sample, not the entire market.</div>',
        unsafe_allow_html=True,
    )

    try:
        from src.ai_engine.gtm_copilot import answer_question, load_data

        if "gtm_copilot_data" not in st.session_state:
            with st.spinner("Loading Copilot datasets..."):
                st.session_state["gtm_copilot_data"] = load_data()

        if "gtm_copilot_history" not in st.session_state:
            st.session_state["gtm_copilot_history"] = []

        top_left, top_right = st.columns([4, 1])
        with top_left:
            st.caption("Model: llama3.2 · Local Ollama API")
        with top_right:
            if st.button("Clear chat", key="clear_gtm_copilot"):
                st.session_state["gtm_copilot_history"] = []
                st.rerun()

        # Render previous conversation turns.
        for message in st.session_state["gtm_copilot_history"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if message["role"] == "assistant" and message.get("verified_facts"):
                    with st.expander("View verified dataset facts"):
                        st.markdown(message["verified_facts"])
                    if message.get("datasets_used"):
                        st.caption("Datasets: " + ", ".join(message["datasets_used"]))

        prompt = st.chat_input(
            "Ask about competitors, AI skills, market gaps or GTM opportunities...",
            key="gtm_copilot_prompt",
        )

        if prompt:
            st.session_state["gtm_copilot_history"].append({
                "role": "user",
                "content": prompt,
            })

            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                try:
                    with st.spinner("Analysing your market data..."):
                        result = answer_question(
                            prompt,
                            st.session_state["gtm_copilot_data"],
                        )

                    st.markdown(result["answer"])

                    if result.get("verified_facts"):
                        with st.expander("View verified dataset facts", expanded=False):
                            st.markdown(result["verified_facts"])

                    if result.get("datasets_used"):
                        st.caption("Datasets: " + ", ".join(result["datasets_used"]))

                    st.session_state["gtm_copilot_history"].append({
                        "role": "assistant",
                        "content": result["answer"],
                        "verified_facts": result.get("verified_facts", ""),
                        "datasets_used": result.get("datasets_used", []),
                    })

                except Exception as error:
                    error_message = str(error)
                    st.error(error_message)
                    st.session_state["gtm_copilot_history"].append({
                        "role": "assistant",
                        "content": f"Copilot error: {error_message}",
                    })

        if not st.session_state["gtm_copilot_history"]:
            st.markdown("**Try asking:**")
            examples = [
                "Compare upGrad and Emeritus based on AI skills.",
                "Which AI skills have the lowest competitor coverage?",
                "What opportunities exist for a new Agentic AI programme?",
                "What should upGrad focus on to differentiate its AI programmes?",
            ]
            for example in examples:
                if st.button(example, key="copilot_example_" + str(examples.index(example))):
                    st.session_state["gtm_copilot_history"].append({
                        "role": "user",
                        "content": example,
                    })
                    st.session_state["gtm_copilot_pending_question"] = example
                    st.rerun()

        # Handle a suggested question selected from the example prompts.
        pending_question = st.session_state.pop("gtm_copilot_pending_question", None)
        if pending_question:
            with st.chat_message("assistant"):
                try:
                    with st.spinner("Analysing your market data..."):
                        result = answer_question(
                            pending_question,
                            st.session_state["gtm_copilot_data"],
                        )
                    st.markdown(result["answer"])
                    if result.get("verified_facts"):
                        with st.expander("View verified dataset facts"):
                            st.markdown(result["verified_facts"])
                    if result.get("datasets_used"):
                        st.caption("Datasets: " + ", ".join(result["datasets_used"]))
                    st.session_state["gtm_copilot_history"].append({
                        "role": "assistant",
                        "content": result["answer"],
                        "verified_facts": result.get("verified_facts", ""),
                        "datasets_used": result.get("datasets_used", []),
                    })
                except Exception as error:
                    st.error(str(error))
                    st.session_state["gtm_copilot_history"].append({
                        "role": "assistant",
                        "content": f"Copilot error: {error}",
                    })

    except Exception as error:
        st.error(f"Could not initialise the GTM Copilot: {error}")
        st.info(
            "Check that src/ai_engine/gtm_copilot.py exists, its dependencies are installed, "
            "and the processed CSV datasets are present."
        )


# ============================================================
# PAGE 8 — DATA & METHODOLOGY
# ============================================================
elif page == "Data & Methodology":
    page_intro("Data & methodology", "Inspect source-file status, dataset dimensions and the interpretation rules used by this dashboard.")

    status_rows = []
    for key, path in DATA_FILES.items():
        frame = data[key]
        status_rows.append({
            "Dataset": path.name,
            "Status": "Loaded" if not frame.empty else "Empty",
            "Rows": len(frame),
            "Columns": len(frame.columns),
        })
    with st.container(border=True):
        section_title("Source file status")
        table(pd.DataFrame(status_rows), 235)

    st.write("")
    a, b = st.columns(2)
    with a:
        with st.container(border=True):
            section_title("Coverage definition")
            st.markdown(
                """
                **Competitor coverage** is calculated as:

                `Competitors with observed skill ÷ Total competitors in sample × 100`

                A matrix value of **1** means the skill was observed in at least one collected programme for that competitor. A value of **0** means it was not observed in the collected sample.
                """
            )
    with b:
        with st.container(border=True):
            section_title("Important limitations")
            st.markdown(
                """
                - The dataset covers only collected programmes, not every provider offering.
                - Extracted skills and taxonomy categories may contain errors.
                - Coverage does not measure learner demand, employer demand or market share.
                - Low observed coverage is a research lead, not proof of an unmet need.
                - Pricing and placement claims require separate verification.
                """
            )

    st.write("")
    with st.container(border=True):
        section_title("Preview source tables")
        dataset_choice = st.selectbox(
            "Choose a dataset",
            list(data.keys()),
            format_func=lambda key: {
                "competitor_breadth": "Competitor breadth",
                "skill_coverage": "Skill market coverage",
                "category_coverage": "Category market coverage",
                "competitor_matrix": "Competitor skill matrix",
                "potential_gaps": "Potential skill gaps",
            }[key],
        )
        show_data_table(data[dataset_choice], 430)
        st.download_button("Download selected dataset", data[dataset_choice].to_csv(index=False).encode("utf-8"),
                           file_name=f"{dataset_choice}.csv", mime="text/csv")


# ============================================================
# FOOTER
# ============================================================
st.divider()
st.markdown(
    """
    <div style="display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;color:#7b889b;font-size:11px;">
        <span>GTM INTELLIGENCE · AI / ML EDUCATION MARKET</span>
        <span>Built with Streamlit · Python · Pandas · Plotly</span>
        <span>Sample-based research · Validate before decisions</span>
    </div>
    """,
    unsafe_allow_html=True,
)