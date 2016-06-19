from flask import Flask, request, session, redirect, url_for, abort, render_template, flash
from dsd.ui.web import app
from dsd.ui.web.utils import *

@app.route("/manage/system", endpoint='manage.system', methods=['GET', 'POST'])
def manage_system():
    if is_admin():
        if request.method == 'GET':
            system = list(db.system.find())
            return render_template('manage_system.html')
        else:
            pass
    else:
        flash('Invalid login. Login again.')
        return redirect(url_for('index'))
