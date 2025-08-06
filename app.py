import streamlit as st
import ee
import geemap.foliumap as geemap
import json
import os

st.set_page_config(layout="wide")
st.title("🌍 Air Quality & Population Explorer (Sentinel-5P + LandScan)")

# Authenticate with Earth Engine using service account
credentials = ee.ServiceAccountCredentials(
    os.environ["GEE_SERVICE_ACCOUNT"],
    key_data=json.loads(os.environ["GEE_PRIVATE_KEY"])
)
ee.Initialize(credentials)

# UI inputs
col1, col2 = st.columns(2)
with col1:
    pollutant = st.selectbox("Select pollutant", ["NO2", "SO2", "CO", "Aerosol"])
with col2:
    vis_type = st.radio("Visualization", ["Daily", "Monthly Average"])

Map = geemap.Map(center=[20, 78], zoom=4, add_google_map=False)
Map.add_basemap("HYBRID")

# Pollutant collection mapping
pollutants = {
    "NO2": {
        "collection": "COPERNICUS/S5P/OFFL/L3_NO2",
        "band": "NO2_column_number_density",
        "vis": {"min": 0, "max": 0.0002, "palette": ["black", "purple", "blue", "cyan", "green", "yellow", "red"]},
    },
    "SO2": {
        "collection": "COPERNICUS/S5P/OFFL/L3_SO2",
        "band": "SO2_column_number_density",
        "vis": {"min": 0, "max": 0.0005, "palette": ["black", "blue", "green", "yellow", "red"]},
    },
    "CO": {
        "collection": "COPERNICUS/S5P/OFFL/L3_CO",
        "band": "CO_column_number_density",
        "vis": {"min": 0, "max": 0.05, "palette": ["black", "blue", "green", "yellow", "red"]},
    },
    "Aerosol": {
        "collection": "COPERNICUS/S5P/OFFL/L3_AER_AI",
        "band": "absorbing_aerosol_index",
        "vis": {"min": 0, "max": 2, "palette": ["black", "purple", "blue", "cyan", "green", "yellow", "red"]},
    }
}

# Add selected pollutant layer
info = pollutants[pollutant]
collection = ee.ImageCollection(info["collection"]).select(info["band"])

if vis_type == "Daily":
    image = collection.sort("system:time_start", False).first()
    Map.addLayer(image, info["vis"], f"{pollutant} Latest")
else:
    image = collection.filterDate("2023-01-01", "2023-12-31").mean()
    Map.addLayer(image, info["vis"], f"{pollutant} Monthly Avg (2023)")

# Add LandScan population
landscan = ee.ImageCollection("projects/sat-io/open-datasets/ORNL/LANDSCAN_GLOBAL")
latest_pop = landscan.sort("system:time_start", False).first()
Map.addLayer(latest_pop, {"min": 0, "max": 5000, "palette": ["white", "orange", "red", "black"]}, "Population")

Map.addLayerControl()
Map.to_streamlit(width=1200, height=600)