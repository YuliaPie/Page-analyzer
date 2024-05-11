from flask import Flask
from dotenv import load_dotenv


load_dotenv()
app = Flask(__name__)


@app.route('/')
def welcome():
    return 'Welcome to Flask!'