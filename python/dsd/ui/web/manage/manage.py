from flask import Flask, request, session, redirect, url_for, abort, render_template, flash
from dsd.ui.web import app
from dsd.ui.web.utils import *
import requests
import socket

@app.route("/manage", endpoint='manage.index', methods=['GET'])
def index():
    if is_admin():

        nvd = get_nvd()
        if nvd:
            gpu_global = nvd.gpuGlobalInfo()
            gpu_lst = nvd.gpuInfo()
            for gpu in list(db.gpus.find()):
                gpu_lst[gpu['index']]['containers'] = len(gpu['container_oids'])
        else:
            gpu_global = None
            gpu_lst = []

        return render_template('manage_index.html',
                               gpu_global=gpu_global,
                               gpu_lst=gpu_lst,)
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

        unmanaged_lst = docker.ps(all=True)
        total = len(unmanaged_lst)
        try:
            dsd_container = docker.container(socket.gethostname())
            print dsd_container
            unmanaged_lst = [container for container in unmanaged_lst if container['container_id'] != dsd_container['container_id']]
        except None:
            dsd_container = None

        managed_lst = list(db.containers.find())
        managed_ids = []
        managed_alive = 0
        managed_gpu = 0
        managed_alive_gpu = 0
        for container in managed_lst:
            container['user'] = db.users.find_one({'_id':container['user_oid']})
            container['auth_image'] = db.auth_images.find_one({'_id':container['auth_image_oid']})
            if 'ps_id' in container and container['ps_id']:
                container['ps'] = docker.container(container['ps_id'])
                managed_ids.append(container['ps_id'])
                if container['ps']['running']:
                    managed_alive += 1
                    managed_alive_gpu += container['gpu']
            if container['auth_image']:
                container['auth_image']['image'] = docker.image(id=container['auth_image']['image_id'], name=container['auth_image']['name'])
            if 'ps' in container:
                container['status_str'] = container['ps']['status_str']
            else:
                container['status_str'] = 'Initial'
            managed_gpu += container['gpu']

        unmanaged_lst = [container for container in unmanaged_lst if container['container_id'] not in managed_ids]
        unmanaged_alive = 0
        for container in unmanaged_lst:
            if container['status_str'].startswith('Up'):
                unmanaged_alive += 1

        return render_template('manage_container.html', managed_lst=managed_lst,
                               unmanaged_lst=unmanaged_lst, dsd_container=dsd_container,
                               total=total,
                               managed_alive=managed_alive, managed_gpu=managed_gpu, managed_alive_gpu=managed_alive_gpu,
                               unmanaged_alive=unmanaged_alive,
                               default_host=request.url_root.rsplit(':')[1])
    else:
        return invalid_login('Administrators only. Login again.')

@app.route('/manage/container/<id>/start', endpoint='manage.container.start', methods=['GET', 'POST'])
def manage_container_start(id):
    if is_admin():
        try:
            docker = get_docker()
            container = docker.container(id)
            name = container['container_name']
            docker.start(container=id)
        except Exception as e:
            flash('Something\'s wrong: ' + str(e), 'warning')
        else:
            flash('Container %s is running.' % name, 'success')
        return redirect(url_for('manage.container'))
    else:
        return invalid_login('Administrators only. Login again.')

@app.route('/manage/container/<id>/stop', endpoint='manage.container.stop', methods=['GET', 'POST'])
def manage_container_stop(id):
    if is_admin():
        try:
            docker = get_docker()
            container = docker.container(id)
            name = container['container_name']
            docker.stop(container=id)
        except Exception as e:
            flash('Something\'s wrong: ' + str(e), 'warning')
        else:
            flash('Container %s is stopped.' % name, 'success')
        return redirect(url_for('manage.container'))
    else:
        return invalid_login('Administrators only. Login again.')

@app.route('/manage/container/<id>/restart', endpoint='manage.container.restart', methods=['GET', 'POST'])
def manage_container_restart(id):
    if is_admin():
        try:
            docker = get_docker()
            container = docker.container(id)
            name = container['container_name']
            docker.stop(container=id)
            docker.start(container=id)
        except Exception as e:
            flash('Something\'s wrong: ' + str(e), 'warning')
        else:
            flash('Container %s is restarted.' % name, 'success')
        return redirect(url_for('manage.container'))
    else:
        return invalid_login('Administrators only. Login again.')

@app.route('/manage/container/<id>/remove', endpoint='manage.container.remove', methods=['GET', 'POST'])
def manage_container_remove(id):
    if is_admin():
        try:
            docker = get_docker()
            container = docker.container(id)
            name = container['container_name']
            docker.stop(container=id)
            docker.rm(container=id)
        except Exception as e:
            flash('Something\'s wrong: ' + str(e), 'warning')
        else:
            flash('Container %s is removed.' % name, 'success')
        return redirect(url_for('manage.container'))
    else:
        return invalid_login('Administrators only. Login again.')
