from pathlib import Path

import altair as alt
import folium
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    layout="wide",
    initial_sidebar_state="collapsed",
    page_title="Australian Windfarm Output Map",
)

# ---------------- DATA LOCATIONS ----------------
DATA_URL = "https://raw.githubusercontent.com/rshaw13/au_wind_map/refs/heads/main/data/latest_wind_data.csv"
HISTORY_URL = "https://raw.githubusercontent.com/rshaw13/au_wind_map/refs/heads/main/data/wind_history_24h.csv"

LOCAL_DATA_FILE = Path("data/latest_wind_data.csv")
LOCAL_HISTORY_FILE = Path("data/wind_history_24h.csv")

# ---------------- STYLING ----------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Cormorant+Garamond:wght@500;600;700&display=swap');

    :root {
        --bg-deep: #421815;
        --bg-mid: #55201b;
        --card: #662820;
        --card-soft: #743027;
        --accent: #ff6938;
        --accent-soft: #e58a65;
        --cream: #f4d8cf;
        --muted: #d6a095;
        --line: rgba(255, 105, 56, 0.55);
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }

    .stApp {
        background:
            radial-gradient(circle at 22% 16%, rgba(255, 105, 56, 0.12), transparent 26%),
            radial-gradient(circle at 86% 72%, rgba(255, 105, 56, 0.10), transparent 30%),
            linear-gradient(180deg, #421815 0%, #4b1b17 52%, #32100f 100%);
        background-attachment: fixed;
        color: var(--cream);
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1220px;
    }

    .hero-wrap {
        text-align: center;
        margin: 0.5rem 0 1rem 0;
    }

    .hero {
        display: inline-block;
        width: auto;
        max-width: 980px;
        padding: 18px 42px 20px 42px;
        border: 1px solid var(--line);
        border-radius: 22px;
        background: rgba(66, 24, 21, 0.72);
        box-shadow: 0 16px 45px rgba(0, 0, 0, 0.28);
    }

    .hero h1 {
        color: var(--cream);
        font-family: 'Cormorant Garamond', serif !important;
        font-weight: 700;
        font-size: clamp(2.5rem, 6vw, 5.2rem);
        line-height: 0.92;
        letter-spacing: -0.04em;
        margin: 0;
    }

    .hero .highlight {
        color: var(--accent);
    }

    .subheader-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
        margin: 0 0 1rem 0;
        color: var(--muted);
        font-size: 0.9rem;
    }

    .subheader-bar a {
        color: var(--accent);
        text-decoration: none;
        font-weight: 600;
    }

    .status-panel {
        border: 1px solid var(--line);
        background: rgba(84, 32, 27, 0.78);
        border-radius: 20px;
        padding: 18px;
        margin: 16px 0 22px 0;
        box-shadow: 0 16px 38px rgba(0, 0, 0, 0.24);
    }

    .status-title {
        font-family: 'Cormorant Garamond', serif !important;
        color: var(--cream);
        font-size: 2rem;
        line-height: 1;
        margin-bottom: 14px;
    }

    .metric-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 12px;
    }

    .metric-card {
        border: 1px solid rgba(255, 105, 56, 0.36);
        border-radius: 16px;
        padding: 16px 18px;
        background: rgba(65, 22, 18, 0.65);
    }

    .metric-label {
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-size: 0.76rem;
        font-weight: 700;
    }

    .metric-value {
        color: var(--cream);
        font-size: clamp(2rem, 4vw, 3.7rem);
        font-weight: 800;
        line-height: 1.05;
        margin-top: 6px;
    }

    .metric-note {
        color: var(--muted);
        font-size: 0.86rem;
        margin-top: 4px;
    }

    .content-card {
        border: 1px solid rgba(255, 105, 56, 0.35);
        background: rgba(84, 32, 27, 0.72);
        border-radius: 20px;
        padding: 18px;
        margin: 18px 0;
        box-shadow: 0 16px 38px rgba(0, 0, 0, 0.24);
        color: var(--cream) !important;
        overflow-x: auto;
    }

    .section-title {
        font-family: 'Cormorant Garamond', serif !important;
        font-size: 2.05rem;
        color: var(--cream);
        margin: 0 0 10px 0;
        line-height: 1.05;
    }

    .section-copy {
        color: var(--muted);
        font-size: 0.96rem;
        margin-bottom: 12px;
    }

    .custom-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
        font-family: 'Inter', sans-serif !important;
        color: var(--cream);
    }

    .custom-table th {
        text-align: left;
        padding: 12px 10px;
        background-color: rgba(255, 105, 56, 0.26);
        color: var(--cream);
        border-bottom: 1px solid rgba(255, 105, 56, 0.38);
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    .custom-table td {
        padding: 12px 10px;
        border-bottom: 1px solid rgba(244, 216, 207, 0.12);
        color: var(--cream);
        font-size: 0.95rem;
    }

    div[data-testid="stSelectbox"] label {
        color: var(--cream) !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 1rem;
        font-weight: 600;
    }

    div[data-testid="stSelectbox"] > div {
        color: var(--cream) !important;
    }

    .map-frame {
        border: 1px solid rgba(255, 105, 56, 0.38);
        border-radius: 20px;
        overflow: hidden;
        box-shadow: 0 22px 50px rgba(0,0,0,0.28);
        margin-bottom: 18px;
    }

    .caption-text {
        color: var(--muted);
        font-size: 0.9rem;
        margin-top: 8px;
    }

    @media (max-width: 820px) {
        .metric-grid {
            grid-template-columns: 1fr;
        }

        .subheader-bar {
            flex-direction: column;
            align-items: flex-start;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def format_mw(value) -> str:
    try:
        if pd.isna(value):
            return "—"
        return f"{float(value):,.0f} MW"
    except Exception:
        return "—"


def format_price(value) -> str:
    try:
        if pd.isna(value):
            return "—"
        return f"${float(value):,.2f}/MWh"
    except Exception:
        return "—"


@st.cache_data(ttl=300)
def load_latest_data() -> pd.DataFrame:
    if LOCAL_DATA_FILE.exists():
        return pd.read_csv(LOCAL_DATA_FILE)
    return pd.read_csv(DATA_URL)


@st.cache_data(ttl=300)
def load_history_data() -> pd.DataFrame:
    try:
        if LOCAL_HISTORY_FILE.exists():
            return pd.read_csv(LOCAL_HISTORY_FILE)
        return pd.read_csv(HISTORY_URL)
    except Exception:
        return pd.DataFrame()


def coerce_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    df = df.copy()
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def choose_default_asset(names: list[str]) -> int:
    preferred_terms = ["macarthur", "stockyard", "ryan corner", "musselroe"]
    lowered = [str(name).lower() for name in names]
    for term in preferred_terms:
        for idx, name in enumerate(lowered):
            if term in name:
                return idx
    return 0


try:
    df = load_latest_data()
except Exception as e:
    st.error("Could not load latest wind data. Check data/latest_wind_data.csv and DATA_URL.")
    st.code(DATA_URL)
    st.exception(e)
    st.stop()

if df.empty:
    st.error("Latest wind data loaded, but it is empty.")
    st.stop()

required_cols = ["Station Name", "DUID", "SCADAVALUE", "MAX_CAP", "Latitude", "Longitude", "SETTLEMENTDATE"]
missing = [c for c in required_cols if c not in df.columns]
if missing:
    st.error(f"latest_wind_data.csv is missing required columns: {missing}")
    st.stop()

# Defensive cleanup
df = coerce_numeric(df, ["SCADAVALUE", "MAX_CAP", "utilisation_pct", "Latitude", "Longitude", "REGION_RRP"])
df = df.dropna(subset=["Latitude", "Longitude", "SCADAVALUE", "MAX_CAP"])
df["Station Name"] = df["Station Name"].astype(str)
df["DUID"] = df["DUID"].astype(str)
if "Region" not in df.columns:
    df["Region"] = pd.NA
if "REGION_RRP" not in df.columns:
    df["REGION_RRP"] = pd.NA

history_df = load_history_data()
if not history_df.empty:
    history_df = coerce_numeric(history_df, ["SCADAVALUE", "MAX_CAP", "utilisation_pct", "REGION_RRP"])
    if "SETTLEMENTDATE" in history_df.columns:
        history_df["SETTLEMENTDATE"] = pd.to_datetime(history_df["SETTLEMENTDATE"], errors="coerce")

# ---------------- HEADER ----------------
st.markdown(
    """
    <div class="hero-wrap">
        <div class="hero">
            <h1>Australian <span class="highlight">windfarm</span> output map</h1>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

linkedin_url = "https://www.linkedin.com/in/ryan-shaw13/"
st.markdown(
    f"""
    <div class="subheader-bar">
        <div>An energy project by Ryan Shaw.</div>
        <div>Contact me on <a href="{linkedin_url}" target="_blank">LinkedIn</a></div>
    </div>
    """,
    unsafe_allow_html=True,
)

latest_time = str(df["SETTLEMENTDATE"].iloc[0])
total_wind_mw = df["SCADAVALUE"].sum()
total_capacity_mw = df["MAX_CAP"].sum()
asset_count = df["DUID"].nunique()
avg_utilisation = (total_wind_mw / total_capacity_mw * 100) if total_capacity_mw else 0

st.markdown(
    f"""
    <div class="status-panel">
        <div class="status-title">Current wind output</div>
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-label">Total wind volume now</div>
                <div class="metric-value">{total_wind_mw:,.0f} MW</div>
                <div class="metric-note">Across {asset_count} wind farm DUIDs</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Registered capacity</div>
                <div class="metric-value">{total_capacity_mw:,.0f} MW</div>
                <div class="metric-note">Mapped assets in this dashboard</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Average utilisation</div>
                <div class="metric-value">{avg_utilisation:,.0f}%</div>
                <div class="metric-note">Output divided by registered capacity</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------- MAP ----------------
asset_names = sorted(df["Station Name"].dropna().unique())
default_idx = choose_default_asset(asset_names)
selected_name = asset_names[default_idx]

# Use session state so the map renders before the dropdown, while the dropdown below controls selection.
if "selected_wind_name" not in st.session_state:
    st.session_state["selected_wind_name"] = selected_name
selected_name = st.session_state["selected_wind_name"]
selected_row = df[df["Station Name"] == selected_name].iloc[0]

m = folium.Map(
    location=[-30, 145],
    zoom_start=4.5,
    tiles="OpenStreetMap",
    width="100%",
    height="100%",
    control_scale=True,
)

# CSS injected into the Folium iframe.
map_css = """
<style>
.leaflet-tile-pane img {
    filter: sepia(0.78) saturate(1.65) hue-rotate(318deg) brightness(0.82) contrast(1.18) !important;
}
.leaflet-container {
    background: #421815 !important;
    font-family: 'Inter', Arial, sans-serif !important;
}
.leaflet-popup-content-wrapper {
    background: rgba(66, 24, 21, 0.96) !important;
    color: #f4d8cf !important;
    border: 1px solid rgba(255, 105, 56, 0.55) !important;
    border-radius: 14px !important;
    box-shadow: 0 12px 35px rgba(0,0,0,0.40) !important;
}
.leaflet-popup-content {
    width: max-content !important;
    min-width: 285px !important;
    max-width: 520px !important;
    white-space: nowrap !important;
    font-family: 'Inter', Arial, sans-serif !important;
    font-size: 13px !important;
    line-height: 1.55 !important;
}
.leaflet-popup-tip {
    background: rgba(66, 24, 21, 0.96) !important;
}
.wind-marker {
    position: relative;
    border-radius: 999px;
    transform: translate(-50%, -50%);
    border: 1.5px solid rgba(244, 216, 207, 0.70);
    background: rgba(255, 105, 56, 0.18);
    box-shadow: 0 0 16px rgba(255, 105, 56, 0.35);
}
.wind-marker .inner-dot {
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    border-radius: 999px;
    background: rgba(255, 105, 56, 0.78);
    box-shadow: 0 0 14px rgba(255, 105, 56, 0.55);
}
.wind-marker.selected {
    border: 2px solid #f4d8cf;
    background: rgba(255, 105, 56, 0.34);
    box-shadow: 0 0 24px rgba(255, 105, 56, 0.78);
}
</style>
"""
m.get_root().header.add_child(folium.Element(map_css))

valid_bounds = []
max_capacity = max(df["MAX_CAP"].max(), 1)

for _, row in df.iterrows():
    lat = row["Latitude"]
    lon = row["Longitude"]
    if pd.isna(lat) or pd.isna(lon):
        continue

    is_selected = row["Station Name"] == selected_name
    capacity = max(float(row.get("MAX_CAP", 0) or 0), 1)
    output = max(float(row.get("SCADAVALUE", 0) or 0), 0)
    utilisation = float(row.get("utilisation_pct", 0) or 0)

    outer_size = max(18, min(64, 18 + (capacity / max_capacity) * 54))
    inner_size = max(6, min(outer_size - 5, 6 + (output / capacity) * (outer_size - 10)))

    popup_text = f"""
    <div>
        <b style="font-size: 15px; color: #ff6938;">{row['Station Name']}</b><br>
        DUID: {row['DUID']}<br>
        Region: {row.get('Region', '—')}<br>
        Output: {output:,.1f} MW<br>
        Capacity: {capacity:,.1f} MW<br>
        Utilisation: {utilisation:,.1f}%<br>
        Regional price: {format_price(row.get('REGION_RRP'))}
    </div>
    """

    icon_html = f"""
    <div class="wind-marker {'selected' if is_selected else ''}" style="width:{outer_size}px; height:{outer_size}px;">
        <div class="inner-dot" style="width:{inner_size}px; height:{inner_size}px;"></div>
    </div>
    """

    icon = folium.DivIcon(
        html=icon_html,
        icon_size=(outer_size, outer_size),
        icon_anchor=(outer_size / 2, outer_size / 2),
    )

    marker = folium.Marker(
        location=[lat, lon],
        icon=icon,
        tooltip=str(row["Station Name"]),
    )
    marker.add_child(folium.Popup(popup_text, min_width=285, max_width=520))
    marker.add_to(m)
    valid_bounds.append([lat, lon])

if valid_bounds:
    m.fit_bounds(valid_bounds, padding=(20, 20))

map_height = 590
st.markdown('<div class="map-frame">', unsafe_allow_html=True)
components.html(m.get_root().render(), height=map_height, scrolling=False)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown(
    f'<div class="caption-text">Last update (AEMO dispatch interval): {latest_time}. Latest published AEMO data can lag real time.</div>',
    unsafe_allow_html=True,
)

# Dropdown below the map
selected_name = st.selectbox(
    "Hover over a plant on the map to find its name, then use the drop-down to inspect a wind farm.",
    asset_names,
    index=asset_names.index(st.session_state["selected_wind_name"]) if st.session_state["selected_wind_name"] in asset_names else 0,
    key="selected_wind_name_selectbox",
)
st.session_state["selected_wind_name"] = selected_name
selected_row = df[df["Station Name"] == selected_name].iloc[0]

# ---------------- SELECTED ASSET TABLE ----------------
table_df = pd.DataFrame([
    {
        "Wind Farm": str(selected_row["Station Name"]),
        "DUID": str(selected_row["DUID"]),
        "Region": str(selected_row.get("Region", "—")),
        "Output (MW)": float(round(selected_row["SCADAVALUE"], 1)),
        "Capacity (MW)": float(round(selected_row["MAX_CAP"], 1)),
        "Utilisation (%)": float(round(selected_row.get("utilisation_pct", 0), 0)),
        "Regional Price": format_price(selected_row.get("REGION_RRP")),
        "Last Update": str(selected_row["SETTLEMENTDATE"]),
    }
]).astype(object)

table_html = table_df.to_html(index=False, classes="custom-table")
st.markdown(
    f"""
    <div class="content-card">
        <h3 class="section-title">Selected wind farm details</h3>
        <div class="table-wrapper">
            {table_html}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------- 24H SELECTED ASSET CHART ----------------
st.markdown(
    """
    <div class="content-card">
        <h3 class="section-title">Last 24 hours selected wind output</h3>
        <div class="section-copy">Output is shown as MW by AEMO dispatch interval for the selected wind farm.</div>
    """,
    unsafe_allow_html=True,
)

asset_history = pd.DataFrame()
if not history_df.empty and {"DUID", "SETTLEMENTDATE", "SCADAVALUE"}.issubset(history_df.columns):
    asset_history = history_df[history_df["DUID"].astype(str) == str(selected_row["DUID"])].copy()
    asset_history = asset_history.dropna(subset=["SETTLEMENTDATE", "SCADAVALUE"])
    asset_history = asset_history.sort_values("SETTLEMENTDATE")

if asset_history.empty or len(asset_history) < 2:
    st.info("The 24-hour chart will populate after the update script has run a few times and built data/wind_history_24h.csv.")
else:
    chart = (
        alt.Chart(asset_history)
        .mark_line(point=True, strokeWidth=3)
        .encode(
            x=alt.X("SETTLEMENTDATE:T", title="Dispatch interval"),
            y=alt.Y("SCADAVALUE:Q", title="Output MW"),
            tooltip=[
                alt.Tooltip("SETTLEMENTDATE:T", title="Time"),
                alt.Tooltip("SCADAVALUE:Q", title="Output MW", format=",.1f"),
                alt.Tooltip("utilisation_pct:Q", title="Utilisation %", format=",.1f"),
                alt.Tooltip("REGION_RRP:Q", title="Regional price $/MWh", format=",.2f"),
            ],
        )
        .properties(height=310)
        .configure_view(strokeWidth=0)
        .configure_axis(labelColor="#f4d8cf", titleColor="#d6a095", gridColor="rgba(244,216,207,0.12)")
        .configure_legend(labelColor="#f4d8cf", titleColor="#d6a095")
    )
    st.altair_chart(chart, use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)

# ---------------- MOST ACTIVE TABLE ----------------
leaderboard = df.sort_values("SCADAVALUE", ascending=False).head(12).copy()
leaderboard_df = leaderboard[["Station Name", "DUID", "Region", "SCADAVALUE", "MAX_CAP", "utilisation_pct", "REGION_RRP"]].copy()
leaderboard_df = leaderboard_df.rename(
    columns={
        "Station Name": "Wind Farm",
        "SCADAVALUE": "Output (MW)",
        "MAX_CAP": "Capacity (MW)",
        "utilisation_pct": "Utilisation (%)",
        "REGION_RRP": "Regional Price ($/MWh)",
    }
)
for col in ["Output (MW)", "Capacity (MW)", "Utilisation (%)", "Regional Price ($/MWh)"]:
    leaderboard_df[col] = pd.to_numeric(leaderboard_df[col], errors="coerce").round(1)

leaderboard_html = leaderboard_df.astype(object).to_html(index=False, classes="custom-table")
st.markdown(
    f"""
    <h3 class="section-title">Most active wind farms right now</h3>
    <div class="section-copy">Ranked by current AEMO SCADA output.</div>
    <div class="table-wrapper">
        {leaderboard_html}
    </div>
    """,
    unsafe_allow_html=True,
)
