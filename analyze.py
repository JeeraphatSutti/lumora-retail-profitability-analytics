"""
analyze.py - Step 2: analysis
Reads data/clean/*.csv and answers the business questions.
Saves tables to outputs/, charts to images/ and key numbers to outputs/metrics.json.
(Synthetic data - Lumora Retail is a fictional company.)

Metric definitions (only Completed orders are counted):
    Net Sales     = unit_price * quantity - discount_amount
    COGS          = unit_cost * quantity
    Gross Profit  = Net Sales - COGS
    GM %          = Gross Profit / Net Sales
    AOV           = Net Sales / number of orders
"""
import os
import json
import pandas as pd
import matplotlib.pyplot as plt

os.makedirs("outputs", exist_ok=True)
os.makedirs("images", exist_ok=True)
metrics = {}

# ============================================================
# 0. Load and combine the tables into one sales table
# ============================================================
orders = pd.read_csv("data/clean/orders.csv", parse_dates=["order_date"])
items = pd.read_csv("data/clean/order_items.csv")
products = pd.read_csv("data/clean/products.csv")
promotions = pd.read_csv("data/clean/promotions.csv")
returns = pd.read_csv("data/clean/returns.csv")

orders = orders[orders["order_status"] == "Completed"]
sales = items.merge(orders, on="order_id").merge(products[["product_id", "product_name", "category"]], on="product_id")
sales = sales.merge(promotions[["promo_id", "promo_type"]], on="promo_id", how="left")
sales["promo_type"] = sales["promo_type"].fillna("No promotion")

sales["gross_sales"] = sales["unit_price"] * sales["quantity"]
sales["net_sales"] = sales["gross_sales"] - sales["discount_amount"]
sales["cogs"] = sales["unit_cost"] * sales["quantity"]
sales["gross_profit"] = sales["net_sales"] - sales["cogs"]
sales["year"] = sales["order_date"].dt.year
sales["month"] = sales["order_date"].dt.month


def summary(df):
    """Standard KPIs for any slice of the sales table."""
    net = df["net_sales"].sum()
    gp = df["gross_profit"].sum()
    n_orders = df["order_id"].nunique()
    return pd.Series({
        "net_sales": net,
        "gross_profit": gp,
        "gm_pct": gp / net,
        "orders": n_orders,
        "aov": net / n_orders,
        "discount_rate": df["discount_amount"].sum() / df["gross_sales"].sum(),
    })


# ============================================================
# 1. Yearly KPIs - is the business growing, and is profit following?
# ============================================================
kpi = sales.groupby("year").apply(summary, include_groups=False)
kpi["online_share"] = sales[sales["channel"] != "Store"].groupby("year")["net_sales"].sum() / kpi["net_sales"]
kpi["sales_growth"] = kpi["net_sales"].pct_change()
kpi["gp_growth"] = kpi["gross_profit"].pct_change()
fees = orders.assign(year=orders["order_date"].dt.year).groupby("year")["platform_fee"].sum()
kpi["marketplace_fees"] = fees
kpi.round(4).to_csv("outputs/kpi_yearly.csv")
print(kpi[["net_sales", "gross_profit", "gm_pct", "discount_rate", "online_share"]].round(3))

k22, k25 = kpi.loc[2022], kpi.loc[2025]
metrics["net_sales_2022"] = k22["net_sales"]
metrics["net_sales_2025"] = k25["net_sales"]
metrics["sales_growth_22_25"] = k25["net_sales"] / k22["net_sales"] - 1
metrics["gross_profit_2022"] = k22["gross_profit"]
metrics["gross_profit_2025"] = k25["gross_profit"]
metrics["gp_change_22_25"] = k25["gross_profit"] / k22["gross_profit"] - 1
metrics["gm_2016"] = kpi.loc[2016, "gm_pct"]
metrics["gm_2022"] = k22["gm_pct"]
metrics["gm_2025"] = k25["gm_pct"]
metrics["online_share_2016"] = kpi.loc[2016, "online_share"]
metrics["online_share_2019"] = kpi.loc[2019, "online_share"]
metrics["online_share_2020"] = kpi.loc[2020, "online_share"]
metrics["online_share_2025"] = k25["online_share"]
metrics["total_net_sales_10y"] = kpi["net_sales"].sum()
metrics["total_orders_10y"] = int(kpi["orders"].sum())

# ============================================================
# 2. Margin: why did it dip to 2022, what drove the recovery, what still holds it back?
# ============================================================
# 2a. Size of the dip and the recovery in baht
k17 = kpi.loc[2017]                                   # margin peak before the dip
metrics["gm_2017"] = k17["gm_pct"]
metrics["gp_lost_at_2022_low"] = k22["net_sales"] * (k17["gm_pct"] - k22["gm_pct"])
metrics["gp_gained_from_recovery_2025"] = k25["net_sales"] * (k25["gm_pct"] - k22["gm_pct"])

# 2b. Mix: share of sales from the low-margin categories (Electronics + Home Appliances)
low_margin_cats = ["Electronics", "Home Appliances"]
for y in [2016, 2022, 2025]:
    year_sales = sales[sales["year"] == y]
    metrics[f"elec_appl_share_{y}"] = (year_sales.loc[year_sales["category"].isin(low_margin_cats), "net_sales"].sum()
                                       / year_sales["net_sales"].sum())

# 2c. Discounts: extra discount cost in 2025 versus the 2022 discount rate
gross_2025 = sales.loc[sales["year"] == 2025, "gross_sales"].sum()
metrics["discount_rate_2022"] = k22["discount_rate"]
metrics["discount_rate_2025"] = k25["discount_rate"]
metrics["extra_discount_cost_2025"] = gross_2025 * (k25["discount_rate"] - k22["discount_rate"])

# 2d. Margin by category, 2022 vs 2025 (did the recovery happen in every category?)
cat = sales[sales["year"].isin([2022, 2025])].groupby(["category", "year"]).apply(summary, include_groups=False).unstack("year")
cat_table = pd.DataFrame({
    "sales_share_2022": cat[("net_sales", 2022)] / cat[("net_sales", 2022)].sum(),
    "sales_share_2025": cat[("net_sales", 2025)] / cat[("net_sales", 2025)].sum(),
    "gm_2022": cat[("gm_pct", 2022)],
    "gm_2025": cat[("gm_pct", 2025)],
}).sort_values("sales_share_2025", ascending=False)
cat_table.round(4).to_csv("outputs/category_2022_vs_2025.csv")
print(cat_table.round(3))

# 2e. Marketplace fees
metrics["marketplace_fees_2022"] = k22["marketplace_fees"]
metrics["marketplace_fees_2025"] = k25["marketplace_fees"]

# ============================================================
# 3. Seasonality and sale days
# ============================================================
monthly = sales.groupby(["year", "month"])["net_sales"].sum().reset_index()
season = monthly.groupby("month")["net_sales"].mean()
season_index = season / season.mean()
season_index.round(3).to_csv("outputs/seasonality_index.csv", header=["index"])
metrics["december_index"] = season_index[12]
metrics["february_index"] = season_index[2]

daily = sales.groupby("order_date")["net_sales"].sum()
sale_days = []
for year in range(2016, 2026):
    for month, day in [(11, 11), (12, 12)]:
        date = pd.Timestamp(year, month, day)
        same_month = daily[(daily.index.year == year) & (daily.index.month == month)]
        sale_days.append({"year": year, "event": f"{month}.{day}",
                          "sales": daily.get(date, 0),
                          "times_normal_day": daily.get(date, 0) / same_month.median()})
sale_days = pd.DataFrame(sale_days)
sale_days.round(2).to_csv("outputs/sale_day_uplift.csv", index=False)
metrics["1111_x_2016"] = sale_days.query("year == 2016 and event == '11.11'")["times_normal_day"].iloc[0]
metrics["1111_x_2025"] = sale_days.query("year == 2025 and event == '11.11'")["times_normal_day"].iloc[0]

# COVID: April-May 2020 versus April-May 2019, store vs online
aprmay = sales[sales["month"].isin([4, 5]) & sales["year"].isin([2019, 2020])]
covid = aprmay.assign(online=aprmay["channel"] != "Store").groupby(["online", "year"])["net_sales"].sum().unstack()
metrics["covid_store_change"] = covid.loc[False, 2020] / covid.loc[False, 2019] - 1
metrics["covid_online_change"] = covid.loc[True, 2020] / covid.loc[True, 2019] - 1

# ============================================================
# 4. Channels
# ============================================================
channel = sales.groupby(["year", "channel"]).apply(summary, include_groups=False)[["net_sales", "gm_pct"]].reset_index()
channel.round(4).to_csv("outputs/channel_yearly.csv", index=False)
ch25 = sales[sales["year"] == 2025].groupby("channel")["net_sales"].sum()
metrics["marketplace_share_2025"] = ch25["Marketplace"] / ch25.sum()
metrics["marketplace_fee_pct_2025"] = k25["marketplace_fees"] / ch25["Marketplace"]

# ============================================================
# 5. Products - best sellers with low margin
# ============================================================
prod = sales[sales["year"] == 2025].groupby(["product_id", "product_name", "category"]).apply(summary, include_groups=False)
prod = prod.sort_values("net_sales", ascending=False).reset_index()
top20 = prod.head(20).copy()
top20["low_margin"] = top20["gm_pct"] < 0.10
top20.round(4).to_csv("outputs/top20_products_2025.csv", index=False)
low = top20[top20["low_margin"]]
metrics["low_margin_skus_in_top20"] = len(low)
metrics["low_margin_sales"] = low["net_sales"].sum()
metrics["low_margin_gp"] = low["gross_profit"].sum()
metrics["low_margin_sales_share"] = low["net_sales"].sum() / prod["net_sales"].sum()

cat25 = sales[sales["year"] == 2025].groupby("category")[["net_sales", "gross_profit"]].sum()
metrics["elec_appl_sales_share_2025"] = cat25.loc[["Electronics", "Home Appliances"], "net_sales"].sum() / cat25["net_sales"].sum()
metrics["elec_appl_gp_share_2025"] = cat25.loc[["Electronics", "Home Appliances"], "gross_profit"].sum() / cat25["gross_profit"].sum()

# ============================================================
# 6. Customers - Pareto, RFM, cohort retention (members only)
# ============================================================
members = sales[sales["customer_type"] == "Member"]

# 6a. Pareto: share of revenue from the top 20% of customers
spend = members.groupby("customer_id")["net_sales"].sum().sort_values(ascending=False)
metrics["top20_customer_share"] = spend.head(int(len(spend) * 0.2)).sum() / spend.sum()

# 6b. RFM for customers who bought in 2023-2025
recent = members[members["order_date"] >= "2023-01-01"]
today = pd.Timestamp("2026-01-01")
rfm = recent.groupby("customer_id").agg(last_order=("order_date", "max"),
                                        frequency=("order_id", "nunique"),
                                        monetary=("net_sales", "sum"))
rfm["recency_days"] = (today - rfm["last_order"]).dt.days
# Scores 1-5 (5 = best). rank() first so equal values do not break qcut.
rfm["R"] = pd.qcut(rfm["recency_days"].rank(method="first"), 5, labels=[5, 4, 3, 2, 1]).astype(int)
rfm["F"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)


def segment(row):
    if row["R"] >= 4 and row["F"] >= 4:
        return "Champions"
    if row["R"] >= 3 and row["F"] >= 3:
        return "Loyal"
    if row["R"] >= 4:
        return "New / Recent"
    if row["F"] >= 3:
        return "At Risk"
    return "Lost"


rfm["segment"] = rfm.apply(segment, axis=1)
seg = rfm.groupby("segment").agg(customers=("monetary", "size"), revenue=("monetary", "sum"),
                                 avg_orders=("frequency", "mean"), avg_recency_days=("recency_days", "mean"))
seg["customer_share"] = seg["customers"] / seg["customers"].sum()
seg["revenue_share"] = seg["revenue"] / seg["revenue"].sum()
seg = seg.sort_values("revenue", ascending=False)
seg.round(3).to_csv("outputs/rfm_segments.csv")
print(seg.round(3))
metrics["rfm"] = seg[["customers", "customer_share", "revenue_share"]].round(4).to_dict(orient="index")

# 6c. Cohort retention: % of customers from each first-purchase year who buy again in later years
first_year = members.groupby("customer_id")["year"].min().rename("cohort")
activity = members[["customer_id", "year"]].drop_duplicates().join(first_year, on="customer_id")
activity["years_after"] = activity["year"] - activity["cohort"]
cohort = activity.pivot_table(index="cohort", columns="years_after", values="customer_id", aggfunc="nunique")
retention = cohort.div(cohort[0], axis=0)
retention.round(3).to_csv("outputs/cohort_retention.csv")
metrics["year1_retention_2016_2019"] = retention.loc[2016:2019, 1].mean()
metrics["year1_retention_2023_2024"] = retention.loc[2023:2024, 1].mean()

# ============================================================
# 7. Promotions (2023-2025) - orders with vs without a promotion
# ============================================================
promo = sales[sales["year"] >= 2023].groupby("promo_type").apply(summary, include_groups=False)
promo = promo.sort_values("net_sales", ascending=False)
promo.round(4).to_csv("outputs/promotions_2023_2025.csv")
print(promo.round(3))
metrics["gm_no_promo"] = promo.loc["No promotion", "gm_pct"]
metrics["gm_mega_sale"] = promo.loc["Mega Sale Day", "gm_pct"]
metrics["discount_mega_sale"] = promo.loc["Mega Sale Day", "discount_rate"]

# ============================================================
# 8. Simple forecast: next year = this year's months x average growth of the last 3 years
# ============================================================
by_month = monthly.pivot(index="month", columns="year", values="net_sales")
yearly = by_month.sum()

# Test the method first: forecast 2025 using data up to 2024, then compare with actual 2025
growth_test = (yearly[2024] / yearly[2021]) ** (1 / 3) - 1
pred_2025 = by_month[2024] * (1 + growth_test)
mape = ((pred_2025 - by_month[2025]).abs() / by_month[2025]).mean()

growth = (yearly[2025] / yearly[2022]) ** (1 / 3) - 1
forecast_2026 = by_month[2025] * (1 + growth)
forecast_2026.round(0).to_csv("outputs/forecast_2026.csv", header=["net_sales_forecast"])
metrics["forecast_growth_rate"] = growth
metrics["forecast_2026_total"] = forecast_2026.sum()
metrics["forecast_mape_2025_test"] = mape

# ============================================================
# 9. Recommendations - simple estimated yearly impact (based on 2025)
# ============================================================
gm25 = k25["gm_pct"]
at_risk = rfm[rfm["segment"] == "At Risk"]
recs = {
    # Bring the discount rate back to the 2022 level
    "R1_discount_back_to_2022": metrics["extra_discount_cost_2025"],
    # Raise price 3% on the best sellers with a margin under 10% (assume the same volume)
    "R2_reprice_low_margin_skus": low["net_sales"].sum() * 0.03,
    # Move 20% of marketplace sales to our own app (saves the marketplace fee)
    "R3_move_20pct_marketplace_to_app": k25["marketplace_fees"] * 0.20,
    # Win back 10% of At Risk customers at their average yearly spend
    "R4_win_back_10pct_at_risk": len(at_risk) * 0.10 * (at_risk["monetary"].mean() / 3) * gm25,
}
recs["total"] = sum(recs.values())
metrics["recommendations"] = recs
metrics["at_risk_customers"] = len(at_risk)

# ============================================================
# 10. Charts
# ============================================================
BLUE, GREY = "#2a78d6", "#c9c8c2"
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "axes.grid.axis": "y", "grid.color": "#e6e5e0", "axes.axisbelow": True})

fig, ax = plt.subplots(1, 2, figsize=(12, 4))
ax[0].bar(kpi.index, kpi["net_sales"] / 1e6, color=GREY)
ax[0].bar(kpi.index, kpi["gross_profit"] / 1e6, color=BLUE)
ax[0].set_title("Net Sales (grey) and Gross Profit (blue), THB million", loc="left")
ax[1].plot(kpi.index, kpi["gm_pct"] * 100, color=BLUE, marker="o", linewidth=2)
ax[1].set_title("Gross margin %", loc="left")
for a in ax:
    a.set_xticks(kpi.index)
fig.suptitle("Margin dipped until 2022, then recovered to a 10-year high in 2025 - Lumora Retail (synthetic data)", x=0.01, ha="left")
fig.tight_layout()
fig.savefig("images/01_sales_and_margin.png", dpi=150)
plt.close()

fig, ax = plt.subplots(figsize=(12, 3.8))
m = sales.set_index("order_date")["net_sales"].resample("MS").sum()
ax.plot(m.index, m.values / 1e6, color=BLUE, linewidth=1.5)
ax.axvspan(pd.Timestamp("2020-03-22"), pd.Timestamp("2020-05-31"), color=GREY, alpha=0.5, label="COVID lockdown")
ax.set_title("Monthly Net Sales (THB million) - December peaks every year", loc="left")
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig("images/02_monthly_sales.png", dpi=150)
plt.close()

fig, ax = plt.subplots(figsize=(8, 4.2))
share = cat25.assign(sales_share=cat25["net_sales"] / cat25["net_sales"].sum(),
                     gp_share=cat25["gross_profit"] / cat25["gross_profit"].sum()).sort_values("sales_share")
y = range(len(share))
ax.barh([i + 0.2 for i in y], share["sales_share"] * 100, height=0.4, color=GREY, label="Share of sales")
ax.barh([i - 0.2 for i in y], share["gp_share"] * 100, height=0.4, color=BLUE, label="Share of gross profit")
ax.set_yticks(list(y), share.index)
ax.grid(axis="x")
ax.grid(axis="y", visible=False)
ax.set_title("2025: share of sales vs share of gross profit (%)", loc="left")
ax.legend(frameon=False, loc="lower right")
fig.tight_layout()
fig.savefig("images/03_category_share.png", dpi=150)
plt.close()

fig, ax = plt.subplots(figsize=(9, 5))
table = retention.drop(columns=0).iloc[:, :5]
ax.imshow(table.values, cmap="Blues", vmin=0, vmax=0.6, aspect="auto")
ax.set_xticks(range(table.shape[1]), [f"Year +{c}" for c in table.columns])
ax.set_yticks(range(len(table)), table.index)
ax.grid(False)
for i in range(table.shape[0]):
    for j in range(table.shape[1]):
        v = table.values[i, j]
        if v == v:  # skip NaN
            ax.text(j, i, f"{v:.0%}", ha="center", va="center", fontsize=8, color="white" if v > 0.35 else "black")
ax.set_title("Cohort retention by first-purchase year", loc="left")
fig.tight_layout()
fig.savefig("images/04_cohort_retention.png", dpi=150)
plt.close()

# ============================================================
# Save key numbers
# ============================================================
def to_number(v):
    if isinstance(v, dict):
        return {k: to_number(x) for k, x in v.items()}
    return round(float(v), 4)


json.dump(to_number(metrics), open("outputs/metrics.json", "w"), indent=1)
print(json.dumps(to_number(metrics), indent=1))
