import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# styling
st.set_page_config(layout="wide")

st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">

<style>
html, body, [class*="css"] {
    font-family: "Inter", sans-serif;
}

/* Hero banner */
.hero {
    background-image: url("https://esdnews.com.au/wp-content/uploads/2023/08/Palmer-Wind-Farm-SA.jpg");
    background-size: cover;
    background-position: center;
    padding: 90px 40px;
    border-radius: 12px;
    margin-bottom: 25px;
}

.hero h1 {
    color: white;
    text-shadow: 0 2px 6px rgba(0,0,0,0.6);
}

/* Table styling */
[data-testid="stDataFrame"] thead tr th {
    background-color: #e6f2ff;
    color: black;
}

[data-testid="stDataFrame"] tbody tr {
    background-color: white;
}
</style>

<div class="hero">
    <h1>Australian Wind Farm Output</h1>
</div>
""", unsafe_allow_html=True)

# loading DATA

DATA_URL = (
    "https://raw.githubusercontent.com/rshaw13/au_wind_map/refs/heads/main/data/latest_wind_data.csv"
)

@st.cache_data(ttl=300)
def load_data():
    return pd.read_csv(DATA_URL)

df = load_data()
st.caption(f"Last update (UTC): {df['timestamp_utc'].iloc[0]}")

# setting up folium map

m = folium.Map(
    location=[-30, 145],
    zoom_start=4.5,
    tiles="CartoDB positron"
)

scale = 0.15
openweathermap_api_key = st.secrets["OPENWEATHERMAP_API_KEY"]

# wind layer

wind_tiles = (
    "https://tile.openweathermap.org/map/wind_new/{z}/{x}/{y}.png"
    f"?appid={openweathermap_api_key}"
)

folium.raster_layers.TileLayer(
    tiles=wind_tiles,
    attr="OpenWeatherMap",
    name="Wind",
    overlay=True,
    control=True,
    opacity=0.9,
).add_to(m)

# wind farm markers

for _, row in df.iterrows():

    popup_text = f"""
        <b>{row['Station Name']}</b><br>
        Output: {row['SCADAVALUE']} MW<br>
        Capacity: {row['REG_CAP']} MW<br>
        Utilisation: {row['utilisation_pct']:.1f}%
        """


    # Actual output
    folium.CircleMarker(
        location=[row["Latitude"], row["Longitude"]],
        radius=row["SCADAVALUE"] * scale,
        fill=True,
        fill_opacity=0.5,
        fill_color="green" if row["utilisation_pct"] > 50 else "red",
        stroke=False,
        tooltip=popup_text,
    ).add_to(m)

    # Capacity ring
    folium.CircleMarker(
        location=[row["Latitude"], row["Longitude"]],
        radius=row["REG_CAP"] * scale,
        color="gray",
        weight=1,
        fill=True,
        fill_opacity=0,
        fill_color="green",
        tooltip=popup_text,
    ).add_to(m)

# render map and capture clicks
map_data = st_folium(
    m,
    width=1400,
    height=700,
    key="wind_map",
    returned_objects=["last_popup"]
)

# click-reactive table
st.markdown("---")

st.markdown("---")

if map_data and map_data.get("last_popup"):
    popup_html = map_data["last_popup"]

    # Extract station name from popup
    for _, row in df.iterrows():
        if row["Station Name"] in popup_html:
            selected = row
            break
    else:
        selected = None

    if selected is not None:
        table_df = pd.DataFrame([{
            "Wind Farm": selected["Station Name"],
            "Output (MW)": selected["SCADAVALUE"],
            "Capacity (MW)": selected["REG_CAP"],
            "Utilisation (%)": round(selected["utilisation_pct"], 1),
            "Last Update (UTC)": selected["timestamp_utc"],
        }])

        st.dataframe(
            table_df,
            use_container_width=True,
            hide_index=True
        )
else:
    st.info("Click a wind farm marker to see details.")
