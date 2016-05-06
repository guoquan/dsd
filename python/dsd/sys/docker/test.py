from pydocker import pydocker

docker = pydocker()


print'##############docker images#################'
ims = docker.images()
for im in ims:
    print im['RepoTags'], '---', im['repository'], '---',im['tag']


print
print'##############docker ps -a #################'
pses = docker.ps(all=True)
for ps in pses:
    print ps['name'], '---',ps['image'], ps['state'], ps['status']
