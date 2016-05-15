from docker import Client
from io import BytesIO
import os

class pydocker():
    # initialize cli
    def __init__(self, base_url='unix://var/run/docker.sock'):
        print 'init pydocker'
        self.cli = Client(base_url)
    
    '''  docker images
    '''
    def images(self):
        images_api = self.cli.images()
        images_info_all = list()
        for imgage in images_api:
            img_info_single = dict()
            img_info_single['RepoTags'] = imgage['RepoTags'][0]
            repoTag = imgage['RepoTags'][0].split(':')
            img_info_single['repository'] = repoTag[0]
            img_info_single['tag'] = repoTag[1]
            
            img_info_single['id'] = imgage['Id']
            img_info_single['size'] = imgage['Size']/1e9
            img_info_single['created'] = imgage['Created']
            
            images_info_all.append(img_info_single)
        return images_info_all
    

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
        image = kwargs['image']
        assert(image!=None)
        detach = kwargs.get('detach', False)
        stdin_open = kwargs.get('stdin_open', False)
        tty = kwargs.get('tty', False)
        command = kwargs.get('command', None)
        name = kwargs.get('name', None)
        user = kwargs.get('user', None)
        ports = kwargs.get('ports', None)
        volumes = kwargs.get('volumes', None)
        devices = kwargs.get('devices', None)
        
        # volumes
        volumesList = None
        if volumes is not None:
            volumesList = [key+':'+value for key, value in volumes.items()]
        
        # devices
        devicesList = None
        if devices is not None:
            devicesList = [dev+':'+dev+':rwm' for dev in devices]

        try:
            container  = self.cli.create_container(image=image, 
                                               detach=detach, 
                                               stdin_open=stdin_open, 
                                               tty=tty, 
                                               command=command, 
                                               name=name,
                                               user=user,
                                               ports=ports.keys(),
                                               volumes=volumes.values(),
                                               host_config=self.cli.create_host_config(
                                                                                        port_bindings=ports, 
                                                                                        binds=volumesList,
                                                                                        devices=devicesList),
                                               )
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