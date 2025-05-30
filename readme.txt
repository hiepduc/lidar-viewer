To create a dashboard with streamlit

(1) Install streamlit in conda
conda install streamlit

(2)
Create a directory where strealit application (Python program) lives

say /mnt/scratch_lustre/duch/lidar/lidar-viewer-app

The app.py is a dahboard python program uisng streamlit package

Under /mnt/scratch_lustre/duch/lidar/lidar-viewer-app there are files and directory
app.py
images/  (contain all image files)
requirements.txt
README.md


(3) to github.com (create your account if used first time)

Go to https://github.com

Click “+” → New repository

Name it something like lidar-dashboard

Check “Add a README” (optional)

Click “Create repository”

(4) Go back to host 
cd /mnt/scratch_lustre/duch/lidar/lidar-viewer-app
git init
git remote add origin https://github.com/your-username/lidar-dashboard.git

git add .
git commit -m "Initial commit with dashboard and graphs"
git branch -M main
git push -u origin main

Now your files (including images) are uploaded to GitHub!

(5)  Deploy to Streamlit Cloud (Free)
Go to https://streamlit.io/cloud

Click “Sign in with GitHub”

Click “New app”

Choose your repo and select app.py as the main file

Click “Deploy”


