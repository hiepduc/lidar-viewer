import streamlit as st
import os
from datetime import datetime, timedelta
from PIL import Image
import folium
from streamlit_folium import st_folium
import streamlit.components.v1 as components

from streamlit_folium import folium_static
import io
import tempfile
import glob
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Define available sites and coordinates
sites = {
    "Lidcombe": [-33.865, 151.045],
    "Merriwa": [-32.15, 150.035],
    "Rozelle": [-33.85, 151.17],
    "Campbelltown": [-34.065, 150.814]
}


# Layout: create 2 columns (left narrow for map)
col1, col2 = st.columns([1, 3])

with col1:
    st.markdown("### NSW Site Locations")

    # Create the Folium map
    m = folium.Map(location=[-33.5, 147.0], zoom_start=6)
    for name, coords in sites.items():
        folium.Marker(location=coords, popup=name).add_to(m)

    # Save to a temporary HTML file
    with tempfile.NamedTemporaryFile('w', delete=False, suffix='.html') as f:
        m.save(f.name)
        map_html_path = f.name

    # Read and display map
    with open(map_html_path, 'r', encoding='utf-8') as f:
        map_html = f.read()

    components.html(map_html, height=400, width=250)

with col2:

   # Configuration
   IMAGE_FOLDER = "images"

   # Extract full site names from filenames
   SITE_OPTIONS = sorted({"_".join(f.split("_")[:-1]) for f in os.listdir(IMAGE_FOLDER) if f.endswith(".png")})

   # Title
   st.title("Lidar Graph Viewer Dashboard")

   # Site selection
   selected_site = st.selectbox("Select Site", SITE_OPTIONS)


   # Get .png dates from IMAGE_FOLDER
   png_dates = {
       f.split("_")[-1][:8]
       for f in os.listdir(IMAGE_FOLDER)
       if f.endswith(".png") and f.startswith(selected_site)
   }

   # Get .csv dates from blh_csv folder
   csv_dates = {
       f.split("_")[-1][:8]
       for f in os.listdir("blh_csv")
       if f.endswith(".csv") and f.startswith(selected_site)
   }

   # Combine and sort
   available_dates = sorted(png_dates.union(csv_dates))

   #all_files = [f for f in os.listdir(IMAGE_FOLDER) if f.endswith(".png")]
   #available_dates = sorted({
   #    f.split("_")[-1][:8]
   #    for f in all_files
   #    if f.startswith(selected_site)
   #})

   available_datetimes = [datetime.strptime(d, "%Y%m%d").date() for d in available_dates]

   # --- Initialize session state if not set ---
   if "selected_date" not in st.session_state or st.session_state.selected_date not in available_datetimes:
       # Default to the latest available date
       st.session_state.selected_date = max(available_datetimes) if available_datetimes else datetime.today().date()

   # Date navigation
   col1, col2, col3 = st.columns([1, 2, 1])
   with col1:
   #   if st.button("⬅️ Previous Day"):
   #       st.session_state.selected_date -= timedelta(days=1)
       if st.button("⬅️ Previous Day"):
           idx = available_datetimes.index(st.session_state.selected_date)
           if idx > 0:
               st.session_state.selected_date = available_datetimes[idx - 1]

   with col3:
   #   if st.button("Next Day ➡️"):
   #       st.session_state.selected_date += timedelta(days=1)
        if st.button("Next Day ➡️"):
            idx = available_datetimes.index(st.session_state.selected_date)
            if idx < len(available_datetimes) - 1:
                st.session_state.selected_date = available_datetimes[idx + 1]

   # Manual date override
   manual_date = st.date_input("Select Date", value=st.session_state.selected_date,min_value=min(available_datetimes),max_value=max(available_datetimes),)
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

   # Option to show BLH chart
   show_blh = st.checkbox("Show Boundary Layer Height (BLH) chart for this day")

   if show_blh:
      # --- Boundary Layer Height Plot Section ---
      st.subheader("Boundary Layer Height (BLH) versus Time ")

      # Format date string
      date_str = selected_date.strftime("%Y%m%d")

      # Search for the BLH CSV matching the selected site and date
      blh_folder = "blh_csv"
      blh_pattern = f"L3_*_{date_str}_{selected_site.split('_')[0]}.csv"
      blh_matches = glob.glob(os.path.join(blh_folder, blh_pattern))

      if blh_matches:
          blh_filepath = blh_matches[0]  # use the first match
          try:
              blh_df = pd.read_csv(blh_filepath)

              # Expecting columns: 'time' (like "00", "01", ...) and 'bl_height'
              # Try to auto-detect the correct column names if needed
              time_col = [col for col in blh_df.columns if "time" in col.lower()]
              bl_col = [col for col in blh_df.columns if "bl" in col.lower() or "height" in col.lower()]

              if time_col and bl_col:
                  time_col = time_col[0]
                  bl_col = bl_col[0]

                  fig, ax = plt.subplots()
                  # Convert time column to datetime
                  # blh_df[time_col] = pd.to_datetime(blh_df[time_col], dayfirst=True, errors='coerce')
                  # Parse time column with dayfirst format
                  blh_df[time_col] = pd.to_datetime(blh_df[time_col], dayfirst=True, errors='coerce')

                  # Replace -999 with NaN in BLH column
                  blh_df[bl_col] = pd.to_numeric(blh_df[bl_col], errors='coerce')
                  blh_df[bl_col] = blh_df[bl_col].replace(-999, np.nan)

                  # Drop rows with missing time or BLH
                  blh_df = blh_df.dropna(subset=[time_col, bl_col])

                  # Drop rows with invalid datetime
                  blh_df = blh_df.dropna(subset=[time_col])

                  # Plot
                  fig, ax = plt.subplots(figsize=(10, 4))
                  ax.plot(blh_df[time_col], blh_df[bl_col], marker='o', linestyle='-')

                  # Format x-axis
                  ax.set_xlabel("Time ")
                  ax.set_ylabel("Boundary Layer Height (m)")
                  ax.set_title(f"BLH for {selected_site} on {selected_date.strftime('%Y-%m-%d')}")
                  ax.grid(True)

                  # Format datetime ticks
                  fig.autofmt_xdate(rotation=45)
                  ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%H:%M'))

                  st.pyplot(fig)
                  # --- Add download buttons ---
                  # 1. Download the BLH CSV
                  st.download_button(
                      label="Download BLH CSV",
                      data=blh_df.to_csv(index=False),
                      file_name=os.path.basename(blh_filepath),
                      mime="text/csv"
                  )

                  # 2. Download the chart as PNG
                  # Save matplotlib figure to buffer
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

