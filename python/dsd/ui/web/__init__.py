from flask import Flask

app = Flask(__name__)
app.secret_key='123edft654edfgY^%R#$%^&**&^'

from dsd.ui.web import site
from dsd.ui.web import container