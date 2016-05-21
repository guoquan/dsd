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

@app.route("/manage/container", methods=['GET'])
def manage_container():
    if is_admin():
        container_lst = list(db().containers.find())
        print container_lst
        return render_template('manage_container.html', container_lst=container_lst)
    else:
        flash('Invalid login. Login again.')
        return redrect(url_for('index'));
@app.route("/manage/container/add", methods=['GET'])
def manage_container_add():
    if is_admin():
        user_lst = list(db().users.find())
        db().containers.save({
            'container_name':'test-jp2t',
            'container_id':'d4cdc086814f5c65e484c806861afb102c47a11d0ebca42ab40a880eb53fa511',
            'image':'dsd-console',
            'created':'1463531671',
            'user':user_lst[1],
            'gpu':[0],
            'max_disk':20020,
            'max_memory':3000})
        container_lst = list(db().containers.find())
        print container_lst
        return render_template('manage_container.html', container_lst=container_lst)
    else:
        flash('Invalid login. Login again.')
        return redrect(url_for('index'));