from flask import Flask, request, session, render_template
from dsd.ui.web import app
from dsd.ui.web.utils import *

@app.route("/user", endpoint='user.index', methods=['GET'])
def index():
    if is_login():
        return render_template('user_index.html')
    else:
        return invalid_login('Administrators only. Login again.')
