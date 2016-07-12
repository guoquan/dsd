from flask import Flask, request, session, redirect, url_for, render_template, flash
from dsd.ui.web import app
from dsd.ui.web.utils import *
from bson.objectid import ObjectId
import threading

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

critical_fields = ['volume_h', 'volume_c',
                   'data_volume_h', 'data_volume_c',
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

    if source['volume_h'] not in ['0', '']:
        raise ValueError('Wrong workspace setting. Try again.')
    target['volume_h'] = source['volume_h']
    target['volume_c'] = source['volume_c']

    if source['data_volume_h'] not in ['0', '']:
        raise ValueError('Wrong data storage setting. Try again.')
    target['data_volume_h'] = source['data_volume_h']
    target['data_volume_c'] = source['data_volume_c']

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
    # stop the docker container
    # remove the docker container
    # create a new docker container
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
                #flash('Critical change(s) detected in %s. Reinstall is applied automatically.' % critical, 'warning')
                flash('Critical change(s) detected. Reinstall is applied automatically.', 'warning')
                reinstall_container(container)
            db.containers.save(container)
        except Exception as e:
            flash('Something\'s wrong: ' + str(e), 'warning')
        else:
            flash('Container information saved.', 'success')

        return redirect(url_for('user.container'))
    else:
        return invalid_login()

def create_ps(container):
    examine_user(container)
    docker = get_docker()
    # TODO create ps
    if container['gpu']:
        # TODO run with nvdocker
        raise SystemError('Starting with GPU is not implemented yet. Come back later.')
    else:
        user = session['user']
        auth_image = db.auth_images.find_one({'_id':container['auth_image_oid']})
        volumes = []
        if container['volume_h'] and container['volume_c']:
            volumes.append(HCP(container['volume_h'], container['volume_c']))
        if container['data_volume_h'] and container['data_volume_c']:
            volumes.append(HCP(container['data_volume_h'], container['data_volume_c']))
        params = {'image': auth_image['image_name'],
                  'detach': True,
                  'name': user['username']+'_'+container['name']+'_'+str(container['_id']),
                  'ports': [HC(c=port) for port in auth_image['ports']],
                  'volumes': volumes}
        ps_id = docker.create(**params)
        return ps_id

def run_ps(ps_id):
    docker = get_docker()
    docker.start(container=ps_id)

def check_ps(ps, state, done=None, done_args=None,
             timeout=100, fail=None, fail_args=None):
    # TODO check started in new thread
    # invoke callback after change to specific state
    pass

@app.route("/user/container/start", endpoint='user.container.start', methods=['GET', 'POST'])
def user_container_start():
    if is_login():
        docker = get_docker()
        if not docker:
            return no_host_redirect()

        oid = ObjectId(request.values['id'])
        container = db.containers.find_one({'_id':oid})

        try:
            if container['status'] == ContainerStatus.Initial or 'ps_id' not in container:
                ps_id = create_ps(container)
                container['ps_id'] = ps_id
                container['status'] = ContainerStatus.Ready
                db.containers.save(container)
            elif container['status'] == ContainerStatus.Ready:
                pass
            elif container['status'] == ContainerStatus.Starting:
                raise SystemError('Container %s is already starting.' % container['name'])
            elif container['status'] == ContainerStatus.Started:
                raise SystemError('Container %s is already started.' % container['name'])
            elif container['status'] == ContainerStatus.Stopping:
                raise SystemError('Container %s is stopping. Wait after it is stopped.' % container['name'])
            elif container['status'] == ContainerStatus.Stopped:
                pass

            # status in [Ready, Stopped]
            run_ps(container['ps_id'])
            container['status'] = ContainerStatus.Starting
            db.containers.save(container)

            def update():
                # refresh container from db
                container = db.containers.find_one({'_id':container['_id']})
                container['status'] = ContainerStatus.Started
                db.containers.save(container)
            check_ps(ps=container['ps_id'], state='start', done=update, done_args=None)
        except Exception as e:
            flash('Something\'s wrong: ' + str(e), 'warning')
            raise
        else:
            flash('Container %s is running.' % container['name'], 'success')

        return redirect(url_for('user.container'))
    else:
        return invalid_login()

def stop_ps(ps):
    # TODO run ps
    pass

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

def execute_ps(ps, commond):
    # TODO run ps
    pass

@app.route("/user/container/execute", endpoint='user.container.execute', methods=['POST'])
def user_container_execute():
    if is_login():
        flash('Execute not implemented yet.', 'warning')
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
