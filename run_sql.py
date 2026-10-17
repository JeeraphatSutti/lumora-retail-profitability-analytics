"""
run_sql.py - load data/clean/*.csv into DuckDB and run every query in sql/analysis_queries.sql
"""
import duckdb

con = duckdb.connect()
for table in ["orders", "order_items", "products", "customers", "returns", "promotions", "stores"]:
    con.execute(f"CREATE TABLE {table} AS SELECT * FROM read_csv_auto('data/clean/{table}.csv')")

sql = open("sql/analysis_queries.sql").read()
for query in sql.split(";"):
    lines = query.strip().splitlines()
    title = next((line for line in lines if line.startswith("-- Q")), None)
    if title is None:
        continue
    print("\n" + title)
    result = con.execute(query)
    if result.description:  # SELECT queries return rows; CREATE VIEW does not
        print(result.df().to_string(index=False))
