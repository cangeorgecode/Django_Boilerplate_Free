#! /bin/bash

echo "[INFO] Installing python packages..."
pip install -r requirements.txt

echo "[SUCCESS] Finished installing python packages"
echo "[INFO] Installing Tailwind"
python manage.py install tailwind

echo "[SUCCESS] Finished installing Tailwind"
echo "[INFO] Installing DaisyUI..."
cd theme/static_src
npm i -D daisyui@latest
cd ../../

echo "[SUCCESS] Finished installing DaisyUI"
echo "[INFO] Building Tailwind..."
python manage.py tailwind build

echo "[SUCCESS] Finished building Tailwind"
echo "[INFO] Collecting static files..."
python manage.py collectstatic --noinput

echo "[SUCCESS] Finished collecting static files"
echo "[INFO] Making migrations..."
python manage.py makemigrations
python manage.py migrate

echo "[SUCCESS] Finished migration" 
echo "[SUCCESS] Setup is complete. Enjoy!" 