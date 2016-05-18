from flask import Flask, request, session, redirect, url_for, abort, render_template, flash
from dsd.ui.web import app
from dsd.ui.web.functions import *
@app.route("/manage", endpoint='manage.index', methods=['GET'])
def index():
    return render_template('manage_main.html')
@app.route("/manage/user", methods=['GET'])
def manage_user():
    if is_admin():
        user_lst = list(db().users.find())
        return render_template('manage_user.html', user_lst=user_lst)
    else:
        flash('Invalid login. Login again.')
        return redrect(url_for('index'));

@app.route('/manage/user/add', methods=['GET', 'POST'])
def manage_user_add():
    if is_admin():
        # create user
        if request.method == 'GET':
            return render_template('manage_user_add.html')
        else:
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

@app.route("/manage/gpu", methods=['GET'])
def manage_gpu():
    if is_admin():
        user_lst = list(db().users.find())
        print user_lst
        return render_template('manage_user.html', user_lst=user_lst)
    else:
        flash('Invalid login. Login again.')
        return redrect(url_for('index'));