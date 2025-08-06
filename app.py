import streamlit as st
import geemap.foliumap as geemap
import ee
import datetime

# Earth Engine authentication
ee.Authenticate()
ee.Initialize(project='ee-syedadnanbukhari63')

# Streamlit layout
st.set_page_config(layout="wide")
st.title("🌫️ Air Quality + Population Dashboard (Sentinel-5P + LandScan)")

# Sidebar controls
pollutant = st.sidebar.selectbox("Pollutant", ['NO2', 'SO2', 'CO', 'Aerosol Index'])
start_date = st.sidebar.date_input("Start Date", datetime.date(2022, 1, 1))
end_date = st.sidebar.date_input("End Date", datetime.date(2022, 1, 10))
show_population = st.sidebar.checkbox("Show LandScan Population", value=True)
buffer_km = st.sidebar.slider("Buffer (km) for Point", 1, 50, 10)

dataset_dict = {
    "NO2": ("COPERNICUS/S5P/OFFL/L3_NO2", "tropospheric_NO2_column_number_density", 0.0005),
    "SO2": ("COPERNICUS/S5P/OFFL/L3_SO2", "SO2_column_number_density", 0.0005),
    "CO": ("COPERNICUS/S5P/OFFL/L3_CO", "CO_column_number_density", 0.05),
    "Aerosol Index": ("COPERNICUS/S5P/OFFL/L3_AER_AI", "absorbing_aerosol_index", 2),
}
collection_id, band_name, max_vis = dataset_dict[pollutant]

# Draw map
st.subheader("🗺️ Draw AOI on Map (Point, Rectangle, Polygon)")
Map = geemap.Map(center=[20, 78], zoom=4)
Map.add_basemap("SATELLITE")
Map.add_draw_control()
Map.to_streamlit()

if "aoi" not in st.session_state:
    st.session_state.aoi = None

if st.button("✅ Submit AOI"):
    drawn = Map.user_roi
    if drawn:
        geom_type = drawn.geometry().type().getInfo()
        st.success(f"{geom_type} selected")
        if geom_type == 'Point':
            geom = drawn.buffer(buffer_km * 1000).bounds()
        else:
            geom = drawn.geometry().bounds()
        st.session_state.aoi = geom
    else:
        st.warning("No geometry drawn")

# If AOI exists, process data
if st.session_state.aoi:
    aoi = ee.Geometry(st.session_state.aoi)

    ic = ee.ImageCollection(collection_id).select(band_name).filterDate(str(start_date), str(end_date)).filterBounds(aoi)
    mean_img = ic.mean().clip(aoi)

    map2 = geemap.Map()
    map2.addLayer(mean_img, {"min": 0, "max": max_vis, "palette": ["white", "blue", "purple"]}, f"{pollutant} Mean")

    if show_population:
        pop = ee.ImageCollection("projects/sat-io/open-datasets/ORNL/LANDSCAN_GLOBAL").sort("system:time_start", False).first()
        pop_vis = {"min": 0, "max": 2000, "palette": ['white', 'orange', 'red']}
        map2.addLayer(pop.clip(aoi).visualize(**pop_vis), {}, "LandScan Population")

    map2.centerObject(aoi, 8)
    map2.to_streamlit(height=500)