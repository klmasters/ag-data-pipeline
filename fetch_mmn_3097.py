import os
from datetime import datetime
import requests
import psycopg2
from psycopg2.extras import execute_values, Json

MMN_API_KEY = os.environ["MMN_API_KEY"]
DB_URL = os.environ["SUPABASE_DB_URL"]

REPORT_ID = "3097"  # Kansas Direct Cattle Report


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
            parse_date(r.get("report_date")),
            parse_datetime(r.get("published_date") or r.get("published_Date")),
            r.get("final_ind"),
            r.get("report_narrative"),
            r.get("special_notes"),
            r.get("office_name"),
            r.get("office_code"),
            r.get("office_city"),
            r.get("office_state"),
            r.get("market_location_name"),
            r.get("market_location_city"),
            r.get("market_location_state"),
            r.get("geographical_indicator"),
            r.get("geographical_location"),
            Json(r),
        ))
    with conn.cursor() as cur:
        cur.execute("delete from ag_data.raw_mmn_3097_header")
        execute_values(
            cur,
            """
            insert into ag_data.raw_mmn_3097_header
                (slug_id, slug_name, report_title, report_begin_date, report_end_date,
                 report_date, published_date, final_ind, report_narrative, special_notes,
                 office_name, office_code, office_city, office_state, market_location_name,
                 market_location_city, market_location_state, geographical_indicator,
                 geographical_location, raw_data)
            values %s
            """,
            rows,
        )
    print(f"Loaded {len(rows)} header rows")


def load_details(conn, results: list[dict]) -> None:
    rows = []
    for r in results:
        rows.append((
            r.get("category"),
            r.get("office_name"),
            r.get("office_code"),
            r.get("office_city"),
            r.get("office_state"),
            parse_date(r.get("report_begin_date")),
            parse_date(r.get("report_end_date")),
            parse_datetime(r.get("published_date") or r.get("published_Date")),
            r.get("market_location_name"),
            r.get("market_location_city"),
            r.get("market_location_state"),
            r.get("geographical_indicator"),
            r.get("geographical_location"),
            r.get("commodity"),
            r.get("market_type"),
            r.get("slug_id"),
            r.get("slug_name"),
            r.get("report_title"),
            r.get("final_ind"),
            parse_date(r.get("report_date")),
            r.get("grp"),
            r.get("class"),
            r.get("purchase_type"),
            r.get("weight_Collect") or r.get("weight_collect"),
            r.get("freight"),
            r.get("price_unit"),
            r.get("frame"),
            r.get("muscle_grade"),
            r.get("quality_grade_name"),
            r.get("yield_grade"),
            r.get("dressing"),
            r.get("age"),
            r.get("pregnancy"),
            r.get("offspring_weight_estimate"),
            r.get("lot_desc"),
            r.get("current"),
            r.get("basis_futures_month"),
            r.get("delivery_month"),
            r.get("head_count"),
            r.get("weight_min"),
            r.get("weight_max"),
            r.get("wtd_avg_wt"),
            r.get("price_min"),
            r.get("price_max"),
            r.get("wtd_avg_price"),
            r.get("weight_break_low"),
            r.get("weight_break_high"),
            Json(r),
        ))
    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            insert into ag_data.raw_mmn_3097_details
                (category, office_name, office_code, office_city, office_state,
                 report_begin_date, report_end_date, published_date, market_location_name,
                 market_location_city, market_location_state, geographical_indicator,
                 geographical_location, commodity, market_type, slug_id, slug_name,
                 report_title, final_ind, report_date, grp, class, purchase_type,
                 weight_collect, freight, price_unit, frame, muscle_grade,
                 quality_grade_name, yield_grade, dressing, age, pregnancy,
                 offspring_weight_estimate, lot_desc, current_ind, basis_futures_month,
                 delivery_month, head_count, weight_min, weight_max, wtd_avg_wt,
                 price_min, price_max, wtd_avg_price, weight_break_low, weight_break_high,
                 raw_data)
            values %s
            on conflict (row_key) do update set
                head_count = excluded.head_count,
                weight_min = excluded.weight_min,
                weight_max = excluded.weight_max,
                wtd_avg_wt = excluded.wtd_avg_wt,
                price_min = excluded.price_min,
                price_max = excluded.price_max,
                wtd_avg_price = excluded.wtd_avg_price,
                published_date = excluded.published_date,
                final_ind = excluded.final_ind,
                current_ind = excluded.current_ind,
                basis_futures_month = excluded.basis_futures_month,
                geographical_indicator = excluded.geographical_indicator,
                geographical_location = excluded.geographical_location,
                raw_data = excluded.raw_data
            """,
            rows,
        )
    print(f"Loaded {len(rows)} detail rows")


def load_receipts(conn, results: list[dict]) -> None:
    rows = [(Json(r),) for r in results]
    with conn.cursor() as cur:
        cur.execute("delete from ag_data.raw_mmn_3097_receipts")
        execute_values(
            cur,
            "insert into ag_data.raw_mmn_3097_receipts (raw_data) values %s",
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