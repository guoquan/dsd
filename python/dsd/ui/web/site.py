from flask import request, session, redirect, url_for, render_template, flash
from dsd.ui.web import app
from dsd.ui.web.utils import *
from bson.objectid import ObjectId

@app.route("/", methods=['GET'])
def index():
    if is_login():
        if session['user']['type'] is UserTypes.Administrator:
            return redirect(url_for('manage.index'))
        elif session['user']['type'] is UserTypes.User:
            return redirect(url_for('user.index'))
        else:
            flash('Unrecognized user type. Login again.', 'warning')
            return render_template('index.html')
    else:
        return render_template('index.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html', error=None, next=get_redirect_target())
    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user, message = check_login(username, password)
        if user:
            session['is_login'] = True
            user_id = str(user['_id'])
            del user['_id'] # session cannot hold ObjectId from MongoDB
            user['id'] = user_id
            session['user'] = user
            flash(message)
            return redirect_back()
        else:
            session.pop('is_login', None)
            session.pop('user', None)
            return render_template('login.html', error=message, next=get_redirect_target())

@app.route('/logout')
def logout():
    session.pop('is_login', None)
    session.pop('user', None)
    flash('You were logged out')
    return redirect(url_for('index'))

@app.route("/profile", endpoint='profile', methods=['GET', 'POST'])
def profile():
    if is_login():
        if is_admin():
            base = 'manage'
        else:
            base = 'user'

        error = None
        if request.method == 'POST':
            old_password = request.form['old_password']
            new_password = request.form['new_password']
            new_again_password = request.form['new_again_password']

            user, message = check_login(session['user']['username'], old_password)
            if not user:
                error = 'Old password is incorrect!'
            elif new_password != new_again_password:
                error = 'The two new passwords are not match!'
            else:
                # okey, encrypt the new password
                user['password'] = encrypt_password(new_password, user['username'], user['salt'])
                db.users.save(user)
                flash('Password has been updated!', 'success')
                return redirect(url_for('profile'))

        if is_admin() and 'oid' in request.args:
            user = db.users.find_one({'_id':ObjectId(request.args['oid'])})
            if not user:
                flash('Specific user not found.', 'warning')
        else:
            user = session['user']

        return render_template('profile.html', base=base, user=user, error=error)
    else:
        return invalid_login()

@app.route('/error', endpoint='error')
def error():
    error_message = request.values['error']
    next = request.values['next']
    if not next or not is_safe_url(next):
        next = '#'
    return render_template('error.html', error=error_message, next=next)
