import streamlit as st
import folium
from streamlit_folium import st_folium
import rasterio


def main():
    st.title("Remote Sensing Classification Viewer")
    raster_path = st.text_input("Classification raster", "outputs/prediction.tif")
    if st.button("Display Map"):
        with rasterio.open(raster_path) as src:
            data = src.read(1)
            bounds = src.bounds
        m = folium.Map(location=[(bounds.top + bounds.bottom) / 2,
                                 (bounds.left + bounds.right) / 2],
                       zoom_start=12)
        folium.raster_layers.ImageOverlay(
            image=data,
            bounds=[[bounds.bottom, bounds.left], [bounds.top, bounds.right]],
            opacity=0.7,
        ).add_to(m)
        st_folium(m, width=700, height=500)


if __name__ == "__main__":
    main()
