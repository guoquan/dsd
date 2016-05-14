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
            flash('Login as %s. Welcome!' % username)
            return redirect(url_for('index'))
        else:
            session.pop('Is_Login', None)
            session.pop('User_Type', None)
            flash('Invalid login. Login again.')
            return render_template('login.html',error=error)
    else:
        flash('Invalid login. Login again.')
        return redrect(url_for('index'))

@app.route("/manage/user", methods=['GET'])
def manage_user():
    if is_admin():
        return render_template('manage_user.html')
    else:
        flash('Invalid login. Login again.')
        return redrect(url_for('index'));

@app.route('/manage/user/add', methods=['POST'])
def manage_user_add():
    if is_admin():
        # create user
        username = request.form.get('Username')
        password = request.form.get('Password')
        max_container_count = request.form.get('Max_Container_Count')
        max_disk_space = request.form.get('Max_Disk_Space')
        user_type = request.form.get('User_Type')
        db().users.save(
            {'Username':username,
             'Password':encrypt_password(password),
             'User_Type':user_type,
             'Max_Container_Count':max_container_count,
             'Max_Disk_Space':max_disk_space})
        flash('User %s created.' % username)
        return redirect(url_for('manage_user'))
    else:
        flash('Invalid login. Login again.')
        return redrect(url_for('index'))

@app.route('/manage/user/remove', methods=['POST'])
def manage_user_remove():
    if is_admin():
        # TODO implement user remove
        flash('Not implemented yet.')
        return redirect(url_for('manage_user'))
    else:
        flash('Invalid login. Login again.')
        return redrect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('Is_Login', None)
    session.pop('User_Type', None)
    flash('You were logged out')
    return redirect(url_for('index'))
