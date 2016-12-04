from flask import Flask, request, session, render_template
from dsd.ui.web import app
from dsd.ui.web.utils import *
from bson.objectid import ObjectId

@app.route("/user", endpoint='user.index', methods=['GET'])
def index():
    if is_login():
        docker = get_docker()

        alive = 0
        container_lst = list(db.containers.find({'user_oid':ObjectId(session['user']['oid'])}))
        for container in container_lst:
            container['auth_image'] = db.auth_images.find_one({'_id':container['auth_image_oid']})
            if 'ps_id' in container and container['ps_id']:
                container['ps'] = docker.container(container['ps_id'])
                if container['ps']['running']:
                    alive += 1
            if container['auth_image']:
                container['auth_image']['image'] = docker.image(id=container['auth_image']['image_id'], name=container['auth_image']['name'])
            if 'ps' in container:
                container['status_str'] = container['ps']['status_str']
            else:
                container['status_str'] = 'Initial'

        nvd = get_nvd()
        if nvd:
            gpu_global = nvd.gpuGlobalInfo()
            gpu_lst = nvd.gpuInfo()
        else:
            gpu_global = None
            gpu_lst = []

        user_gpu = get_user_gpu(session['user']['oid'])

        return render_template('user_index.html',
                               count_container=len(container_lst),
                               count_live_container=alive,
                               max_container=session['user']['max_container'],
                               max_live_container=session['user']['max_live_container'],
                               max_gpu=session['user']['max_gpu'],
                               max_disk=session['user']['max_disk'],
                               container_lst=container_lst,
                               default_host=request.url_root.rsplit(':')[1].rstrip('/'),
                               gpu_global=gpu_global,
                               gpu_lst=gpu_lst,
                               user_gpu=user_gpu,
                               )
    else:
        return invalid_login('Administrators only. Login again.')
