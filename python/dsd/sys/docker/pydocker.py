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

HC = namedtuple_with_defaults('HC', ['h', 'c']) # host, container
HCP = namedtuple_with_defaults('HCP', ['h', 'c', 'p']) # host, container, privilege

def _defaultJoin(strings, deli=':', default=''):
    return deli.join([string if string is not None else default for string in strings])

def _trimJoin(strings, deli=':'):
    return deli.join([string for string in strings if string])

def _docker_time(time):
    if isinstance(time, datetime.datetime):
        return datetime
    elif isinstance(time, int):
        return datetime.datetime.fromtimestamp(time)
    elif isinstance(time, basestring):
        try:
            return datetime.datetime.strptime(time[:26], '%Y-%m-%dT%H:%M:%S.%f')
        except ValueError:
            return '<cannot parse: %s>' % time
    else:
        return '<cannot resolve: %s>' % time

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
            self.images()
        except Exception as e:
            return False
        return True

    '''  docker images
    '''
    def images(self, inspect=True):
        images_api = self.cli.images()

        if inspect:
            images_info_all = [self.image(id=image['Id']) for image in images_api]
            images_info_all = list(itertools.chain(*images_info_all))
        else:
            images_info_all = []
            for image in images_api:
                img_info_single = {}
                img_info_single['id'] = image['Id']
                img_info_single['size'] = image['Size']/1e9
                img_info_single['created'] = _docker_time(image['Created'])
                img_info_single['repo_tags'] = image['RepoTags']

                # each image may have multiple RepoTags
                # for each one we add an instance to the list
                for repo_tag in img_info_single['repo_tags']:
                    img_info_single['name'] = repo_tag
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
        img_info['size'] = image['Size']/1e9
        img_info['created'] = _docker_time(image['Created'])
        img_info['repo_tags'] = image['RepoTags']
        try:
            img_info['ports'] = [int(port.split('/')[0]) for port in image['Config']['ExposedPorts']]
        except (ValueError, KeyError):
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
    def ps(self, **kwargs):
        ps_api = None
        if 'all' in kwargs:
            ps_api = self.cli.containers(all=True)
        else:
            ps_api = self.cli.containers()

        ps_all = list()
        for ps in ps_api:
            ps_single = dict()
            ps_single['container_id'] = ps['Id']
            ps_single['image'] = ps['Image']
            ps_single['imageid'] = ps['ImageID']
            ps_single['command'] = ps['Command']
            ps_single['created'] = ps['Created']
            ps_single['status'] = ps['Status']
            ps_single['state'] = ps['State']
            ps_single['port'] = ps['Ports']
            ps_single['name'] = ps['Names'][0]

            ps_all.append(ps_single)

        return ps_all


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
            raise ValueError('Must specify an image to create a container!')

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

        # tr create container
        try:
            container = self.cli.create_container(image=image,
                                                  detach=detach, stdin_open=stdin_open, tty=tty,
                                                  command=command, name=name, user=user,
                                                  ports=portList,
                                                  volumes=volumeList,
                                                  volume_driver=volume_driver,
                                                  host_config=host_config)
            return container
        except Exception, e:
            print e
            raise e
            return None


    '''  docker start
    '''
    def start(self, container):
        try:
            response = self.cli.start(container=container)
            return True
        except Exception, e:
            print e
            raise e
            return None


    '''  docker stop
    '''
    def stop(self, **kwargs):
        container = kwargs.get('container', None)
        timeout = kwargs.get('timeout', 0)
        try:
            response = self.cli.stop(container=container, timeout=timeout)
            return True
        except Exception, e:
            print e
            raise e
            return None


    '''  docker attach
    '''
    def attach(self, **kwargs):
        container = kwargs.get('container', None)
        stdout = kwargs.get('stdout', False)
        stderr = kwargs.get('stderr', False)
        stream = kwargs.get('stream', False)
        logs = kwargs.get('logs', None)
        try:
            response = self.cli.attach(container=containerId,
                                       stdout=stdout,
                                       stderr=stderr,
                                       stream=stream,
                                       logs=logs)
            return response
        except Exception, e:
            print e
            raise e
            return None

    '''  docker rm
    '''
    def rm(self, **kwargs):
        container = kwargs.get('container', None)
        # assert(container!=None)
        try:
            self.cli.remove_container(container=container)
            return True
        except Exception, e:
            print e
            raise e
            return None


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
            print dockerfileStr
            dockerfileObj = BytesIO(dockerfileStr.encode('utf-8'))
            fileobj = dockerfileObj

        try:
            response = [line for line in self.cli.build(fileobj=fileobj, tag=tag)]
            return response
        except Exception, e:
            print e
            raise e
            return None


    '''  docker rmi
    '''
    def rmi(self, **kwargs):
        image = kwargs.get('image', None)
        force  = kwargs.get('force', False)
        noprune  = kwargs.get('noprune', False)
        try:
            self.cli.remove_image(image=image,
                                  force=force,
                                  noprune=noprune)
            return True
        except Exception, e:
            print e
            raise e
            return None

    ''' docker volume inspect
    '''
    def volume_inspect(self, name):
        return self.cli.inspect_volume(name)
