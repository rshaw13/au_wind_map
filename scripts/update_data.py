import csv
import io
import zipfile
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup


# ---------------- CONFIG ----------------
SCADA_INDEX_URL = "https://www.nemweb.com.au/REPORTS/CURRENT/Dispatch_SCADA/"
DISPATCHIS_INDEX_URL = "https://www.nemweb.com.au/REPORTS/CURRENT/DispatchIS_Reports/"

CAPACITY_FILE = "Full NEM Plant Registration.csv"
COORDS_FILE = "Clean Coords.csv"

OUTPUT_FILE = "data/latest_wind_data.csv"
HISTORY_FILE = "data/wind_history_24h.csv"
PRICE_OUTPUT_FILE = "data/latest_regional_price_data.csv"
HISTORY_HOURS = 24
# ----------------------------------------


def get_latest_zip_url(index_url: str, filename_contains: str) -> str:
    """Return the latest matching zip from a NEMWEB directory listing."""
    r = requests.get(index_url, timeout=30)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    zip_links = [
        a["href"]
        for a in soup.find_all("a", href=True)
        if filename_contains in a["href"] and a["href"].endswith(".zip")
    ]

    if not zip_links:
        raise RuntimeError(f"No {filename_contains} zip files found at {index_url}")

    zip_links.sort(reverse=True)
    return urljoin(index_url, zip_links[0])


def get_latest_scada_url() -> str:
    return get_latest_zip_url(SCADA_INDEX_URL, "PUBLIC_DISPATCHSCADA")


def get_latest_dispatchis_url() -> str:
    return get_latest_zip_url(DISPATCHIS_INDEX_URL, "PUBLIC_DISPATCHIS")


def get_latest_scada(zip_url: str) -> pd.DataFrame:
    r = requests.get(zip_url, timeout=30)
    r.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        csv_name = z.namelist()[0]
        with z.open(csv_name) as f:
            df = pd.read_csv(f)

    df.columns = df.iloc[0]
    df = df.iloc[1:-1][["SETTLEMENTDATE", "DUID", "SCADAVALUE"]].copy()
    df["SETTLEMENTDATE"] = pd.to_datetime(df["SETTLEMENTDATE"], errors="coerce")
    df["SCADAVALUE"] = pd.to_numeric(df["SCADAVALUE"], errors="coerce").round(2)
    df = df.dropna(subset=["SETTLEMENTDATE", "DUID", "SCADAVALUE"])
    return df


def read_mms_zip_tables(zip_url: str) -> dict[str, pd.DataFrame]:
    """Read an AEMO MMS-format zip and return each data table as a dataframe.

    DispatchIS files contain I rows with table headers and D rows with data.
    This parser groups D rows under the matching I header.
    """
    r = requests.get(zip_url, timeout=30)
    r.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        csv_name = z.namelist()[0]
        with z.open(csv_name) as f:
            text = io.TextIOWrapper(f, encoding="utf-8-sig", newline="")
            rows = list(csv.reader(text))

    headers: dict[tuple[str, ...], list[str]] = {}
    data_rows: dict[tuple[str, ...], list[list[str]]] = {}

    for row in rows:
        if len(row) < 5:
            continue

        row_type = row[0]
        table_key = tuple(row[1:4])

        if row_type == "I":
            headers[table_key] = row[4:]
            data_rows.setdefault(table_key, [])
        elif row_type == "D" and table_key in headers:
            data_rows.setdefault(table_key, []).append(row[4:])

    tables: dict[str, pd.DataFrame] = {}
    for key, header in headers.items():
        rows_for_table = data_rows.get(key, [])
        if not rows_for_table:
            continue

        width = len(header)
        normalised_rows = []
        for row in rows_for_table:
            if len(row) < width:
                row = row + [None] * (width - len(row))
            normalised_rows.append(row[:width])

        tables["|".join(key)] = pd.DataFrame(normalised_rows, columns=header)

    return tables


def find_table(tables: dict[str, pd.DataFrame], required_cols: list[str]) -> pd.DataFrame:
    required = set(required_cols)
    for _, table in tables.items():
        if required.issubset(set(table.columns)):
            return table.copy()
    available = {name: list(df.columns)[:15] for name, df in tables.items()}
    raise RuntimeError(f"Could not find table with columns {required_cols}. Available table starts: {available}")


def get_latest_regional_price_data(dispatchis_url: str) -> pd.DataFrame:
    """Fetch latest regional spot price from DispatchIS_Reports."""
    tables = read_mms_zip_tables(dispatchis_url)
    price = find_table(tables, ["SETTLEMENTDATE", "REGIONID", "RRP"])

    price = price[["SETTLEMENTDATE", "REGIONID", "RRP"]].copy()
    price["SETTLEMENTDATE"] = pd.to_datetime(price["SETTLEMENTDATE"], errors="coerce")
    price["REGIONID"] = price["REGIONID"].astype(str).str.strip()
    price["RRP"] = pd.to_numeric(price["RRP"], errors="coerce")
    price = price.dropna(subset=["SETTLEMENTDATE", "REGIONID"])

    latest_interval = price["SETTLEMENTDATE"].max()
    price = price[price["SETTLEMENTDATE"] == latest_interval].copy()
    price["timestamp_utc"] = datetime.utcnow().isoformat()
    return price.sort_values("REGIONID")


def build_wind_dataset(scada: pd.DataFrame, regional_price: pd.DataFrame | None = None) -> pd.DataFrame:
    capacity = pd.read_csv(CAPACITY_FILE)
    capacity.columns = capacity.columns.str.strip()

    wind = capacity[
        capacity["Fuel Source - Primary"].astype(str).str.contains("Wind", case=False, na=False)
    ].copy()

    keep_cols = [
        "Participant",
        "Station Name",
        "Fuel Source - Primary",
        "DUID",
        "Max Cap generation (MW)",
    ]
    if "Region" in wind.columns:
        keep_cols.append("Region")

    wind = wind[keep_cols].copy()
    wind = wind.rename(columns={"Max Cap generation (MW)": "MAX_CAP"})
    wind["MAX_CAP"] = pd.to_numeric(wind["MAX_CAP"], errors="coerce")

    merged = scada.merge(wind, on="DUID", how="inner")

    # If the registration CSV did not include region, keep the app alive but price will be blank.
    if "Region" not in merged.columns:
        merged["Region"] = pd.NA

    merged["utilisation_pct"] = (
        merged["SCADAVALUE"] / merged["MAX_CAP"] * 100
    ).replace([float("inf"), -float("inf")], 0).fillna(0).round(2)

    coords = pd.read_csv(COORDS_FILE)
    coords.columns = coords.columns.str.strip()
    merged = merged.merge(coords, left_on="Station Name", right_on="Plant", how="inner")

    if regional_price is not None and not regional_price.empty:
        price_cols = regional_price[["REGIONID", "RRP"]].copy()
        price_cols = price_cols.rename(columns={"REGIONID": "Region", "RRP": "REGION_RRP"})
        merged = merged.merge(price_cols, on="Region", how="left")
    else:
        merged["REGION_RRP"] = pd.NA

    merged["asset_label"] = merged["Station Name"] + " (" + merged["DUID"] + ")"
    merged["timestamp_utc"] = datetime.utcnow().isoformat()

    preferred = [
        "SETTLEMENTDATE",
        "timestamp_utc",
        "asset_label",
        "Station Name",
        "DUID",
        "Region",
        "Participant",
        "Fuel Source - Primary",
        "SCADAVALUE",
        "MAX_CAP",
        "utilisation_pct",
        "REGION_RRP",
        "Latitude",
        "Longitude",
    ]
    other_cols = [c for c in merged.columns if c not in preferred]
    return merged[preferred + other_cols]


def update_24h_history(latest: pd.DataFrame) -> pd.DataFrame:
    """Append latest wind output to a rolling 24-hour history file."""
    history_path = Path(HISTORY_FILE)

    latest = latest.copy()
    latest["SETTLEMENTDATE"] = pd.to_datetime(latest["SETTLEMENTDATE"], errors="coerce")
    latest = latest.dropna(subset=["SETTLEMENTDATE", "DUID"])

    if history_path.exists():
        existing = pd.read_csv(history_path)
        existing["SETTLEMENTDATE"] = pd.to_datetime(existing["SETTLEMENTDATE"], errors="coerce")
        existing = existing.dropna(subset=["SETTLEMENTDATE", "DUID"])
        history = pd.concat([existing, latest], ignore_index=True)
    else:
        history = latest

    history = history.drop_duplicates(subset=["DUID", "SETTLEMENTDATE"], keep="last")

    newest_time = history["SETTLEMENTDATE"].max()
    cutoff = newest_time - pd.Timedelta(hours=HISTORY_HOURS)
    history = history[history["SETTLEMENTDATE"] >= cutoff].copy()

    history = history.sort_values(["DUID", "SETTLEMENTDATE"])
    history.to_csv(history_path, index=False)
    return history


def main():
    Path("data").mkdir(parents=True, exist_ok=True)

    print("Fetching latest DispatchIS regional price data...")
    dispatchis_url = get_latest_dispatchis_url()
    print(f"Using DispatchIS file: {dispatchis_url}")
    regional_price = get_latest_regional_price_data(dispatchis_url)
    regional_price.to_csv(PRICE_OUTPUT_FILE, index=False)
    print(f"Saved {len(regional_price)} rows → {PRICE_OUTPUT_FILE}")

    print("Fetching SCADA...")
    latest_url = get_latest_scada_url()
    print(f"Using SCADA file: {latest_url}")
    scada = get_latest_scada(latest_url)

    print("Merging wind assets, coordinates and regional price...")
    final = build_wind_dataset(scada, regional_price=regional_price)
    final.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved {len(final)} rows → {OUTPUT_FILE}")

    history = update_24h_history(final)
    print(f"Saved rolling 24h history: {len(history)} rows → {HISTORY_FILE}")


if __name__ == "__main__":
    main()
