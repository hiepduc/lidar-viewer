import streamlit as st
import os
from datetime import datetime, timedelta
from PIL import Image

# Configuration
IMAGE_FOLDER = "images"

# Extract full site names from filenames
SITE_OPTIONS = sorted({"_".join(f.split("_")[:-1]) for f in os.listdir(IMAGE_FOLDER) if f.endswith(".png")})

# Title
st.title("Lidar Graph Viewer Dashboard")

# Site selection
selected_site = st.selectbox("Select Site", SITE_OPTIONS)

# Session state for date navigation
if "selected_date" not in st.session_state:
    st.session_state.selected_date = datetime.today().date()

# Date navigation
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    if st.button("⬅️ Previous Day"):
        st.session_state.selected_date -= timedelta(days=1)
with col3:
    if st.button("Next Day ➡️"):
        st.session_state.selected_date += timedelta(days=1)

# Manual date override
manual_date = st.date_input("Select Date", value=st.session_state.selected_date)
st.session_state.selected_date = manual_date
selected_date = st.session_state.selected_date
date_str = selected_date.strftime("%Y%m%d")

# Detect available hours
available_hours = []
for hour in range(24):
    hour_str = f"{hour:02d}"
    filename = f"{selected_site}_{date_str}{hour_str}00.png"
    filepath = os.path.join(IMAGE_FOLDER, filename)
    if os.path.exists(filepath):
        available_hours.append(hour_str)

# Dropdown to select hour
if available_hours:
    selected_hour = st.selectbox("Select Hour", available_hours)
    filename = f"{selected_site}_{date_str}{selected_hour}00.png"
    filepath = os.path.join(IMAGE_FOLDER, filename)
    if os.path.exists(filepath):
        image = Image.open(filepath)
        st.image(image, caption=f"{selected_site} - {selected_date} {selected_hour}:00", use_container_width=True)
        # Add download button
        with open(filepath, "rb") as img_file:
            st.download_button(
            label="Download this image",
            data=img_file,
            file_name=filename,
            mime="image/png"
        )
else:
    st.warning(f"No images found for {selected_site} on {selected_date.strftime('%Y-%m-%d')}.")

# Optionally show all images in a grid
if st.checkbox("Show all available images for the day"):
    st.subheader("Available Hourly Graphs")
    cols = st.columns(4)
    for i, hour_str in enumerate(available_hours):
        filename = f"{selected_site}_{date_str}{hour_str}00.png"
        filepath = os.path.join(IMAGE_FOLDER, filename)
        if os.path.exists(filepath):
            with cols[i % 4]:
                image = Image.open(filepath)
                st.image(image, caption=f"{hour_str}:00", use_container_width=True)

