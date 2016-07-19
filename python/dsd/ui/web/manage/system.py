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
        docker = get_docker()
        nvd = get_nvd()

        docker_url = request.form['docker_url']
        use_tls = bool(request.form['use_tls'])
        path_client_cert = request.form['path_client_cert']
        path_client_key = request.form['path_client_key']
        path_ca = request.form['path_ca']
        nvd_url = request.form['nvd_url']

        config = db.config.find_one()
        config['docker_url'] = docker_url
        config['docker_tls'] = {'use_tls':use_tls,
                                'path_client_cert':path_client_cert,
                                'path_client_key':path_client_key,
                                'path_ca':path_ca}
        config['nvd_url'] = nvd_url
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

@app.route("/manage/system/resource", endpoint='manage.system.resource', methods=['POST'])
def manage_system_resource():
    if is_admin():
        config = db.config.find_one()
        try:
            cur_workspaces = config['resource']['volume']['workspaces']
            cur_data = config['resource']['volume']['data']

            config['resource']['max_gpu_assignment'] = request.form['resource_max_gpu_assignment']
            config['resource']['volume']['workspaces'] = request.form['resource_volume_workspaces']
            config['resource']['volume']['data'] = request.form['resource_volume_data']

            try:
                config['resource']['max_gpu_assignment'] = int(config['resource']['max_gpu_assignment'])
            except ValueError:
                error={'resource':'Set Max GPU Assignment an integer.'}
                raise ValueError('Max GPU Assignment must be an integer.')

            if os.path.exists(os.path.join(config['env']['volume_prefix'], cur_workspaces)):
                #os.renames(cur_workspaces, config['resource']['volume']['workspaces'])
                flash('Files are detected in old workspaces base. They are moved to the new path automatically.')
                shutil.move(os.path.join(config['env']['volume_prefix'], cur_workspaces),
                            os.path.join(config['env']['volume_prefix'], config['resource']['volume']['workspaces']))
            if os.path.exists(os.path.join(config['env']['volume_prefix'], cur_data)):
                #os.renames(cur_data, config['resource']['volume']['data'])
                flash('Files are detected in old data base. They are moved to the new path automatically.')
                shutil.move(os.path.join(config['env']['volume_prefix'], cur_data),
                            os.path.join(config['env']['volume_prefix'], config['resource']['volume']['data']))

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
