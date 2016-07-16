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
            if 'ps_id' in container and container['ps_id']:
                container['ps'] = docker.container(container['ps_id'])
            if container['auth_image']:
                container['auth_image']['image'] = docker.image(id=container['auth_image']['image_id'], name=container['auth_image']['name'])
            if 'ps' in container:
                container['status_str'] = container['ps']['status_str']
            else:
                container['status_str'] = 'Initial'
        return render_template('user_container.html', container_lst=container_lst, default_host=request.url_root.rsplit(':')[1])
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
                             'auth_image_oid':auth_image_oid}
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
    if container['gpu']:
        # TODO run with nvdocker
        raise SystemError('Starting with GPU is not implemented yet. Come back later.')
    else:
        user = session['user']
        auth_image = db.auth_images.find_one({'_id':container['auth_image_oid']})
        volumes = []
        if container['volume_h'] and container['volume_c']:
            host_path = os.path.join(VOLUME_BASE_WORKSPACES, save_name('-'.join([user['username'], str(container['volume_h'])])))
            ensure_path(host_path)
            client_path = container['volume_c']
            ensure_path(client_path)
            volumes.append(HCP(h=host_path, c=client_path))
        if container['data_volume_h'] and container['data_volume_c']:
            host_path = os.path.join(VOLUME_BASE_DATA, save_name('-'.join(['public', str(container['data_volume_h'])])))
            ensure_path(host_path)
            client_path = container['data_volume_c']
            ensure_path(client_path)
            volumes.append(HCP(h=host_path, c=client_path))
        params = {'image': auth_image['image_name'],
                  'detach': True,
                  'name': save_name('-'.join([user['username'], container['name'], str(container['_id'])])),
                  'ports': [HC(c=port) for port in auth_image['ports']],
                  'volumes': volumes}
        ps_id = docker.create(**params)
        return ps_id

def run_ps(container):
    examine_user(container)
    docker = get_docker()
    docker.start(container=container['ps_id'])

@app.route("/user/container/start", endpoint='user.container.start', methods=['GET', 'POST'])
def user_container_start():
    if is_login():
        docker = get_docker()
        if not docker:
            return no_host_redirect()

        oid = ObjectId(request.values['id'])
        container = db.containers.find_one({'_id':oid})

        try:
            examine_user(container)
            if 'ps_id' not in container or not container['ps_id']:
                ps_id = create_ps(container)
                container['ps_id'] = ps_id
                db.containers.save(container)
            container['ps'] = docker.container(container['ps_id'])
            state_code = container['ps']['state_code']
            if state_code == ContainerState.Paused:
                pass
            elif state_code == ContainerState.Restarting:
                raise SystemError('Container %s is restarting.' % container['name'])
            elif state_code == ContainerState.RunningHealth:
                raise SystemError('Container %s is already running (%s).' % (container['name'], container['ps']['state']['Health']))
            elif state_code == ContainerState.Running:
                raise SystemError('Container %s is already running.' % container['name'])
            elif state_code == ContainerState.RemovalInProgress:
                raise SystemError('Container %s is being removed.' % container['name'])
            elif state_code == ContainerState.Dead:
                pass
            elif state_code == ContainerState.Created:
                pass
            elif state_code == ContainerState.UnFinished:
                raise SystemError('Container %s is not finished.' % container['name'])
            elif state_code == ContainerState.Exited:
                pass

            run_ps(container)

        except Exception as e:
            flash('Something\'s wrong: ' + str(e), 'warning')
        else:
            flash('Container %s is running.' % container['name'], 'success')

        return redirect(url_for('user.container'))
    else:
        return invalid_login()

def stop_ps(container):
    examine_user(container)
    docker = get_docker()
    docker.stop(container=container['ps_id'])

@app.route("/user/container/stop", endpoint='user.container.stop', methods=['GET', 'POST'])
def user_container_stop():
    if is_login():
        docker = get_docker()
        if not docker:
            return no_host_redirect()

        oid = ObjectId(request.values['id'])
        container = db.containers.find_one({'_id':oid})

        try:
            examine_user(container)
            if 'ps_id' not in container or not container['ps_id']:
                raise SystemError('Container %s has never been run.' % container['name'])
            container['ps'] = docker.container(container['ps_id'])
            state_code = container['ps']['state_code']
            if state_code == ContainerState.Paused:
                pass
            elif state_code == ContainerState.Restarting:
                pass
            elif state_code == ContainerState.RunningHealth:
                pass
            elif state_code == ContainerState.Running:
                pass
            elif state_code == ContainerState.RemovalInProgress:
                pass
            elif state_code == ContainerState.Dead:
                raise SystemError('Container %s is already dead.' % container['name'])
            elif state_code == ContainerState.Created:
                raise SystemError('Container %s has never been run.' % container['name'])
            elif state_code == ContainerState.UnFinished:
                pass
            elif state_code == ContainerState.Exited:
                raise SystemError('Container %s is already exited.' % container['name'])

            stop_ps(container)

        except Exception as e:
            flash('Something\'s wrong: ' + str(e), 'warning')
        else:
            flash('Container %s is stopped.' % container['name'], 'success')

        return redirect(url_for('user.container'))
    else:
        return invalid_login()

@app.route("/user/container/restart", endpoint='user.container.restart', methods=['GET', 'POST'])
def user_container_restart():
    if is_login():
        docker = get_docker()
        if not docker:
            return no_host_redirect()

        oid = ObjectId(request.values['id'])
        container = db.containers.find_one({'_id':oid})

        try:
            examine_user(container)
            if 'ps_id' not in container or not container['ps_id']:
                raise SystemError('Container %s has never been run.' % container['name'])
            container['ps'] = docker.container(container['ps_id'])
            state_code = container['ps']['state_code']
            if state_code == ContainerState.Paused:
                flash('Container %s is paused. Still try to restart it.' % container['name'], 'warning')
            elif state_code == ContainerState.Restarting:
                raise SystemError('Container %s is already Restarting.' % container['name'])
            elif state_code == ContainerState.RunningHealth:
                flash('Container %s is running (%s). Still try to restart it.' % (container['name'], container['ps']['state']['Health']), 'warning')
            elif state_code == ContainerState.Running:
                pass
            elif state_code == ContainerState.RemovalInProgress:
                raise SystemError('Container %s is being removed.' % container['name'])
            elif state_code == ContainerState.Dead:
                flash('Container %s is already dead. Just start it.' % container['name'], 'warning')
            elif state_code == ContainerState.Created:
                flash('Container %s has never been run. Just start it.' % container['name'], 'warning')
            elif state_code == ContainerState.UnFinished:
                flash('Container %s is not finished. Still try to restart if.' % container['name'], 'warning')
            elif state_code == ContainerState.Exited:
                flash('Container %s is already exited. Just start it.' % container['name'], 'warning')

            stop_ps(container)
            run_ps(container)

        except Exception as e:
            flash('Something\'s wrong: ' + str(e), 'warning')
        else:
            flash('Container %s is restarted.' % container['name'], 'success')

        return redirect(url_for('user.container'))
    else:
        return invalid_login()

def execute_ps(container, commond):
    # TODO execute commond in ps
    pass

@app.route("/user/container/execute", endpoint='user.container.execute', methods=['POST'])
def user_container_execute():
    if is_login():
        flash('Execute not implemented yet.', 'warning')
        return redirect(url_for('user.container'))
    else:
        return invalid_login()

def remove_ps(container):
    examine_user(container)
    docker = get_docker()
    docker.rm(container=container['ps_id'])

@app.route("/user/container/remove", endpoint='user.container.remove', methods=['GET', 'POST'])
def user_container_remove():
    if is_login():
        docker = get_docker()
        if not docker:
            return no_host_redirect()

        oid = ObjectId(request.values['id'])
        container = db.containers.find_one({'_id':oid})

        try:
            examine_user(container)
            if 'ps_id' in container and container['ps_id']:
                container['ps'] = docker.container(container['ps_id'])
                state_code = container['ps']['state_code']
                # TODO do with differnt situation
                if state_code == ContainerState.Paused:
                    pass
                elif state_code == ContainerState.Restarting:
                    pass
                elif state_code == ContainerState.RunningHealth:
                    pass
                elif state_code == ContainerState.Running:
                    pass
                elif state_code == ContainerState.RemovalInProgress:
                    pass
                elif state_code == ContainerState.Dead:
                    pass
                elif state_code == ContainerState.Created:
                    pass
                elif state_code == ContainerState.UnFinished:
                    pass
                elif state_code == ContainerState.Exited:
                    pass
                stop_ps(container)
                # TODO maybe wait some time? and wait for stop
                remove_ps(container)
            else:
                # never run, no docker ps
                pass
            db.containers.delete_one({'_id':container['_id']})

        except Exception as e:
            flash('Something\'s wrong: ' + str(e), 'warning')
        else:
            flash('Container %s is restarted.' % container['name'], 'success')

        return redirect(url_for('user.container'))
    else:
        return invalid_login()
