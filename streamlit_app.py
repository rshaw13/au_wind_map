import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# styling
st.set_page_config(layout="wide")

st.markdown(
    """
    <style>
    /* Import font correctly */
    @import url('https://fonts.googleapis.com');

    /* Global Font */
    .stMarkdown, p, label, .stSelectbox {
            font-family: "Inter", sans-serif !important;
    }

    /* Background Gradient */
    .stApp {
        background: RGBA(68, 159, 186, 1);
        background: linear-gradient(180deg, rgba(68, 159, 186, 0.9) 7%, rgba(239, 208, 187, 0.9) 86%);
        background-attachment: fixed;
    }

    /* Hero banner - Gradient */
    .hero {
        background: linear-gradient(90deg, rgba(225, 169, 131, 1) 9%, rgba(202, 94, 47, 1) 67%); 
        padding: 60px 40px;
        border-radius: 12px;
        margin-bottom: 25px;
        text-align: center;
        background-size: cover;
        background-position: center;
        box-shadow: 2px 4px 14px 5px rgba(86,47,20,0.39);
    }

    .hero h1 {
        color: #EFD0BB;
        font-family: 'Garamond', serif;
        font-weight: 700;
        font-size: 4rem; 
        margin: 0;
        text-shadow: 2px 4px 14px 5px rgba(86,47,20,0.39);
    }

    .content-card {
        background-color: white !important;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.2);
        margin-bottom: 20px;
        color: #31333F !important;
    }

    .custom-text {
        color: #0a0a0a;
        font-size: 35px;
        font-weight: bold;
        margin-top: 20px;
    }
    
  /* Style the HTML table to look like Streamlit's */
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
    }
    .custom-table th {
        text-align: left;
        padding: 12px 8px;
        background-color: #e1a983;
        color: black;
        border-bottom: 2px solid #f0f2f6;
    }
    .custom-table td {
        padding: 12px 8px;
        border-bottom: 1px solid #f0f2f6;
        color: #31333F;
    }

    /* Target the wind tiles specifically */
    /* This filter chain turns the rainbow tiles into a soft peach/orange tint */
    .leaflet-tile-pane .leaflet-layer:nth-child(2) img {
        filter: grayscale(100%) sepia(100%) hue-rotate(330deg) saturate(2) brightness(1.1) !important;
        mix-blend-mode: multiply; /* Helps the color blend into the map */
    }

    /* Alternative for a Blue tint (#449FBA):
       filter: grayscale(100%) sepia(100%) hue-rotate(160deg) saturate(3) brightness(0.8) !important;
    */

    </style>
    """,
    unsafe_allow_html=True
)

# loading DATA
DATA_URL = (
    "https://raw.githubusercontent.com/rshaw13/au_wind_map/refs/heads/main/data/latest_wind_data.csv"
)
@st.cache_data(ttl=300)
def load_data():
    return pd.read_csv(DATA_URL)

df = load_data()

# title and linkedin caption
st.markdown(
    """
    <div class="hero">
        <h1>Australian Windfarm Output Map</h1>
    </div>
    """,
    unsafe_allow_html=True
)

linkedin_url = "https://www.linkedin.com/in/ryan-shaw13/"
st.markdown(
    f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; color: #0a0a0a; font-size: 0.85rem;">
        <div>An energy project by Ryan Shaw.</div>
        <div style="display: flex; align-items: center; gap: 10px;">
            <span>Contact me on LinkedIn: </span>
            <a href="{linkedin_url}" target="_blank">
                <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/81/LinkedIn_icon.svg/250px-LinkedIn_icon.svg.png" width="18px">
            </a>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# title for map section
st.markdown("""
<style>
.custom-text {
    color: #31333F; 
    font-size: 35px;
}
</style>
<p class="custom-text"><strong>Current Plant Output Map</strong></p>
""", unsafe_allow_html=True)

# wind farm selector
selected_name = st.selectbox(
    "Hover over a plant on the map to find its name, then use the drop-down to select a wind farm for output information in the table below",
    df["Station Name"].sort_values().unique()
)

selected_row = df[df["Station Name"] == selected_name].iloc[0]


# setting up folium map
m = folium.Map(
    location=[-30, 145],
    zoom_start=4.5,
    tiles="CartoDB positron",
    width='100%',
    height='100%'
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

    is_selected = row["Station Name"] == selected_name

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
        fill_color="#FC0C3B" if is_selected else (
            "#449fba" if row["utilisation_pct"] > 50 else "#ca5e2f"
        ),
        stroke=False,
        tooltip=row['Station Name'],
        popup=popup_text,
    ).add_to(m)

    # Capacity ring
    folium.CircleMarker(
        location=[row["Latitude"], row["Longitude"]],
        radius=row["REG_CAP"] * scale,
        color="gray",
        weight=1,
        fill=True,
        fill_opacity=0.2 if is_selected else 0,
        fill_color="#FC0C3B",
        tooltip=row['Station Name'],
        popup=popup_text,
    ).add_to(m)

# render map
map_data = st_folium(
    m,
    width=None,
    height=700,
    key="wind_map",
)


st.caption(f"Last update (UTC): {df['timestamp_utc'].iloc[0]}")


# selection-specific farm data table
table_df = pd.DataFrame([{
    "Wind Farm": str(selected_row["Station Name"]),
    "DUID": str(selected_row["DUID"]),
    "Output (MW)": float(round(selected_row["SCADAVALUE"],1)),
    "Capacity (MW)": float(round(selected_row["REG_CAP"],1)),
    "Utilisation (%)": float(round(selected_row["utilisation_pct"], 0)),
    "Last Update (UTC)": str(selected_row["timestamp_utc"]),
}])

# forcing as object dtype then making bare html for streamlit
table_df = table_df.astype(object)
table_html = table_df.to_html(index=False, classes='custom-table')

st.markdown(
    f"""
    <div class="content-card">
        <h3 style="color: #31333F;">Selected Wind Farm Details</h3>
        {table_html}
    </div>
    """,
    unsafe_allow_html=True
)