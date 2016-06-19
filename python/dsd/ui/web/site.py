from flask import Flask, request, session, redirect, url_for, abort, render_template, flash
from dsd.ui.web import app
from dsd.ui.web.utils import *

@app.route("/", methods=['GET'])
def index():
    if is_login():
        if session['user']['type'] is UserTypes.Administrator:
            return redirect(url_for('manage.index'))
        elif session['user']['type'] is UserTypes.User:
            return redirect(url_for('user.index'))
        else:
            flash('Unrecognized user type. Login again.')
            return render_template('index.html')
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
        user, error = check_login(username, password)
        if user:
            session['is_login'] = True
            session['user'] = user
            return redirect(url_for('index'))
        else:
            session.pop('is_login', None)
            session.pop('user', None)
            flash('Invalid login. Login again.')
            return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('is_login', None)
    session.pop('user', None)
    flash('You were logged out')
    return redirect(url_for('index'))
