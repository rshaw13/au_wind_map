import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# styling
st.set_page_config(layout="wide")

# st.title("Australian Wind Farm Output")

st.markdown(
    """
    <style>
 */
    @import url('https://fonts.googleapis.com');

    html, body, [class*="css"] {
        font-family: "Inter", sans-serif;
    }

    /* Hero banner */
    .hero {
        background-image: url("https://esdnews.com.au");
        background-size: cover;
        background-position: center;
        padding: 90px 40px;
        border-radius: 12px;
        margin-bottom: 25px;
    }

    .hero h1 {
        color: #fc214c;
        font-family: 'Cormorant Garamond', serif;
        font-weight: bold;
        font-size: 3rem; 
    }

    /* Table styling */
    [data-testid="stDataFrame"] thead tr th {
        background-color: #67a4e6;
        color: black;
    }

    [data-testid="stDataFrame"] tbody tr {
        background-color: #5aabc2;
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


# st.image(
#    "https://esdnews.com.au/wp-content/uploads/2020/11/windfarm.jpg",
#    use_column_width=True
# )

# loading DATA

DATA_URL = (
    "https://raw.githubusercontent.com/rshaw13/au_wind_map/refs/heads/main/data/latest_wind_data.csv"
)

@st.cache_data(ttl=300)
def load_data():
    return pd.read_csv(DATA_URL)

df = load_data()
st.caption(f"Last update (UTC): {df['timestamp_utc'].iloc[0]}")

# wind farm selector

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
    "https://tile.openweathermap.org{z}/{x}/{y}.png"
    f"?appid={openweathermap_api_key}"
    f"&palette={wind_colour_palette}"
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
        fill_color="blue" if is_selected else (
            "green" if row["utilisation_pct"] > 50 else "red"
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
        fill_color="blue",
        tooltip=row['Station Name'],
        popup=popup_text,
    ).add_to(m)

# render map
map_data = st_folium(
    m,
    width=1400,
    height=700,
    key="wind_map",
)

# selection-specific farm data table
st.markdown("### Selected wind farm")


table_df = pd.DataFrame([{
    "Wind Farm": str(selected_row["Station Name"]),
    "DUID": str(selected_row["DUID"]),
    "Output (MW)": float(selected_row["SCADAVALUE"]),
    "Capacity (MW)": float(selected_row["REG_CAP"]),
    "Utilisation (%)": float(round(selected_row["utilisation_pct"], 1)),
    "Last Update (UTC)": str(selected_row["timestamp_utc"]),
}])

table_df = table_df.astype(object)

st.table(table_df)
