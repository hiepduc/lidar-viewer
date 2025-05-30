import os

# Folder containing your lidar images
image_folder = "images"

# Loop through files in the folder
for filename in os.listdir(image_folder):
    if "Lidcombe_CEILOMETER" in filename:
        new_name = filename.replace("Lidcombe_CEILOMETER", "Lidcombe_Ceilometer")
        old_path = os.path.join(image_folder, filename)
        new_path = os.path.join(image_folder, new_name)
        os.rename(old_path, new_path)
        print(f"Renamed: {filename} -> {new_name}")
