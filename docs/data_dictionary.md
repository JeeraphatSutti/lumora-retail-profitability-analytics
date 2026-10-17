# Data Dictionary — Lumora Retail (Synthetic Dataset)

> **All data is synthetic**, created by `generate_data.py` (seed 42). Lumora Retail is a fictional company and there is no real customer data.
> Size: 7 tables · ~266,000 orders · ~575,000 order items · 52,000 members · 880 products · 1 Jan 2016 – 31 Dec 2025

## How the tables connect

```
customers 1──* orders *──1 stores
                 │  *──1 promotions
                 1
                 *
            order_items *──1 products
                 1
                 0..1
              returns
```

## 1. `orders` — one row per order

| Column | Type | Description | Problems in raw data |
|---|---|---|---|
| order_id | text (key) | Order ID, numbered in date order (e.g. O0000123) | ~0.4% duplicate rows |
| order_date | date | Date of the order | 4 mixed formats: `YYYY-MM-DD`, `DD/MM/YYYY`, `YYYY-MM-DD HH:MM:SS`, `DD-Mon-YYYY` |
| customer_id | text | Member ID. Empty for walk-in store guests | Missing on some online orders (error) |
| store_id | text | Store. `ONL01` = website/app, `MKT01` = marketplace | |
| channel | text | `Store`, `Website`, `Mobile App`, `Marketplace` | ~1% in upper case (e.g. `STORE`) |
| payment_method | text | Cash, Credit Card, QR PromptPay, Cash on Delivery, Mobile Banking, E-Wallet | |
| promo_id | text | Promotion used (empty = none) | |
| shipping_fee | number | Shipping fee paid by the customer (THB) | |
| shipping_cost | number | Shipping cost paid by the company (THB) | |
| platform_fee | number | Marketplace commission (THB) | |
| order_status | text | `Completed` or `Cancelled` (only Completed is analysed) | |
| customer_type | text | `Member`, `Guest` or `Unknown` — **added during cleaning** | |

## 2. `order_items` — one row per product in an order

| Column | Type | Description | Problems in raw data |
|---|---|---|---|
| order_item_id | text (key) | Line ID | ~0.2% duplicate rows |
| order_id | text | Order ID | |
| product_id | text | Product ID | |
| quantity | integer | Units sold | Some zeros |
| unit_price | number | Selling price per unit before discount (THB) | Some negative values |
| unit_cost | number | Cost per unit (THB) | ~0.3% missing |
| discount_amount | number | Total discount on this line (THB) | |

## 3. `customers` — one row per member

| Column | Type | Description | Problems in raw data |
|---|---|---|---|
| customer_id | text (key) | Member ID | 150 duplicate rows |
| gender | text | F / M / U after cleaning | Mixed labels: F, Female, female, M, Male, male, Unspecified |
| birth_date | date | Date of birth | ~8% missing, some placeholder 1900-01-01 |
| province | text | Home province | ~3% missing |
| region | text | Bangkok, Central, North, Northeast, East, South, Others | |
| signup_date | date | Membership signup date (some members joined in 2014–2015) | 2 mixed formats |
| signup_channel | text | Store, Website, Mobile App | |
| membership_tier | text | Classic, Silver, Gold, Platinum | |
| email | text | Fake email (`@example.com`) | ~6% missing |
| marketing_opt_in | boolean | Agreed to receive marketing | |

## 4. `products` — one row per product

| Column | Type | Description | Problems in raw data |
|---|---|---|---|
| product_id | text (key) | Product ID | |
| product_name | text | Product name (fictional brands) | |
| category | text | Electronics, Home Appliances, Home & Living, Beauty & Personal Care, Fashion, Grocery & FMCG, Sports & Outdoor | ~3% inconsistent spacing or case |
| subcategory | text | e.g. Smartphone, Air Fryer | |
| brand | text | Brand (fictional) | ~2% missing |
| list_price_2016 | number | Starting price in 2016 (yearly prices are in `order_items.unit_price`) | |
| unit_cost_2016 | number | Starting cost in 2016 | |
| is_private_label | boolean | Company's own brand ("Lumora ...") | |

## 5. `stores` — one row per store or online channel

| Column | Type | Description |
|---|---|---|
| store_id | text (key) | S001–S025 = physical stores, ONL01 = website/app, MKT01 = marketplace |
| store_name | text | Store name |
| store_type | text | Flagship, Mall, Community, Online |
| province / region | text | Location (empty for online channels) |
| open_date / close_date | date | Opening and closing dates (S014 closed in June 2021) |
| size_sqm | integer | Sales floor area (m²) |

## 6. `promotions` — one row per campaign

| Column | Type | Description |
|---|---|---|
| promo_id | text (key) | Promotion ID |
| promo_name | text | e.g. "11.11 Online Sale 2025" |
| promo_type | text | Mega Sale Day (9.9 / 10.10 / 11.11 / 12.12), Festival, Seasonal, Payday, Clearance |
| start_date / end_date | date | Campaign dates |
| discount_pct | number | Discount, e.g. 0.25 = 25% |
| channel_scope | text | All, Online or Store |
| min_spend | integer | Minimum spend (THB) |

## 7. `returns` — one row per returned item

| Column | Type | Description | Problems in raw data |
|---|---|---|---|
| return_id | text (key) | Return ID | |
| order_item_id / order_id | text | Returned line and its order | |
| return_date | date | Date of return | |
| return_qty | integer | Units returned | |
| refund_amount | number | Refund (THB) | |
| return_reason | text | Wrong size, Defective, Not as described, Changed mind, Damaged in transit, Late delivery | ~5% missing |
| return_status | text | Approved, Rejected, Pending | |

## Metric definitions (Completed orders only)

| Metric | Formula |
|---|---|
| Net Sales | `unit_price × quantity − discount_amount` |
| COGS | `unit_cost × quantity` |
| Gross Profit | Net Sales − COGS |
| Gross Margin % | Gross Profit ÷ Net Sales |
| AOV (average order value) | Net Sales ÷ number of orders |
| Discount rate | discount_amount ÷ (unit_price × quantity) |
| Next-year retention | % of customers from a first-purchase year who buy again the following year |
