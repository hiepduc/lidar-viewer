import streamlit as st
import os
from datetime import datetime, timedelta
from PIL import Image
import folium
import streamlit.components.v1 as components
import io
import tempfile
import glob
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# -----------------------------
# Site locations
# -----------------------------
sites = {
    "Lidcombe": [-33.865, 151.045],
    "Merriwa": [-32.15, 150.035],
    "Rozelle": [-33.85, 151.17],
    "Singleton": [-32.57, 151.178],
    "Muswellbrook": [-32.261, 150.89],
    "Campbelltown": [-34.065, 150.814]
}

# -----------------------------
# Layout: Map column
# -----------------------------
col1, col2 = st.columns([1, 3])
with col1:
    st.markdown("### NSW Site Locations")
    m = folium.Map(location=[-33.5, 151.0], zoom_start=6)
    for name, coords in sites.items():
        folium.Marker(location=coords, popup=name).add_to(m)
    with tempfile.NamedTemporaryFile('w', delete=False, suffix='.html') as f:
        m.save(f.name)
        map_html_path = f.name
    with open(map_html_path, 'r', encoding='utf-8') as f:
        map_html = f.read()
    components.html(map_html, height=400, width=250)

# -----------------------------
# Main column: Site selection and viewer
# -----------------------------
with col2:
    IMAGE_FOLDER = "images"
    SITE_OPTIONS = sorted({"_".join(f.split("_")[:-1]) for f in os.listdir(IMAGE_FOLDER) if f.endswith(".png")})

    st.title("Lidar Graph Viewer Dashboard")
    selected_site = st.selectbox("Select Site", SITE_OPTIONS)

    # -----------------------------
    # Available dates for site
    # -----------------------------
    png_dates = {
        f.split("_")[-1][:8]
        for f in os.listdir(IMAGE_FOLDER)
        if f.endswith(".png") and f.startswith(selected_site)
    }

    site_prefix = selected_site.split("_")[0]
    csv_dates = {
        f.split("_")[-2]
        for f in os.listdir("blh_csv")
        if f.endswith(".csv") and f.startswith("L3_") and f.endswith(f"_{site_prefix}.csv")
    }

    # --- Extract site and instrument ---
    site_prefix, instrument = selected_site.split("_")  # e.g., 'Lidcombe', 'MPL'

    # --- PNG dates for the selected site ---
    png_dates = {
        f.split("_")[-1][:8]
        for f in os.listdir(IMAGE_FOLDER)
        if f.endswith(".png") and f.startswith(selected_site)
    }

    # --- BLH CSV dates (only for instruments with BLH data) ---
    instruments_with_blh = ["Ceilometer"]  # Only Ceilometer has BLH CSV
    csv_dates = set()
    if instrument in instruments_with_blh:
        csv_dates = {
            f.split("_")[-2]
            for f in os.listdir("blh_csv")
            if f.endswith(".csv")
            and f.startswith("L3_")
            and f.endswith(f"_{site_prefix}.csv")
        }

    # --- Combine dates ---
    available_dates = sorted(png_dates.union(csv_dates))

    # --- Convert to datetime.date objects ---
    available_datetimes = sorted([datetime.strptime(d, "%Y%m%d").date() for d in available_dates])

    # --- Session state key ---
    site_key = f"selected_date_{selected_site}"
    date_input_key = f"date_input_{selected_site}"

    if available_datetimes:
        latest_date = max(available_datetimes)

        # Initialize per-site session state when missing or invalid
        if site_key not in st.session_state or st.session_state[site_key] not in available_datetimes:
            st.session_state[site_key] = latest_date

        # Date navigation buttons
        col_prev, col_mid, col_next = st.columns([1, 2, 1])
        with col_prev:
            if st.button("⬅️ Previous Day", key=f"prev_{selected_site}"):
                idx = available_datetimes.index(st.session_state[site_key])
                if idx > 0:
                    st.session_state[site_key] = available_datetimes[idx - 1]

        with col_next:
            if st.button("Next Day ➡️", key=f"next_{selected_site}"):
                idx = available_datetimes.index(st.session_state[site_key])
                if idx < len(available_datetimes) - 1:
                    st.session_state[site_key] = available_datetimes[idx + 1]

        # Manual date selection
        manual_date = st.date_input(
            "Select Date",
            value=st.session_state[site_key],
            min_value=min(available_datetimes),
            max_value=max(available_datetimes),
            key=date_input_key
        )

        # Update session state
        st.session_state[site_key] = manual_date
        selected_date = st.session_state[site_key]
        date_str = selected_date.strftime("%Y%m%d")
    else:
        st.warning(f"No dates available for site {selected_site}")
        selected_date = None
        date_str = None

    # -----------------------------
    # Find images for the selected date
    # -----------------------------
    if selected_date:
        pattern = os.path.join(IMAGE_FOLDER, f"{selected_site}_{date_str}*.png")
        file_list = sorted(glob.glob(pattern))

        available_times = []
        time_to_file = {}
        for filepath in file_list:
            filename = os.path.basename(filepath)
            try:
                timestamp = filename.replace(".png", "").split("_")[-1]
                hhmm = timestamp[-4:]
                if len(hhmm) == 4 and hhmm.isdigit():
                    available_times.append(hhmm)
                    time_to_file[hhmm] = filepath
            except Exception:
                continue

        if available_times:
            selected_time = st.selectbox("Select Time (HHMM)", sorted(available_times))
            selected_filepath = time_to_file[selected_time]

            if os.path.exists(selected_filepath):
                image = Image.open(selected_filepath)
                formatted_time = f"{selected_time[:2]}:{selected_time[2:]}"
                st.image(image, caption=f"{selected_site} - {selected_date} {formatted_time}", use_container_width=True)

                with open(selected_filepath, "rb") as img_file:
                    st.download_button(
                        label="Download this image",
                        data=img_file,
                        file_name=os.path.basename(selected_filepath),
                        mime="image/png"
                    )
        else:
            st.warning(f"No images found for {selected_site} on {selected_date}.")

        # --- Show all images checkbox ---
        if st.checkbox("Show all available images for the day"):
            st.subheader("Available Time-Stamped Images")
            cols = st.columns(4)
            for i, hhmm in enumerate(sorted(available_times)):
                filepath = time_to_file[hhmm]
                if os.path.exists(filepath):
                    with cols[i % 4]:
                        image = Image.open(filepath)
                        st.image(image, caption=f"{hhmm[:2]}:{hhmm[2:]}", use_container_width=True)

        # --- BLH chart ---
        show_blh = st.checkbox("Show Boundary Layer Height (BLH) chart for this day")
        if show_blh:
            st.subheader("Boundary Layer Height (BLH) versus Time ")
            blh_folder = "blh_csv"
            blh_pattern = f"L3_*_{date_str}_{site_prefix}.csv"
            blh_matches = glob.glob(os.path.join(blh_folder, blh_pattern))

            if blh_matches:
                blh_filepath = blh_matches[0]
                try:
                    blh_df = pd.read_csv(blh_filepath)
                    time_col = [col for col in blh_df.columns if "time" in col.lower()]
                    bl_col = [col for col in blh_df.columns if "bl" in col.lower() or "height" in col.lower()]
                    if time_col and bl_col:
                        time_col = time_col[0]
                        bl_col = bl_col[0]

                        blh_df[time_col] = pd.to_datetime(blh_df[time_col], dayfirst=True, errors='coerce')
                        blh_df[bl_col] = pd.to_numeric(blh_df[bl_col], errors='coerce').replace(-999, np.nan)
                        blh_df = blh_df.dropna(subset=[time_col, bl_col])

                        fig, ax = plt.subplots(figsize=(10, 4))
                        ax.plot(blh_df[time_col], blh_df[bl_col], marker='o', linestyle='-')
                        ax.set_xlabel("Time")
                        ax.set_ylabel("Boundary Layer Height (m)")
                        ax.set_title(f"BLH for {selected_site} on {selected_date}")
                        ax.grid(True)
                        fig.autofmt_xdate(rotation=45)
                        ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%H:%M'))
                        st.pyplot(fig)

                        # Download buttons
                        st.download_button(
                            label="Download BLH CSV",
                            data=blh_df.to_csv(index=False),
                            file_name=os.path.basename(blh_filepath),
                            mime="text/csv"
                        )
                        img_buffer = io.BytesIO()
                        fig.savefig(img_buffer, format='png')
                        img_buffer.seek(0)
                        st.download_button(
                            label="Download BLH Chart (PNG)",
                            data=img_buffer,
                            file_name=f"{selected_site}_{date_str}_blh_chart.png",
                            mime="image/png"
                        )
                    else:
                        st.warning("Could not find expected 'time' and 'BL height' columns in the CSV.")
                except Exception as e:
                    st.error(f"Error reading BLH CSV: {e}")
            else:
                st.info("Boundary Layer Height (BLH) data not available for this site and date.")

