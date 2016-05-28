from docker import Client
from urlparse import urljoin

class NvDocker():
    def __init__(self, base_url='http://localhost:3476'):
        self.base_url = base_url
        self.cli = Client(base_url)
    
    def _get(self, path):
        return self.cli.get(urljoin(self.base_url, path))
    
    def _queryInfo(self):
        return self._get('/gpu/info/json').json()
        
    def _queryStatus(self):
        return self._get('/gpu/status/json').json()
        
    def _queryCli(self, dev=None):
        if dev:
            if dev is 'all':
                return self._get('/docker/cli/json').json()
            elif isinstance(dev, list):
                return self._get('/docker/cli/json?dev=' + '+'.join(dev)).json()
        else:
            return {'VolumeDriver':'',
                    'Volumes':[],
                    'Devices':[]}
        
    def gpuInfo(self):
        info = self._queryInfo()
        status = self._queryStatus()
        
        gpuStatus = list()
        for dev_info, dev_status in zip(info['Devices'], status['Devices']):
            infoSingle = dict()
            ############## From info
            # Card name
            infoSingle['Model'] = dev_info['Model']
            # device path
            infoSingle['Path'] = dev_info['Path']
            # memory total
            infoSingle['MemoryTotal'] = dev_info['Memory']['Global']
            ############## From status
            # memory used
            infoSingle['MemoryUsed'] = dev_status['Memory']['GlobalUsed']
            # gpu utilization
            infoSingle['UtilizationGpu'] = dev_status['Utilization']['GPU']
            # memory utilization
            infoSingle['UtilizationMemory'] = dev_status['Utilization']['Memory']
            # temperature
            infoSingle['Temperature'] = dev_status['Temperature']
            # processes
            infoSingle['Processes'] = dev_status['Processes']
            
            gpuStatus.append(infoSingle)
            
        return gpuStatus
     
    # cuda version, driver version
    def gpuGlobalInfo(self):
        info = self._queryInfo()
        
        gpuGlobalInfo = dict()
        # cuda version
        gpuGlobalInfo['CudaVersion'] = info['Version']['CUDA']
        # driver version
        gpuGlobalInfo['DriverVersion'] = info['Version']['Driver']

        return gpuGlobalInfo

    def cliStrings(self, dev=None):
        cli = self._queryCli(dev)
        # {"VolumeDriver":"nvidia-docker",
        #  "Volumes":["nvidia_driver_352.39:/usr/local/nvidia:ro"],
        #  "Devices":["/dev/nvidia0",
        #             "/dev/nvidia1",
        #             "/dev/nvidiactl",
        #             "/dev/nvidia-uvm"]}
        
        cliQuery = {'VolumeDriver': cli['VolumeDriver'],
               'Volumes': [tuple(volume.split(':')) for volume in cli['Volumes']],
               'Devices': cli['Devices']
              }
        return cliQuery
    