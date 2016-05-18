from flask import Flask, request, session, redirect, url_for, abort, render_template, flash
from dsd.ui.web import app
from dsd.ui.web.functions import *

@app.route("/", methods=['GET'])
def index():
    if is_login():
        if session['User_Type'] == 'Admin':
            return render_template('main_page.html')
        if session['User_Type'] == 'Common':
            return render_template('jupyter_page.html')
    else:
        return render_template('welcome_page.html')

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
            session['User_Type'] = user_type
            if user_type.upper() == "ADMIN":
                return redirect(url_for('manage.index'))
            else:
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
