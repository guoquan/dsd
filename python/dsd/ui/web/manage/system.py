from flask import Flask, request, session, redirect, url_for, abort, render_template, flash
from dsd.ui.web import app
from dsd.ui.web.utils import *
import os
import shutil

@app.route("/manage/system", endpoint='manage.system', methods=['GET'])
def manage_system(error={}, config=None):
    if is_admin():
        docker = get_docker()
        nvd = get_nvd()

        if not config:
            config = db.config.find_one()
        return render_template('manage_system.html', error=error, config=config, docker=bool(docker), nvd=bool(nvd))
    else:
        return invalid_login('Administrators only. Login again.')

@app.route("/manage/system/host", endpoint='manage.system.host', methods=['POST'])
def manage_system_host():
    if is_admin():
        docker_url = request.form['docker_url']
        use_tls = bool('use_tls' in request.form and request.form['use_tls'])
        path_client_cert = request.form['path_client_cert']
        path_client_key = request.form['path_client_key']
        path_ca = request.form['path_ca']
        nvd_url = request.form['nvd_url']

        config = db.config.find_one()
        config['docker']['url'] = docker_url
        config['docker']['tls'] = {'use_tls':use_tls,
                                   'path_client_cert':path_client_cert,
                                   'path_client_key':path_client_key,
                                   'path_ca':path_ca}
        config['nvd']['url'] = nvd_url
        db.config.save(config)

        docker = get_docker(True)
        nvd = get_nvd(True)

        flash('Host information has been updated!', 'success')
        return redirect(url_for('manage.system'))
    else:
        return invalid_login('Administrators only. Login again.')

@app.route("/manage/system/default", endpoint='manage.system.default', methods=['POST'])
def manage_system_default():
    if is_admin():
        config = db.config.find_one()
        try:
            config['default']['user']['max_container'] = request.form['default_user_max_container']
            config['default']['user']['max_live_container'] = request.form['default_user_max_live_container']
            config['default']['user']['max_gpu'] = request.form['default_user_max_gpu']
            config['default']['user']['max_disk'] = request.form['default_user_max_disk']

            try:
                config['default']['user']['max_container'] = int(config['default']['user']['max_container'])
            except ValueError:
                error={'resource':'Set default user max container an integer.'}
                raise ValueError('Default user max container must be an integer.')

            try:
                config['default']['user']['max_live_container'] = int(config['default']['user']['max_live_container'])
            except ValueError:
                error={'resource':'Set default user max live container an integer.'}
                raise ValueError('Default user max container must be an integer.')

            try:
                config['default']['user']['max_gpu'] = int(config['default']['user']['max_gpu'])
            except ValueError:
                error={'resource':'Set default user max GPU an integer.'}
                raise ValueError('Default user max GPU must be an integer.')

            try:
                config['default']['user']['max_disk'] = int(config['default']['user']['max_disk'])
            except ValueError:
                error={'resource':'Set default user max disk an integer.'}
                raise ValueError('Default user max disk must be an integer.')

            db.config.save(config)
        except Exception as e:
            flash('Something\'s wrong: %s.' % str(e), 'warning')
            flash('Nothing is updated due to error.', 'warning')
            return manage_system(error=error, config=config)
        else:
            flash('Default configuration has been updated!', 'success')
        return redirect(url_for('manage.system'))
    else:
        return invalid_login('Administrators only. Login again.')


def prepare_path(path, old_path, prefix, message_path_name='', error={}):
    if os.path.isabs(path):
        error.update({'resource':'Set %s path to a relative path within %s.' % (message_path_name, prefix)})
        raise ValueError('Absolute path is not allow for %s.' % (message_path_name))

    if path.startswith('..'):
        error.update({'resource':'Set %s to a relative path within %s.' % (message_path_name, prefix)})
        raise ValueError('Path of %s must be in %s.' % (message_path_name, prefix))

    old_full = os.path.join(prefix, old_path)
    if os.path.exists(old_full):
        ensure_path(full)
        if not os.path.samefile(old_full, full):
            flash('Files are detected in old %s. They are moved to the new path.' % message_path_name)
            shutil.move(old_full, full)
    return path

@app.route("/manage/system/resource", endpoint='manage.system.resource', methods=['POST'])
def manage_system_resource():
    if is_admin():
        config = db.config.find_one()
        try:
            error = {}

            old_workspaces = config['resource']['volume']['workspaces']
            old_data = config['resource']['volume']['data']

            config['resource']['max_gpu_assignment'] = request.form['resource_max_gpu_assignment']
            config['resource']['volume']['workspaces'] = request.form['resource_volume_workspaces']
            config['resource']['volume']['data'] = request.form['resource_volume_data']

            try:
                config['resource']['max_gpu_assignment'] = int(config['resource']['max_gpu_assignment'])
            except ValueError:
                error.update({'resource':'Set Max GPU Assignment an integer.'})
                raise ValueError('Max GPU Assignment must be an integer.')

            prefix = config['env']['volume_prefix']

            config['resource']['volume']['workspaces'] = \
                prepare_path(config['resource']['volume']['workspaces'], old_workspaces, prefix, \
                             message_path_name='workspaces base', error=error)
            config['resource']['volume']['data'] = \
                prepare_path(config['resource']['volume']['data'], old_data, prefix, \
                             message_path_name='data base', error=error)

            db.config.save(config)
        except Exception as e:
            flash('Something\'s wrong: %s.' % str(e), 'warning')
            flash('Nothing is updated due to error.', 'warning')
            return manage_system(error=error, config=config)
        else:
            flash('Resource configuration has been updated!', 'success')
        return redirect(url_for('manage.system'))
    else:
        return invalid_login('Administrators only. Login again.')
