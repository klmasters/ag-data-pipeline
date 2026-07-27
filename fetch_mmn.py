import os
from datetime import datetime
import requests
import psycopg2
from psycopg2.extras import execute_values, Json

MMN_API_KEY = os.environ["MMN_API_KEY"]
DB_URL = os.environ["SUPABASE_DB_URL"]

REPORT_ID = "1895"  # Kansas Weekly Cattle Auction Summary


def fetch_report(report_id: str) -> list[dict]:
    url = f"https://marsapi.ams.usda.gov/services/v1.2/reports/{report_id}"
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


def to_rows(report_id: str, results: list[dict]) -> list[tuple]:
    rows = []
    for r in results:
        rows.append((
            report_id,
            r.get("slug_id"),
            r.get("slug_name"),
            r.get("report_title"),
            parse_date(r.get("report_begin_date")),
            parse_date(r.get("report_end_date")),
            parse_date(r.get("report_date")),
            parse_datetime(r.get("published_date")),
            r.get("final_ind"),
            r.get("group"),
            r.get("category"),
            r.get("commodity"),
            r.get("class"),
            r.get("frame"),
            r.get("age"),
            r.get("dressing"),
            r.get("muscle_grade"),
            r.get("yield_grade"),
            r.get("quality_grade_name"),
            r.get("pregnancy_stage"),
            r.get("lot_desc"),
            r.get("weight_collect"),
            r.get("weight_break_low"),
            r.get("weight_break_high"),
            r.get("avg_weight"),
            r.get("avg_weight_min"),
            r.get("avg_weight_max"),
            r.get("avg_price"),
            r.get("avg_price_min"),
            r.get("avg_price_max"),
            r.get("price_unit"),
            r.get("freight"),
            r.get("head_count"),
            r.get("receipts"),
            r.get("receipts_week_ago"),
            r.get("receipts_year_ago"),
            r.get("offspring_weight_est"),
            r.get("market_type"),
            r.get("market_type_category"),
            r.get("market_location_name"),
            r.get("market_location_city"),
            r.get("market_location_state"),
            r.get("office_code"),
            r.get("office_name"),
            r.get("office_city"),
            r.get("office_state"),
            r.get("comments_commodity"),
            r.get("report_narrative"),
            Json(r),
        ))
    return rows


def load_rows(report_id: str, rows: list[tuple]) -> None:
    if not rows:
        return
    conn = psycopg2.connect(DB_URL)
    try:
        with conn.cursor() as cur:
            execute_values(
                cur,
                """
                insert into ag_data.raw_mmn_1895
                    (report_id, slug_id, slug_name, report_title, report_begin_date,
                     report_end_date, report_date, published_date, final_ind, "group",
                     category, commodity, class, frame, age, dressing, muscle_grade,
                     yield_grade, quality_grade_name, pregnancy_stage, lot_desc,
                     weight_collect, weight_break_low, weight_break_high, avg_weight,
                     avg_weight_min, avg_weight_max, avg_price, avg_price_min, avg_price_max,
                     price_unit, freight, head_count, receipts, receipts_week_ago,
                     receipts_year_ago, offspring_weight_est, market_type,
                     market_type_category, market_location_name, market_location_city,
                     market_location_state, office_code, office_name, office_city,
                     office_state, comments_commodity, report_narrative, raw_data)
                values %s
                on conflict (row_key) do update set
                    slug_id = excluded.slug_id,
                    slug_name = excluded.slug_name,
                    report_title = excluded.report_title,
                    published_date = excluded.published_date,
                    final_ind = excluded.final_ind,
                    "group" = excluded."group",
                    category = excluded.category,
                    dressing = excluded.dressing,
                    yield_grade = excluded.yield_grade,
                    quality_grade_name = excluded.quality_grade_name,
                    weight_collect = excluded.weight_collect,
                    weight_break_high = excluded.weight_break_high,
                    avg_weight_min = excluded.avg_weight_min,
                    avg_weight_max = excluded.avg_weight_max,
                    avg_price_min = excluded.avg_price_min,
                    avg_price_max = excluded.avg_price_max,
                    price_unit = excluded.price_unit,
                    freight = excluded.freight,
                    receipts = excluded.receipts,
                    receipts_week_ago = excluded.receipts_week_ago,
                    receipts_year_ago = excluded.receipts_year_ago,
                    offspring_weight_est = excluded.offspring_weight_est,
                    market_type = excluded.market_type,
                    market_type_category = excluded.market_type_category,
                    market_location_name = excluded.market_location_name,
                    market_location_city = excluded.market_location_city,
                    market_location_state = excluded.market_location_state,
                    office_code = excluded.office_code,
                    office_name = excluded.office_name,
                    office_city = excluded.office_city,
                    office_state = excluded.office_state,
                    comments_commodity = excluded.comments_commodity,
                    report_narrative = excluded.report_narrative,
                    raw_data = excluded.raw_data
                """,
                rows,
            )
        conn.commit()
    finally:
        conn.close()


def main():
    results = fetch_report(REPORT_ID)
    rows = to_rows(REPORT_ID, results)
    load_rows(REPORT_ID, rows)
    print(f"Loaded {len(rows)} rows for report {REPORT_ID}")


if __name__ == "__main__":
    main()