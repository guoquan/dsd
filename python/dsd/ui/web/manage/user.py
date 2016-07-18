from flask import request, redirect, url_for, render_template, flash
from dsd.ui.web import app
from dsd.ui.web.utils import *
import datetime
from bson.objectid import ObjectId

@app.route("/manage/user", endpoint='manage.user', methods=['GET'])
def manage_user():
    if is_admin():
        docker = get_docker()
        if not docker:
            return no_host_redirect()

        user_lst = list(db.users.find())
        for user in user_lst:
            containers = list(db.containers.find({'user_oid':user['_id']}))
            user['containers'] = len(containers)
            user['ps'] = 0
            for container in containers:
                if 'ps_id' in container and container['ps_id']:
                    ps = docker.container(container['ps_id'])
                    if ps['state']['Running']:
                        user['ps'] += 1
        return render_template('manage_user.html', cur_user=session['user'], user_lst=user_lst)
    else:
        return invalid_login('Administrators only. Login again.')

@app.route("/manage/user/<oid>", endpoint='manage.user.oid', methods=['GET', 'POST'])
def manage_user_oid(oid):
    if is_admin():
        docker = get_docker()
        if not docker:
            return no_host_redirect()

        user_oid = ObjectId(oid)
        user = db.users.find_one({'_id':user_oid})

        if request.method == 'GET':
            user['containers'] = list(db.containers.find({'user_oid':user_oid}))
            if user['containers']:
                for container in user['containers']:
                    container['auth_image'] = db.auth_images.find_one({'_id':container['auth_image_oid']})
                    if 'ps_id' in container and container['ps_id']:
                        container['ps'] = docker.container(container['ps_id'])

            return render_template('manage_user_oid.html', user=user)
        else:
            try:
                user['active'] = bool('active' in request.form and request.form['active'])

                if user['type'] == UserTypes.Administrator:
                    pass
                elif user['type'] == UserTypes.User:
                    try:
                        user['max_container'] = int(request.form['max_container'])
                    except ValueError:
                        error = 'Max container number must be integer.'
                        raise ValueError(error)
                    try:
                        user['max_live_container'] = int(request.form['max_live_container'])
                    except ValueError:
                        error = 'Max live container number must be integer.'
                        raise ValueError(error)
                    try:
                        user['max_gpu'] = int(request.form['max_gpu'])
                    except ValueError:
                        error = 'Max GPU number must be integer.'
                        raise ValueError(error)
                    try:
                        user['max_disk'] = int(request.form['max_disk'])
                    except ValueError:
                        error = 'Max disk volumn must be integer.'
                        raise ValueError(error)
                else:
                    raise ValueError('Unknown user type. Please choose user type from options.')

                if ('new_password' in request.form and request.form['new_password']) or \
                        ('new_again_password' in request.form and request.form['new_again_password']):
                    user['salt'] = os.urandom(16).encode('hex')
                    password = request.form['new_password']
                    password_again = request.form['new_again_password']
                    if password_again != password:
                        error = 'Repeated password must match the password.'
                        raise ValueError('Repeated password does not match')
                    user['password'] = encrypt_password(password, user['username'], user['salt'])

                db.users.save(user)

            except Exception as e:
                flash('Something\'s wrong: ' + str(e), 'warning')
                flash('Nothing is updated due to error.', 'warning')
                #return redirect(url_for('manage.user.add'))
                return render_template('manage_user_oid.html', user=user, error=error)

            flash('User %s is updated.' % user['username'], 'success')
            return render_template('manage_user_oid.html', user=user)
    else:
        return invalid_login('Administrators only. Login again.')

@app.route('/manage/user/add', endpoint='manage.user.add', methods=['GET', 'POST'])
def manage_user_add():
    if is_admin():
        # create user
        if request.method == 'GET':
            config = db.config.find_one()
            return render_template('manage_user_add.html', config=config)
        else:
            try:
                new_user={}
                new_user['active'] = True
                new_user['username'] = request.form['username']
                if db.users.find_one({'username':new_user['username']}):
                    error = 'Try a username not used by others.'
                    raise ValueError('Username already taken.')
                try:
                    new_user['type'] = int(request.form['type'])
                except ValueError:
                    error = 'Wrong user type.'
                    raise ValueError('Please choose user type from options.')
                if new_user['type'] == UserTypes.Administrator:
                    pass
                elif new_user['type'] == UserTypes.User:
                    try:
                        new_user['max_container'] = int(request.form['max_container'])
                    except ValueError:
                        error = 'Max container number must be integer.'
                        raise ValueError(error)
                    try:
                        new_user['max_live_container'] = int(request.form['max_live_container'])
                    except ValueError:
                        error = 'Max live container number must be integer.'
                        raise ValueError(error)
                    try:
                        new_user['max_gpu'] = int(request.form['max_gpu'])
                    except ValueError:
                        error = 'Max GPU number must be integer.'
                        raise ValueError(error)
                    try:
                        new_user['max_disk'] = int(request.form['max_disk'])
                    except ValueError:
                        error = 'Max disk volumn must be integer.'
                        raise ValueError(error)
                else:
                    raise ValueError('Unknown user type. Please choose user type from options.')

                new_user['salt'] = os.urandom(16).encode('hex')
                password = request.form['new_password']
                password_again = request.form['new_again_password']
                if password_again != password:
                    error = 'Repeated password must match the password.'
                    raise ValueError('Repeated password does not match')
                new_user['password'] = encrypt_password(password, new_user['username'], new_user['salt'])

                db.users.save(new_user)
            except Exception as e:
                flash('Something\'s wrong: ' + str(e), 'warning')
                #return redirect(url_for('manage.user.add'))
                config = db.config.find_one()
                return render_template('manage_user_add.html', config=config, error=error, **request.form)

            flash('New user created.', 'success')
            return redirect(url_for('manage.user'))
    else:
        return invalid_login('Administrators only. Login again.')

@app.route('/manage/user/remove/<oid>', endpoint='manage.user.remove.oid', methods=['GET', 'POST'])
def manage_user_remove_oid(oid):
    if is_admin():
        user_oid = ObjectId(oid)
        user = db.users.find_one({'_id':user_oid})
        if user['active']:
            flash('Cannot remove user permanently. User is set to inactive instead.', 'warning')
            user['active'] = False
        else:
            flash('Cannot remove user permanently. User is already inactive.', 'warning')

        db.users.save(user)

        return redirect(url_for('manage.user'))
    else:
        return invalid_login('Administrators only. Login again.')
