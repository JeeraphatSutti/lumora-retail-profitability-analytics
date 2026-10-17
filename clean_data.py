"""
clean_data.py - Step 1: clean the raw data
Reads data/raw/*.csv, fixes data quality problems, saves data/clean/*.csv
and writes a short cleaning log to reports/cleaning_log.csv.
(Synthetic data - Lumora Retail is a fictional company.)
"""
import os
import pandas as pd

os.makedirs("data/clean", exist_ok=True)
os.makedirs("reports", exist_ok=True)

log = []  # one row per fix, so we can show what was cleaned


def add_log(table, issue, rows):
    log.append({"table": table, "issue": issue, "rows_affected": int(rows)})
    print(f"{table:12s} {issue:45s} {rows:>7,}")


def read(name):
    return pd.read_csv(f"data/raw/{name}.csv")


# ---------- products ----------
products = read("products")
clean_cat = products["category"].str.strip().str.title().str.replace("Fmcg", "FMCG")
add_log("products", "inconsistent category names", (products["category"] != clean_cat).sum())
products["category"] = clean_cat
add_log("products", "missing brand", products["brand"].isna().sum())
products["brand"] = products["brand"].fillna("Unknown")

# ---------- customers ----------
customers = read("customers")
add_log("customers", "duplicate rows", customers.duplicated().sum())
customers = customers.drop_duplicates()

gender_map = {"F": "F", "Female": "F", "female": "F", "M": "M", "Male": "M", "male": "M", "Unspecified": "U"}
add_log("customers", "inconsistent gender labels", (~customers["gender"].isin(["F", "M", "Unspecified"])).sum())
customers["gender"] = customers["gender"].map(gender_map).fillna("U")

# signup_date has two formats: YYYY-MM-DD and DD/MM/YYYY
iso = pd.to_datetime(customers["signup_date"], format="%Y-%m-%d", errors="coerce")
dmy = pd.to_datetime(customers["signup_date"], format="%d/%m/%Y", errors="coerce")
customers["signup_date"] = iso.fillna(dmy)

customers["birth_date"] = pd.to_datetime(customers["birth_date"], errors="coerce")
bad_birth = customers["birth_date"].dt.year < 1930          # placeholder value 1900-01-01
customers.loc[bad_birth, "birth_date"] = pd.NaT
add_log("customers", "missing or invalid birth_date", customers["birth_date"].isna().sum())

add_log("customers", "missing province", customers["province"].isna().sum())
customers["province"] = customers["province"].fillna("Unknown")

# ---------- orders ----------
orders = read("orders")
add_log("orders", "duplicate rows", orders.duplicated().sum())
orders = orders.drop_duplicates()

# order_date has 4 formats. Parse one format at a time.
# (pd.to_datetime(format="mixed", dayfirst=True) silently swaps day and month on some rows.)
add_log("orders", "order_date not in YYYY-MM-DD format", (~orders["order_date"].str.match(r"^\d{4}-\d{2}-\d{2}$")).sum())
dates = pd.Series(pd.NaT, index=orders.index)
for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S", "%d-%b-%Y"]:
    missing = dates.isna()
    dates[missing] = pd.to_datetime(orders.loc[missing, "order_date"], format=fmt, errors="coerce")
assert dates.notna().all(), "some dates could not be parsed"
orders["order_date"] = dates.dt.normalize()

add_log("orders", "inconsistent channel casing", (orders["channel"] != orders["channel"].str.title()).sum())
orders["channel"] = orders["channel"].str.title()

# Empty customer_id: in a store it is a walk-in guest (not an error); online it is a data error.
no_id = orders["customer_id"].isna()
add_log("orders", "missing customer_id on online orders", (no_id & (orders["channel"] != "Store")).sum())
orders["customer_type"] = "Member"
orders.loc[no_id & (orders["channel"] == "Store"), "customer_type"] = "Guest"
orders.loc[no_id & (orders["channel"] != "Store"), "customer_type"] = "Unknown"

# ---------- order_items ----------
items = read("order_items")
add_log("order_items", "duplicate rows", items.duplicated().sum())
items = items.drop_duplicates()

add_log("order_items", "negative unit_price", (items["unit_price"] < 0).sum())
items["unit_price"] = items["unit_price"].abs()

add_log("order_items", "quantity = 0", (items["quantity"] == 0).sum())
items = items[items["quantity"] > 0]

# Fill a missing cost with the median cost of the same product
add_log("order_items", "missing unit_cost", items["unit_cost"].isna().sum())
items["unit_cost"] = items["unit_cost"].fillna(items.groupby("product_id")["unit_cost"].transform("median"))

# ---------- returns ----------
returns = read("returns")
add_log("returns", "missing return_reason", returns["return_reason"].isna().sum())
returns["return_reason"] = returns["return_reason"].fillna("Not specified")

# ---------- save ----------
tables = {"products": products, "customers": customers, "orders": orders, "order_items": items,
          "returns": returns, "stores": read("stores"), "promotions": read("promotions")}
for name, df in tables.items():
    df.to_csv(f"data/clean/{name}.csv", index=False)
pd.DataFrame(log).to_csv("reports/cleaning_log.csv", index=False)
print("Saved clean files to data/clean/")
