@echo off

python -m venv venv

call venv\Scripts\activate

pip install Flask Flask-SQLAlchemy Flask-Migrate werkzeug

move app.py venv\app.py
move static venv\static
move templates venv\templates

cd venv

flask db init
flask db migrate -m "Initial migration."
flask db upgrade

start http://127.0.0.1:5000

python app.py

