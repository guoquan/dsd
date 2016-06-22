from flask import request, redirect, url_for, render_template, flash
from dsd.ui.web import app
from dsd.ui.web.utils import *
import datetime
from bson.objectid import ObjectId

@app.template_filter('timestamp2datetime')
def jinja2_filter_timestamp2datetime(timestamp):
    return str(datetime.datetime.fromtimestamp(timestamp))

@app.route("/manage/image", endpoint='manage.image', methods=['GET'])
def manage_image():
    if is_admin():
        docker = get_docker()
        if not docker:
            return no_host_redirect()

        all_images = docker.images()
        authorized_images = list(db.images.find())
        return render_template('manage_image.html',
                            image_lst=all_images,
                            authorized_image_lst=authorized_images)
    else:
        return invalid_login('Administrators only. Login again.')

@app.route("/manage/image/remove", endpoint='manage.image.remove', methods=['GET'])
def manage_image_remove():
    if is_admin():
        docker = get_docker()
        if not docker:
            return no_host_redirect()

        image_id = request.args.get('id')
        try:
            image = docker.image(image_id)
            flag = docker.rmi(image=image_id)
        except Exception as e:
            flash(str(e), 'warning')
        else:
            flash('Image removed: %s' % image['RepoTags'], 'success')

        return redirect(url_for('manage.image'))
    else:
        return invalid_login('Administrators only. Login again.')

@app.route("/manage/image/authorize", endpoint='manage.image.authorize', methods=['GET', 'POST'])
def manage_image_authorize():
    if is_admin():
        docker = get_docker()
        if not docker:
            return no_host_redirect()

        if request.method == 'GET':
            image_id = request.args.get('id')
            image_lst = docker.images()
            image = {'id':image_id}
            for image_ in image_lst:
                if image_id == image_['id']:
                    image['RepoTags'] = image_['RepoTags']
            return render_template('manage_image_authorize.html', image=image)
        else:
            image_id = request.form.get('id')
            name = request.form.get('name')
            ports = [int(p) for p in request.form.get('ports').split(' ') if p]
            description = request.form.get('description')

            db.images.save({'id':image_id, 'name':name, 'ports':ports, 'description':description})
            return redirect(url_for('manage.image'))
    else:
        return invalid_login('Administrators only. Login again.')

@app.route("/manage/image/revoke", endpoint='manage.image.revoke', methods=['GET', 'POST'])
def manage_image_revoke():
    if is_admin():
        authorized_id = request.values.get('id')
        try:
            image = db.images.find_one({'_id':ObjectId(authorized_id)})
            image_name = image['name']
            db.images.delete_one({'_id':ObjectId(authorized_id)})
        except Exception as e:
            flash(str(e), 'warning')
        else:
            flash('Authorized image revoked: %s' % image_name, 'success')
        return redirect(url_for('manage.image'))
    else:
        return invalid_login('Administrators only. Login again.')
