"""
app.py - Lumora Retail sales dashboard (Streamlit, iOS-inspired design)
Synthetic data - Lumora Retail is a fictional company.

Run:  python -m streamlit run app.py
"""
import html
import os
import subprocess
import sys

import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Lumora Retail", layout="centered")

# ------------------------------------------------------------------
# Colours and page style
# ------------------------------------------------------------------
# iOS dark mode system colours
BLUE, GREEN, RED, ORANGE = "#0A84FF", "#30D158", "#FF453A", "#FF9F0A"
TEAL, PURPLE = "#64D2FF", "#BF5AF2"
WHITE, GREY = "#FFFFFF", "#8E8E93"          # primary and secondary text
CARD, SEPARATOR, MUTED = "#1C1C1E", "#38383A", "#3A3A3C"   # card background, lines, inactive bars
CHANNEL_COLOURS = {"Store": BLUE, "Mobile App": TEAL, "Website": PURPLE, "Marketplace": ORANGE}
FONT = '-apple-system, BlinkMacSystemFont, "SF Pro Text", "Inter", "Helvetica Neue", sans-serif'

st.markdown(f"""
<style>
html, body, [class*="st-"], .stApp {{ font-family: {FONT}; }}
.stApp {{ background: #000000; color: {WHITE}; }}
header[data-testid="stHeader"], footer, #MainMenu {{ display: none; }}
.block-container {{ max-width: 860px; padding-top: 2.5rem; padding-bottom: 4rem; }}
.stMarkdown p, .stMarkdown strong {{ color: {WHITE}; }}

/* Containers created with key="card_..." become dark rounded cards */
div[class*="st-key-card"] {{ background: {CARD}; border: none !important; border-radius: 18px; padding: 16px 16px 8px; }}

/* iOS segmented control: dark track, lighter selected segment */
div:has(> button[data-variant="segmented_control"]) {{
    background: #2C2C2E; border-radius: 9px; padding: 2px; gap: 0; display: inline-flex;
}}
button[data-variant="segmented_control"] {{
    background: transparent !important; border: none !important; border-radius: 7px !important;
    color: {WHITE} !important; font-size: 13px; font-weight: 500; min-height: 28px; padding: 2px 14px;
}}
button[data-variant="segmented_control"][aria-checked="true"] {{
    background: #636366 !important; font-weight: 600; box-shadow: 0 1px 3px rgba(0,0,0,.4);
}}
div[data-baseweb="select"] > div {{ background: {CARD}; border: none; border-radius: 10px; color: {WHITE}; }}

.eyebrow {{ color: {GREY}; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: .02em; }}
.large-title {{ font-size: 34px; font-weight: 700; letter-spacing: -.02em; margin: 2px 0 18px; color: {WHITE}; }}
.section {{ color: {GREY}; font-size: 13px; text-transform: uppercase; letter-spacing: .02em; margin: 26px 0 8px 16px; }}
.footnote {{ color: {GREY}; font-size: 13px; margin: 8px 16px 0; }}

/* KPI cards */
.kpi {{ background: {CARD}; border-radius: 18px; padding: 16px 18px; height: 100%; }}
.kpi .label {{ color: {GREY}; font-size: 13px; font-weight: 600; }}
.kpi .value {{ font-size: 26px; font-weight: 700; letter-spacing: -.02em; margin: 4px 0 6px; color: {WHITE}; }}
.pill {{ display: inline-block; font-size: 12px; font-weight: 600; padding: 2px 8px; border-radius: 999px; }}
.up {{ color: {GREEN}; background: rgba(48,209,88,.16); }}
.down {{ color: {RED}; background: rgba(255,69,58,.16); }}
.neutral {{ color: {GREY}; background: rgba(142,142,147,.16); }}

/* Settings-style list */
.list {{ background: {CARD}; border-radius: 18px; overflow: hidden; }}
.row {{ display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; margin-left: 0; }}
.row + .row {{ border-top: 0.5px solid {SEPARATOR}; }}
.row .name {{ font-size: 16px; color: {WHITE}; }}
.row .sub {{ font-size: 13px; color: {GREY}; }}
.row .right {{ text-align: right; font-size: 15px; color: {WHITE}; white-space: nowrap; }}

/* Storage-style stacked bar */
.storage {{ display: flex; height: 22px; border-radius: 6px; overflow: hidden; gap: 2px; margin: 6px 0 12px; }}
.legend {{ display: flex; flex-wrap: wrap; gap: 6px 18px; font-size: 13px; color: {GREY}; }}
.dot {{ display: inline-block; width: 9px; height: 9px; border-radius: 50%; margin-right: 6px; }}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------
# Data
# ------------------------------------------------------------------
if not os.path.exists("data/clean/orders.csv"):
    with st.spinner("First run: generating and cleaning the synthetic data (about 30 seconds)..."):
        subprocess.run([sys.executable, "generate_data.py"], check=True)
        subprocess.run([sys.executable, "clean_data.py"], check=True)


@st.cache_data
def load_data():
    orders = pd.read_csv("data/clean/orders.csv", parse_dates=["order_date"])
    items = pd.read_csv("data/clean/order_items.csv")
    products = pd.read_csv("data/clean/products.csv")

    orders = orders[orders["order_status"] == "Completed"]
    df = items.merge(orders, on="order_id").merge(products[["product_id", "product_name", "category"]], on="product_id")
    df["net_sales"] = df["unit_price"] * df["quantity"] - df["discount_amount"]
    df["gross_profit"] = df["net_sales"] - df["unit_cost"] * df["quantity"]
    df["year"] = df["order_date"].dt.year
    df["month"] = df["order_date"].dt.to_period("M").dt.to_timestamp()
    return df


df = load_data()


def money(value):
    baht = "\u0e3f"  # Thai baht sign
    return f"{baht}{value / 1e6:,.1f}M" if abs(value) >= 1e6 else f"{baht}{value:,.0f}"


def pill(text, good):
    """Green pill if good is True, red if False, grey if None (nothing to compare)."""
    style = "neutral" if good is None else ("up" if good else "down")
    return f'<span class="pill {style}">{text}</span>'


def card(label, value, change_text, good):
    return f'<div class="kpi"><div class="label">{label}</div><div class="value">{value}</div>{pill(change_text, good)}</div>'


def chart_style(chart, height=220):
    """Clean iOS-like chart: no borders, light horizontal grid, grey labels."""
    return (chart.properties(height=height)
            .configure_view(strokeWidth=0)
            .configure_axis(labelFont=FONT, labelColor=GREY, labelFontSize=11,
                            domain=False, ticks=False, gridColor=SEPARATOR)
            .configure_axisX(grid=False)
            .configure(font=FONT, background=CARD))


# ------------------------------------------------------------------
# Header and filters
# ------------------------------------------------------------------
st.markdown('<div class="eyebrow">Lumora Retail · Synthetic data</div><div class="large-title">Sales</div>',
            unsafe_allow_html=True)

years = sorted(df["year"].unique())
year = st.selectbox("Year", sorted(years, reverse=True), label_visibility="collapsed")  # newest year first
channel_choice = st.segmented_control("Channel", ["All", "Store", "Online"], default="All",
                                      label_visibility="collapsed") or "All"
category = st.selectbox("Category", ["All categories"] + sorted(df["category"].unique()), label_visibility="collapsed")

data = df
if channel_choice == "Store":
    data = data[data["channel"] == "Store"]
elif channel_choice == "Online":
    data = data[data["channel"] != "Store"]
if category != "All categories":
    data = data[data["category"] == category]

this_year = data[data["year"] == year]
last_year = data[data["year"] == year - 1]
if this_year.empty:
    st.info("No sales for these filters.")
    st.stop()

# ------------------------------------------------------------------
# KPI cards: selected year vs the year before
# ------------------------------------------------------------------
def kpis(d):
    sales, profit, orders = d["net_sales"].sum(), d["gross_profit"].sum(), d["order_id"].nunique()
    return {"sales": sales, "profit": profit, "margin": profit / sales if sales else 0,
            "aov": sales / orders if orders else 0}


now, before = kpis(this_year), kpis(last_year)


has_previous = before["sales"] > 0   # the first year (2016) has nothing to compare with


def growth(key):
    if not has_previous:
        return "no earlier year", None
    g = now[key] / before[key] - 1
    return f"{'▲' if g >= 0 else '▼'} {abs(g):.1%}", g >= 0


def margin_growth():
    if not has_previous:
        return "no earlier year", None
    change = (now["margin"] - before["margin"]) * 100
    return f"{'▲' if change >= 0 else '▼'} {abs(change):.1f} pts", change >= 0


heading = f"{year} compared with {year - 1}" if has_previous else f"{year}"
st.markdown(f'<div class="section">{heading}</div>', unsafe_allow_html=True)
cols = st.columns(4, gap="small")
cols[0].markdown(card("Net Sales", money(now["sales"]), *growth("sales")), unsafe_allow_html=True)
cols[1].markdown(card("Gross Profit", money(now["profit"]), *growth("profit")), unsafe_allow_html=True)
cols[2].markdown(card("Gross Margin", f"{now['margin']:.1%}", *margin_growth()), unsafe_allow_html=True)
cols[3].markdown(card("Avg Order", money(now["aov"]), *growth("aov")), unsafe_allow_html=True)

# ------------------------------------------------------------------
# Trends
# ------------------------------------------------------------------
yearly = data.groupby("year")[["net_sales", "gross_profit"]].sum().reset_index()
yearly["margin"] = yearly["gross_profit"] / yearly["net_sales"]
yearly["selected"] = yearly["year"] == year

st.markdown('<div class="section">Trends</div>', unsafe_allow_html=True)
with st.container(key="card_sales"):
    st.markdown("**Net Sales by year**")
    bars = alt.Chart(yearly).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6, size=26).encode(
        x=alt.X("year:O", title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("net_sales:Q", title=None, axis=alt.Axis(format="~s", tickCount=4)),
        color=alt.condition("datum.selected", alt.value(BLUE), alt.value(MUTED)),
        tooltip=[alt.Tooltip("year:O", title="Year"), alt.Tooltip("net_sales:Q", title="Net Sales", format=",.0f")])
    st.altair_chart(chart_style(bars), width="stretch")

with st.container(key="card_margin"):
    trend = "recovering" if yearly["margin"].iloc[-1] > yearly["margin"].iloc[-2] else "falling"
    st.markdown(f"**Gross margin** · {trend} in {yearly['year'].iloc[-1]}")
    base = alt.Chart(yearly).encode(
        x=alt.X("year:O", title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("margin:Q", title=None, axis=alt.Axis(format=".0%", tickCount=4), scale=alt.Scale(zero=False)),
        tooltip=[alt.Tooltip("year:O", title="Year"), alt.Tooltip("margin:Q", title="Gross margin", format=".1%")])
    line = base.mark_line(color=GREY, strokeWidth=2.5, point=alt.OverlayMarkDef(color=GREY, size=40))
    # Highlight the latest year: green if the margin went up, red if it went down
    last_point = base.transform_filter(alt.datum.year == int(yearly["year"].iloc[-1])).mark_point(
        filled=True, size=140, color=GREEN if trend == "recovering" else RED, opacity=1)
    st.altair_chart(chart_style(line + last_point, 200), width="stretch")

with st.container(key="card_monthly"):
    st.markdown("**Monthly Net Sales** · peaks every December")
    monthly = data.groupby("month")["net_sales"].sum().reset_index()
    area = alt.Chart(monthly).mark_area(
        line={"color": BLUE, "strokeWidth": 1.5},
        color=alt.Gradient(gradient="linear", x1=1, x2=1, y1=1, y2=0,
                           stops=[alt.GradientStop(color="rgba(10,132,255,0)", offset=0),
                                  alt.GradientStop(color="rgba(10,132,255,0.35)", offset=1)])).encode(
        x=alt.X("month:T", title=None, axis=alt.Axis(format="%Y", tickCount="year")),
        y=alt.Y("net_sales:Q", title=None, axis=alt.Axis(format="~s", tickCount=4)),
        tooltip=[alt.Tooltip("month:T", title="Month", format="%b %Y"),
                 alt.Tooltip("net_sales:Q", title="Net Sales", format=",.0f")])
    st.altair_chart(chart_style(area, 200), width="stretch")

# ------------------------------------------------------------------
# Channels: storage-style bar
# ------------------------------------------------------------------
channel_sales = this_year.groupby("channel")["net_sales"].sum().sort_values(ascending=False)
share = channel_sales / channel_sales.sum()
segments = "".join(f'<div style="width:{s * 100:.2f}%;background:{CHANNEL_COLOURS[c]}"></div>' for c, s in share.items())
legend = "".join(f'<span><span class="dot" style="background:{CHANNEL_COLOURS[c]}"></span>{c} {s:.0%}</span>'
                 for c, s in share.items())
st.markdown(f'<div class="section">Sales by channel · {year}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="list" style="padding:14px 16px"><div class="row" style="padding:0">'
            f'<span class="name">{money(channel_sales.sum())}</span><span class="sub">Net Sales</span></div>'
            f'<div class="storage">{segments}</div><div class="legend">{legend}</div></div>',
            unsafe_allow_html=True)

# ------------------------------------------------------------------
# Categories and products: settings-style lists
# ------------------------------------------------------------------
def list_rows(table, name_col, sub_col=None):
    rows = []
    for _, r in table.iterrows():
        sub = f'<div class="sub">{html.escape(str(r[sub_col]))}</div>' if sub_col else ""
        margin = pill(f"{r['margin']:.0%} margin", r["margin"] >= 0.10)
        rows.append(f'<div class="row"><div><div class="name">{html.escape(str(r[name_col]))}</div>{sub}</div>'
                    f'<div class="right">{money(r["net_sales"])}<br>{margin}</div></div>')
    return '<div class="list">' + "".join(rows) + "</div>"


cat = this_year.groupby("category")[["net_sales", "gross_profit"]].sum().reset_index()
cat["margin"] = cat["gross_profit"] / cat["net_sales"]
st.markdown(f'<div class="section">Categories · {year}</div>', unsafe_allow_html=True)
st.markdown(list_rows(cat.sort_values("net_sales", ascending=False), "category"), unsafe_allow_html=True)

top = this_year.groupby(["product_name", "category"])[["net_sales", "gross_profit"]].sum().reset_index()
top["margin"] = top["gross_profit"] / top["net_sales"]
top = top.sort_values("net_sales", ascending=False).head(10)
low = (top["margin"] < 0.10).sum()
st.markdown(f'<div class="section">Top 10 products · {year}</div>', unsafe_allow_html=True)
st.markdown(list_rows(top, "product_name", "category"), unsafe_allow_html=True)
st.markdown(f'<div class="footnote">{low} of the top 10 best sellers have a gross margin under 10% (red).</div>',
            unsafe_allow_html=True)

# ------------------------------------------------------------------
# Customers
# ------------------------------------------------------------------
members = data[(data["customer_type"] == "Member") & (data["year"] <= year)]
spend = members.groupby("customer_id")["net_sales"].sum().sort_values(ascending=False)
top20 = spend.head(int(len(spend) * 0.2)).sum() / spend.sum()
st.markdown('<div class="section">Customers</div>', unsafe_allow_html=True)
st.markdown(f'<div class="list"><div class="row"><div><div class="name">Top 20% of members</div>'
            f'<div class="sub">Share of member revenue, 2016–{year}</div></div>'
            f'<div class="right" style="font-size:22px;font-weight:700">{top20:.0%}</div></div></div>',
            unsafe_allow_html=True)

st.markdown('<div class="footnote">Lumora Retail is a fictional company. All data is synthetic.</div>',
            unsafe_allow_html=True)
