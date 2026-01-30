import pandas as pd
import requests
import zipfile
import io
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin


# ---------------- CONFIG ----------------
SCADA_INDEX_URL = "https://www.nemweb.com.au/REPORTS/CURRENT/Dispatch_SCADA/"

CAPACITY_FILE = "Full NEM Plant Registration.csv"
COORDS_FILE = "Clean Coords.csv"

OUTPUT_FILE = "data/latest_wind_data.csv"
# ----------------------------------------

def get_latest_scada_url() -> str:
    r = requests.get(SCADA_INDEX_URL, timeout=30)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    zip_links = [
        a["href"]
        for a in soup.find_all("a", href=True)
        if "PUBLIC_DISPATCHSCADA" in a["href"] and a["href"].endswith(".zip")
    ]

    if not zip_links:
        raise RuntimeError("No Dispatch_SCADA zip files found")

    zip_links.sort(reverse=True)

    # urljoin safely handles absolute vs relative paths
    latest_url = urljoin(SCADA_INDEX_URL, zip_links[0])

    return latest_url


def get_latest_scada(zip_url: str) -> pd.DataFrame:
    r = requests.get(zip_url, timeout=30)
    r.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        csv_name = z.namelist()[0]
        with z.open(csv_name) as f:
            df = pd.read_csv(f)

    df.columns = df.iloc[0]
    df = df.iloc[1:-1][["SETTLEMENTDATE", "DUID", "SCADAVALUE"]]
    df["SCADAVALUE"] = df["SCADAVALUE"].astype(float).round(2)

    return df


def build_wind_dataset(scada: pd.DataFrame) -> pd.DataFrame:
    capacity = pd.read_csv(CAPACITY_FILE)

    wind = capacity[
        capacity["Fuel Source - Primary"].str.contains("Wind", na=False)
    ][
        ["Participant", "Station Name", "Fuel Source - Primary", "DUID", "Reg Cap generation (MW)"]
    ]

    wind = wind.rename(columns={"Reg Cap generation (MW)": "REG_CAP"})
    wind["REG_CAP"] = wind["REG_CAP"].astype(float)

    merged = scada.merge(wind, on="DUID", how="inner")

    merged["utilisation_pct"] = (merged["SCADAVALUE"] / merged["REG_CAP"] * 100).round(2)

    coords = pd.read_csv(COORDS_FILE)
    merged = merged.merge(coords, left_on="Station Name", right_on="Plant", how="inner")

    merged["timestamp_utc"] = datetime.utcnow().isoformat()

    return merged


def main():
    print("Fetching SCADA...")
    latest_url = get_latest_scada_url()
    print(f"Using SCADA file: {latest_url}")
    scada = get_latest_scada(latest_url)


    print("Merging datasets...")
    final = build_wind_dataset(scada)

    # Ensure data directory exists
    Path("data").mkdir(parents=True, exist_ok=True)

    final.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved {len(final)} rows → {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
