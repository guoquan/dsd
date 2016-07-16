from flask import request, redirect, url_for, render_template, flash
from dsd.ui.web import app
from dsd.ui.web.utils import *
import datetime

@app.route("/manage/user", endpoint='manage.user', methods=['GET'])
def manage_user():
    if is_admin():
        user_lst = list(db.users.find())
        return render_template('manage_user.html', cur_user=session['user'], user_lst=user_lst)
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

@app.route('/manage/user/remove', endpoint='manage.user.remove', methods=['POST'])
def manage_user_remove():
    if is_admin():
        # TODO implement user remove
        flash('Not implemented yet.', 'warning')
        return redirect(url_for('manage.user'))
    else:
        return invalid_login('Administrators only. Login again.')
