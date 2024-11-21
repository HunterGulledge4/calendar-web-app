#!/bin/bash

python3 -m venv venv

source venv/bin/activate

pip install Flask Flask-SQLAlchemy Flask-Migrate werkzeug

mv app.py venv/app.py
mv static venv/static
mv templates venv/templates

cd venv

flask db init
flask db migrate -m "Initial migration."
flask db upgrade

xdg-open http://127.0.0.1:5000 &

python app.py
