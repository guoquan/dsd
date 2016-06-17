from flask import Flask, request, session, redirect, url_for, abort, render_template, flash
from dsd.ui.web import app
from dsd.ui.web.utils import *

@app.route("/user", endpoint='user.index', methods=['GET'])
def index():
    return render_template('user_index.html')

@app.route("/user/container", endpoint='user.container', methods=['GET'])
def user_container():
    if is_login():
        #container_lst = docker().ps(all=True)
        container_lst = []
        user_container_lst = list(db().containers.find({'user':session['user_name']}))
        all_containers = docker().ps(all=True)
        for ps_container in all_containers:
            for user_container in user_container_lst:
                if ps_container['container_id'] == user_container['container_id']:
                    port = [{'PrivatePort':con['PrivatePort'],'PublicPort':con['PublicPort']} for con in ps_container['port']]
                    container = {'status':ps_container['status'],
                                 'name':ps_container['name'],
                                 'image':ps_container['image'],
                                 'state':ps_container['state'],
                                 'port':port,
                                 'gpu':user_container['gpu'],
                                'container_id':ps_container['container_id']}
                    container_lst.append(container)
        return render_template('user_container.html', container_lst=container_lst)
    else:
        flash('Invalid login. Login again.')
        return redirect(url_for('index'));

@app.route("/user/container/add", endpoint='user.container.add', methods=['GET', 'POST'])
def user_container_add():
    if is_login():
        if request.method == 'GET':
            image_lst = db().images.find()
            return render_template('user_container_add.html', image_lst=image_lst)
        else:
            image_tag = request.form['image']
            img = list(db().images.find({'RepoTags':image_tag}))
            ports = img[0]['ports'].split(',')
            ports = [int(port) for port in ports]
            name = request.form['name']
            workspace = "/home/%s/" % session['user_name']
            devices = [0,1]
            # run it
            try:
                container = docker().run(detach=True,
                                image=image_tag,
                                name=name,
                                ports_dict={},
                                ports_list=ports,
                                volumes={workspace:'/root/workspace','/home/wjyong/data':'/home/data'},
                                devices=devices,)
                db().containers.save({
                                'container_id':container['Id'],
                                'user':session['user_name'],
                                'gpu':devices,
                                'max_disk':20020,
                                'max_memory':3000})
                flash('Container created.')
            except Exception as e:
                flash('Failed to create a container. Please check the input and try again.')

            return redirect(url_for('user.container'))
    else:
        flash('Invalid login. Login again.')
        return redirect(url_for('index'));

@app.route("/user/container/remove", endpoint='user.container.remove', methods=['GET'])
def user_container_remove():
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
        return redirect(url_for('index'));

@app.route("/user/container/stop", endpoint='user.container.stop', methods=['GET'])
def user_container_stop():
    if is_login():
        container = request.args.get('id')
        flag = docker().stop(container=container)
        if flag is None:
            flash('Failed to stop a container. Please check the input and try again.')
        else:
            return redirect(url_for('user.container'))
    else:
        flash('Invalid login. Login again.')
        return redirect(url_for('index'));

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
        return redirect(url_for('index'));
