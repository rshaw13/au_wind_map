import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

DATA_URL = (
    "https://raw.githubusercontent.com/rshaw13/au_wind_map/refs/heads/main/data/latest_wind_data.csv"
)

st.set_page_config(layout="wide")
st.title("Australian Wind Farm Output")

@st.cache_data(ttl=300)
def load_data():
    return pd.read_csv(DATA_URL)

df = load_data()

st.caption(f"Last update (UTC): {df['timestamp_utc'].iloc[0]}")

m = folium.Map(location=[-30, 145], zoom_start=4.5, tiles="CartoDB positron")

scale = 0.15

openweathermap_api_key = st.secrets["OPENWEATHERMAP_API_KEY"]

for _, row in df.iterrows():

    wind_tiles = (
        f"https://tile.openweathermap.org/map/wind_new/{z}/{x}/{y}.png?appid={openweathermap_api_key}"
    )

    folium.raster_layers.TileLayer(
        tiles=wind_tiles,
        attr="OpenWeatherMap",
        name="Wind",
        overlay=True,
        control=True,
    ).add_to(m)

    popup_text = (f"{row['Station Name']}\n{row['SCADAVALUE']} MW Output / {row['REG_CAP']} MW Capacity.\n({row['utilisation_%']:.1f}% Utilisation)"
    )

    folium.CircleMarker(
        location=[row["Latitude"], row["Longitude"]],
        radius=row["SCADAVALUE"] * scale,
        fill=True,
        fill_opacity=0.5,
        fill_color="green" if row["utilisation_pct"] > 50 else "red",
        stroke=False,
        popup=popup_text, 
        tooltip=popup_text,
    ).add_to(m)

    folium.CircleMarker(
        location=[row["Latitude"], row["Longitude"]],
        radius=row["REG_CAP"] * scale,
        color="gray",
        weight=1,
        fill_opacity=0,
        fill_color="black",
        tooltip=popup_text,
        popup=popup_text,
    ).add_to(m)

st_folium(m, width=1400, height=700)