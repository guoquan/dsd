from flask import Flask, request, session, redirect, url_for, render_template, flash
from dsd.ui.web import app
from dsd.ui.web.utils import *
from bson.objectid import ObjectId
import threading
import urllib2
import requests

@app.template_filter('docker_image')
def jinja2_filter_docker_image(id, fields=None, delimiter=' | '):
    docker = get_docker()
    if not docker:
        return '<no docker connection>'

    try:
        image = docker.image(id)
    except Exception as e:
        return '<%s>' % str(e)
    else:
        if not fields:
            fields = [('Image: %s', 'RepoTags'), ('Size: %s GB', 'size')]

    return delimiter.join([format % image[field] for format, field in fields if field in image])

@app.template_filter('db')
def jinja2_filter_db(oid, collection, fields=None, delimiter=' | '):
    try:
        document = db[collection].find_one({'_id':ObjectId(oid)})
    except Exception as e:
        return '<%s>' % str(e)
    else:
        if not fields:
            fields = [('ObjectId: %s', '_id')]
    return delimiter.join([format % document[field] for format, field in fields if field in document])

@app.route("/user/container", endpoint='user.container', methods=['GET'])
def user_container():
    if is_login():
        docker = get_docker()

        alive = 0
        container_lst = list(db.containers.find({'user_oid':ObjectId(session['user']['oid'])}))
        for container in container_lst:
            container['auth_image'] = db.auth_images.find_one({'_id':container['auth_image_oid']})
            if 'ps_id' in container and container['ps_id']:
                container['ps'] = docker.container(container['ps_id'])
                if container['ps']['running']:
                    alive += 1
            if container['auth_image']:
                container['auth_image']['image'] = docker.image(id=container['auth_image']['image_id'], name=container['auth_image']['name'])
            if 'ps' in container:
                container['status_str'] = container['ps']['status_str']
            else:
                container['status_str'] = 'Initial'

        user_gpu = get_user_gpu(session['user']['oid'])
        gpu_num = db.gpus.find().count()

        return render_template('user_container.html',
                               count_container=len(container_lst),
                               count_live_container=alive,
                               max_container=session['user']['max_container'],
                               max_live_container=session['user']['max_live_container'],
                               max_gpu=session['user']['max_gpu'],
                               max_disk=session['user']['max_disk'],
                               user_gpu=user_gpu,
                               container_lst=container_lst,
                               gpu_num=gpu_num,
                               default_host=request.url_root.rsplit(':')[1])
    else:
        return invalid_login()

@app.route("/user/container/add", endpoint='user.container.add', methods=['GET', 'POST'])
def user_container_add():
    if is_login():
        if session['user']['max_container'] <= db.containers.find({'user_oid':ObjectId(session['user']['oid'])}).count():
            flash('You can have at most %d containers.' % session['user']['max_container'], 'warning')
            return redirect(url_for('user.container'))

        if request.method == 'GET':
            auth_image_lst = db.auth_images.find()
            gpu_num = db.gpus.find().count()
            return render_template('user_container_add.html', auth_image_lst=auth_image_lst, gpu_num=gpu_num)
        else:
            try:
                name = container_add(request.form)
            except Exception as e:
                flash('Something\'s wrong: ' + str(e), 'warning')
                return redirect(url_for('user.container.add'))
            else:
                flash('New container %s is created.' % name, 'success')
            return redirect(url_for('user.container'))
    else:
        return invalid_login()

@app.route("/user/container/save", endpoint='user.container.save', methods=['POST'])
def user_container_save():
    if is_login():
        oid = request.form['oid']
        try:
            name = container_save(oid, request.form)
        except Exception as e:
            flash('Something\'s wrong: ' + str(e), 'warning')
        else:
            flash('Container %s is updated.' % name, 'success')

        return redirect(url_for('user.container'))
    else:
        return invalid_login()

@app.route("/user/container/<oid>/reinstall", endpoint='user.container.reinstall')
def user_container_reinstall(oid):
    if is_login():
        try:
            name = container_reinstall(oid)
        except Exception as e:
            flash('Something\'s wrong: ' + str(e), 'warning')
        else:
            flash('Container %s is reinstalled.' % name, 'success')
        return redirect(url_for('user.container'))
    else:
        return invalid_login()

@app.route("/user/container/<oid>/start", endpoint='user.container.start')
def user_container_start(oid):
    if is_login():
        try:
            name = container_start(oid)
        except Exception as e:
            flash('Something\'s wrong: ' + str(e), 'warning')
            #raise
        else:
            flash('Container %s is running.' % name, 'success')
        return redirect(url_for('user.container'))
    else:
        return invalid_login()

@app.route("/user/container/<oid>/stop", endpoint='user.container.stop')
def user_container_stop(oid):
    if is_login():
        try:
            name = container_stop(oid)
        except Exception as e:
            flash('Something\'s wrong: ' + str(e), 'warning')
        else:
            flash('Container %s is stopped.' % name, 'success')
        return redirect(url_for('user.container'))
    else:
        return invalid_login()

@app.route("/user/container/<oid>/restart", endpoint='user.container.restart')
def user_container_restart(oid):
    if is_login():
        try:
            name = container_restart(oid)
        except Exception as e:
            flash('Something\'s wrong: ' + str(e), 'warning')
        else:
            flash('Container %s is restarted.' % name, 'success')
        return redirect(url_for('user.container'))
    else:
        return invalid_login()

@app.route("/user/container/execute", endpoint='user.container.execute', methods=['POST'])
def user_container_execute():
    if is_login():
        flash('Execute not implemented yet.', 'warning')
        return redirect(url_for('user.container'))
    else:
        return invalid_login()

@app.route("/user/container/<oid>/remove", endpoint='user.container.remove')
def user_container_remove(oid):
    if is_login():
        try:
            name = container_remove(oid)
        except Exception as e:
            flash('Something\'s wrong: ' + str(e), 'warning')
        else:
            flash('Container %s is removed.' % name, 'success')
        return redirect(url_for('user.container'))
    else:
        return invalid_login()
