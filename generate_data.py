"""
generate_data.py
================
Creates a SYNTHETIC dataset for a fictional omnichannel retailer, "Lumora Retail".
For a portfolio Sales Analysis project only. This is not real company data.

Output (data/raw/):
    stores.csv, products.csv, customers.csv, promotions.csv,
    orders.csv, order_items.csv, returns.csv

Run:      python generate_data.py
Requires: Python 3.9+, pandas, numpy
Uses a fixed random seed (SEED = 42), so every run produces identical files.
"""
import os
import numpy as np
import pandas as pd

SEED = 42
rng = np.random.default_rng(SEED)
OUT_DIR = os.path.join("data", "raw")
os.makedirs(OUT_DIR, exist_ok=True)

START, END = pd.Timestamp("2016-01-01"), pd.Timestamp("2025-12-31")
DAYS = pd.date_range(START, END, freq="D")
ND = len(DAYS)
D_YEAR, D_MONTH, D_DOM, D_DOW = DAYS.year.values, DAYS.month.values, DAYS.day.values, DAYS.dayofweek.values
YEARS = np.arange(2016, 2026)


def day_idx(ts):
    return (pd.Timestamp(ts) - START).days


# ---------------------------------------------------------------------------
# 1) STORES
# ---------------------------------------------------------------------------
store_rows = [
    # id, name, type, province, region, open_date, close_date, size_sqm
    ("S001", "Lumora Rama 9 Flagship", "Flagship", "Bangkok", "Bangkok", "2010-03-01", None, 4800),
    ("S002", "Lumora Ladprao", "Mall", "Bangkok", "Bangkok", "2012-07-15", None, 2600),
    ("S003", "Lumora Bang Na", "Mall", "Bangkok", "Bangkok", "2013-05-01", None, 2400),
    ("S004", "Lumora Pinklao", "Mall", "Bangkok", "Bangkok", "2014-11-20", None, 2200),
    ("S005", "Lumora Ngamwongwan", "Mall", "Nonthaburi", "Central", "2014-02-10", None, 2100),
    ("S006", "Lumora Rangsit", "Mall", "Pathum Thani", "Central", "2015-04-01", None, 2300),
    ("S007", "Lumora Srinakarin", "Community", "Samut Prakan", "Central", "2015-09-01", None, 1200),
    ("S008", "Lumora Ayutthaya", "Community", "Phra Nakhon Si Ayutthaya", "Central", "2016-06-01", None, 1100),
    ("S009", "Lumora Nakhon Pathom", "Community", "Nakhon Pathom", "Central", "2017-03-15", None, 1000),
    ("S010", "Lumora Chiang Mai Nimman", "Mall", "Chiang Mai", "North", "2013-08-01", None, 2500),
    ("S011", "Lumora Chiang Rai", "Community", "Chiang Rai", "North", "2018-02-01", None, 1100),
    ("S012", "Lumora Phitsanulok", "Community", "Phitsanulok", "North", "2017-10-01", None, 1000),
    ("S013", "Lumora Khon Kaen", "Mall", "Khon Kaen", "Northeast", "2014-06-01", None, 2200),
    ("S014", "Lumora Korat Downtown", "Community", "Nakhon Ratchasima", "Northeast", "2015-01-15", "2021-06-30", 900),
    ("S015", "Lumora Korat Terminal", "Mall", "Nakhon Ratchasima", "Northeast", "2019-11-01", None, 2300),
    ("S016", "Lumora Udon Thani", "Mall", "Udon Thani", "Northeast", "2016-09-01", None, 2000),
    ("S017", "Lumora Ubon", "Community", "Ubon Ratchathani", "Northeast", "2018-07-01", None, 1100),
    ("S018", "Lumora Pattaya", "Mall", "Chon Buri", "East", "2014-12-01", None, 2400),
    ("S019", "Lumora Rayong", "Community", "Rayong", "East", "2017-05-01", None, 1200),
    ("S020", "Lumora Phuket", "Mall", "Phuket", "South", "2015-03-01", None, 2300),
    ("S021", "Lumora Hat Yai", "Mall", "Songkhla", "South", "2016-02-01", None, 2200),
    ("S022", "Lumora Surat Thani", "Community", "Surat Thani", "South", "2019-03-01", None, 1000),
    ("S023", "Lumora Bang Sue", "Community", "Bangkok", "Bangkok", "2022-08-01", None, 1300),
    ("S024", "Lumora Chon Buri City", "Community", "Chon Buri", "East", "2023-04-01", None, 1100),
    ("S025", "Lumora Thonglor", "Community", "Bangkok", "Bangkok", "2024-02-01", None, 900),
    ("ONL01", "Lumora Online (Website & App)", "Online", None, "Online", "2015-06-01", None, None),
    ("MKT01", "Lumora Official Store (Marketplace)", "Online", None, "Online", "2018-03-01", None, None),
]
stores = pd.DataFrame(store_rows, columns=["store_id", "store_name", "store_type", "province", "region",
                                           "open_date", "close_date", "size_sqm"])
phys = stores[stores.store_type != "Online"].reset_index(drop=True)
phys_open = np.array([day_idx(d) for d in phys.open_date])
phys_close = np.array([day_idx(d) if d else 10**6 for d in phys.close_date])
phys_region = phys.region.values

# ---------------------------------------------------------------------------
# 2) PRODUCTS
# ---------------------------------------------------------------------------
CATS = {
    # category: (n_products, median_price, sigma, min, max, base_margin, subcategories, brands)
    "Electronics": (90, 4500, 0.85, 390, 45900, 0.17,
                    ["Smartphone", "Tablet", "Laptop", "Headphones", "Smartwatch", "Power Bank", "Bluetooth Speaker"],
                    ["VoltEdge", "Nexora", "Pixelon", "SonicPeak", "Lumora Tech"]),
    "Home Appliances": (90, 2000, 0.7, 290, 24900, 0.27,
                        ["Air Fryer", "Rice Cooker", "Electric Fan", "Air Purifier", "Vacuum Cleaner", "Microwave", "Water Heater"],
                        ["HomeBright", "Kitcha", "AeroLife", "Lumora Home"]),
    "Home & Living": (160, 450, 0.7, 59, 6900, 0.46,
                      ["Bedding", "Storage Box", "Cookware", "Lamp", "Towel", "Home Decor", "Kitchen Utensil"],
                      ["CasaNest", "Woodly", "Lumora Living", "SoftHaven"]),
    "Beauty & Personal Care": (140, 320, 0.6, 39, 2900, 0.53,
                               ["Sunscreen", "Serum", "Shampoo", "Lipstick", "Body Lotion", "Facial Foam"],
                               ["Glowra", "PureLeaf", "Siamese Botanic", "Lumora Beauty"]),
    "Fashion": (150, 690, 0.6, 99, 5900, 0.56,
                ["T-Shirt", "Jeans", "Dress", "Sneakers", "Bag", "Sleepwear"],
                ["UrbanThread", "Kaya", "StrideOn", "Lumora Basics"]),
    "Grocery & FMCG": (170, 85, 0.6, 12, 650, 0.22,
                       ["Snacks", "Beverage", "Instant Noodle", "Coffee", "Rice", "Cooking Oil", "Household Cleaner"],
                       ["FarmFresh", "DailyJoy", "ThaiTaste", "Lumora Value"]),
    "Sports & Outdoor": (80, 790, 0.8, 99, 12900, 0.42,
                         ["Yoga Mat", "Dumbbell", "Running Shoes", "Water Bottle", "Camping Gear", "Bicycle Accessory"],
                         ["FitCore", "TrailMax", "Lumora Active"]),
}
cat_names = list(CATS.keys())
prod_rows, pid = [], 1
cat_product_idx = {}
for c in cat_names:
    n, med, sig, lo, hi, m, subs, brands = CATS[c]
    price = np.clip(rng.lognormal(np.log(med), sig, n), lo, hi)
    price = np.where(price > 100, np.ceil(price / 10) * 10 - 1, np.round(price))
    margin = np.clip(m + rng.normal(0, 0.05, n), 0.04, 0.75)
    # "Best sellers with low margin": the 3 most popular items in some categories get a very low margin
    if c in ("Electronics", "Home Appliances", "Grocery & FMCG", "Beauty & Personal Care"):
        margin[:3] = rng.uniform(0.04, 0.09, 3)
    idxs = []
    for i in range(n):
        sub = subs[i % len(subs)]
        brand = brands[rng.integers(len(brands))]
        prod_rows.append({
            "product_id": f"P{pid:05d}",
            "product_name": f"{brand} {sub} {chr(65 + rng.integers(26))}{rng.integers(10, 99)}",
            "category": c,
            "subcategory": sub,
            "brand": brand,
            "list_price_2016": float(price[i]),
            "unit_cost_2016": round(float(price[i] * (1 - margin[i])), 2),
            "is_private_label": brand.startswith("Lumora"),
            "popularity_rank": i + 1,
        })
        idxs.append(len(prod_rows) - 1)
        pid += 1
    cat_product_idx[c] = np.array(idxs)
products = pd.DataFrame(prod_rows)
P_PRICE = products.list_price_2016.values
P_COST = products.unit_cost_2016.values

# Prices rise 2%/year. Costs rise 2%/year until 2021, then ~3.5%/year -> margins get squeezed
price_factor = {y: 1.02 ** (y - 2016) for y in YEARS}
cost_factor = {y: 1.02 ** (y - 2016) * (1.015 ** max(0, y - 2021)) for y in YEARS}
# From 2023 the company renegotiates supplier contracts and sells more own-brand products.
# Savings are phased in, so the margin recovers step by step instead of jumping in one year.
COST_SAVINGS = {2022: 0.988, 2023: 0.955, 2024: 0.93, 2025: 0.885}  # 2022: early supplier deals soften the low point
for y, saving in COST_SAVINGS.items():
    cost_factor[y] *= saving

# ---------------------------------------------------------------------------
# 3) PROMOTIONS
# ---------------------------------------------------------------------------
promo_rows = []


def add_promo(name, ptype, start, end, disc, scope, min_spend=0):
    promo_rows.append({"promo_id": f"PR{len(promo_rows) + 1:04d}", "promo_name": name, "promo_type": ptype,
                       "start_date": pd.Timestamp(start).date(), "end_date": pd.Timestamp(end).date(),
                       "discount_pct": round(disc, 3), "channel_scope": scope, "min_spend": min_spend})


for y in YEARS:
    k = y - 2016
    deep = 0.015 * max(0, y - 2022)  # deeper discounts in 2023-2025 (price competition)
    add_promo(f"New Year Sale {y}", "Festival", f"{y}-01-01", f"{y}-01-03", 0.10 + deep, "All")
    add_promo(f"Songkran Sale {y}", "Seasonal", f"{y}-04-10", f"{y}-04-16", 0.08 + deep, "All")
    add_promo(f"Back to School {y}", "Seasonal", f"{y}-05-01", f"{y}-05-15", 0.07, "All")
    add_promo(f"Mid-Year Sale {y}", "Seasonal", f"{y}-06-20", f"{y}-07-10", 0.10 + deep, "All", 500)
    if y >= 2019:
        add_promo(f"9.9 Online Sale {y}", "Mega Sale Day", f"{y}-09-09", f"{y}-09-09", 0.12 + 0.01 * k + deep, "Online")
    if y >= 2021:
        add_promo(f"10.10 Online Sale {y}", "Mega Sale Day", f"{y}-10-10", f"{y}-10-10", 0.12 + 0.01 * k + deep, "Online")
    add_promo(f"11.11 Online Sale {y}", "Mega Sale Day", f"{y}-11-11", f"{y}-11-11", 0.10 + 0.012 * k + deep, "Online")
    if y >= 2017:
        add_promo(f"12.12 Online Sale {y}", "Mega Sale Day", f"{y}-12-12", f"{y}-12-12", 0.10 + 0.011 * k + deep, "Online")
    if y >= 2019:
        bf = pd.Timestamp(f"{y}-11-01") + pd.offsets.WeekOfMonth(week=3, weekday=4)
        add_promo(f"Black Friday {y}", "Festival", bf, bf + pd.Timedelta(days=2), 0.12 + deep, "All")
    add_promo(f"Year-End Sale {y}", "Festival", f"{y}-12-24", f"{y}-12-31", 0.12 + deep, "All", 1000)
    if y >= 2022:
        for mth in range(1, 13):
            if (mth == 12) or (mth == 11):
                continue
            add_promo(f"Payday Sale {y}-{mth:02d}", "Payday", f"{y}-{mth:02d}-25", f"{y}-{mth:02d}-27", 0.08, "Online")
    add_promo(f"Clearance {y}", "Clearance", f"{y}-08-15", f"{y}-08-31", 0.25, "Store")

promotions = pd.DataFrame(promo_rows)
# map each day -> active promotion (per channel scope)
promo_by_day = {s: np.full(ND, -1) for s in ("All", "Online", "Store")}
for i, r in promotions.iterrows():
    a, b = day_idx(r.start_date), day_idx(r.end_date)
    a, b = max(a, 0), min(b, ND - 1)
    if a <= b:
        promo_by_day[r.channel_scope][a:b + 1] = i
PROMO_DISC = promotions.discount_pct.values
PROMO_TYPE = promotions.promo_type.values

# ---------------------------------------------------------------------------
# 4) DAILY DEMAND CURVE (seasonality + festivals + COVID)
# ---------------------------------------------------------------------------
month_f = np.array([0.93, 0.85, 0.95, 1.00, 0.95, 0.98, 1.00, 0.97, 0.94, 1.00, 1.12, 1.32])
dow_f = np.array([0.90, 0.90, 0.92, 0.95, 1.05, 1.22, 1.16])
w = month_f[D_MONTH - 1] * dow_f[D_DOW]
yk = D_YEAR - 2016
mega = np.zeros(ND, dtype=bool)
for (m, d, start_y, base) in [(11, 11, 2016, 1.4), (12, 12, 2017, 1.3), (9, 9, 2019, 1.2), (10, 10, 2021, 1.2)]:
    sel = (D_MONTH == m) & (D_DOM == d) & (D_YEAR >= start_y)
    w[sel] *= base + 0.38 * yk[sel]           # mega sale days get bigger every year
    mega |= sel
w[(D_MONTH == 12) & (D_DOM >= 24)] *= 1.45      # New Year period
w[(D_MONTH == 1) & (D_DOM <= 3)] *= 1.25
w[(D_MONTH == 4) & (D_DOM >= 10) & (D_DOM <= 16)] *= 1.20  # Songkran
w[(D_DOM >= 25) & (D_YEAR >= 2022)] *= 1.15     # payday
lock1 = (DAYS >= "2020-03-22") & (DAYS <= "2020-05-31")   # first COVID lockdown
lock2 = (DAYS >= "2021-07-12") & (DAYS <= "2021-09-30")   # Delta wave
w[lock1] *= 0.70
w[lock2] *= 0.82
CDF = np.concatenate([[0], np.cumsum(w)])
CDF /= CDF[-1]

# ---------------------------------------------------------------------------
# 5) CUSTOMERS
# ---------------------------------------------------------------------------
N_CUST = 52000
prov_region = [("Bangkok", "Bangkok", .34), ("Nonthaburi", "Central", .05), ("Pathum Thani", "Central", .04),
               ("Samut Prakan", "Central", .05), ("Nakhon Pathom", "Central", .02),
               ("Phra Nakhon Si Ayutthaya", "Central", .02), ("Chiang Mai", "North", .06),
               ("Chiang Rai", "North", .02), ("Phitsanulok", "North", .02), ("Khon Kaen", "Northeast", .05),
               ("Nakhon Ratchasima", "Northeast", .05), ("Udon Thani", "Northeast", .03),
               ("Ubon Ratchathani", "Northeast", .02), ("Chon Buri", "East", .06), ("Rayong", "East", .03),
               ("Phuket", "South", .03), ("Songkhla", "South", .04), ("Surat Thani", "South", .02),
               ("Others", "Others", .05)]
pr_p = np.array([x[2] for x in prov_region]); pr_p /= pr_p.sum()
pr_i = rng.choice(len(prov_region), N_CUST, p=pr_p)
c_prov = np.array([prov_region[i][0] for i in pr_i])
c_region = np.array([prov_region[i][1] for i in pr_i])

# Signup year: an existing base from before 2016 + new members every year (COVID boosts online signups)
sy_years = np.arange(2014, 2026)
sy_w = np.array([.085, .085, .075, .075, .075, .080, .100, .090, .085, .080, .080, .080])
sy = rng.choice(sy_years, N_CUST, p=sy_w / sy_w.sum())
signup = pd.to_datetime([f"{y}-01-01" for y in sy]) + pd.to_timedelta(rng.integers(0, 365, N_CUST), unit="D")
signup = signup.where(signup <= END, END - pd.Timedelta(days=1))
signup_d = ((signup - START).days).values

online_aff = rng.normal(0, 1.0, N_CUST) + np.where(sy >= 2020, 0.9, 0.0)
c_signup_channel = np.where(online_aff + rng.normal(0, .5, N_CUST) > 0.6,
                            rng.choice(["Website", "Mobile App"], N_CUST, p=[.4, .6]), "Store")

# Purchase frequency is lognormal, so a small group of customers drives most revenue
propensity = rng.lognormal(0, 0.62, N_CUST)
propensity /= propensity.mean()
# Customers acquired in 2022+ (marketplace / discounts) are deal hunters: more one-time buyers, shorter lifetime
late = sy >= 2022
lifetime_yrs = rng.exponential(3.2, N_CUST) * (0.6 + 0.4 * np.minimum(propensity, 3)) * np.where(late, 0.70, 1.0)
one_timer = rng.random(N_CUST) < np.where(late, 0.34, np.where(sy >= 2020, 0.24, 0.18))
start_d = np.maximum(signup_d, 0)
# Customers who signed up before 2016 start their lifetime on 1 Jan 2016
end_d = np.minimum(start_d + (lifetime_yrs * 365).astype(int), ND - 1)
end_d = np.maximum(end_d, start_d)
active_years = (end_d - start_d + 1) / 365.0
n_orders = 1 + rng.poisson(1.45 * propensity * active_years)
n_orders = np.where(one_timer, 1, n_orders)
n_orders = np.minimum(n_orders, 220)
basket_boost = np.clip(propensity ** 0.25, 0.7, 1.6)  # high-value customers buy slightly bigger baskets

# each member gets a home store in their region
c_home_store = np.empty(N_CUST, dtype=int)
for reg in np.unique(c_region):
    cand = np.where(phys_region == reg)[0]
    if len(cand) == 0:
        cand = np.where(phys_region == "Bangkok")[0]
    sel = np.where(c_region == reg)[0]
    c_home_store[sel] = rng.choice(cand, len(sel))

age = np.clip(rng.normal(36, 11, N_CUST), 16, 78)
birth = pd.to_datetime("2025-12-31") - pd.to_timedelta((age * 365.25).astype(int), unit="D")
gender = rng.choice(["F", "M", "Unspecified"], N_CUST, p=[.58, .38, .04])
tier_score = propensity * rng.lognormal(0, .3, N_CUST)
tier = np.select([tier_score > 3, tier_score > 1.6, tier_score > 0.8], ["Platinum", "Gold", "Silver"], "Classic")

customers = pd.DataFrame({
    "customer_id": [f"C{i + 1:06d}" for i in range(N_CUST)],
    "gender": gender,
    "birth_date": birth.date,
    "province": c_prov,
    "region": c_region,
    "signup_date": signup.date,
    "signup_channel": c_signup_channel,
    "membership_tier": tier,
    "email": [f"user{i + 1:06d}@example.com" for i in range(N_CUST)],
    "marketing_opt_in": rng.random(N_CUST) < 0.55,
})

# ---------------------------------------------------------------------------
# 6) ORDERS - member orders (dates follow the demand curve while the customer is active)
# ---------------------------------------------------------------------------
cust_rep = np.repeat(np.arange(N_CUST), n_orders)
lo, hi = CDF[start_d[cust_rep]], CDF[end_d[cust_rep] + 1]
u = lo + rng.random(len(cust_rep)) * (hi - lo)
o_day = np.clip(np.searchsorted(CDF, u, side="right") - 1, 0, ND - 1)

# guest orders (walk-in, non-member store customers -> customer_id is legitimately empty)
N_GUEST = 68000
g_day = np.clip(np.searchsorted(CDF, rng.random(N_GUEST), side="right") - 1, 0, ND - 1)

all_day = np.concatenate([o_day, g_day])
all_cust = np.concatenate([cust_rep, np.full(N_GUEST, -1)])
N_ORD = len(all_day)
o_year = D_YEAR[all_day]

# Channel: online share grows every year and jumps during COVID and on mega sale days
base_online = dict(zip(YEARS, [.06, .08, .11, .15, .30, .36, .33, .37, .41, .45]))
p = np.array([base_online[y] for y in o_year])
p = np.where(mega[all_day], p + 0.55 * (1 - p), p)
logit = np.log(p / (1 - p)) + np.where(all_cust >= 0, online_aff[np.maximum(all_cust, 0)], -9)
p_on = 1 / (1 + np.exp(-logit))
p_on = np.where((lock1 | lock2)[all_day] & (all_cust >= 0), np.maximum(p_on, 0.85), p_on)
is_online = rng.random(N_ORD) < p_on

mkt_share = dict(zip(YEARS, [0, 0, .12, .20, .28, .33, .36, .40, .43, .46]))
ms = np.array([mkt_share[y] for y in o_year])
mkt_ok = all_day >= day_idx("2018-03-01")
r = rng.random(N_ORD)
channel = np.where(~is_online, "Store",
                   np.where(mkt_ok & (r < ms), "Marketplace",
                            np.where(rng.random(N_ORD) < np.clip(0.25 + 0.06 * (o_year - 2016), 0, .75),
                                     "Mobile App", "Website")))

# Store
store_idx = np.where(all_cust >= 0, c_home_store[np.maximum(all_cust, 0)], rng.integers(0, len(phys), N_ORD))
not_open = (all_day < phys_open[store_idx]) | (all_day > phys_close[store_idx])
store_idx = np.where(not_open, 0, store_idx)  # store not open yet / already closed -> buy at the flagship
store_id = np.where(channel == "Store", phys.store_id.values[store_idx],
                    np.where(channel == "Marketplace", "MKT01", "ONL01"))

# payment
pay = np.empty(N_ORD, dtype=object)
st = channel == "Store"
qr_share = np.clip(0.05 + 0.08 * (o_year - 2016), 0.05, 0.55)
rr = rng.random(N_ORD)
pay[st] = np.where(rr[st] < qr_share[st], "QR PromptPay", np.where(rr[st] < qr_share[st] + 0.35, "Credit Card", "Cash"))
on = ~st
pay[on] = rng.choice(["Credit Card", "Cash on Delivery", "Mobile Banking", "E-Wallet"], on.sum(), p=[.38, .22, .25, .15])

# promotion available on that day
pr_all = promo_by_day["All"][all_day]
pr_on = promo_by_day["Online"][all_day]
pr_st = promo_by_day["Store"][all_day]
promo_i = np.where(st, np.where(pr_st >= 0, pr_st, pr_all), np.where(pr_on >= 0, pr_on, pr_all))
use_p = np.where(promo_i >= 0, np.where(st, 0.55, 0.85), 0)
promo_i = np.where(rng.random(N_ORD) < use_p, promo_i, -1)

order_status = np.where(rng.random(N_ORD) < np.where(st, 0.004, 0.035), "Cancelled", "Completed")

# sort by date, then number the orders
order_sort = np.argsort(all_day * 10 + rng.random(N_ORD), kind="stable")
for arr_name in ["all_day", "all_cust", "channel", "store_id", "pay", "promo_i", "order_status", "o_year"]:
    globals()[arr_name] = globals()[arr_name][order_sort]
order_ids = np.array([f"O{i + 1:07d}" for i in range(N_ORD)])

# ---------------------------------------------------------------------------
# 7) ORDER ITEMS
# ---------------------------------------------------------------------------
cust_boost = np.where(all_cust >= 0, basket_boost[np.maximum(all_cust, 0)], 0.9)
n_items = np.clip(1 + rng.poisson(1.15 * cust_boost), 1, 9)
li_order = np.repeat(np.arange(N_ORD), n_items)
L = len(li_order)
li_year = o_year[li_order]
li_chan = channel[li_order]
li_online = li_chan != "Store"

base_cat_w = np.array([0.045, 0.070, 0.17, 0.19, 0.15, 0.30, 0.075])
W = np.tile(base_cat_w, (L, 1))
# Mix shift: online shoppers buy more Electronics/Appliances every year (high sales, low margin)
W[:, 0] *= np.where(li_online, 1.3 + 0.12 * (li_year - 2016), 1.0)
W[:, 1] *= np.where(li_online, 1.2 + 0.06 * (li_year - 2016), 1.0)
W[:, 5] *= np.where(li_online, 0.65, 1.0)
W /= W.sum(1, keepdims=True)
cat_i = (W.cumsum(1) < rng.random(L)[:, None]).sum(1)
cat_i = np.minimum(cat_i, len(cat_names) - 1)

li_prod = np.empty(L, dtype=int)
for ci, c in enumerate(cat_names):
    sel = np.where(cat_i == ci)[0]
    idx = cat_product_idx[c]
    zipf = 1 / np.arange(1, len(idx) + 1) ** 0.95
    li_prod[sel] = rng.choice(idx, len(sel), p=zipf / zipf.sum())

qty_lam = np.array([0.05, 0.05, 0.25, 0.45, 0.20, 1.6, 0.15])[cat_i]
qty = 1 + rng.poisson(qty_lam)

pf = np.array([price_factor[y] for y in YEARS])[li_year - 2016]
cf = np.array([cost_factor[y] for y in YEARS])[li_year - 2016]
unit_price = np.round(P_PRICE[li_prod] * pf, 2)
unit_cost = np.round(P_COST[li_prod] * cf * rng.normal(1, 0.02, L), 2)

li_promo = promo_i[li_order]
disc_pct = np.where(li_promo >= 0, PROMO_DISC[np.maximum(li_promo, 0)], 0.0)
# small member coupons outside campaigns (used more often after 2022)
coupon = (li_promo < 0) & (rng.random(L) < np.where(li_year >= 2023, 0.10, 0.04))
disc_pct = np.where(coupon, 0.05, disc_pct)
gross = unit_price * qty
discount_amount = np.round(gross * disc_pct, 2)

order_items = pd.DataFrame({
    "order_item_id": [f"OI{i + 1:08d}" for i in range(L)],
    "order_id": order_ids[li_order],
    "product_id": products.product_id.values[li_prod],
    "quantity": qty,
    "unit_price": unit_price,
    "unit_cost": unit_cost,
    "discount_amount": discount_amount,
})

# ---------------------------------------------------------------------------
# 8) SHIPPING / PLATFORM FEE (order level)
# ---------------------------------------------------------------------------
net_line = gross - discount_amount
order_net = np.bincount(li_order, weights=net_line, minlength=N_ORD)
online_o = channel != "Store"
ship_cost = np.where(online_o, np.round(rng.uniform(38, 75, N_ORD) * (1 + 0.03 * (o_year - 2016)), 2), 0)
free_th = np.where(o_year >= 2022, 299, 499)
free_ship = online_o & ((order_net >= free_th) | mega[all_day])
ship_fee = np.where(online_o & ~free_ship, 40.0, 0.0)
fee_rate = dict(zip(YEARS, [0, 0, .04, .05, .055, .065, .08, .095, .105, .115]))
platform_fee = np.where(channel == "Marketplace",
                        np.round(order_net * np.array([fee_rate[y] for y in YEARS])[o_year - 2016], 2), 0)

orders = pd.DataFrame({
    "order_id": order_ids,
    "order_date": DAYS[all_day],
    "customer_id": np.where(all_cust >= 0, np.char.add("C", np.char.zfill((all_cust + 1).astype(str), 6)), None),
    "store_id": store_id,
    "channel": channel,
    "payment_method": pay,
    "promo_id": np.where(promo_i >= 0, promotions.promo_id.values[np.maximum(promo_i, 0)], None),
    "shipping_fee": ship_fee,
    "shipping_cost": ship_cost,
    "platform_fee": platform_fee,
    "order_status": order_status,
})

# ---------------------------------------------------------------------------
# 9) RETURNS
# ---------------------------------------------------------------------------
li_cat_name = np.array(cat_names)[cat_i]
ret_p = np.full(L, 0.025)
ret_p[li_cat_name == "Fashion"] = 0.06
ret_p[(li_cat_name == "Fashion") & li_online] = 0.14
ret_p[(li_cat_name == "Electronics") & li_online] = 0.05
ret_p[li_cat_name == "Grocery & FMCG"] = 0.004
completed_li = order_status[li_order] == "Completed"
is_ret = completed_li & (rng.random(L) < ret_p)
ri = np.where(is_ret)[0]
reasons = np.array(["Wrong size", "Defective", "Not as described", "Changed mind", "Damaged in transit", "Late delivery"])
rprob = np.where((li_cat_name[ri] == "Fashion")[:, None], [.45, .08, .17, .2, .05, .05], [.02, .38, .2, .15, .17, .08])
rprob = rprob / rprob.sum(1, keepdims=True)
r_reason = reasons[(rprob.cumsum(1) < rng.random(len(ri))[:, None]).sum(1).clip(0, 5)]
r_date = DAYS[all_day[li_order[ri]]] + pd.to_timedelta(rng.integers(1, 30, len(ri)), unit="D")
returns = pd.DataFrame({
    "return_id": [f"R{i + 1:07d}" for i in range(len(ri))],
    "order_item_id": order_items.order_item_id.values[ri],
    "order_id": order_items.order_id.values[ri],
    "return_date": r_date.date,
    "return_qty": qty[ri],
    "refund_amount": np.round(net_line[ri], 2),
    "return_reason": r_reason,
    "return_status": rng.choice(["Approved", "Approved", "Approved", "Approved", "Rejected", "Pending"], len(ri)),
})

# ---------------------------------------------------------------------------
# 10) DIRTY DATA - problems added on purpose to practise data cleaning
# ---------------------------------------------------------------------------
# 10.1 orders: mixed date formats
fmt_r = rng.random(len(orders))
od = orders.order_date
orders["order_date"] = np.select(
    [fmt_r < 0.82, fmt_r < 0.93, fmt_r < 0.98],
    [od.dt.strftime("%Y-%m-%d"), od.dt.strftime("%d/%m/%Y"), od.dt.strftime("%Y-%m-%d %H:%M:%S")],
    od.dt.strftime("%d-%b-%Y"))
# 10.2 orders: missing customer_id on some member orders (system error) + inconsistent channel casing
miss = orders.customer_id.notna() & (rng.random(len(orders)) < 0.006)
orders.loc[miss, "customer_id"] = None
ch_mess = rng.random(len(orders)) < 0.01
orders.loc[ch_mess, "channel"] = orders.loc[ch_mess, "channel"].str.upper()
# 10.3 orders: duplicate rows (double export)
dup_o = orders.sample(frac=0.004, random_state=SEED)
orders = pd.concat([orders, dup_o]).sort_values("order_id", kind="stable").reset_index(drop=True)

# 10.4 order_items: negative prices, missing costs, quantity = 0, duplicate rows
neg = rng.random(len(order_items)) < 0.0012
order_items.loc[neg, "unit_price"] *= -1
order_items.loc[rng.random(len(order_items)) < 0.003, "unit_cost"] = np.nan
order_items.loc[rng.random(len(order_items)) < 0.0008, "quantity"] = 0
dup_i = order_items.sample(frac=0.002, random_state=SEED + 1)
order_items = pd.concat([order_items, dup_i]).sort_values("order_item_id", kind="stable").reset_index(drop=True)

# 10.5 customers: inconsistent gender labels, missing/odd birth dates, missing province/email, mixed signup_date formats
g = customers.gender.copy()
gr = rng.random(len(g))
g = np.where((g == "F") & (gr < 0.15), "Female", np.where((g == "F") & (gr < 0.22), "female", g))
g = np.where((g == "M") & (gr < 0.15), "Male", np.where((g == "M") & (gr < 0.22), "male", g))
customers["gender"] = g
customers.loc[rng.random(len(customers)) < 0.08, "birth_date"] = None
odd = rng.random(len(customers)) < 0.002
customers.loc[odd, "birth_date"] = pd.Timestamp("1900-01-01").date()
customers.loc[rng.random(len(customers)) < 0.03, "province"] = None
customers.loc[rng.random(len(customers)) < 0.06, "email"] = None
sd = pd.to_datetime(customers.signup_date)
customers["signup_date"] = np.where(rng.random(len(customers)) < 0.1, sd.dt.strftime("%d/%m/%Y"),
                                    sd.dt.strftime("%Y-%m-%d"))
customers = pd.concat([customers, customers.sample(n=150, random_state=SEED)]).reset_index(drop=True)

# 10.6 products: inconsistent category names + missing brand
pm = rng.random(len(products))
products.loc[pm < 0.02, "category"] = products.loc[pm < 0.02, "category"].str.upper()
products.loc[(pm >= 0.02) & (pm < 0.04), "category"] = " " + products.loc[(pm >= 0.02) & (pm < 0.04), "category"] + " "
products.loc[rng.random(len(products)) < 0.02, "brand"] = None
products = products.drop(columns=["popularity_rank"])

# 10.7 returns: missing reason
returns.loc[rng.random(len(returns)) < 0.05, "return_reason"] = None

# ---------------------------------------------------------------------------
# SAVE
# ---------------------------------------------------------------------------
for name, df in [("stores", stores), ("products", products), ("customers", customers),
                 ("promotions", promotions), ("orders", orders), ("order_items", order_items),
                 ("returns", returns)]:
    df.to_csv(os.path.join(OUT_DIR, f"{name}.csv"), index=False)
    print(f"{name:12s} {len(df):>9,d} rows")
print("Done. SYNTHETIC DATA - for portfolio/education use only.")
