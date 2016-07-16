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
            return render_template('manage_user_add.html')
        else:
            # TODO implement user addition
            flash('Not implemented yet.', 'warning')
            return redirect(url_for('manage.user.add'))
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
