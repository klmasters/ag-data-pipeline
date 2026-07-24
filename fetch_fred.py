
import os
import requests
import psycopg2
from psycopg2.extras import execute_values

FRED_API_KEY = os.environ["FRED_API_KEY"]
DB_URL = os.environ["SUPABASE_DB_URL"]

SERIES_IDS = ["PCU311119311119H", "WPU0131"]


def fetch_observations(series_id: str) -> list[dict]:
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json()["observations"]


def to_rows(series_id: str, observations: list[dict]) -> list[tuple]:
    rows = []
    for obs in observations:
        value = None if obs["value"] == "." else float(obs["value"])
        rows.append((series_id, obs["date"], value))
    return rows


def upsert_rows(rows: list[tuple]) -> None:
    if not rows:
        return
    conn = psycopg2.connect(DB_URL)
    try:
        with conn.cursor() as cur:
            execute_values(
                cur,
                """
                insert into ag_data.raw_fred_observations
                    (series_id, observation_date, value)
                values %s
                on conflict (series_id, observation_date)
                do update set value = excluded.value, ingested_at = now()
                """,
                rows,
            )
        conn.commit()
    finally:
        conn.close()


def main():
    all_rows = []
    for series_id in SERIES_IDS:
        observations = fetch_observations(series_id)
        rows = to_rows(series_id, observations)
        all_rows.extend(rows)
        print(f"{series_id}: fetched {len(rows)} observations")

    upsert_rows(all_rows)
    print(f"Upserted {len(all_rows)} rows total")


if __name__ == "__main__":
    main()