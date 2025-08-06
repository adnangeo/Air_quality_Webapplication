import streamlit as st
import geemap.foliumap as geemap
import ee
import os
import json
from datetime import date

# Authenticate with service account
service_account = os.environ["GEE_SERVICE_ACCOUNT"]
key_data = json.loads(os.environ["GEE_PRIVATE_KEY_JSON"])
credentials = ee.ServiceAccountCredentials(service_account, key_data)
ee.Initialize(credentials)

# App title
st.set_page_config(layout="wide")
st.title("🌍 Air Quality & Population Explorer (Sentinel-5P + LandScan)")

# Sidebar filters
st.sidebar.title("Filters")
pollutant = st.sidebar.selectbox("Select a pollutant", ["NO2", "SO2", "CO", "Aerosol"])
start_date = st.sidebar.date_input("Start Date", date(2024, 1, 1))
end_date = st.sidebar.date_input("End Date", date(2024, 1, 31))

# Instructions
st.write("Draw a shape on the map to analyze data.")

# Initialize map
m = geemap.Map(center=[23, 78], zoom=4)
m.add_draw_control()
m.to_streamlit(height=600)

# Display selected pollutant
pollutant_dict = {
    "NO2": "COPERNICUS/S5P/NRTI/L3_NO2",
    "SO2": "COPERNICUS/S5P/OFFL/L3_SO2",
    "CO": "COPERNICUS/S5P/OFFL/L3_CO",
    "Aerosol": "COPERNICUS/S5P/OFFL/L3_AER_AI"
}

band_dict = {
    "NO2": "tropospheric_NO2_column_number_density",
    "SO2": "SO2_column_number_density",
    "CO": "CO_column_number_density",
    "Aerosol": "absorbing_aerosol_index"
}

dataset = ee.ImageCollection(pollutant_dict[pollutant]) \
    .filterDate(str(start_date), str(end_date)) \
    .select(band_dict[pollutant])

image = dataset.mean().clip(m.user_roi) if m.user_roi else dataset.mean()

vis_params = {
    "min": 0,
    "max": image.reduceRegion(ee.Reducer.max(), image.geometry(), 10000).get(band_dict[pollutant]).getInfo(),
    "palette": ["blue", "green", "yellow", "orange", "red"]
}

m.addLayer(image, vis_params, f"{pollutant} Mean ({start_date} to {end_date})")

# Add population (LandScan)
if st.sidebar.checkbox("Show LandScan Population", value=True):
    landscan = ee.ImageCollection("projects/sat-io/open-datasets/ORNL/LANDSCAN_GLOBAL") \
        .filterDate("2020-01-01", "2021-01-01") \
        .mean().clip(m.user_roi if m.user_roi else image.geometry())

    m.addLayer(landscan, {"min": 0, "max": 500, "palette": ["white", "blue", "purple", "red"]}, "Population (LandScan)")

    if m.user_roi:
        total_pop = landscan.reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=m.user_roi.geometry(),
            scale=1000,
            maxPixels=1e13
        ).getInfo()

        pop_sum = list(total_pop.values())[0]
        st.success(f"Estimated Population in selected area: **{int(pop_sum):,}**")

m.to_streamlit(height=700)
