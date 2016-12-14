import logging
from flask import session, flash
from dsd.sys.docker.pydocker import HC, HCP
from bson.objectid import ObjectId
from dsd.ui.web.utils.basic import *
import urllib2
import requests

_logger = logging.getLogger()

def get_user_gpu(user_oid):
    if not isinstance(user_oid, ObjectId):
        user_oid = ObjectId(user_oid)
    docker = get_docker()
    containers = list(db.containers.find({'user_oid':user_oid}))
    user_gpu = 0
    if containers:
        for container in containers:
            if container['gpu'] and \
                    'ps_id' in container and container['ps_id']:
                ps = docker.container(container['ps_id'])
                if ps['running']:
                    user_gpu += container['gpu']
    return user_gpu

def get_user_live(user_oid):
    if not isinstance(user_oid, ObjectId):
        user_oid = ObjectId(user_oid)
    docker = get_docker()
    containers = list(db.containers.find({'user_oid':user_oid}))
    live = 0
    for container in containers:
        if 'ps_id' in container and container['ps_id']:
            container['ps'] = docker.container(container['ps_id'])
            if container['ps']['running']:
                live += 1
    return live

def examine_user(container, user):
    if container['user_oid'] != ObjectId(user['_id']):
        raise SystemError('You can only operate your own container.')

critical_fields = ['auth_image_oid',
                   'volume_h', 'volume_c',
                   'data_volume_h', 'data_volume_c',
                   'gpu', #'cpu', 'memory',
                   ]
def critical_change(target, source):
    for field in critical_fields:
        if field in source and \
            (field not in target or source[field] != str(target[field])):
            return field
    return None

def save_container(container, source, user):
    critical = critical_change(container, source)
    container['name'] = source['name']
    #container['auth_image_oid'] = ObjectId(source['auth_image_oid']) # don't allow change image
    if source['volume_h'] not in ['0', '']:
        raise ValueError('Wrong workspace setting. Try again.')
    container['volume_h'] = source['volume_h']
    container['volume_c'] = source['volume_c']
    if source['data_volume_h'] not in ['0', '']:
        raise ValueError('Wrong data storage setting. Try again.')
    container['data_volume_h'] = source['data_volume_h']
    container['data_volume_c'] = source['data_volume_c']
    try:
        container['gpu'] = int(source['gpu'])
    except ValueError:
        raise ValueError('Wrong GPU number. Try again.')
    #container['cpu'] = source['cpu']
    #container['memory'] = source['memory']
    container['notes'] = source['notes']
    db.containers.save(container)

    if critical and 'ps_id' in container and container['ps_id']:
        #flash('Critical change(s) detected in %s. Reinstall is applied automatically.' % critical, 'warning')
        flash('Critical change(s) detected. Reinstall is applied automatically.')
        docker = get_docker()
        ps = docker.container(container['ps_id'])
        was_running = ps['running']
        remove_ps(container, user)
        if was_running:
            container['ps_id'] = create_ps(container)
            db.containers.save(container)
            run_ps(container)

def create_ps(container, user):
    examine_user(container, user)
    docker = get_docker()
    config = db.config.find_one()
    auth_image = db.auth_images.find_one({'_id':container['auth_image_oid']})
    volumes = []
    if container['volume_h'] and container['volume_c']:
        dsd_path = os.path.join(config['env']['volume_prefix'],
                                config['resource']['volume']['workspaces'],
                                save_name('-'.join([user['username'], str(container['volume_h'])])))
        ensure_path(dsd_path)
        host_path = os.path.join(config['env']['host_volume_prefix'],
                                 config['resource']['volume']['workspaces'],
                                 save_name('-'.join([user['username'], str(container['volume_h'])])))
        client_path = container['volume_c']
        volumes.append(HCP(h=host_path, c=client_path))
    if container['data_volume_h'] and container['data_volume_c']:
        dsd_path = os.path.join(config['env']['volume_prefix'],
                                config['resource']['volume']['data'],
                                save_name('-'.join(['public', str(container['data_volume_h'])])))
        ensure_path(dsd_path)
        host_path = os.path.join(config['env']['host_volume_prefix'],
                                 config['resource']['volume']['data'],
                                 save_name('-'.join(['public', str(container['data_volume_h'])])))
        client_path = container['data_volume_c']
        volumes.append(HCP(h=host_path, c=client_path))
    params = {'image': auth_image['image_name'],
              'detach': True,
              'name': save_name('-'.join([user['username'], container['name'], str(container['_id'])])),
              'ports': [HC(c=port) for port in auth_image['ports']],
              'volumes': volumes}

    if container['gpu']:
        nvd = get_nvd()
        if not nvd:
            return no_host_redirect('Unable to connect to the nvidia-docker host.', )
        try:
            gpu_indexes = gpu_dispatch(container['gpu'])
            gpu_params = nvd.cliParams(dev=gpu_indexes)
        except (requests.exceptions.HTTPError, urllib2.URLError) as e:
            raise SystemError('Can\'t generate docker configuration according to your current GPU setting. Adjust it and try start the container again.')

        for volume in gpu_params['volumes']:
            try:
                docker.volume_inspect(volume.h)
            except errors.NotFound:
                break
        else:
            del gpu_params['volume_driver']

        #print params
        #print gpu_params
        dict_deep_update(params, gpu_params)
    #print params

    # create the container
    ps_id = docker.create(**params)

    # update gpu list
    if container['gpu']:
        for gpu_index in gpu_indexes:
            gpu = db.gpus.find_one({'index':gpu_index})
            gpu['container_oids'].append(container['_id'])

    container['ps_id'] = ps_id
    db.containers.save(container)
    return ps_id

def run_ps(container, user):
    examine_user(container, user)
    user_gpu = get_user_gpu(user['_id'])
    if user_gpu + container['gpu'] > user['max_gpu']:
        raise SystemError('You can only have %d GPU(s) running. Adjust container setting and try start the container again.' % user['max_gpu'])
    docker = get_docker()
    docker.start(container=container['ps_id'])

def stop_ps(container, user):
    examine_user(container, user)
    docker = get_docker()
    docker.stop(container=container['ps_id'])

def execute_ps(container, command, user):
    examine_user(container, user)
    # TODO execute commond in ps
    pass

def remove_ps(container, user):
    examine_user(container, user)
    docker = get_docker()
    ps = docker.container(container['ps_id'])
    state = ps['raw']['State'] # using the raw interface
    if ps['running'] or ('RemovalInProgress' in state and state['RemovalInProgress']):
        stop_ps(container, user)
        # FIXME shall we wait some time for the container to be really stopped
    docker.rm(container=container['ps_id'])
    del container['ps_id']
    db.containers.save(container)

def get_container(container_oid):
    if not isinstance(container_oid, ObjectId):
        container_oid = ObjectId(container_oid)
    container = db.containers.find_one({'_id':container_oid})
    if not container:
        raise SystemError('Specified container not found.')
    return container

def get_user(user_oid):
    if not user_oid:
        user_oid = session['user']['oid']
    if not isinstance(user_oid, ObjectId):
        user_oid = ObjectId(user_oid)
    user = db.users.find_one({'_id':user_oid})
    if not user:
        raise SystemError('Specified user not found.')
    return user

def get_container_user(container_oid, user_oid):
    container = get_container(container_oid)
    user = get_user(user_oid)
    examine_user(container, user)
    return container, user

def get_state_code(container):
    docker = get_docker()
    if 'ps_id' not in container or not container['ps_id']:
        raise SystemError('Container %s has never been run.' % container['name'])
    ps = docker.container(container['ps_id'])
    return ps['state']

def container_add(source, user_oid=None):
    user = get_user(user_oid)
    if user['max_container'] <= db.containers.find({'user_oid':user['_id']}).count():
        raise SystemError('You can have at most %d containers.' % user['max_container'])
    if db.containers.find_one({'user_oid':user['_id'], 'name':source['name']}):
        raise SystemError('You already have a container with the same name %s! Choose another name for your new container.' % source['name'])
    container = {'user_oid':user['_id'],
                 'auth_image_oid':ObjectId(source['auth_image_oid'])}
    save_container(container, source, user)
    return container

def container_save(container_oid, source, user_oid=None):
    container, user = get_container_user(container_oid, user_oid)
    save_container(container, source, user)
    return container

def container_reinstall(container_oid, user_oid=None):
    container, user = get_container_user(container_oid, user_oid)
    if 'ps_id' not in container or not container['ps_id']:
        raise SystemError('Container %s has never been run. No need to reinstall.' % container['name'])
    remove_ps(container, user)
    return container

def container_start(container_oid, user_oid=None):
    container, user = get_container_user(container_oid, user_oid)
    if user['max_live_container'] <= get_user_live(user['_id']):
        raise SystemError('You can have at most %d container(s) running.' % user['max_live_container'])
    if 'ps_id' not in container or not container['ps_id']:
        ps_id = create_ps(container, user)
    state_code = get_state_code(container)
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
    run_ps(container, user)
    return container

def container_stop(container_oid, user_oid=None):
    container, user = get_container_user(container_oid, user_oid)
    state_code = get_state_code(container)
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
    stop_ps(container, user)
    return container

def container_restart(container_oid, user_oid=None):
    container, user = get_container_user(container_oid, user_oid)
    state_code = get_state_code(container)
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
    stop_ps(container, user)
    run_ps(container, user)
    return container

def container_execute(container_oid, command, user_oid=None):
    container, user = get_container_user(container_oid, user_oid)
    raise SystemError('Execute is not implemented.')

def container_remove(container_oid, user_oid=None):
    container, user = get_container_user(container_oid, user_oid)
    if 'ps_id' in container and container['ps_id']:
        remove_ps(container, user)
    db.containers.delete_one({'_id':container['_id']})
    return container

def unmanaged_start(id):
    docker = get_docker()
    container = docker.container(id)
    name = container['container_name']
    docker.start(container=id)
    return name

def unmanaged_stop(id):
    docker = get_docker()
    container = docker.container(id)
    name = container['container_name']
    docker.stop(container=id)
    return name

def unmanaged_restart(id):
    docker = get_docker()
    container = docker.container(id)
    name = container['container_name']
    docker.stop(container=id)
    docker.start(container=id)
    return name

def unmanaged_remove(id):
    docker = get_docker()
    container = docker.container(id)
    name = container['container_name']
    docker.stop(container=id)
    docker.rm(container=id)
    return name
