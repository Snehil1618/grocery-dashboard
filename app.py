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
        _fetch_all("receipts", "receipt_id, store_name, purchase_date, total_amount")
    )
    items = pd.DataFrame(
        _fetch_all("line_items", "item_id, receipt_id, item_name, unit_price, category")
    )
    if receipts.empty or items.empty:
        return pd.DataFrame(), 0

    df = items.merge(receipts, on="receipt_id", how="left")

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
                  date=("purchase_date", "first")))
    sig = sig.sort_values("date")
    # Rule 1: same store + same total + same line items (catches misread dates)
    sig = sig[~sig.duplicated(subset=["store", "total", "lines"], keep="last")]
    # Rule 2: same store + same date + same non-zero total (catches OCR spelling drift)
    total = sig["total"].fillna(0)
    rule2 = sig[total > 0].duplicated(subset=["store", "date", "total"], keep="last")
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
def inr(x: float) -> str:
    return f"−₹{abs(x):,.2f}" if x < 0 else f"₹{x:,.2f}"


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


# ──────────────────────────────────────────────────────────────────────────────
# App
# ──────────────────────────────────────────────────────────────────────────────
def main() -> None:
    inject_css()

    try:
        raw, dupes = load_data()
    except Exception as exc:  # network / auth / schema problems
        st.error(f"Couldn't load data from Supabase: {exc}")
        st.stop()

    if raw.empty:
        st.info("No receipts found yet. Send a receipt to the Telegram bot, then refresh. "
                "If Supabase has rows, check that Row Level Security allows reads for this key.")
        if st.button("↻ Refresh data"):
            st.cache_data.clear()
            st.rerun()
        st.stop()

    df = add_standard_names(raw)

    # ── Sidebar ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown('<div class="sb-brand">🛒 Domestic Gc Analyst</div>'
                    '<div class="sb-sub">Grocery price & consumption intelligence</div>',
                    unsafe_allow_html=True)

        categories = sorted(df["category"].unique())
        cat = st.selectbox("Category", ["All categories"] + categories)
        scope = df if cat == "All categories" else df[df["category"] == cat]

        # Most-bought items first so the default selection is meaningful
        item_counts = scope["standard_item_name"].value_counts()
        items = item_counts.index.tolist()
        item = st.selectbox(
            "Item", items,
            format_func=lambda n: f"{n}  ·  {item_counts[n]}×",
            help="Similar spellings (fuzzy score > 85) are merged into one standard name.",
        )

        dmin, dmax = df["purchase_date"].min().date(), df["purchase_date"].max().date()
        date_range = st.date_input("Date range", (dmin, dmax), min_value=dmin, max_value=dmax)

        stores = sorted(df["store_name"].unique())
        sel_stores = st.multiselect("Stores", stores, default=stores)

        st.divider()
        if st.button("↻ Refresh data", width="stretch"):
            st.cache_data.clear()
            st.rerun()
        st.caption(f"{len(df):,} line items · {df['receipt_id'].nunique():,} receipts · "
                   f"{df['standard_item_name'].nunique():,} standard items"
                   + (f" · {dupes} duplicate receipt{'s' if dupes != 1 else ''} ignored" if dupes else ""))

    # ── Filter ───────────────────────────────────────────────────────────────
    d = df[df["standard_item_name"] == item]
    if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
        start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
        d = d[(d["purchase_date"] >= start) & (d["purchase_date"] <= end + pd.Timedelta(days=1))]
    if sel_stores:
        d = d[d["store_name"].isin(sel_stores)]
    d = d.sort_values("purchase_date")

    # ── Header ───────────────────────────────────────────────────────────────
    variants = sorted(df.loc[df["standard_item_name"] == item, "item_name"].unique())
    category_label = d["category"].mode().iat[0] if not d.empty else "—"
    st.markdown(
        f'<div class="page-eyebrow">Item analysis</div>'
        f'<div class="page-title">{item}</div>'
        f'<div class="page-sub"><span class="chip">{category_label}</span>'
        f'{len(variants)} receipt spelling{"s" if len(variants) != 1 else ""} merged</div>',
        unsafe_allow_html=True,
    )

    if d.empty:
        st.warning("No purchases of this item match the current filters.")
        st.stop()

    # ── KPIs ─────────────────────────────────────────────────────────────────
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

    # ── Charts ───────────────────────────────────────────────────────────────
    left, right = st.columns([1.35, 1], gap="medium")
    with left:
        with st.container(border=True):
            card_header("Unit price over time",
                        "Average price paid per purchase date" +
                        (", split by store" if d["store_name"].nunique() > 1 else ""))
            st.plotly_chart(price_chart(d), width="stretch",
                            config={"displayModeBar": False})
    with right:
        with st.container(border=True):
            hc, tc = st.columns([1.3, 1])
            with hc:
                card_header("Consumption volume", "Units bought per period")
            with tc:
                freq = toggle("Granularity", ["Weekly", "Monthly"], key="freq")
            st.plotly_chart(volume_chart(d, freq), width="stretch",
                            config={"displayModeBar": False})

    # ── Detail ───────────────────────────────────────────────────────────────
    with st.expander(f"Purchase history · {len(d)} rows"):
        table = d[["purchase_date", "store_name", "item_name", "unit_price",
                   "quantity", "item_total_amount"]].sort_values("purchase_date", ascending=False)
        st.dataframe(
            table, hide_index=True, width="stretch",
            column_config={
                "purchase_date": st.column_config.DateColumn("Date", format="DD MMM YYYY"),
                "store_name": "Store",
                "item_name": "Name on receipt",
                "unit_price": st.column_config.NumberColumn("Unit price", format="₹%.2f"),
                "quantity": st.column_config.NumberColumn("Qty"),
                "item_total_amount": st.column_config.NumberColumn("Line total", format="₹%.2f"),
            },
        )


if __name__ == "__main__":
    main()
