from flask import request, redirect, url_for, render_template, flash
from dsd.ui.web import app
from dsd.ui.web.utils import *
import socket
from bson.objectid import ObjectId

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
        for container in unmanaged_lst:
            unmanaged = db.unmanaged.find_one({'ps_id':container['container_id']})
            if unmanaged:
                container['user'] = db.users.find_one({'_id':unmanaged['user_oid']})
        unmanaged_alive = 0
        for container in unmanaged_lst:
            if container['status_str'].startswith('Up'):
                unmanaged_alive += 1
        user_lst = list(db.users.find({'active':True, 'type':UserTypes.User}))

        return render_template('manage_container.html', managed_lst=managed_lst,
                               unmanaged_lst=unmanaged_lst, dsd_container=dsd_container,
                               total=total,
                               managed_alive=managed_alive, managed_gpu=managed_gpu, managed_alive_gpu=managed_alive_gpu,
                               unmanaged_alive=unmanaged_alive,
                               user_lst=user_lst,
                               default_host=request.url_root.rsplit(':')[1])
    else:
        return invalid_login('Administrators only. Login again.')

@app.route('/manage/unmanaged/<id>/start', endpoint='manage.unmanaged.start', methods=['GET', 'POST'])
def manage_unmanaged_start(id):
    if is_admin():
        try:
            name = unmanaged_start(id)
        except Exception as e:
            flash('Something\'s wrong: ' + str(e), 'warning')
        else:
            flash('Unmanaged container %s is running.' % name, 'success')
        return redirect(default_url_for('manage.container'))
    else:
        return invalid_login('Administrators only. Login again.')

@app.route('/manage/unmanaged/<id>/stop', endpoint='manage.unmanaged.stop', methods=['GET', 'POST'])
def manage_unmanaged_stop(id):
    if is_admin():
        try:
            name = unmanaged_stop(id)
        except Exception as e:
            flash('Something\'s wrong: ' + str(e), 'warning')
        else:
            flash('Unmanaged container %s is stopped.' % name, 'success')
        return redirect(default_url_for('manage.container'))
    else:
        return invalid_login('Administrators only. Login again.')

@app.route('/manage/unmanaged/<id>/restart', endpoint='manage.unmanaged.restart', methods=['GET', 'POST'])
def manage_unmanaged_restart(id):
    if is_admin():
        try:
            name = unmanaged_restart(id)
        except Exception as e:
            flash('Something\'s wrong: ' + str(e), 'warning')
        else:
            flash('Unmanaged container %s is restarted.' % name, 'success')
        return redirect(default_url_for('manage.container'))
    else:
        return invalid_login('Administrators only. Login again.')

@app.route('/manage/unmanaged/<id>/remove', endpoint='manage.unmanaged.remove', methods=['GET', 'POST'])
def manage_unmanaged_remove(id):
    if is_admin():
        try:
            name = unmanaged_remove(id)
        except Exception as e:
            flash('Something\'s wrong: ' + str(e), 'warning')
        else:
            flash('Unmanaged container %s is removed.' % name, 'success')
        return redirect(default_url_for('manage.container'))
    else:
        return invalid_login('Administrators only. Login again.')

@app.route("/manage/unmanaged/<id>/assign", endpoint='manage.unmanaged.assign', methods=['GET', 'POST'])
def manage_unmanaged_assign(id):
    if is_login():
        try:
            docker = get_docker()
            container = docker.container(id)
            if not container:
                raise SystemError('Specified container is not found.')
            unmanaged = db.unmanaged.find_one({'ps_id':id})
            if request.values:
                user_oid = ObjectId(request.values.get('user_oid', None))
            else:
                user_oid = None
            if user_oid:
                user = db.users.find_one({'_id':user_oid})
                if unmanaged:
                    unmanaged.update({'user_oid':user_oid})
                else:
                    unmanaged = {'user_oid':user_oid, 'ps_id':id}
                db.unmanaged.save(unmanaged)
                flash('Unmanaged container %s is assigned to %s.' % (container['container_name'], user['username']), 'success')
            else:
                if unmanaged:
                    user = db.users.find_one({'_id':unmanaged['user_oid']})
                    db.unmanaged.delete_one(unmanaged)
                    flash('Unmanaged container %s is released from %s.' % (container['container_name'], user['username']), 'success')
                else:
                    raise SystemError('Unmanaged container %s is not assigned to any one.' % container['container_name'])
        except Exception as e:
            flash('Something\'s wrong: ' + str(e), 'warning')
            return redirect(default_url_for('manage.container'))
        return redirect(default_url_for('manage.container'))
    else:
        return invalid_login()
