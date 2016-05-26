from docker import Client
class NvDocker():
    def __init__(self, base_url='http://0.0.0.0:3476'):
        self.base_url = base_url
        self.cli = Client(base_url)
        
    def _queryInfo(self):
        self.status = self.cli.get(self.base_url+'/gpu/status/json').json()
        
    def _queryStatus(self):
        self.info = self.cli.get(self.base_url+'/gpu/info/json').json()
        
    def _queryGpuInfo(self):
        self._queryInfo()
        self._queryStatus()
        
    def GpuInfo(self):
        self._queryGpuInfo()
        
        self.devicesCount = len(self.info['Devices'])
        gpuStatus = list()
        for i in range(self.devicesCount):
            infoSingle = dict()
            ############## From info
            # Card name
            infoSingle['Model'] = self.info['Devices'][i]['Model']
            # device path
            infoSingle['Path'] = self.info['Devices'][i]['Path']
            # memory total
            infoSingle['Memory_Total'] = self.info['Devices'][i]['Memory']['Global']
            ############## From status
            # memory used
            infoSingle['Memory_Used'] = self.status['Devices'][i]['Memory']['GlobalUsed']
            # gpu utilization
            infoSingle['Utilization_Gpu'] = self.status['Devices'][i]['Utilization']['GPU']
            # memory utilization
            infoSingle['Utilization_Memory'] = self.status['Devices'][i]['Utilization']['Memory']
            # temperature
            infoSingle['Temperature'] = self.status['Devices'][i]['Temperature']
            # processes
            infoSingle['Processes'] = self.status['Devices'][i]['Processes']
            
            gpuStatus.append(infoSingle)
            
        return gpuStatus
     
    # cuda version, driver version
    def GpuGlobalInfo(self):
        self._queryGpuInfo()
        
        gpuGlobalInfo = dict()
        # cuda version
        gpuGlobalInfo['Cuda_Version'] = self.info['Version']['CUDA']
        # driver version
        gpuGlobalInfo['Driver_Version'] = self.info['Version']['Driver']

        return gpuGlobalInfo
