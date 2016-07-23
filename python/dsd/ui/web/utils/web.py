import logging
from flask import session, redirect, url_for, flash, request
from urlparse import urlparse, urljoin
from dsd.ui.web.utils.basic import *

def check_login(username, password):
    user = db.users.find_one({'username':username})
    if not user:
        return None, 'No such user!'
    elif not user['active']:
        return None, 'User inactive.'
    elif encrypt_password(password, user['username'], user['salt']) == user['password']:
        return user, 'Login succeed!'
    else:
        _logger.debug('check_login: %s | %s | %s' % (password, user['username'], user['salt']))
        _logger.debug('check_login: %s != %s' % (encrypt_password(password, user['username'], user['salt']), user['password']))
        return None, 'Password mismatch!'

def is_login():
    return 'is_login' in session and session['is_login']

def is_admin():
    return is_login() and session['user']['type'] is UserTypes.Administrator

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc

def get_redirect_target():
    for target in request.values.get('next', None), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return target
    return None

def redirect_back(endpoint='index', **values):
    if 'next' in request.form:
        target = request.form['next']
    else:
        target = None
    if not target or not is_safe_url(target):
        target = url_for(endpoint, **values)
    return redirect(target)

def invalid_login(message='Invalid login. Login again.', next=None):
    flash(message, 'warning')
    if not next:
        next = request.url
    return redirect(url_for('login', next=next))

def no_host_redirect(state_message=None, user_back=None):
    if not state_message:
        state_message = 'Unable to connect to the host.'
    if is_admin():
        flash(state_message + ' Please check the system configuration.', 'danger')
        return redirect(url_for('manage.system'))
    else:
        return redirect(url_for('error', error=state_message+' Please contact system administrator.', next=get_redirect_target()))
