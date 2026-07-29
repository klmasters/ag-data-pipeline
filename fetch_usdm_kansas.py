import os
from datetime import datetime
import requests
import psycopg2
from psycopg2.extras import execute_values, Json

DB_URL = os.environ["SUPABASE_DB_URL"]

URL = (
    "https://usdmdataservices.unl.edu/api/StateStatistics/"
    "GetDroughtSeverityStatisticsByAreaPercent"
    "?aoi=20&startdate=1/1/2000&enddate=12/31/2026&statisticsType=1"
)


def fetch_data() -> list[dict]:
    resp = requests.get(URL, headers={"Accept": "application/json"})
    resp.raise_for_status()
    return resp.json()


def parse_datetime_to_date(value):
    if not value:
        return None
    return datetime.fromisoformat(value).date()


def load_rows(conn, results: list[dict]) -> None:
    rows = []
    for r in results:
        rows.append((
            parse_datetime_to_date(r.get("mapDate")),
            r.get("stateAbbreviation"),
            r.get("none"),
            r.get("d0"),
            r.get("d1"),
            r.get("d2"),
            r.get("d3"),
            r.get("d4"),
            parse_datetime_to_date(r.get("validStart")),
            parse_datetime_to_date(r.get("validEnd")),
            r.get("statisticFormatID"),
            Json(r),
        ))
    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            insert into ag_data.raw_usdm_kansas
                (map_date, state_abbreviation, none_pct, d0_pct, d1_pct, d2_pct,
                 d3_pct, d4_pct, valid_start, valid_end, statistic_format_id, raw_data)
            values %s
            on conflict (row_key) do update set
                none_pct = excluded.none_pct,
                d0_pct = excluded.d0_pct,
                d1_pct = excluded.d1_pct,
                d2_pct = excluded.d2_pct,
                d3_pct = excluded.d3_pct,
                d4_pct = excluded.d4_pct,
                valid_start = excluded.valid_start,
                valid_end = excluded.valid_end,
                raw_data = excluded.raw_data
            """,
            rows,
        )
    print(f"Loaded {len(rows)} rows")


def main():
    results = fetch_data()
    conn = psycopg2.connect(DB_URL)
    try:
        load_rows(conn, results)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    main()