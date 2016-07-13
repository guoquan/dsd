from docker import Client, tls, errors
from io import BytesIO
import os
import collections
import datetime
import itertools

def namedtuple_with_defaults(typename, field_names, default_values=()):
    T = collections.namedtuple(typename, field_names)
    T.__new__.__defaults__ = (None,) * len(T._fields)
    if isinstance(default_values, collections.Mapping):
        prototype = T(**default_values)
    else:
        prototype = T(*default_values)
    T.__new__.__defaults__ = tuple(prototype)
    return T

HC = namedtuple_with_defaults(u'HC', [u'h', u'c']) # host, container
HCP = namedtuple_with_defaults(u'HCP', [u'h', u'c', u'p']) # host, container, privilege

def _defaultJoin(strings, deli=u':', default=u''):
    return deli.join([string if string is not None else default for string in strings])

def _trimJoin(strings, deli=u':'):
    return deli.join([string for string in strings if string])

def _docker_time(time):
    if isinstance(time, datetime.datetime):
        return datetime
    elif isinstance(time, int):
        return datetime.datetime.fromtimestamp(time)
    elif isinstance(time, basestring):
        try:
            # example u'2016-07-12T14:03:17.995524517Z'
            return datetime.datetime.strptime(time[:26], u'%Y-%m-%dT%H:%M:%S.%f')
        except ValueError:
            pass # then try plan B
        try:
            # example u'0001-01-01T00:00:00Z'
            return datetime.datetime.strptime(time, u'%Y-%m-%dT%H:%M:%SZ')
        except ValueError:
            return u'<cannot parse: %s>' % time
    else:
        return u'<cannot resolve: %s>' % time

def _human_time_abs_delta(delta):
    # this follows https://github.com/docker/docker/blob/master/vendor/src/github.com/docker/go-units/duration.go
    seconds = int(delta.total_seconds())
    if seconds < 1:
        return u'Less than a second'
    elif seconds < 60:
        return u'%d seconds' % seconds
    minutes = int(seconds / 60)
    if minutes == 1:
        return u'About a minute'
    elif minutes < 60:
        return u'%d minutes' % minutes
    hours = int(minutes / 60)
    if hours == 1:
        return u'About a hour'
    elif hours < 48:
        return u'%d hours' % hours
    elif hours < 24*7*2:
        return u'%d days' % (hours/24)
    elif hours < 24*30*3:
        return u'%d weeks' % (hours/24/7)
    elif hours < 24*365*2:
        return u'%d months' % (hours/24/30)
    return u'%d years' % (hours/24/365)

def _docker_status_str(state):
    # this follows https://github.com/docker/docker/blob/master/container/state.go
    if state['Running']:
        if state['Paused']:
            return u'Up %s (Paused)' % _human_time_abs_delta(datetime.datetime.now() - _docker_time(state['StartedAt']))

        if state['Restarting'] :
            return u'Restarting (%d) %s ago' % (state['ExitCode'], _human_time_abs_delta(datetime.datetime.now() - _docker_time(state['FinishedAt'])))

        if 'Health' in state and state['Health']:
            return u'Up %s (%s)' % (_human_time_abs_delta(datetime.datetime.now() - _docker_time(state['StartedAt'])), str(state['Health']))

        return u'Up %s' % _human_time_abs_delta(datetime.datetime.now() - _docker_time(state['StartedAt']))

    if 'RemovalInProgress' in state and state['RemovalInProgress']:
        return u'Removal In Progress'

    if state['Dead']:
        return u'Dead'

    if not _docker_time(state['StartedAt']):
        return u'Created'

    if not _docker_time(state['FinishedAt']):
        return u''

    return u'Exited (%d) %s ago' % (state['ExitCode'], _human_time_abs_delta(datetime.datetime.now() - _docker_time(state['FinishedAt'])))

class PyDocker():
    # initialize cli
    def __init__(self, base_url='unix://var/run/docker.sock', **tls_params):
        try:
            if tls_params:
                self.cli = Client(base_url, tls=tls.TLSConfig(**tls_params), version='auto')
            else:
                self.cli = Client(base_url, version='auto')
        except errors.DockerException:
            pass

    def alive(self):
        try:
            self.images(inspect=False)
        except Exception as e:
            return False
        return True

    '''  docker images
    '''
    def images(self, inspect=False, all=False):
        if inspect:
            images_api = self.cli.images(quiet=True, all=all)
            images_info_all = [self.image(id=id) for id in images_api]
            images_info_all = list(itertools.chain(*images_info_all))
        else:
            images_api = self.cli.images(all=all)
            images_info_all = []
            for image in images_api:
                img_info_single = {}
                img_info_single['id'] = image['Id']
                img_info_single['size'] = image['Size'] / 1e9 # turn in GB
                img_info_single['created'] = _docker_time(image['Created'])
                img_info_single['repo_tags'] = image['RepoTags']

                # each image may have multiple RepoTags
                # for each one we add an instance to the list
                for repo_tag in img_info_single['repo_tags']:
                    img_info_single['name'] = repo_tag
                    [img_info_single['repository'], img_info_single['tag']] = repo_tag.split(':')
                    images_info_all.append(img_info_single.copy())

        return images_info_all

    '''  docker image
    '''
    def image(self, id=None, name=None):
        if not id and not name:
            return None

        image = self.cli.inspect_image(id or name)
        img_info = {}
        img_info['id'] = image['Id']
        img_info['size'] = image['Size'] / 1e9 # turn in GB
        img_info['created'] = _docker_time(image['Created'])
        img_info['repo_tags'] = image['RepoTags']
        if 'Config' in image and image['Config'] and 'ExposedPorts' in image['Config']:
            try:
                img_info['ports'] = [int(port.split('/')[0]) for port in image['Config']['ExposedPorts']]
            except (ValueError):
                img_info['ports'] = []

        # each image may have multiple RepoTags
        # for each one we add an instance to the list
        if name:
            if name in img_info['repo_tags']:
                img_info['name'] = name
                [img_info['repository'], img_info['tag']] = name.split(':')
                return img_info
            else:
                return None
        else:
            img_infos = []
            for repo_tag in img_info['repo_tags']:
                img_info['name'] = repo_tag
                [img_info['repository'], img_info['tag']] = repo_tag.split(':')
                img_infos.append(img_info.copy())
            return img_infos

    '''  docker ps
         docker ps -a
    '''
    def ps(self, all=False):
        ps_api = self.cli.containers(all=all)

        ps_all = []
        for ps in ps_api:
            ps_single = {}
            # container naming problem:
            # 1. they have a forward slash in the front!
            # according to some discussions:
            #   https://github.com/docker/docker/issues/7519
            #   https://github.com/docker/docker/issues/6705
            # this slash imply a parent relationship
            # names are prefixed with their parent
            # where only one '/' means local to docker daemon
            # let's just use the part after last slash
            # 2. a name list?
            # according to some discussions again:
            #   https://github.com/docker/libnetwork/issues/737
            # a container could have multiple name for the convenience of network linking
            # let's just use the first name in list as main name and keep the whole list for reference
            ps_single['container_name'] = ps['Names'][0].split('/')[-1]
            ps_single['container_id'] = ps['Id']
            ps_single['image_name'] = ps['Image']
            ps_single['image_id'] = ps['ImageID']

            ps_single['command'] = ps['Command']
            ps_single['status_str'] = ps['Status'] # TODO process this string to guess more accurate state
            ps_single['created'] = _docker_time(ps['Created'])
            # remote api before version 1.23, for example on my Mac,
            #   does not have this field 'State'
            # but it is avaliable in inspect
            ps_single['state'] = ps.get('State', None)
            ports = []
            for port in ps['Ports']:
                if port['Type'] == u'tcp': # u'tcp' == 'tcp' is True
                    ports.append(HCP(h=port['PublicPort'],
                                     c=port['PrivatePort'],
                                     p=port['IP']))
            ps_single['ports'] = ports # need process
            ps_single['names'] = [name.split('/')[-1] for name in ps['Names']]

            ps_all.append(ps_single)

        return ps_all

    '''  docker inspect (container)
    '''
    def container(self, container_id):
        # created|restarting|running|paused|exited
        # container_id could be id or name
        api = self.cli.inspect_container(container_id)

        container = {}
        container['container_name'] = api['Name'].split('/')[-1]
        container['container_id'] = api['Id']
        container['image_name'] = api['Config']['Image']
        container['image_id'] = api['Image']

        container['command'] = ' '.join(api['Config']['Cmd'])
        container['status_str'] = _docker_status_str(api['State'])
        container['created'] = _docker_time(api['Created'])
        container['state'] = api['State'] # https://github.com/docker/docker/blob/master/container/state.go
        ports = []
        for k, v in api['NetworkSettings']['Ports'].iteritems():
            client_port, port_type = k.split('/')
            if port_type == u'tcp': # u'tcp' == 'tcp' is True
                for vv in v:
                    ports.append(HCP(h=vv['HostPort'],
                                     c=client_port,
                                     p=vv['HostIp']))
        container['ports'] = ports
        container['names'] = [api['Name'].split('/')[-1]]

        return container


    '''  docker run
    '''
    def run(self, **kwargs):
        container = self.create(**kwargs)
        return self.start(container)

    '''  create a container but not run
    '''
    def create(self, image,
            detach=False, stdin_open=False, tty=False,
            command=None, name=None, user=None,
            ports=[], devices=[],
            volumes=[], volume_driver=None):
        if image is None:
            raise ValueError(u'Must specify an image to create a container!')

        # ports
        # ports is a list of HC tuple
        portList = [port.c for port in ports]
        portMap = {port.c:port.h for port in ports}

        # volumes
        # volumes is a list of HCP tuple
        volumes = [volume for volume in volumes if volume.c]
        volumeList = [volume.c for volume in volumes]
        volumeMapList = [_trimJoin(volume) for volume in volumes]

        # devices
        # devices is a list of HCP tuple
        devices_ = []
        for device in devices:
            if device.h is not None and device.c is not None:
                devices_.append(device)
            elif device.h is None and device.c is not None:
                devices_.append(HCP(device.c, device.c, device.p))
            elif device.c is None and device.h is not None:
                devices_.append(HCP(device.h, device.h, device.p))
            else:
                devices.remove(device)
        devices = devices_
        deviceMapList = [_defaultJoin(device, default='rwm') for device in devices]

        # prepare host_config
        host_config = self.cli.create_host_config(port_bindings=portMap,
                                                  binds=volumeMapList,
                                                  devices=deviceMapList)

        # create container
        container = self.cli.create_container(image=image,
                                              detach=detach, stdin_open=stdin_open, tty=tty,
                                              command=command, name=name, user=user,
                                              ports=portList,
                                              volumes=volumeList,
                                              volume_driver=volume_driver,
                                              host_config=host_config)
        if container:
            return container.get('Id')
        else:
            return 0 # return 0(falsy) on error


    '''  docker start
    '''
    def start(self, container):
        response = self.cli.start(container=container)
        return response


    '''  docker stop
    '''
    def stop(self, container=None, timeout=0):
        response = self.cli.stop(container=container, timeout=timeout)
        return response


    '''  docker attach
    '''
    def attach(self, container=None, stdout=False, stderr=False, stream=False, logs=None):
        response = self.cli.attach(container=containerId,
                                   stdout=stdout,
                                   stderr=stderr,
                                   stream=stream,
                                   logs=logs)
        return response

    '''  docker rm
    '''
    def rm(self, container):
        self.cli.remove_container(container=container)


    '''  docker build
    '''
    def build(self, **kwargs):
        dockerfilePath = kwargs.get('dockerfilePath', None)

        path = kwargs.get('path', None)

        tag = kwargs.get('tag', None)

        quiet = kwargs.get('quiet', True)  #  Whether to return the status

        fileobj = kwargs.get('fileobj', None)  #  A file object to use as the Dockerfile. (Or a file-like object)

        nocache = kwargs.get('nocache', True)  #  Don't use the cache when set to True

        rm = kwargs.get('rm', False)  #  Remove intermediate containers. (Changed the default value to False)

        stream = kwargs.get('stream', False)  #  Return a blocking generator you can iterate over to retrieve build output as it happens

        timeout = kwargs.get('timeout', 3)  #  HTTP timeout

        custom_context = kwargs.get('custom_context', True)  #  Optional if using fileobj

        encoding = kwargs.get('encoding', 'gzip')  # The encoding for a stream. Set to gzip for compressing

        pull = kwargs.get('pull', False)  #  Downloads any updates to the FROM image in Dockerfiles

        forcerm = kwargs.get('forcerm', False)  #  Always remove intermediate containers, even after unsuccessful builds

        dockerfile = kwargs.get('dockerfile', None)  #  path within the build context to the Dockerfile

        '''
        container_limits (dict): A dictionary of limits applied to each container created by the build process. Valid keys:
        memory (int): set memory limit for build
        memswap (int): Total memory (memory + swap), -1 to disable swap
        cpushares (int): CPU shares (relative weight)
        cpusetcpus (str): CPUs in which to allow execution, e.g., "0-3", "0,1"
        '''
        container_limits_default = {'memory':1024,
                                    'memswap':1024,
                                    'cpushares':4,
                                    'cpusetcpus':"0-3"}

        container_limits = kwargs.get('container_limits', None)

        decode = kwargs.get('decode', False)  #  If set to True, the returned stream will be decoded into dicts on the fly. Default False.

        # read Dockerfile
        if fileobj is None:
            dockerfile_default = 'Dockerfile'
            with open(os.path.join(dockerfilePath, dockerfile_default), 'r') as f:
                dockerfileStr = f.read()

            dockerfileObj = BytesIO(dockerfileStr.encode('utf-8'))
            fileobj = dockerfileObj

        response = [line for line in self.cli.build(fileobj=fileobj, tag=tag)]
        return response


    '''  docker rmi
    '''
    def rmi(self, image=None, force=False, noprune=False):
        self.cli.remove_image(image=image,
                              force=force,
                              noprune=noprune)

    ''' docker volume inspect
    '''
    def volume_inspect(self, name):
        return self.cli.inspect_volume(name)
