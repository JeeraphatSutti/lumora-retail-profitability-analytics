-- =====================================================================
-- Lumora Retail - business questions in SQL (synthetic data)
-- Tables come from data/clean/*.csv. Tested on DuckDB, also works on PostgreSQL.
-- Run all queries with:  python run_sql.py
-- =====================================================================

-- Q0. Helper view: one row per product sold in a completed order
CREATE OR REPLACE VIEW sales AS
SELECT
    o.order_id,
    CAST(o.order_date AS DATE)                        AS order_date,
    EXTRACT(YEAR FROM CAST(o.order_date AS DATE))     AS year,
    EXTRACT(MONTH FROM CAST(o.order_date AS DATE))    AS month,
    o.customer_id,
    o.customer_type,
    o.channel,
    o.promo_id,
    p.product_name,
    p.category,
    oi.quantity,
    oi.unit_price * oi.quantity                       AS gross_sales,
    oi.discount_amount,
    oi.unit_price * oi.quantity - oi.discount_amount  AS net_sales,
    oi.unit_cost * oi.quantity                        AS cogs
FROM order_items oi
JOIN orders o   ON o.order_id = oi.order_id
JOIN products p ON p.product_id = oi.product_id
WHERE o.order_status = 'Completed';


-- Q1. Yearly KPIs
SELECT
    year,
    ROUND(SUM(net_sales))                                   AS net_sales,
    ROUND(SUM(net_sales - cogs))                            AS gross_profit,
    ROUND(SUM(net_sales - cogs) / SUM(net_sales) * 100, 1)  AS gm_pct,
    COUNT(DISTINCT order_id)                                AS orders,
    ROUND(SUM(net_sales) / COUNT(DISTINCT order_id))        AS aov
FROM sales
GROUP BY year
ORDER BY year;


-- Q2. Year-over-year growth of sales and gross profit
WITH yearly AS (
    SELECT year, SUM(net_sales) AS net_sales, SUM(net_sales - cogs) AS gross_profit
    FROM sales
    GROUP BY year
)
SELECT
    year,
    ROUND(net_sales)                                                     AS net_sales,
    ROUND((net_sales / LAG(net_sales) OVER (ORDER BY year) - 1) * 100, 1)       AS sales_growth_pct,
    ROUND((gross_profit / LAG(gross_profit) OVER (ORDER BY year) - 1) * 100, 1) AS gp_growth_pct
FROM yearly
ORDER BY year;


-- Q3. Seasonality: average sales for each calendar month
WITH monthly AS (
    SELECT year, month, SUM(net_sales) AS net_sales
    FROM sales
    GROUP BY year, month
)
SELECT month, ROUND(AVG(net_sales)) AS avg_monthly_sales
FROM monthly
GROUP BY month
ORDER BY month;


-- Q4. Sales and margin by channel in 2025
SELECT
    channel,
    ROUND(SUM(net_sales))                                   AS net_sales,
    ROUND(SUM(net_sales - cogs) / SUM(net_sales) * 100, 1)  AS gm_pct
FROM sales
WHERE year = 2025
GROUP BY channel
ORDER BY net_sales DESC;


-- Q5. Category: share of sales vs gross margin in 2025
SELECT
    category,
    ROUND(SUM(net_sales))                                                  AS net_sales,
    ROUND(SUM(net_sales) * 100.0 / (SELECT SUM(net_sales) FROM sales WHERE year = 2025), 1) AS sales_share_pct,
    ROUND(SUM(net_sales - cogs) / SUM(net_sales) * 100, 1)                 AS gm_pct
FROM sales
WHERE year = 2025
GROUP BY category
ORDER BY net_sales DESC;


-- Q6. Top 20 products in 2025, flagging best sellers with a margin under 10%
SELECT
    product_name,
    category,
    ROUND(SUM(net_sales))                                   AS net_sales,
    ROUND(SUM(net_sales - cogs) / SUM(net_sales) * 100, 1)  AS gm_pct,
    CASE WHEN SUM(net_sales - cogs) / SUM(net_sales) < 0.10 THEN 'LOW MARGIN' ELSE '' END AS flag
FROM sales
WHERE year = 2025
GROUP BY product_name, category
ORDER BY net_sales DESC
LIMIT 20;


-- Q7. Pareto: how much revenue comes from the top 20% of members?
WITH customer_sales AS (
    SELECT customer_id, SUM(net_sales) AS total_spend
    FROM sales
    WHERE customer_type = 'Member'
    GROUP BY customer_id
),
groups AS (
    SELECT total_spend, NTILE(5) OVER (ORDER BY total_spend DESC) AS spend_group  -- 1 = top 20%
    FROM customer_sales
)
SELECT
    spend_group,
    COUNT(*)                                                         AS customers,
    ROUND(SUM(total_spend) * 100.0 / (SELECT SUM(total_spend) FROM customer_sales), 1) AS revenue_share_pct
FROM groups
GROUP BY spend_group
ORDER BY spend_group;


-- Q8. Promotions 2023-2025: discount rate and margin by promotion type
SELECT
    COALESCE(pr.promo_type, 'No promotion')                          AS promo_type,
    COUNT(DISTINCT s.order_id)                                       AS orders,
    ROUND(SUM(s.net_sales))                                          AS net_sales,
    ROUND(SUM(s.discount_amount) / SUM(s.gross_sales) * 100, 1)      AS discount_pct,
    ROUND(SUM(s.net_sales - s.cogs) / SUM(s.net_sales) * 100, 1)     AS gm_pct
FROM sales s
LEFT JOIN promotions pr ON pr.promo_id = s.promo_id
WHERE s.year >= 2023
GROUP BY 1
ORDER BY net_sales DESC;


-- Q9. Cohort retention: % of each first-purchase year that buys again the next year
WITH first_purchase AS (
    SELECT customer_id, MIN(year) AS cohort
    FROM sales
    WHERE customer_type = 'Member'
    GROUP BY customer_id
),
active AS (
    SELECT DISTINCT s.customer_id, f.cohort, s.year
    FROM sales s
    JOIN first_purchase f ON f.customer_id = s.customer_id
)
SELECT
    cohort,
    COUNT(DISTINCT CASE WHEN year = cohort THEN customer_id END)     AS new_customers,
    ROUND(COUNT(DISTINCT CASE WHEN year = cohort + 1 THEN customer_id END) * 100.0
          / COUNT(DISTINCT CASE WHEN year = cohort THEN customer_id END), 1) AS next_year_retention_pct
FROM active
WHERE cohort < 2025          -- 2025 customers have no "next year" yet
GROUP BY cohort
ORDER BY cohort;
