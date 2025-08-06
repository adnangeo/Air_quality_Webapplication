import streamlit as st
import ee
import json
import os
from datetime import datetime
import geemap.foliumap as geemap

# Authenticate with Earth Engine using service account
credentials = ee.ServiceAccountCredentials(
    os.environ["GEE_SERVICE_ACCOUNT"],
    key_data=os.environ["GEE_PRIVATE_KEY"]
)
ee.Initialize(credentials)

st.set_page_config(layout="wide")
st.title("🌍 Air Quality & Population Explorer (Sentinel-5P + LandScan)")

m = geemap.Map(center=[20, 78], zoom=4)
m.add_basemap("HYBRID")

with st.sidebar:
    st.header("Select a pollutant")
    pollutant = st.selectbox("Pollutant", ["NO2", "SO2", "CO", "Aerosol"])
    start_date = st.date_input("Start Date", datetime(2024, 1, 1))
    end_date = st.date_input("End Date", datetime(2024, 1, 31))
    show_population = st.checkbox("Show LandScan Population", value=True)
    st.markdown("Draw a shape on the map to analyze data.")

# Load Sentinel-5P based on pollutant
pollutant_dict = {
    "NO2": "COPERNICUS/S5P/NRTI/L3_NO2",
    "SO2": "COPERNICUS/S5P/NRTI/L3_SO2",
    "CO": "COPERNICUS/S5P/NRTI/L3_CO",
    "Aerosol": "COPERNICUS/S5P/NRTI/L3_AER_AI",
}
dataset = ee.ImageCollection(pollutant_dict[pollutant])     .filterDate(str(start_date), str(end_date))     .select(0)     .mean()

vis_params = {"min": 0, "max": 0.0005, "palette": ["black", "blue", "purple", "cyan", "green", "yellow", "red"]}
m.addLayer(dataset, vis_params, f"{pollutant} Mean")

# LandScan population overlay
if show_population:
    landscan = ee.ImageCollection("projects/sat-io/open-datasets/ORNL/LANDSCAN_GLOBAL").mean()
    m.addLayer(landscan, {"min": 0, "max": 5000, "palette": ["white", "orange", "red"]}, "LandScan Population")

m.add_draw_control()
m.to_streamlit(height=600)