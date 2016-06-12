from flask import Flask, request, session, redirect, url_for, abort, render_template, flash
from dsd.ui.web import app
from dsd.ui.web.utils import *

@app.route("/", methods=['GET'])
def index():
    if is_login():
        if session['User_Type'] == 'Admin':
            return redirect(url_for('manage.index'))
        if session['User_Type'] == 'Common':
            return redirect(url_for('user.index'))
    else:
        return render_template('index.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        error = None
        return render_template('login.html',error=error)
    elif request.method == 'POST':
        username = request.form.get('Username')
        password = request.form.get('Password')
        state, error, user_type = check_login(username, password)
        if state:
            session['Is_Login'] = '1'
            session['user_name'] = username
            session['User_Type'] = user_type
            return redirect(url_for('index'))
        else:
            session.pop('Is_Login', None)
            session.pop('User_Type', None)
            flash('Invalid login. Login again.')
            return render_template('login.html',error=error)
    else:
        flash('Invalid login. Login again.')
        return redrect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('Is_Login', None)
    session.pop('User_Type', None)
    flash('You were logged out')
    return redirect(url_for('index'))
