"""
Domestic Gc Analyst — grocery price & consumption dashboard.

Data: Supabase tables
  receipts   (receipt_id PK, store_name, purchase_date, total_amount)
  line_items (item_id PK, receipt_id FK, item_name, unit_price, category)

Run:  streamlit run app.py
Secrets (.streamlit/secrets.toml):
  [supabase]
  url = "https://xxxx.supabase.co"
  key = "your-key"
"""

from __future__ import annotations

import re
from collections import Counter

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from thefuzz import fuzz

# ──────────────────────────────────────────────────────────────────────────────
# Page config & design tokens
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Domestic Gc Analyst",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

INK = "#0F172A"          # primary text
INK_MUTED = "#64748B"    # secondary text
LINE = "#E2E8F0"         # hairlines / borders
SURFACE = "#FFFFFF"
CANVAS = "#F7F8FA"
ACCENT = "#5E6AD2"       # Linear-style indigo
POSITIVE = "#0E9F6E"
NEGATIVE = "#E0484B"
PALETTE = ["#5E6AD2", "#3FA7A0", "#E0A43C", "#C2577A", "#7C8DA6", "#8B6FCB"]
FONT_STACK = ("Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, "
              "'Helvetica Neue', Arial, sans-serif")

FUZZY_THRESHOLD = 85     # similarity must be > this to merge names
PAGE_SIZE = 1000         # Supabase/PostgREST default max rows per request


def inject_css() -> None:
    st.markdown(
        f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"], .stApp, .stMarkdown, button, input, select, textarea {{
    font-family: {FONT_STACK} !important;
    -webkit-font-smoothing: antialiased;
}}
.stApp {{ background: {CANVAS}; color: {INK}; }}

/* Strip default Streamlit chrome & padding */
#MainMenu, footer, [data-testid="stDecoration"], [data-testid="stAppDeployButton"],
.stDeployButton {{ display: none !important; }}
header[data-testid="stHeader"] {{ background: transparent; height: 0; }}
.block-container, [data-testid="stMainBlockContainer"] {{
    padding: 1.75rem 2.25rem 2.5rem 2.25rem !important;
    max-width: 1400px;
}}

/* Sidebar */
section[data-testid="stSidebar"] {{
    background: {SURFACE};
    border-right: 1px solid {LINE};
}}
section[data-testid="stSidebar"] .block-container,
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {{
    padding-top: 1.5rem;
}}
.sb-brand {{ font-weight: 700; font-size: 1.05rem; letter-spacing: -0.01em; color: {INK}; }}
.sb-sub {{ color: {INK_MUTED}; font-size: 0.8rem; margin-bottom: 1.25rem; }}

/* Page header */
.page-eyebrow {{
    text-transform: uppercase; letter-spacing: 0.08em; font-size: 0.72rem;
    font-weight: 600; color: {ACCENT}; margin-bottom: 0.25rem;
}}
.page-title {{
    font-size: 1.75rem; font-weight: 700; letter-spacing: -0.02em;
    color: {INK}; margin: 0 0 0.25rem 0; line-height: 1.2;
}}
.page-sub {{ color: {INK_MUTED}; font-size: 0.92rem; margin-bottom: 1.5rem; }}
.chip {{
    display: inline-block; padding: 2px 10px; border-radius: 999px;
    background: #EEF0FB; color: {ACCENT}; font-size: 0.75rem; font-weight: 600;
    margin-right: 6px;
}}

/* KPI cards (st.metric) */
[data-testid="stMetric"] {{
    background: {SURFACE};
    border: 1px solid {LINE};
    border-radius: 14px;
    padding: 1.1rem 1.25rem 1rem 1.25rem;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04), 0 4px 16px rgba(15, 23, 42, 0.04);
    transition: box-shadow .15s ease, transform .15s ease;
}}
[data-testid="stMetric"]:hover {{
    box-shadow: 0 2px 4px rgba(15, 23, 42, 0.06), 0 10px 28px rgba(15, 23, 42, 0.07);
    transform: translateY(-1px);
}}
[data-testid="stMetricLabel"] p {{
    color: {INK_MUTED} !important; font-size: 0.78rem !important; font-weight: 500 !important;
    text-transform: uppercase; letter-spacing: 0.05em;
}}
[data-testid="stMetricValue"] {{
    color: {INK} !important; font-size: 1.7rem !important; font-weight: 650 !important;
    letter-spacing: -0.02em;
}}
[data-testid="stMetricDelta"] {{ font-size: 0.8rem !important; font-weight: 500; }}

/* Chart cards */
.card-title {{ font-weight: 600; font-size: 0.98rem; color: {INK}; margin: 0; }}
.card-sub {{ color: {INK_MUTED}; font-size: 0.8rem; margin: 0.1rem 0 0.4rem 0; }}
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"] .card-title) {{
    background: {SURFACE};
    border: 1px solid {LINE} !important;
    border-radius: 14px;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04), 0 4px 16px rgba(15, 23, 42, 0.04);
}}

/* Inputs */
div[data-baseweb="select"] > div, .stDateInput input {{
    border-radius: 10px !important; border-color: {LINE} !important;
}}
div[role="radiogroup"] label p {{ font-size: 0.85rem; }}

/* Dataframe & expander */
[data-testid="stExpander"] {{
    background: {SURFACE}; border: 1px solid {LINE}; border-radius: 14px;
}}
hr {{ border-color: {LINE}; }}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{ gap: 4px; border-bottom: 1px solid {LINE}; }}
.stTabs [data-baseweb="tab"] {{
    height: 40px; padding: 0 14px; border-radius: 10px 10px 0 0;
    font-weight: 500; color: {INK_MUTED};
}}
.stTabs [aria-selected="true"] {{ color: {INK} !important; }}
.stTabs [data-baseweb="tab-highlight"] {{ background-color: {ACCENT}; }}

/* User card */
.user-card {{
    display: flex; align-items: center; gap: 10px; padding: 10px 12px;
    border: 1px solid {LINE}; border-radius: 12px; margin-bottom: 1rem; background: {CANVAS};
}}
.user-avatar {{
    width: 32px; height: 32px; border-radius: 999px; background: #EEF0FB; color: {ACCENT};
    display: flex; align-items: center; justify-content: center; font-weight: 700;
}}
.user-name {{ font-weight: 600; font-size: 0.88rem; color: {INK}; line-height: 1.2; }}
.user-meta {{ font-size: 0.74rem; color: {INK_MUTED}; }}

/* Login card */
.login-wrap {{ max-width: 420px; margin: 12vh auto 0 auto; text-align: center; }}
.login-wrap .page-title {{ font-size: 1.6rem; }}
</style>
""",
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Data layer
# ──────────────────────────────────────────────────────────────────────────────
def _get_secrets() -> tuple[str, str]:
    """Accept either a [supabase] table or flat SUPABASE_URL / SUPABASE_KEY."""
    try:
        if "supabase" in st.secrets:
            return st.secrets["supabase"]["url"], st.secrets["supabase"]["key"]
        return st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
    except Exception:
        st.error(
            "Supabase credentials not found. Add them to `.streamlit/secrets.toml`:\n\n"
            "```toml\n[supabase]\nurl = \"https://xxxx.supabase.co\"\nkey = \"your-key\"\n```"
        )
        st.stop()


@st.cache_resource(show_spinner=False)
def get_client():
    from supabase import create_client

    url, key = _get_secrets()
    return create_client(url, key)


def _fetch_all(table: str, columns: str) -> list[dict]:
    """Page through a table so we are not capped at PostgREST's 1000-row limit."""
    client = get_client()
    rows: list[dict] = []
    start = 0
    while True:
        resp = (
            client.table(table)
            .select(columns)
            .range(start, start + PAGE_SIZE - 1)
            .execute()
        )
        batch = resp.data or []
        rows.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
        start += PAGE_SIZE
    return rows


@st.cache_data(ttl=300, show_spinner="Fetching receipts from Supabase…")
def load_data() -> tuple[pd.DataFrame, int]:
    receipts = pd.DataFrame(
        _fetch_all("receipts", "*")
    )
    items = pd.DataFrame(
        _fetch_all("line_items", "item_id, receipt_id, item_name, unit_price, category")
    )
    if receipts.empty or items.empty:
        return pd.DataFrame(), 0

    if "telegram_user_id" not in receipts.columns:
        receipts["telegram_user_id"] = None
    receipts = receipts[["receipt_id", "store_name", "purchase_date", "total_amount",
                         "telegram_user_id"]]
    df = items.merge(receipts, on="receipt_id", how="left")
    df["telegram_user_id"] = pd.to_numeric(df["telegram_user_id"], errors="coerce")

    # Types & cleaning
    df["purchase_date"] = pd.to_datetime(df["purchase_date"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df["total_amount"] = pd.to_numeric(df["total_amount"], errors="coerce")
    df["item_name"] = df["item_name"].fillna("").astype(str).str.strip()
    df["category"] = df["category"].fillna("Uncategorised").astype(str).str.strip()
    df["store_name"] = df["store_name"].fillna("Unknown store").astype(str).str.strip()
    df = df.dropna(subset=["purchase_date", "unit_price"])
    df = df[(df["item_name"] != "") & (df["unit_price"] > 0)]   # drop ₹0 / blank lines

    # Store names: "RJ SUPER MARKET" and "R J SUPER MARKET" → one store
    df["_store_key"] = df["store_name"].str.lower().str.replace(r"[^a-z0-9]", "", regex=True)
    store_display = (df.groupby("_store_key")["store_name"]
                       .agg(lambda s: s.value_counts().index[0]))
    df["store_name"] = df["_store_key"].map(store_display)

    df, dupes = _drop_duplicate_receipts(df)

    # Schema fallback: DB has no quantity / item_total_amount
    if "quantity" not in df.columns:
        df["quantity"] = 1
    if "item_total_amount" not in df.columns:
        df["item_total_amount"] = df["unit_price"] * df["quantity"]

    df = df.drop(columns=["_store_key"])
    return df.sort_values("purchase_date").reset_index(drop=True), dupes


def _drop_duplicate_receipts(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """
    The same paper receipt is sometimes sent to the bot more than once (and the
    OCR can misread the year). Receipts with the same store, total and set of
    line items are treated as one; the copy with the latest date is kept.
    """
    sig = (df.assign(_line=df["item_name"].str.lower().str.replace(r"\s+", "", regex=True)
                     + "@" + df["unit_price"].round(0).astype(int).astype(str))
             .groupby("receipt_id")
             .agg(store=("_store_key", "first"),
                  total=("total_amount", "first"),
                  lines=("_line", lambda s: "|".join(sorted(s))),
                  date=("purchase_date", "first"),
                  user=("telegram_user_id", "first")))
    sig["user"] = sig["user"].fillna(-1)          # duplicates only count within one sender
    sig = sig.sort_values("date")
    # Rule 1: same store + same total + same line items (catches misread dates)
    sig = sig[~sig.duplicated(subset=["user", "store", "total", "lines"], keep="last")]
    # Rule 2: same store + same date + same non-zero total (catches OCR spelling drift)
    total = sig["total"].fillna(0)
    rule2 = sig[total > 0].duplicated(subset=["user", "store", "date", "total"], keep="last")
    sig = sig.drop(rule2[rule2].index)
    removed = df["receipt_id"].nunique() - len(sig)
    return df[df["receipt_id"].isin(sig.index)].copy(), int(removed)


def _pretty(name: str) -> str:
    """'NILKAMAL SATOO 250GM' -> 'Nilkamal Satoo 250gm'; mixed-case names are kept."""
    name = " ".join(name.split())
    if not (name.isupper() or name.islower()):
        return name
    name = name.title()
    return re.sub(r"(\d)([A-Za-z]+)", lambda m: m.group(1) + m.group(2).lower(), name)


@st.cache_data(ttl=300, show_spinner="Standardising item names…")
def build_name_map(names: tuple[str, ...], counts: tuple[int, ...],
                   threshold: int = FUZZY_THRESHOLD) -> dict[str, str]:
    """
    Greedy fuzzy clustering. Names are visited most-frequent first; each one
    joins the first existing cluster whose canonical name scores > threshold,
    otherwise it starts a new cluster. The canonical label is the most
    frequently purchased spelling in the cluster.
    """
    freq = Counter(dict(zip(names, counts)))
    ordered = sorted(freq, key=lambda n: (-freq[n], n))
    canon_keys: list[str] = []          # normalised canonical strings
    canon_names: list[str] = []         # display canonical strings
    mapping: dict[str, str] = {}

    for name in ordered:
        key = " ".join(name.lower().split())
        match = None
        for i, ck in enumerate(canon_keys):
            if key == ck or fuzz.token_sort_ratio(key, ck) > threshold:
                match = i
                break
        if match is None:
            canon_keys.append(key)
            canon_names.append(_pretty(name))
            mapping[name] = canon_names[-1]
        else:
            mapping[name] = canon_names[match]
    return mapping


def add_standard_names(df: pd.DataFrame) -> pd.DataFrame:
    vc = df["item_name"].value_counts()
    mapping = build_name_map(tuple(vc.index), tuple(int(c) for c in vc.values))
    df = df.copy()
    df["standard_item_name"] = df["item_name"].map(mapping)
    # One category per standard item (the most common one the parser assigned)
    cat_mode = df.groupby("standard_item_name")["category"].agg(lambda s: s.value_counts().index[0])
    df["category"] = df["standard_item_name"].map(cat_mode)
    return df


# ──────────────────────────────────────────────────────────────────────────────
# Charts
# ──────────────────────────────────────────────────────────────────────────────
def style_fig(fig: go.Figure, height: int = 360) -> go.Figure:
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_STACK, size=12, color=INK_MUTED),
        margin=dict(l=8, r=8, t=8, b=8),
        hovermode="x unified",
        hoverlabel=dict(bgcolor=SURFACE, bordercolor=LINE,
                        font=dict(family=FONT_STACK, color=INK, size=12)),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
        colorway=PALETTE,
    )
    fig.update_xaxes(showgrid=False, linecolor=LINE, tickcolor=LINE, ticks="outside",
                     ticklen=4, zeroline=False)
    fig.update_yaxes(gridcolor="#EEF1F5", zeroline=False, linecolor="rgba(0,0,0,0)")
    return fig


def price_chart(d: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    stores = d["store_name"].unique().tolist()
    multi = len(stores) > 1
    groups = d.groupby("store_name") if multi else [("Unit price", d)]
    for i, (store, g) in enumerate(groups):
        g = g.groupby("purchase_date", as_index=False)["unit_price"].mean()
        color = PALETTE[i % len(PALETTE)]
        fig.add_trace(go.Scatter(
            x=g["purchase_date"], y=g["unit_price"], name=store,
            mode="lines+markers",
            line=dict(color=color, width=2.4, shape="spline", smoothing=0.6),
            marker=dict(size=7, color=SURFACE, line=dict(color=color, width=2)),
            fill="tozeroy" if not multi else None,
            fillcolor="rgba(94,106,210,0.08)" if not multi else None,
            hovertemplate="₹%{y:,.2f}<extra>%{fullData.name}</extra>",
        ))
    style_fig(fig)
    fig.update_yaxes(tickprefix="₹", rangemode="tozero" if not multi else "normal")
    span_days = (d["purchase_date"].max() - d["purchase_date"].min()).days
    xaxis = dict(tickformat="%d %b" if span_days < 330 else "%b %Y", hoverformat="%d %b %Y")
    if span_days < 14:
        # Few days of data: one tick per day, padded so single points aren't on the edge
        pad = pd.Timedelta(days=1)
        xaxis.update(dtick=86_400_000, range=[d["purchase_date"].min() - pad,
                                              d["purchase_date"].max() + pad])
    fig.update_xaxes(**xaxis)
    fig.update_layout(showlegend=multi)
    return fig


def volume_chart(d: pd.DataFrame, freq: str) -> go.Figure:
    rule = "W-MON" if freq == "Weekly" else "MS"
    s = (d.set_index("purchase_date")
           .resample(rule, label="left", closed="left")["quantity"].sum()
           .reset_index())
    s = s[s["quantity"] > 0] if len(s) > 24 else s   # keep gaps visible for short histories
    labels = (("Wk of " + s["purchase_date"].dt.strftime("%d %b %y")) if freq == "Weekly"
              else s["purchase_date"].dt.strftime("%b %Y"))
    fig = go.Figure(go.Bar(
        x=labels, y=s["quantity"],
        marker=dict(color=ACCENT, opacity=0.85, cornerradius=6) if _supports_cornerradius()
        else dict(color=ACCENT, opacity=0.85),
        hovertemplate="%{x}<br><b>%{y} units</b><extra></extra>",
    ))
    style_fig(fig)
    fig.update_layout(hovermode="closest", bargap=0.35)
    fig.update_xaxes(type="category")
    ymax = float(s["quantity"].max()) if len(s) else 1
    fig.update_yaxes(rangemode="tozero", tickformat=",d",
                     dtick=1 if ymax <= 6 else None, range=[0, max(ymax * 1.15, 1)])
    return fig


def _supports_cornerradius() -> bool:
    try:
        go.bar.Marker(cornerradius=4)
        return True
    except Exception:
        return False


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
def inr(x: float, decimals: int = 2) -> str:
    sign = "−" if x < 0 else ""
    return f"{sign}₹{abs(x):,.{decimals}f}"


def toggle(label: str, options: list[str], key: str) -> str:
    """Segmented control when available (Streamlit ≥1.40), radio otherwise."""
    if hasattr(st, "segmented_control"):
        val = st.segmented_control(label, options, default=options[0], key=key,
                                   label_visibility="collapsed")
        return val or options[0]
    return st.radio(label, options, horizontal=True, key=key, label_visibility="collapsed")


def card_header(title: str, sub: str) -> None:
    st.markdown(f'<p class="card-title">{title}</p><p class="card-sub">{sub}</p>',
                unsafe_allow_html=True)


def chart(fig: go.Figure) -> None:
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def _secret(section: str, key: str, default=None):
    try:
        return st.secrets[section][key]
    except Exception:
        return default


# ──────────────────────────────────────────────────────────────────────────────
# People & personal links
#   Table dashboard_users(id, display_name, access_code, telegram_user_id, is_admin)
#   Each person opens   <app url>/?u=<access_code>   — no accounts or passwords.
# ──────────────────────────────────────────────────────────────────────────────
USERS_TABLE = "dashboard_users"


@st.cache_data(ttl=300, show_spinner=False)
def load_users() -> tuple[pd.DataFrame, bool]:
    cols = ["id", "display_name", "access_code", "telegram_user_id", "is_admin"]
    try:
        rows = _fetch_all(USERS_TABLE, "*")
    except Exception:
        return pd.DataFrame(columns=cols), False
    users = pd.DataFrame(rows)
    for c in cols:
        if c not in users.columns:
            users[c] = None
    users["telegram_user_id"] = pd.to_numeric(users["telegram_user_id"], errors="coerce")
    users["is_admin"] = users["is_admin"].fillna(False).astype(bool)
    users["access_code"] = users["access_code"].astype(str)
    return users[cols], True


def app_url() -> str:
    return str(_secret("app", "public_url", "https://grocery-dash.streamlit.app")).rstrip("/")


def personal_link(code: str) -> str:
    return f"{app_url()}/?u={code}"


def current_profile(users: pd.DataFrame) -> dict | None:
    """Identify the visitor from ?u=<code> (kept in the URL so it can be bookmarked)."""
    code = st.query_params.get("u") or st.session_state.get("access_code")
    if not code:
        return None
    match = users[users["access_code"] == str(code).strip()]
    if match.empty:
        return {"invalid": True}
    st.session_state["access_code"] = code
    if st.query_params.get("u") != code:
        st.query_params["u"] = code
    r = match.iloc[0]
    return {"id": r["id"], "name": r["display_name"], "telegram_user_id": r["telegram_user_id"],
            "is_admin": bool(r["is_admin"]), "code": code}


def render_welcome(invalid: bool = False) -> None:
    st.markdown(
        '<div class="login-wrap"><div style="font-size:2.6rem">🛒</div>'
        '<div class="page-title">Your grocery dashboard</div>'
        + ('<div class="page-sub">That link doesn\'t work any more. Ask for a fresh one.</div>'
           if invalid else
           '<div class="page-sub">This dashboard is private. Open the personal link '
           'you were sent, or paste your code below.</div>')
        + '</div>',
        unsafe_allow_html=True,
    )
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        code = st.text_input("Your code", placeholder="Paste your code", label_visibility="collapsed")
        if st.button("Open my dashboard", type="primary", width="stretch") and code.strip():
            st.session_state["access_code"] = code.strip().split("u=")[-1]
            st.rerun()


def sign_out() -> None:
    st.session_state.pop("access_code", None)
    st.query_params.clear()


def _write(op) -> bool:
    try:
        op(get_client().table(USERS_TABLE)).execute()
        load_users.clear()
        return True
    except Exception as exc:
        st.error(f"Couldn't save: {exc}")
        return False


def render_people(users: pd.DataFrame, df_all: pd.DataFrame, me: dict) -> None:
    import secrets as pysecrets

    st.markdown('<p class="card-title">People who can see the dashboard</p>'
                '<p class="card-sub">Send each person their link. Anyone with a link sees that '
                'person\'s receipts, so share it only with them.</p>', unsafe_allow_html=True)

    view = users.copy()
    view["link"] = view["access_code"].map(personal_link)
    view["role"] = view["is_admin"].map({True: "Admin (sees everyone)", False: "Member"})
    view["receipts"] = view["telegram_user_id"].map(
        lambda u: int(df_all.loc[df_all["telegram_user_id"] == u, "receipt_id"].nunique())
        if pd.notna(u) and not df_all.empty else 0)
    st.dataframe(
        view[["display_name", "role", "receipts", "link"]], hide_index=True, width="stretch",
        column_config={
            "display_name": "Name", "role": "Access",
            "receipts": st.column_config.NumberColumn("Receipts"),
            "link": st.column_config.LinkColumn("Personal link", display_text="Open link ↗"),
        },
    )
    with st.expander("Copy a link to send"):
        who = st.selectbox("Person", view["display_name"], key="copy_who")
        st.code(view.loc[view["display_name"] == who, "link"].iloc[0], language=None)

    st.divider()
    known = set(users["telegram_user_id"].dropna())
    senders = (df_all.dropna(subset=["telegram_user_id"])
                     .groupby("telegram_user_id")
                     .agg(n=("receipt_id", "nunique"), last=("purchase_date", "max"))
               if not df_all.empty else pd.DataFrame(columns=["n", "last"]))
    senders = senders[~senders.index.isin(known)]

    left, right = st.columns(2, gap="large")
    with left:
        st.markdown('<p class="card-title">Add a person</p>'
                    '<p class="card-sub">Ask them to send one receipt to the Telegram bot first, '
                    'then pick it below.</p>', unsafe_allow_html=True)
        with st.form("add_person", clear_on_submit=True):
            name = st.text_input("Name", placeholder="e.g. Mom")
            opts = [None] + list(senders.index)
            tg = st.selectbox(
                "Their receipts", opts,
                format_func=lambda u: "Not yet — link later" if u is None else
                f"Telegram sender …{str(int(u))[-4:]} · {int(senders.loc[u, 'n'])} receipt(s), "
                f"last {senders.loc[u, 'last']:%d %b}",
            )
            admin = st.checkbox("Can see everyone's receipts (admin)")
            if st.form_submit_button("Create personal link", type="primary") and name.strip():
                row = {"display_name": name.strip(), "access_code": pysecrets.token_urlsafe(12),
                       "telegram_user_id": int(tg) if tg is not None else None, "is_admin": admin}
                if _write(lambda t: t.insert(row)):
                    st.success(f"Done. {name.strip()}'s link: {personal_link(row['access_code'])}")
    with right:
        st.markdown('<p class="card-title">Change or remove</p>'
                    '<p class="card-sub">Link a person to their receipts, give them a new link '
                    '(the old one stops working), or remove them.</p>', unsafe_allow_html=True)
        others = users[users["id"] != me["id"]]
        if others.empty:
            st.caption("No one else yet.")
        else:
            pid = st.selectbox("Person", others["id"],
                               format_func=lambda i: others.loc[others["id"] == i, "display_name"].iloc[0])
            c1, c2, c3 = st.columns(3)
            if not senders.empty:
                link_to = st.selectbox(
                    "Link to receipts from", list(senders.index),
                    format_func=lambda u: f"Telegram sender …{str(int(u))[-4:]} · "
                                          f"{int(senders.loc[u, 'n'])} receipt(s)")
                if c1.button("Link", width="stretch"):
                    if _write(lambda t: t.update({"telegram_user_id": int(link_to)}).eq("id", int(pid))):
                        st.rerun()
            if c2.button("New link", width="stretch"):
                if _write(lambda t: t.update({"access_code": pysecrets.token_urlsafe(12)}).eq("id", int(pid))):
                    st.rerun()
            if c3.button("Remove", width="stretch"):
                if _write(lambda t: t.delete().eq("id", int(pid))):
                    st.rerun()


# ──────────────────────────────────────────────────────────────────────────────
# Overview analytics
# ──────────────────────────────────────────────────────────────────────────────
def receipts_table(d: pd.DataFrame) -> pd.DataFrame:
    return (d.groupby("receipt_id")
              .agg(date=("purchase_date", "first"), store=("store_name", "first"),
                   items=("item_id", "count"), spend=("item_total_amount", "sum"),
                   billed=("total_amount", "first"))
              .sort_values("date", ascending=False)
              .reset_index())


def price_movers(d: pd.DataFrame) -> pd.DataFrame:
    """Items bought on at least two different dates: first vs latest average price."""
    daily = (d.groupby(["standard_item_name", "purchase_date"])["unit_price"].mean()
               .reset_index().sort_values("purchase_date"))
    g = daily.groupby("standard_item_name")
    out = pd.DataFrame({
        "first_price": g["unit_price"].first(),
        "latest_price": g["unit_price"].last(),
        "first_date": g["purchase_date"].first(),
        "latest_date": g["purchase_date"].last(),
        "times": g["purchase_date"].nunique(),
    })
    out = out[out["times"] >= 2].copy()
    out["change_pct"] = (out["latest_price"] - out["first_price"]) / out["first_price"] * 100
    return out.sort_values("change_pct", key=lambda s: s.abs(), ascending=False).reset_index()


def hbar(series: pd.Series, money: bool = True, height: int | None = None) -> go.Figure:
    series = series.sort_values()
    fig = go.Figure(go.Bar(
        x=series.values, y=series.index, orientation="h",
        marker=dict(color=ACCENT, opacity=0.85, cornerradius=5) if _supports_cornerradius()
        else dict(color=ACCENT, opacity=0.85),
        text=[inr(v, 0) if money else f"{v:,.0f}" for v in series.values],
        textposition="outside", cliponaxis=False,
        hovertemplate="%{y}<br><b>" + ("₹%{x:,.2f}" if money else "%{x:,}") + "</b><extra></extra>",
    ))
    style_fig(fig, height=height or max(220, 34 * len(series) + 40))
    fig.update_layout(hovermode="closest", bargap=0.35, margin=dict(l=8, r=48, t=8, b=8))
    fig.update_xaxes(showticklabels=False, showgrid=False, ticks="", linecolor="rgba(0,0,0,0)")
    fig.update_yaxes(showgrid=False, ticks="")
    return fig


def spend_trend(d: pd.DataFrame, freq: str) -> go.Figure:
    rule = "W-MON" if freq == "Weekly" else "MS"
    s = (d.set_index("purchase_date")
           .resample(rule, label="left", closed="left")["item_total_amount"].sum()
           .reset_index())
    if len(s) > 24:
        s = s[s["item_total_amount"] > 0]
    labels = (("Wk of " + s["purchase_date"].dt.strftime("%d %b %y")) if freq == "Weekly"
              else s["purchase_date"].dt.strftime("%b %Y"))
    fig = go.Figure(go.Bar(
        x=labels, y=s["item_total_amount"],
        marker=dict(color=ACCENT, opacity=0.85, cornerradius=6) if _supports_cornerradius()
        else dict(color=ACCENT, opacity=0.85),
        hovertemplate="%{x}<br><b>₹%{y:,.2f}</b><extra></extra>",
    ))
    style_fig(fig, height=320)
    fig.update_layout(hovermode="closest", bargap=0.35)
    fig.update_xaxes(type="category")
    fig.update_yaxes(tickprefix="₹", rangemode="tozero")
    return fig


def render_overview(d: pd.DataFrame) -> None:
    rec = receipts_table(d)
    total = float(d["item_total_amount"].sum())
    n_rec = len(rec)
    avg_basket = total / n_rec if n_rec else 0.0

    # This month vs last month (calendar months, relative to the latest purchase)
    latest = d["purchase_date"].max()
    this_m = latest.to_period("M")
    month_sp = d.groupby(d["purchase_date"].dt.to_period("M"))["item_total_amount"].sum()
    this_sp = float(month_sp.get(this_m, 0.0))
    last_sp = float(month_sp.get(this_m - 1, 0.0))
    delta = None
    if last_sp:
        delta = f"{(this_sp - last_sp) / last_sp * 100:+.0f}% vs {(this_m - 1).strftime('%b')}"

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total spend", inr(total, 0), help="Sum of itemised lines on your receipts.")
    k2.metric("Receipts", f"{n_rec:,}",
              help=f"{d['purchase_date'].min():%d %b %Y} – {latest:%d %b %Y}")
    k3.metric("Avg basket", inr(avg_basket, 0))
    k4.metric(f"Spend in {this_m.strftime('%b %Y')}", inr(this_sp, 0),
              delta=delta, delta_color="inverse")

    st.write("")
    left, right = st.columns([1.35, 1], gap="medium")
    with left:
        with st.container(border=True):
            hc, tc = st.columns([1.3, 1])
            with hc:
                card_header("Spend over time", "Itemised spend per period")
            with tc:
                freq = toggle("Spend granularity", ["Monthly", "Weekly"], key="spend_freq")
            chart(spend_trend(d, freq))
    with right:
        with st.container(border=True):
            card_header("Spend by category", "Where the money goes")
            chart(hbar(d.groupby("category")["item_total_amount"].sum(), height=320))

    left, right = st.columns([1.35, 1], gap="medium")
    with left:
        with st.container(border=True):
            card_header("Top items by spend", "Your 10 biggest line items")
            top = d.groupby("standard_item_name")["item_total_amount"].sum().nlargest(10)
            chart(hbar(top))
    with right:
        with st.container(border=True):
            card_header("Spend by store", "Total across receipts")
            chart(hbar(d.groupby("store_name")["item_total_amount"].sum(),
                       height=max(160, 44 * d["store_name"].nunique() + 40)))
        with st.container(border=True):
            card_header("Most frequently bought", "Number of times on a receipt")
            freq_items = d.groupby("standard_item_name")["receipt_id"].nunique().nlargest(5)
            chart(hbar(freq_items, money=False))

    with st.container(border=True):
        card_header("Price changes", "Items bought on 2+ dates — first vs latest price")
        movers = price_movers(d)
        if movers.empty:
            st.caption("Not enough repeat purchases yet. This fills in as more receipts come in.")
        else:
            st.dataframe(
                movers[["standard_item_name", "first_price", "latest_price", "change_pct",
                        "times", "latest_date"]].head(15),
                hide_index=True, width="stretch",
                column_config={
                    "standard_item_name": "Item",
                    "first_price": st.column_config.NumberColumn("First price", format="₹%.2f"),
                    "latest_price": st.column_config.NumberColumn("Latest price", format="₹%.2f"),
                    "change_pct": st.column_config.NumberColumn("Change", format="%+.1f%%"),
                    "times": st.column_config.NumberColumn("Purchase dates"),
                    "latest_date": st.column_config.DateColumn("Last bought", format="DD MMM YYYY"),
                },
            )


def render_receipts(d: pd.DataFrame) -> None:
    rec = receipts_table(d)
    st.dataframe(
        rec[["date", "store", "items", "spend", "billed"]],
        hide_index=True, width="stretch",
        column_config={
            "date": st.column_config.DateColumn("Date", format="DD MMM YYYY"),
            "store": "Store",
            "items": st.column_config.NumberColumn("Items"),
            "spend": st.column_config.NumberColumn("Itemised total", format="₹%.2f"),
            "billed": st.column_config.NumberColumn("Bill total", format="₹%.2f",
                                                    help="Total printed on the receipt"),
        },
    )
    if not rec.empty:
        pick = st.selectbox(
            "Show the lines on a receipt", rec["receipt_id"],
            format_func=lambda rid: (lambda r: f"{r['date']:%d %b %Y} · {r['store']} · {inr(r['spend'])}")(
                rec.set_index("receipt_id").loc[rid]),
        )
        lines = d[d["receipt_id"] == pick][["item_name", "standard_item_name", "category", "unit_price"]]
        st.dataframe(
            lines, hide_index=True, width="stretch",
            column_config={
                "item_name": "Name on receipt", "standard_item_name": "Standard name",
                "category": "Category",
                "unit_price": st.column_config.NumberColumn("Price", format="₹%.2f"),
            },
        )


# ──────────────────────────────────────────────────────────────────────────────
# Item explorer (the original single-item view)
# ──────────────────────────────────────────────────────────────────────────────
def render_item_explorer(df: pd.DataFrame) -> None:
    c1, c2 = st.columns([1, 2])
    with c1:
        categories = sorted(df["category"].unique())
        cat = st.selectbox("Category", ["All categories"] + categories, key="ix_cat")
    scope = df if cat == "All categories" else df[df["category"] == cat]
    item_counts = scope["standard_item_name"].value_counts()
    with c2:
        item = st.selectbox(
            "Item", item_counts.index.tolist(), key="ix_item",
            format_func=lambda n: f"{n}  ·  {item_counts[n]}×",
            help="Similar spellings (fuzzy score > 85) are merged into one standard name.",
        )
    if item is None:
        st.info("No items for this selection.")
        return

    d = df[df["standard_item_name"] == item].sort_values("purchase_date")
    variants = sorted(d["item_name"].unique())
    st.markdown(
        f'<div class="page-title" style="font-size:1.35rem;margin-top:.5rem">{item}</div>'
        f'<div class="page-sub"><span class="chip">{d["category"].mode().iat[0]}</span>'
        f'{len(variants)} receipt spelling{"s" if len(variants) != 1 else ""} merged</div>',
        unsafe_allow_html=True,
    )

    first_price = float(d["unit_price"].iloc[0])
    latest_price = float(d["unit_price"].iloc[-1])
    total_units = int(d["quantity"].sum())
    inflation = ((latest_price - first_price) / first_price * 100) if first_price else 0.0
    abs_change = latest_price - first_price

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Latest price", inr(latest_price),
              delta=f"{inr(abs_change)} vs first" if abs_change else None,
              delta_color="inverse",
              help=f"Last bought {d['purchase_date'].iloc[-1]:%d %b %Y}")
    k2.metric("First price", inr(first_price),
              help=f"First bought {d['purchase_date'].iloc[0]:%d %b %Y}")
    k3.metric("Total units", f"{total_units:,}",
              help="Quantity is not stored in the database yet, so each line item counts as 1 unit.")
    k4.metric("% Inflation", f"{inflation:+.1f}%",
              delta="Price up" if inflation > 0 else ("Price down" if inflation < 0 else "Flat"),
              delta_color="inverse" if inflation else "off")

    st.write("")
    left, right = st.columns([1.35, 1], gap="medium")
    with left:
        with st.container(border=True):
            card_header("Unit price over time",
                        "Average price paid per purchase date" +
                        (", split by store" if d["store_name"].nunique() > 1 else ""))
            chart(price_chart(d))
    with right:
        with st.container(border=True):
            hc, tc = st.columns([1.3, 1])
            with hc:
                card_header("Consumption volume", "Units bought per period")
            with tc:
                freq = toggle("Granularity", ["Weekly", "Monthly"], key="freq")
            chart(volume_chart(d, freq))

    with st.expander(f"Purchase history · {len(d)} rows"):
        st.dataframe(
            d[["purchase_date", "store_name", "item_name", "unit_price", "quantity",
               "item_total_amount"]].sort_values("purchase_date", ascending=False),
            hide_index=True, width="stretch",
            column_config={
                "purchase_date": st.column_config.DateColumn("Date", format="DD MMM YYYY"),
                "store_name": "Store",
                "item_name": "Name on receipt",
                "unit_price": st.column_config.NumberColumn("Unit price", format="₹%.2f"),
                "quantity": st.column_config.NumberColumn("Qty"),
                "item_total_amount": st.column_config.NumberColumn("Line total", format="₹%.2f"),
            },
        )


# ──────────────────────────────────────────────────────────────────────────────
# App
# ──────────────────────────────────────────────────────────────────────────────
UNASSIGNED = "Old receipts (no sender)"
EVERYONE = "Everyone"


def main() -> None:
    inject_css()

    # 1. Who is this? (personal link ?u=<code>)
    users, users_table = load_users()
    if not users_table:
        st.error("Setup isn't finished: the dashboard_users table is missing in Supabase.")
        st.stop()
    profile = current_profile(users)
    if profile is None or profile.get("invalid"):
        render_welcome(invalid=bool(profile))
        st.stop()

    # 2. Data
    try:
        raw, dupes = load_data()
    except Exception as exc:
        st.error(f"Couldn't load your receipts right now. Please try again in a minute. ({exc})")
        st.stop()
    df_all = add_standard_names(raw) if not raw.empty else raw

    # 3. Sidebar
    with st.sidebar:
        st.markdown('<div class="sb-brand">🛒 Domestic Gc Analyst</div>'
                    '<div class="sb-sub">Your groceries, in numbers</div>',
                    unsafe_allow_html=True)
        initial = (profile["name"] or "?")[0].upper()
        st.markdown(
            f'<div class="user-card"><div class="user-avatar">{initial}</div>'
            f'<div><div class="user-name">{profile["name"]}</div>'
            f'<div class="user-meta">{"Admin" if profile["is_admin"] else "Personal dashboard"}</div>'
            f'</div></div>', unsafe_allow_html=True)

        view = profile["name"]
        if profile["is_admin"]:
            people = users.dropna(subset=["telegram_user_id"])
            known = set(people["telegram_user_id"])
            unlinked = sorted({int(u) for u in df_all.get("telegram_user_id", pd.Series(dtype=float)).dropna()
                               if u not in known})
            options = ([EVERYONE] + people["display_name"].tolist()
                       + [f"Unlinked sender …{str(u)[-4:]}" for u in unlinked] + [UNASSIGNED])
            view = st.selectbox("Showing", options)
            unlinked_map = {f"Unlinked sender …{str(u)[-4:]}": u for u in unlinked}

    # 4. Whose receipts
    if df_all.empty:
        df = df_all
    elif profile["is_admin"] and view == EVERYONE:
        df = df_all
    elif profile["is_admin"] and view == UNASSIGNED:
        df = df_all[df_all["telegram_user_id"].isna()]
    elif profile["is_admin"] and view in unlinked_map:
        df = df_all[df_all["telegram_user_id"] == unlinked_map[view]]
    elif profile["is_admin"] and view != profile["name"]:
        uid = users.loc[users["display_name"] == view, "telegram_user_id"].iloc[0]
        df = df_all[df_all["telegram_user_id"] == uid]
    elif pd.notna(profile["telegram_user_id"]):
        df = df_all[df_all["telegram_user_id"] == profile["telegram_user_id"]]
    else:
        df = df_all.iloc[0:0]

    with st.sidebar:
        if not df.empty:
            dmin, dmax = df["purchase_date"].min().date(), df["purchase_date"].max().date()
            date_range = st.date_input("Dates", (dmin, dmax), min_value=dmin, max_value=dmax)
            stores = sorted(df["store_name"].unique())
            sel_stores = (st.multiselect("Shops", stores, default=stores)
                          if len(stores) > 1 else stores)
        st.divider()
        if st.button("↻ Refresh", width="stretch"):
            st.cache_data.clear()
            st.rerun()
        st.button("Sign out", on_click=sign_out, width="stretch")
        if profile["is_admin"] and dupes:
            st.caption(f"{dupes} duplicate receipt{'s' if dupes != 1 else ''} ignored")

    # 5. Header
    who = ("your household" if view == EVERYONE else
           "receipts with no sender" if view == UNASSIGNED else
           "you" if view == profile["name"] else view)
    st.markdown(
        f'<div class="page-eyebrow">Hi, {profile["name"]}</div>'
        f'<div class="page-title">Grocery overview</div>'
        f'<div class="page-sub">What you spend, what prices are doing, and what you buy most — for {who}.</div>',
        unsafe_allow_html=True,
    )

    tab_names = ["Overview", "Items", "Receipts"] + (["People"] if profile["is_admin"] else [])
    tabs = st.tabs(tab_names)

    if profile["is_admin"]:
        with tabs[3]:
            render_people(users, df_all, profile)

    if df.empty:
        with tabs[0]:
            st.info("No receipts yet. Send a photo of your bill to the Telegram bot — "
                    "it will show up here within a few minutes.")
        return

    if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
        start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
        df = df[(df["purchase_date"] >= start) & (df["purchase_date"] < end + pd.Timedelta(days=1))]
    if sel_stores:
        df = df[df["store_name"].isin(sel_stores)]
    if df.empty:
        with tabs[0]:
            st.warning("Nothing matches the dates or shops you picked.")
        return

    with tabs[0]:
        render_overview(df)
    with tabs[1]:
        render_item_explorer(df)
    with tabs[2]:
        render_receipts(df)


if __name__ == "__main__":
    main()
