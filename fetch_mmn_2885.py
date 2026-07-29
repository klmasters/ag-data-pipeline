import os
from datetime import datetime
import requests
import psycopg2
from psycopg2.extras import execute_values, Json

MMN_API_KEY = os.environ["MMN_API_KEY"]
DB_URL = os.environ["SUPABASE_DB_URL"]

REPORT_ID = "2885"  # Kansas Direct Hay Report


def fetch_section(report_id: str, section: str) -> list[dict]:
    url = f"https://marsapi.ams.usda.gov/services/v1.2/reports/{report_id}/{section}"
    resp = requests.get(url, auth=(MMN_API_KEY, ""))
    resp.raise_for_status()
    return resp.json()["results"]


def parse_date(value):
    if not value:
        return None
    return datetime.strptime(value, "%m/%d/%Y").date()


def parse_datetime(value):
    if not value:
        return None
    return datetime.strptime(value, "%m/%d/%Y %H:%M:%S")


def load_header(conn, results: list[dict]) -> None:
    rows = []
    for r in results:
        rows.append((
            r.get("slug_id"),
            r.get("slug_name"),
            r.get("report_title"),
            parse_date(r.get("report_begin_date")),
            parse_date(r.get("report_end_date")),
            parse_datetime(r.get("published_date")),
            r.get("office_name"),
            r.get("office_city"),
            r.get("office_state"),
            Json(r),
        ))
    with conn.cursor() as cur:
        cur.execute("delete from ag_data.raw_mmn_2885_header")
        execute_values(
            cur,
            """
            insert into ag_data.raw_mmn_2885_header
                (slug_id, slug_name, report_title, report_begin_date, report_end_date,
                 published_date, office_name, office_city, office_state, raw_data)
            values %s
            """,
            rows,
        )
    print(f"Loaded {len(rows)} header rows")


def load_details(conn, results: list[dict]) -> None:
    rows = []
    for r in results:
        rows.append((
            parse_date(r.get("report_begin_date")),
            parse_date(r.get("report_end_date")),
            parse_datetime(r.get("published_date")),
            r.get("office_name"),
            r.get("office_state"),
            r.get("office_city"),
            r.get("market_type"),
            r.get("market_type_category"),
            r.get("market_location_name"),
            r.get("market_location_state"),
            r.get("market_location_city"),
            r.get("slug_id"),
            r.get("slug_name"),
            r.get("report_title"),
            r.get("group"),
            r.get("category"),
            r.get("commodity"),
            r.get("conventional"),
            r.get("region"),
            r.get("class"),
            r.get("quality"),
            r.get("sale_Type"),
            r.get("price_Unit"),
            r.get("package"),
            r.get("freight"),
            r.get("quantity"),
            r.get("price_Min"),
            r.get("price_Max"),
            r.get("wtd_Avg_Price"),
            r.get("use"),
            r.get("desc"),
            r.get("crop_Age"),
            Json(r),
        ))
    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            insert into ag_data.raw_mmn_2885_details
                (report_begin_date, report_end_date, published_date, office_name,
                 office_state, office_city, market_type, market_type_category,
                 market_location_name, market_location_state, market_location_city,
                 slug_id, slug_name, report_title, grp, category, commodity,
                 conventional, region, class, quality, sale_type, price_unit,
                 package, freight, quantity, price_min, price_max, wtd_avg_price,
                 use_desc, desc_field, crop_age, raw_data)
            values %s
            on conflict (row_key) do update set
                quantity = excluded.quantity,
                price_min = excluded.price_min,
                price_max = excluded.price_max,
                wtd_avg_price = excluded.wtd_avg_price,
                published_date = excluded.published_date,
                market_type = excluded.market_type,
                market_type_category = excluded.market_type_category,
                market_location_name = excluded.market_location_name,
                market_location_state = excluded.market_location_state,
                market_location_city = excluded.market_location_city,
                grp = excluded.grp,
                category = excluded.category,
                commodity = excluded.commodity,
                raw_data = excluded.raw_data
            """,
            rows,
        )
    print(f"Loaded {len(rows)} detail rows")


def load_receipts(conn, results: list[dict]) -> None:
    rows = [(Json(r),) for r in results]
    with conn.cursor() as cur:
        cur.execute("delete from ag_data.raw_mmn_2885_receipts")
        execute_values(
            cur,
            "insert into ag_data.raw_mmn_2885_receipts (raw_data) values %s",
            rows,
        )
    print(f"Loaded {len(rows)} receipt rows")


def main():
    conn = psycopg2.connect(DB_URL)
    try:
        load_header(conn, fetch_section(REPORT_ID, "Report Header"))
        load_details(conn, fetch_section(REPORT_ID, "Report Details"))
        load_receipts(conn, fetch_section(REPORT_ID, "Report Receipts"))
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    main()