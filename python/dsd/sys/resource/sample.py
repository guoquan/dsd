# coding:utf-8
import sys
import datetime
import resource_watcher as rw


def format(value, type):
    factor = {'B': 1.0, 'K': 1024.0, 'M': 1024.0 ** 2, 'G': 1024.0 ** 3}
    return value / factor[type]


if __name__ == '__main__':
    watcher = rw.ResourceWatcher()
    print ''

    print 'cpu usage: %d%%' % watcher.cpu_percent()
    percent = watcher.cpu_percent(percpu=True)
    for i, per in enumerate(percent):
        print '    core %d: %d%%' % (i, per),
    print '\n'

    mem = watcher.memory()
    print 'memory usage: %.2f%%' % mem.percent
    print '    total: %.2fG' % format(mem.total, 'G'),
    print '    used: %.2fG' % format(mem.used, 'G'),
    print '    free: %.2fG' % format(mem.free, 'G'),
    print '\n'

    path = sys.path[0]
    disk = watcher.disk_usage(path)
    dir_size = watcher.get_path_size(path)
    file_size = watcher.get_path_size(__file__)
    print 'wording directory: ', path
    print 'dirctory size: %.2fK' % format(dir_size, 'K')
    print 'script size: %.2fK' % format(file_size, 'K')
    print 'disk partition usage: %.2f%%' % disk.percent
    print '    total: %.2fG' % format(disk.total, 'G'),
    print '    used: %.2fG' % format(disk.used, 'G'),
    print '    free: %.2fG' % format(disk.free, 'G'),
    print '\n'

    pids = watcher.pids()
    attrs = ['pid', 'cpu_percent', 'memory_percent', 'create_time', 'name']
    info = watcher.process_info(pids, attrs)
    info.sort(key=lambda x: x['cpu_percent'], reverse=True)
    print 'top 10 process:'
    print ' pid     cpu      mem        create_time      name'
    for pinfo in info[:10]:
        ctime = datetime.datetime.fromtimestamp(pinfo['create_time']) \
            .strftime("%Y-%m-%d %H:%M:%S")
        print '%5d  %6.2f%%  %6.2f%%  %s  %s' % (pinfo['pid'],
                                                 pinfo['cpu_percent'],
                                                 pinfo['memory_percent'],
                                                 ctime,
                                                 pinfo['name'])
    print ''
