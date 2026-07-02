import csv
import json
import os
import ssl
import sqlite3
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import certifi


url = "https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/O-A0001-001"
CSV_PATH = Path("weather.csv")
DB_PATH = Path("weather.db")
TABLE_NAME = "weather"


def load_env(path=".env"):
    env_path = Path(path)
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def fetch_weather(token):
    query = urlencode(
        {
            "Authorization": token,
            "downloadType": "WEB",
            "format": "JSON",
        }
    )
    request = Request(f"{url}?{query}", method="GET")
    context = ssl.create_default_context(cafile=certifi.where())
    context.verify_flags &= ~ssl.VERIFY_X509_STRICT
    with urlopen(request, timeout=30, context=context) as response:
        return json.loads(response.read().decode("utf-8"))


def flatten(value, prefix=""):
    if isinstance(value, dict):
        flattened = {}
        for key, item in value.items():
            name = f"{prefix}_{key}" if prefix else str(key)
            flattened.update(flatten(item, name))
        return flattened

    if isinstance(value, list):
        flattened = {}
        for index, item in enumerate(value, start=1):
            if isinstance(item, dict):
                name_key = next(
                    (
                        key
                        for key in ("elementName", "CoordinateName")
                        if key in item and item[key]
                    ),
                    None,
                )
                item_name = str(item[name_key]) if name_key else str(index)
                for key, item_value in item.items():
                    if key == name_key:
                        continue
                    flattened.update(flatten(item_value, f"{prefix}_{item_name}_{key}"))
            else:
                flattened.update(flatten(item, f"{prefix}_{index}"))
        return flattened

    return {prefix: value}


def get_station_rows(payload):
    stations = (
        payload.get("cwaopendata", {})
        .get("dataset", {})
        .get("Station", [])
    )
    if isinstance(stations, dict):
        stations = [stations]
    return [flatten(station) for station in stations]


def write_csv(rows, path):
    columns = sorted({column for row in rows for column in row})
    with path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    return columns


def sqlite_type(values):
    numeric_values = [value for value in values if value not in (None, "")]
    if not numeric_values:
        return "TEXT"

    for value in numeric_values:
        if isinstance(value, bool):
            return "TEXT"
        try:
            float(value)
        except (TypeError, ValueError):
            return "TEXT"
    return "REAL"


def write_sqlite(rows, columns, path):
    if path.exists():
        path.unlink()

    column_types = {
        column: sqlite_type(row.get(column) for row in rows)
        for column in columns
    }
    column_defs = ", ".join(
        f'"{column}" {column_types[column]}' for column in columns
    )
    placeholders = ", ".join("?" for _ in columns)
    quoted_columns = ", ".join(f'"{column}"' for column in columns)

    with sqlite3.connect(path) as connection:
        connection.execute(f'CREATE TABLE "{TABLE_NAME}" ({column_defs})')
        connection.executemany(
            f'INSERT INTO "{TABLE_NAME}" ({quoted_columns}) VALUES ({placeholders})',
            [[row.get(column) for column in columns] for row in rows],
        )


def main():
    load_env()
    token = os.environ.get("CWA_TOKEN")
    if not token:
        raise SystemExit("CWA_TOKEN is missing. Add it to .env first.")

    payload = fetch_weather(token)
    rows = get_station_rows(payload)
    if not rows:
        raise SystemExit("No station rows found in the API response.")

    columns = write_csv(rows, CSV_PATH)
    write_sqlite(rows, columns, DB_PATH)
    print(f"Wrote {len(rows)} rows to {CSV_PATH} and {DB_PATH}.")


if __name__ == "__main__":
    main()
