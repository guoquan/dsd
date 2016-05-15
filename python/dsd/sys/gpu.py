from dsd.sys.pygpu import *

class gpu():
    def __init__(self):
        self.gpuCount = len(get_devices())
        
    def gpu_info(self):
        gpuStatus = []
        for i in range(self.gpuCount):
            gpuSingle = dict()
            info = get_nvml_info(i)
            gpuSingle['memory_total'] = info['memory']['total'] / 2**20
            gpuSingle['memory_free'] = info['memory']['free'] / 2**20
            gpuSingle['memory_used'] = info['memory']['used'] / 2**20

            gpuSingle['utilization_gpu'] = info['utilization']['gpu']
            gpuSingle['utilization_memory'] = info['utilization']['memory']

            gpuSingle['temperature'] = info['temperature']
            
            gpuStatus.append(gpuSingle)
            
        return gpuStatus