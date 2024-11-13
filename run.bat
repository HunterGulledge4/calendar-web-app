@echo off

python -m venv venv

REM Activate the virtual environment (adjust path as needed)
call venv\Scripts\activate

REM Install required packages if they aren’t already installed
pip install boto3 Flask Flask-SQLAlchemy Flask-WTF Flask-Bcrypt Flask-Login werkzeug

move app venv\app
move static venv\static
move templates venv\templates

cd venv
cd app

start http://127.0.0.1:5000

python app.py

