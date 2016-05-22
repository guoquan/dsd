from flask import Flask, request, session, redirect, url_for, abort, render_template, flash
from dsd.ui.web import app
from dsd.ui.web.functions import *
@app.route("/user", endpoint='user.index', methods=['GET'])
def index():
    return render_template('user_main.html')
@app.route("/user/container",endpoint='user.container', methods=['GET'])
def user_container():
    if is_login():
        #container_lst = docker().ps(all=True)
        container_lst = []
        user_container_lst = list(db().containers.find({'user':session['user_name']}))
        all_containers = docker().ps(all=True)
        for ps_container in all_containers:
            for user_container in user_container_lst:
                if ps_container['container_id'] == user_container['container_id']:
                    print ps_container
                    user_container = dict(user_container, **ps_container)
                    container_lst.append(user_container)
        return render_template('user_container.html', container_lst=container_lst)
    else:
        flash('Invalid login. Login again.')
        return redrect(url_for('index'));
@app.route("/user/container/add", methods=['GET', 'POST'])
def user_container_add():
    if is_login():
        if request.method == 'GET':
            image_lst = docker().images()
            return render_template('user_container_add.html', image_lst=image_lst)
        else:
            image = request.form['image']
            name = request.form['name']
                    # run it
            container = docker().run(detach=True,
                                     image=image,
                                     name = name,
                                     ports = {},
                                     volumes = {})
            if not container:
                flash('Failed to create a container. Please check the input and try again.')
            else:
                print '--'*20,container
                db().containers.save({
                        'container_id':container['Id'],
                        'user':session['user_name'],
                        'gpu':[0],
                        'max_disk':20020,
                        'max_memory':3000})
            return redirect(url_for('user.container'))
    else:
        flash('Invalid login. Login again.')
        return redrect(url_for('index'));
@app.route("/user/container/del", endpoint='user.container.del', methods=['GET'])
def user_container_del():
    if is_login():
        container = request.args.get('id')
        flag = docker().rm(container=container)
        if flag is None:
            flash('Failed to create a container. Please check the input and try again.')
        else:
            db().containers.remove({'container_id':container,})
            return redirect(url_for('user.container'))
    else:
        flash('Invalid login. Login again.')
        return redrect(url_for('index'));
@app.route("/user/container/stop", endpoint='user.container.stop', methods=['GET'])
def user_container_stop():
    if is_login():
        container = request.args.get('id')
        flag = docker().stop(container=container)
        if flag is None:
            flash('Failed to stop a container. Please check the input and try again.')
        else:
            print 'stoped'
            return redirect(url_for('user.container'))
    else:
        flash('Invalid login. Login again.')
        return redrect(url_for('index'));
@app.route("/user/container/start", endpoint='user.container.start', methods=['GET'])
def user_container_start():
    if is_login():
        container = request.args.get('id')
        flag = docker().start(container=container)
        if flag is None:
            flash('Failed to start a container. Please check the input and try again.')
        else:
            return redirect(url_for('user.container'))
    else:
        flash('Invalid login. Login again.')
        return redrect(url_for('index'));