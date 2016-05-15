# coding:utf-8
import os
import os.path
import time
import psutil
from pynvml import *


class ResourceWatcher(object):

    def __init__(self):
        psutil.cpu_percent()
        self.cli = docker.Client(base_url='unix://var/run/docker.sock')
        nvmlInit()

    @staticmethod
    def cpu_percent(interval=None, percpu=False):
        """return a float or a list representing the CPU utilization

        Args:
            interval: When interval > 0 compares cpu time elapsed before and
                after the interval(blocking). When interval is None compares
                cpu time elapsed since the class .
            percpu: When percpu is true return a list representing every cpu
                core utilization
        """
        return psutil.cpu_percent(interval, percpu)

    @staticmethod
    def get_path_size(path):
        """Return the size of a file or a dir in bytes."""
        if not os.path.exists(path):
            return 0

        if os.path.isfile(path):
            return os.path.getsize(path)

        total_size = 0
        print os.walk(path)
        for root, dirs, files in os.walk(path):
            for directory in dirs:
                total_size += ResourceWatcher.get_path_size(
                    os.path.join(root, directory))
                print directory, total_size
            for file in files:
                total_size += os.path.getsize(os.path.join(root, file))
                print file, total_size
        return total_size

    @staticmethod
    def disk_usage(path):
        """Return disk usage statistics as a namedtuple(struct).

        Only disk partition statistics can be showed.

        Return:
            (total: xxx, used: xxx, free: xxx, percentage: xxx)

        Sample:
            usage = disk_usage('/')
            print usage.total
        """
        return psutil.disk_usage(path)

    @staticmethod
    def memory():
        """Return statistics about system memory usage as a namedtuple.

        Return:
            (total: xxx, available: xxx, percent: xxx, used: xxx, free: xxx)
        """
        return psutil.virtual_memory()

    @staticmethod
    def get_graphical_device_num():
        return nvmlDeviceGetCount()

    @staticmethod
    def get_graphical_device_name(dev_idx):
        handle = nvmlDeviceGetHandleByIndex(dev_idx)
        return nvmlDeviceGetName(handle)

    @staticmethod
    def graphical_memory(dev_idx):
        """Return statistics about graphical memory usage as a namedtuple.

        Return:
            (total: xxx, free: xxx, used: xxx)
        """
        handle = nvmlDeviceGetHandleByIndex(dev_idx)
        info = nvmlDeviceGetMemoryInfo(handle)
        return info

    @staticmethod
    def pids():
        """Return a list of current running PIDs."""
        return psutil.pids()

    @staticmethod
    def process_info(pids, attrs=None):
        """Return a list representing the info of processes in pids.

        Args:
            pids: A list of pid
            attrs: Attributes to get. When attrs is None, all attrs are assumed

        Return:
            If attrs is None, the return value will like
            {
                'cpu_percent': 0.0,
                'create_time': 1463243372.04,           # unix time stamp
                'memory_info': 34852864,                # memory used in bytes
                'memory_percent': 0.04223241225980626,
                'name': 'init',                         # process name
                'pid': 1,                               # process id
                'ppid': 0,                              # parent process id
                'status': 'sleeping',
                'username': 'root'
            }

            Reference: http://pythonhosted.org/psutil/#process-class
        """
        if attrs is None:
            attrs = ['cpu_percent', 'create_time', 'memory_info',
                     'memory_percent', 'name', 'pid', 'ppid', 'status',
                     'username']
        processes = [psutil.Process(pid) for pid in pids]
        for process in processes:
            process.cpu_percent()
        time.sleep(0.1)
        info = []
        for process in processes:
            pinfo = process.as_dict(attrs=attrs)
            if 'memory_info' in pinfo:
                pinfo['memory_info'] = process.memory_info().vms
            info.append(pinfo)
        return info
