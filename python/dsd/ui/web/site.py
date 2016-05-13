from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from flask import render_template
import pymongo
from dsd.ui.web import app

def encrypt_password(password):#TBC
    return password

def check_login(username, password):
    client = pymongo.MongoClient()
    db = client.db_dsd
    cursor = db.users.find({'Username':username})
    if cursor.count() == 0:
        return False, 'No such user!', None
    elif encrypt_password(password) == cursor[0]['Password']:
        return True, 'Login succeed!', cursor[0]['User_Type']
    else:
        return False, 'Password mismatch!', None

def is_login():
    return 'Is_Login' in session and session['Is_Login'] == '1'
            
def is_admin():
    return is_login() and session['User_Type'] == 'Admin'

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
            return redirect(url_for('index'))
        else:
            session.pop('Is_Login', None)
            session.pop('User_Type', None)
            return render_template('login.html',error=error)
    else:
        flash('Invalid login. Login again.')
        return redrect(url_for('index'));

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
        # connect to db
        client = pymongo.MongoClient()
        db = client.db_dsd
        # create user
        username = request.form.get('Username')
        password = request.form.get('Password')
        max_container_count = request.form.get('Max_Container_Count')
        max_disk_space = request.form.get('Max_Disk_Space')
        user_type = request.form.get('User_Type')
        db.users.save(
            {'Username':username,
             'Password':encrypt_password(password),
             'User_Type':user_type,
             'Max_Container_Count':max_container_count,
             'Max_Disk_Space':max_disk_space})
        flash('User %s created.' % username)
        return redirect(url_for('manage_user'))
    else:
        flash('Invalid login. Login again.')
        return redrect(url_for('index'));

@app.route('/manage/user/remove', methods=['POST'])
def manage_user_remove():
    if is_admin():
        # TODO implement user remove
        flash('Not implemented yet.')
        return redirect(url_for('manage_user'))
    else:
        flash('Invalid login. Login again.')
        return redrect(url_for('index'));

@app.route('/logout')
def logout():
    session.pop('Is_Login', None)
    session.pop('User_Type', None)
    flash('You were logged out')
    return redirect(url_for('index'))
