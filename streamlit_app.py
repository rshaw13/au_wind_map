import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# styling
st.set_page_config(layout="wide")

st.image(
    "https://esdnews.com.au/wp-content/uploads/2023/08/Palmer-Wind-Farm-SA.jpg",
    use_container_width=True
)

st.title("Australian Wind Farm Output")

st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"] {
    font-family: "Inter", sans-serif;
}

[data-testid="stDataFrame"] thead tr th {
    background-color: #e6f2ff;
}

[data-testid="stDataFrame"] tbody tr {
    background-color: white;
}
</style>
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
        fill_opacity=0.8 if is_selected else 0.5,
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
        fill_opacity=0,
        fill_color="green",
        tooltip=row['Station Name'],
        popup=popup_text,
    ).add_to(m)

# render map and capture clicks
map_data = st_folium(
    m,
    width=1400,
    height=700,
    key="wind_map",
)

# click-reactive table
st.markdown("### Selected wind farm")

table_df = pd.DataFrame([{
    "Wind Farm": selected_row["Station Name"],
    "Output (MW)": selected_row["SCADAVALUE"],
    "Capacity (MW)": selected_row["REG_CAP"],
    "Utilisation (%)": round(selected_row["utilisation_pct"], 1),
    "Last Update (UTC)": selected_row["timestamp_utc"],
}])

st.dataframe(
    table_df,
    use_container_width=True,
    hide_index=True
)