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
    html, body, [class*="css"], p, label, .stSelectbox {
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
    }

    .hero h1 {
        color: #EFD0BB;
        font-family: 'Cormorant Garamond', serif;
        font-weight: 700;
        font-size: 4rem; 
        margin: 0;
        box-shadow: 2px 4px 14px 5px rgba(86,47,20,0.39);
    }

    /* Content box for table and seleciton box */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: white;
        padding: 20px;
        border-radius: 5px;
        box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }

    /* Remove padding from Streamlit containers to make boxes look better */
    [data-testid="stVerticalBlock"] > div:has(div.content-box) {
        padding: 0;
    }

    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="hero">
        <h1>Australian Wind Farm Output</h1>
    </div>
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


# title for map section
with st.container():
    st.markdown("""
    <style>
    .custom-text {
        color: #132c34; 
        font-size: 35px;
    }
    </style>
    <p class="custom-text"><strong>Windfarm Output Map</strong></p>
    """, unsafe_allow_html=True)


# wind farm selector
with st.container():
    selected_name = st.selectbox(
        "Select a wind farm for output information",
        df["Station Name"].sort_values().unique()
    )

selected_row = df[df["Station Name"] == selected_name].iloc[0]


# setting up folium map
m = folium.Map(
    location=[-30, 145],
    zoom_start=4.5,
    tiles="CartoDB positron"
)

scale = 0.15
openweathermap_api_key = st.secrets["OPENWEATHERMAP_API_KEY"]

# wind layer
wind_colour_palette = "0:fcfcfc;10:a9d3df;50:5aabc2"

wind_tiles = (
    "https://maps.openweathermap.org{z}/{x}/{y}.png"
    f"?appid={openweathermap_api_key}"
    f"&palette={wind_colour_palette}"
    "&fill_bound=true"
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
    width=1700,
    height=800,
    key="wind_map",
)

st.caption(f"Last update (UTC): {df['timestamp_utc'].iloc[0]}")


# Wrap everything below the map in a div with the 'content-box' class
with st.container():
    st.markdown("### Selected Wind Farm Details")

    # selection-specific farm data table
    table_df = pd.DataFrame([{
        "Wind Farm": str(selected_row["Station Name"]),
        "DUID": str(selected_row["DUID"]),
        "Output (MW)": float(round(selected_row["SCADAVALUE"],1)),
        "Capacity (MW)": float(round(selected_row["REG_CAP"],1)),
        "Utilisation (%)": float(round(selected_row["utilisation_pct"], 0)),
        "Last Update (UTC)": str(selected_row["timestamp_utc"]),
    }])
    table_df = table_df.astype(object)

    st.table(table_df)