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

        container_lst = list(db.containers.find({'user_oid':ObjectId(session['user']['id'])}))
        for container in container_lst:
            container['auth_image'] = db.auth_images.find_one({'_id':container['auth_image_oid']})
            if container['auth_image']:
                container['auth_image']['image'] = docker.image(id=container['auth_image']['image_id'], name=container['auth_image']['name'])
            container['status_str'] = ContainerStatus.STR[container['status']]
        return render_template('user_container.html', container_lst=container_lst)
    else:
        return invalid_login()

critical_fields = ['volumn_h', 'volumn_c',
                   'data_volumn_h', 'data_volumn_c',
                   'gpu', #'cpu', 'memory',
                   ]
def critical_change(source, target):
    for field in critical_fields:
        if field in source and \
            (field not in target or source[field] != str(target[field])):
            return field
    return None

def save_container(source, target):
    critical = critical_change(source, target)
    examine_user(target)

    target['name'] = source['name']

    if source['volumn_h'] not in ['0', '']:
        raise ValueError('Wrong workspace setting. Try again.')
    target['volumn_h'] = source['volumn_h']
    target['volumn_c'] = source['volumn_c']

    if source['data_volumn_h'] not in ['0', '']:
        raise ValueError('Wrong data storage setting. Try again.')
    target['data_volumn_h'] = source['data_volumn_h']
    target['data_volumn_c'] = source['data_volumn_c']

    try:
        target['gpu'] = int(source['gpu'])
    except ValueError:
        raise ValueError('Wrong GPU number. Try again.')

    #target['cpu'] = source['cpu']
    #target['memory'] = source['memory']

    target['notes'] = source['notes']

    return critical

@app.route("/user/container/add", endpoint='user.container.add', methods=['GET', 'POST'])
def user_container_add():
    if is_login():
        if request.method == 'GET':
            auth_image_lst = db.auth_images.find()
            return render_template('user_container_add.html', auth_image_lst=auth_image_lst)
        else:
            docker = get_docker()
            if not docker:
                return no_host_redirect()

            user_oid = ObjectId(session['user']['id'])
            name = request.form['name']
            auth_image_oid = ObjectId(request.form['auth_image'])
            try:
                #if db.containers.find_one({'user_oid':user_oid, 'name':name}):
                #    raise SystemError('You already have a container with the same name! Choose another name for your new container.', 'warning')
                # but I do not check in save page... just also do not check here

                container = {'user_oid':user_oid,
                             'auth_image_oid':auth_image_oid,
                             'status':ContainerStatus.Initial}
                save_container(request.form, container)

                db.containers.save(container)
            except Exception as e:
                flash('Something\'s wrong: ' + str(e), 'warning')
                return redirect(url_for('user.container.add'))
            else:
                flash('New container created: %s' % name, 'success')
            return redirect(url_for('user.container'))
    else:
        return invalid_login()

def examine_user(container):
    user = session['user']
    if container['user_oid'] != ObjectId(user['id']):
        raise SystemError('You can only operate your own container.')

def reinstall_container(container):
    examine_user(container)
    # TODO
    # stop the container
    # remove the container
    # create a new container
    # set status
    flash('Reinstall not implemented yet.', 'warning')

@app.route("/user/container/save", endpoint='user.container.save', methods=['POST'])
def user_container_save():
    if is_login():
        oid = ObjectId(request.form['id'])
        container = db.containers.find_one({'_id':oid})
        try:
            critical = save_container(request.form, container)
            if critical:
                flash('Critical change(s) detected in %s. Reinstall is applied automatically.' % critical, 'warning')
                reinstall_container(container)
            db.containers.save(container)
        except Exception as e:
            flash('Something\'s wrong: ' + str(e), 'warning')
        else:
            flash('Container information saved.', 'success')

        return redirect(url_for('user.container'))
    else:
        return invalid_login()

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


@app.route("/user/container/execute", endpoint='user.container.execute', methods=['POST'])
def user_container_execute():
    if is_login():
        flash('Execute not implemented yet.', 'warning')
        return redirect(url_for('user.container'))
    else:
        return invalid_login()