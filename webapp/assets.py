from flask import Flask
from .views import create_view

def create_app():
    app = Flask(__name__)
    app.config['DEBUG'] = True
    create_view(app)
    return app