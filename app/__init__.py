__author__ = 'Alex Hart'

from flask import Flask

app = Flask(__name__)
app.config.from_object(__name__)

from app import views
