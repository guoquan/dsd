# Author: joe
# Date: 2016-5-4 23:55
from docker import Client
class pydocker():
    # initialize cli
    def __init__(self):
        print 'init pydocker'
        self.cli = Client(base_url='unix://var/run/docker.sock')
        
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
    
    # docker ps
    # docker ps -a
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
    
    '''
    image (str): The image to run
    command (str or list): The command to be run in the container
    hostname (str): Optional hostname for the container
    user (str or int): Username or UID
    -d detach (bool): Detached mode: run container in the background and print new container Id
    -i stdin_open (bool): Keep STDIN open even if not attached
    -t tty (bool): Allocate a pseudo-TTY
    mem_limit (float or str): Memory limit (format: [number][optional unit], where unit = b, k, m, or g)
    ports (list of ints): A list of port numbers
    environment (dict or list): A dictionary or a list of strings in the following format ["PASSWORD=xxx"] or {"PASSWORD": "xxx"}.
    dns (list): DNS name servers
    volumes (str or list):
    volumes_from (str or list): List of container names or Ids to get volumes from. Optionally a single string joining container id's with commas
    network_disabled (bool): Disable networking
    name (str): A name for the container
    entrypoint (str or list): An entrypoint
    cpu_shares (int): CPU shares (relative weight)
    working_dir (str): Path to the working directory
    domainname (str or list): Set custom DNS search domains
    memswap_limit (int):
    host_config (dict): A HostConfig dictionary
    mac_address (str): The Mac Address to assign the container
    labels (dict or list): A dictionary of name-value labels (e.g. {"label1": "value1", "label2": "value2"}) or a list of names of labels to set with empty values (e.g. ["label1", "label2"])
    volume_driver (str): The name of a volume driver/plugin.
    stop_signal (str): The stop signal to use to stop the container (e.g. SIGINT).
    create_container(self, image, command=None, hostname=None, user=None, detach=False, stdin_open=False, tty=False, 
    mem_limit=None, ports=None, environment=None, dns=None, volumes=None, volumes_from=None, network_disabled=False, 
    name=None, entrypoint=None, cpu_shares=None, working_dir=None, domainname=None, memswap_limit=None, cpuset=None, 
    host_config=None, mac_address=None, labels=None, volume_driver=None, stop_signal=None, networking_config=None)
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
        container  = self.cli.create_container(image=image, 
                                               detach=detach, 
                                               stdin_open=stdin_open, 
                                               tty=tty, 
                                               command=command, 
                                               name=name,
                                               user=user,
                                               ports=ports.keys(),
                                               host_config=self.cli.create_host_config(port_bindings=ports),
                                               volumes=volumes
                                               )
    
        # container  = self.cli.create_container(image='ubuntu:14.04', detach=True, stdin_open=True, tty=True, command='bash', name='testPyDocker1')
        return container
    
    ############################################################################
    '''
    container (str): The container to remove
    v (bool): Remove the volumes associated with the container
    link (bool): Remove the specified link and not the underlying container
    force (bool): Force the removal of a running container (uses SIGKILL)
    '''
    def rm(self, **kwargs):
        container = kwargs.get('container', None)
        self.cli.remove_container(container=container)
