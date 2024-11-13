#!/bin/bash

python3 -m venv venv

source venv/bin/activate

pip install boto3 Flask Flask-SQLAlchemy Flask-WTF Flask-Bcrypt Flask-Login werkzeug

mv app venv\app
mv static venv\static
mv templates venv\templates

cd venv
cd app

xdg-open http://127.0.0.1:5000

python app.py