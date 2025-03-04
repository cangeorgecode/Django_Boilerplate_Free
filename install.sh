#! /usr/bin/bash

pip install -r requirements.txt
python manage.py tailwind install
npm i kutty --save
python manage.py tailwind start