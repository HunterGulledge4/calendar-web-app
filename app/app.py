import boto3
import json
from flask import Flask, render_template
import config

app = Flask(__name__, template_folder='../templates')
app._static_folder = '../static'

AWS_ACCESS_KEY_ID = config.AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY = config.AWS_SECRET_ACCESS_KEY
REGION_NAME = config.REGION_NAME

CLIENT_ID = config.CLIENT_ID
USER_PASSWORD_AUTH = config.USER_PASSWORD_AUTH



@app.route('/')
def index():
   return render_template('index.html')


if __name__ == '__main__':
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)