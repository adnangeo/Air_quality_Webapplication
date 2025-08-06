import streamlit as st
import ee
import geemap.foliumap as geemap
import json
import os

# --------------------------
# Authenticate Earth Engine
# --------------------------
service_account = st.secrets["GEE_SERVICE_ACCOUNT"]
credentials = ee.ServiceAccountCredentials(
    service_account,
    key_data=json.loads(st.secrets["GEE_PRIVATE_KEY_JSON"])
)
ee.Initialize(credentials)

# --------------------------
# Streamlit Page Setup
# --------------------------
st.set_page_config(layout="wide")
st.title("🌍 Air Quality & Population Explorer (Sentinel-5P + CMIP6)")
st.markdown("Analyze air quality trends and population exposure using Sentinel-5P and CMIP6 data.")

# --------------------------
# Sidebar Filters
# --------------------------
st.sidebar.header("📌 Filters")

pollutant = st.sidebar.selectbox("Select a pollutant", ["NO2", "SO2", "Aerosol"])
start_date = st.sidebar.date_input("Start Date", value=None)
end_date = st.sidebar.date_input("End Date", value=None)

st.sidebar.write("---")
st.sidebar.info("🗺️ Draw a polygon on the map to analyze the area.")

# --------------------------
# Map and AOI Selection
# --------------------------
m = geemap.Map(center=[20, 78], zoom=4)
m.add_basemap("SATELLITE")
m.add_draw_control()

with st.container():
    st.subheader("🗺️ Map Viewer")
    m.to_streamlit(height=500)

# --------------------------
# Processing User AOI
# --------------------------
if m.user_roi is not None and start_date and end_date:
    with st.spinner("Processing selected area and dates..."):
        roi = m.user_roi
        col_dict = {
            "NO2": "COPERNICUS/S5P/OFFL/L3_NO2",
            "SO2": "COPERNICUS/S5P/OFFL/L3_SO2",
            "Aerosol": "COPERNICUS/S5P/OFFL/L3_AER_AI"
        }
        collection_id = col_dict[pollutant]

        col = ee.ImageCollection(collection_id) \
            .filterBounds(roi) \
            .filterDate(str(start_date), str(end_date)) \
            .select(0)

        mean_img = col.mean().clip(roi)
        vis_params = {"min": 0, "max": 0.0002, "palette": ["white", "yellow", "orange", "red"]}
        m.addLayer(mean_img, vis_params, f"Mean {pollutant}")
        st.success(f"{pollutant} mean image loaded for selected area and time!")

        st.subheader("📈 Time Series Chart")
        chart = ui_chart = geemap.chart_image_series(col, roi, reducer=ee.Reducer.mean())
        st.altair_chart(chart, use_container_width=True)

else:
    st.warning("Please select a valid date range and draw a shape on the map to begin analysis.")
