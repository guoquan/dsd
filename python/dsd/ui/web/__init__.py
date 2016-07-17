from flask import Flask

app = Flask(__name__)
app.secret_key = '123edft654edfgY^%R#$%^&**&^'
app.jinja_env.add_extension('jinja2.ext.do')

from dsd.ui.web import site
from dsd.ui.web import manage
from dsd.ui.web import user
