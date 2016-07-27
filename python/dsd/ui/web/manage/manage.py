from flask import Flask, request, session, redirect, url_for, abort, render_template, flash
from dsd.ui.web import app
from dsd.ui.web.utils import *

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
