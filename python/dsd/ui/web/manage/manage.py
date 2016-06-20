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

        container_lst = []
        user_container_lst = list(db.containers.find())
        all_containers = docker.ps(all=True)
        for ps_container in all_containers:
            for user_container in user_container_lst:
                if ps_container['container_id'] == user_container['container_id']:
                    user_container = dict(user_container, **ps_container)
                    container_lst.append(user_container)
                    break
        #container_lst = list(db.containers.find())
        print container_lst
        return render_template('manage_container.html', container_lst=container_lst)
    else:
        return invalid_login('Administrators only. Login again.')
