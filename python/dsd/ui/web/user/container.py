from flask import Flask, request, session, redirect, url_for, render_template, flash
from dsd.ui.web import app
from dsd.ui.web.utils import *
from bson.objectid import ObjectId

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
def jinja2_filter_db(id, collection, fields=None, delimiter=' | '):
    try:
        document = db[collection].find_one({'_id':ObjectId(id)})
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
        if not docker:
            return no_host_redirect()

        container_lst = list(db.containers.find({'user_id':session['user']['id']}))
        for container in container_lst:
            container['image'] = db.images.find_one({'_id':ObjectId(container['image_id'])})
            if container['image']:
                container['image']['image'] = docker.image(container['image']['id'])
        return render_template('user_container.html', container_lst=container_lst)
    else:
        return invalid_login()

@app.route("/user/container/add", endpoint='user.container.add', methods=['GET', 'POST'])
def user_container_add():
    if is_login():
        if request.method == 'GET':
            image_lst = db.images.find()
            return render_template('user_container_add.html', image_lst=image_lst)
        else:
            docker = get_docker()
            if not docker:
                return no_host_redirect()

            user_id = session['user']['id']
            name = request.form['name']
            image_id = request.form['image']
            if db.containers.find_one({'user_id':user_id, 'name':name}):
                flash('You already have a container with the same name! Choose another name for your new container.', 'warning')
                return redirect(url_for('user.container.add'))

            db.containers.save({'user_id':user_id, 'name':name, 'image_id':image_id})
            flash('New container created: %s' % name, 'success')
            return redirect(url_for('user.container'))
    else:
        return invalid_login()

@app.route("/user/container/save", endpoint='user.container.save', methods=['POST'])
def user_container_save():
    pass

@app.route("/user/container/run", endpoint='user.container.run', methods=['POST'])
def user_container_run():
    if is_login():
        docker = get_docker()
        if not docker:
            return no_host_redirect()

        image_tag = request.form['image']
        img = list(db.images.find({'RepoTags':image_tag}))
        ports = img[0]['ports'].split(',')
        ports = [int(port) for port in ports]
        name = request.form['name']
        workspace = "/home/%s/" % session['user']['username']
        devices = [0,1]
        # run it
        try:
            container = docker.run(detach=True,
                            image=image_tag,
                            name=name,
                            ports_dict={},
                            ports_list=ports,
                            volumes={workspace:'/root/workspace','/home/wjyong/data':'/home/data'},
                            devices=devices,)
            db.containers.save({
                            'container_id':container['Id'],
                            'user':session['user']['username'],
                            'gpu':devices,
                            'max_disk':20020,
                            'max_memory':3000})
            flash('Container created.', 'success')
        except Exception as e:
            flash('Failed to create a container. Please check the input and try again.', 'warning')

        return redirect(url_for('user.container'))
    else:
        return invalid_login()

@app.route("/user/container/remove", endpoint='user.container.remove', methods=['GET', 'POST'])
def user_container_remove():
    if is_login():
        docker = get_docker()
        if not docker:
            return no_host_redirect()

        container = request.values['id']
        flag = docker.rm(container=container)
        if flag is None:
            flash('Failed to create a container. Please check the input and try again.', 'warning')
        else:
            db.containers.remove({'container_id':container,})
            return redirect(url_for('user.container'))
    else:
        return invalid_login()

@app.route("/user/container/stop", endpoint='user.container.stop', methods=['GET', 'POST'])
def user_container_stop():
    if is_login():
        docker = get_docker()
        if not docker:
            return no_host_redirect()

        container = request.values['id']
        flag = docker.stop(container=container)
        if flag is None:
            flash('Failed to stop a container. Please check the input and try again.', 'warning')
        else:
            return redirect(url_for('user.container'))
    else:
        return invalid_login()

@app.route("/user/container/restart", endpoint='user.container.restart', methods=['GET', 'POST'])
def user_container_restart():
    if is_login():
        docker = get_docker()
        if not docker:
            return no_host_redirect()

        container = request.values['id']
        flag = docker.start(container=container)
        if flag is None:
            flash('Failed to start a container. Please check the input and try again.', 'warning')
        else:
            return redirect(url_for('user.container'))
    else:
        return invalid_login()

@app.route("/user/container/start", endpoint='user.container.start', methods=['GET', 'POST'])
def user_container_start():
    if is_login():
        docker = get_docker()
        if not docker:
            return no_host_redirect()

        container = request.values['id']
        flag = docker.start(container=container)
        if flag is None:
            flash('Failed to start a container. Please check the input and try again.', 'warning')
        else:
            return redirect(url_for('user.container'))
    else:
        return invalid_login()
