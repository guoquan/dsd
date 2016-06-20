from flask import Flask, request, session, redirect, url_for, abort, render_template, flash
from dsd.ui.web import app
from dsd.ui.web.utils import *

@app.route("/manage/system", endpoint='manage.system', methods=['GET'])
def manage_system(errors={}):
    if is_admin():
        docker = get_docker()
        nvd = get_nvd()

        config = db.config.find_one()
        return render_template('manage_system.html', errors=errors, config=config, docker=(docker is not None), nvd=(nvd is not None))
    else:
        return invalid_login('Administrators only. Login again.')

@app.route("/manage/system/host", endpoint='manage.system.host', methods=['POST'])
def manage_system_host():
    if is_admin():
        docker = get_docker()
        nvd = get_nvd()

        docker_url = request.form.get('docker_url')
        nvd_url = request.form.get('nvd_url')
        config = db.config.find_one()
        config['docker_url'] = docker_url
        config['nvd_url'] = nvd_url
        db.config.save(config)

        docker = get_docker(True)
        nvd = get_nvd(True)

        flash('Host information has been updated!')
        return redirect(url_for('manage.system'))
    else:
        return invalid_login('Administrators only. Login again.')

@app.route("/manage/system/user", endpoint='manage.system.user', methods=['POST'])
def manage_system_user():
    if is_admin():
        default_max_container = request.form.get('default_max_container')
        default_max_disk = request.form.get('default_max_disk')
        config = db.config.find_one()
        config['default_max_container'] = default_max_container
        config['default_max_disk'] = default_max_disk
        db.config.save(config)

        flash('User configuration information has been updated!')
        return redirect(url_for('manage.system'))
    else:
        return invalid_login('Administrators only. Login again.')
