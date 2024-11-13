import boto3
import json
import config
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, template_folder='../templates')
app._static_folder = '../static'
app.secret_key = 'your_secret_key'


AWS_ACCESS_KEY_ID = config.AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY = config.AWS_SECRET_ACCESS_KEY
REGION_NAME = config.REGION_NAME

CLIENT_ID = config.CLIENT_ID
USER_PASSWORD_AUTH = config.USER_PASSWORD_AUTH

# Create an RDS client
#rds_client = boto3.client('rds')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Database URI
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

with app.app_context():
    db.create_all()  # Create tables if they don't exist


@app.route('/index')
def index():
   return render_template('index.html')

@app.route('/', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if the username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('signup'))
        
        # Hash the password and create the new user
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            # Successful login - set session or other authentication mechanism
            flash('Logged in successfully!', 'success')
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))  # Redirect to protected page
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')



if __name__ == '__main__':
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)