from flask import Flask, request, session, redirect, url_for, abort, render_template, flash
from dsd.ui.web import app
from dsd.ui.web.utils import *
import requests

@app.route("/manage", endpoint='manage.index', methods=['GET'])
def index():
    if is_admin():
        return render_template('manage_index.html')
    else:
        return invalid_login('Administrators only. Login again.')

@app.route("/manage/gpu", endpoint='manage.gpu', methods=['GET'])
def manage_gpu():
    if is_admin():
        nvd = get_nvd()
        if not nvd:
            return no_host_redirect()

        gpu_lst = nvd.gpuInfo()
        return render_template('manage_gpu.html', gpu_lst=gpu_lst)
    else:
        return invalid_login('Administrators only. Login again.')

@app.route("/manage/container", endpoint='manage.container', methods=['GET'])
def manage_container():
    if is_admin():
        docker = get_docker()
        if not docker:
            return no_host_redirect()

        container_lst = list(db.containers.find())
        for container in container_lst:
            container['user'] = db.users.find_one({'_id':container['user_oid']})
            container['auth_image'] = db.auth_images.find_one({'_id':container['auth_image_oid']})
            if 'ps_id' in container and container['ps_id']:
                container['ps'] = docker.container(container['ps_id'])
            if container['auth_image']:
                container['auth_image']['image'] = docker.image(id=container['auth_image']['image_id'], name=container['auth_image']['name'])
            if 'ps' in container:
                container['status_str'] = container['ps']['status_str']
            else:
                container['status_str'] = 'Initial'

        return render_template('manage_container.html', container_lst=container_lst)
    else:
        return invalid_login('Administrators only. Login again.')
