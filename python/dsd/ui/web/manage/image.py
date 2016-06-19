from flask import Flask, request, session, redirect, url_for, abort, render_template, flash
from dsd.ui.web import app
from dsd.ui.web.utils import *
import itertools
import datetime

def groupby(data, keyfunc):
    data = sorted(data, key=keyfunc)
    keys = []
    groups = []
    for k, g in itertools.groupby(data, keyfunc):
        keys.append(k)
        groups.append(list(g))      # Store group iterator as a list
    return dict(zip(keys, groups))

@app.template_filter('timestamp2datetime')
def jinja2_filter_timestamp2datetime(timestamp):
    return str(datetime.datetime.fromtimestamp(timestamp))

@app.route("/manage/image", endpoint='manage.image', methods=['GET'])
def manage_image():
    if is_admin():
        all_images = docker.images()
        all_images_d = groupby(all_images, lambda image: image['repository'] if 'repository' in image else None)
        authorized_images = list(db.images.find())
        return render_template('manage_image.html',
                            image_lst=all_images,
                            image_dict=all_images_d,
                            authorized_image_lst=authorized_images)
    else:
        flash('Invalid login. Login again.')
        return redirect(url_for('index'))

@app.route("/manage/image/remove", endpoint='manage.image.remove', methods=['GET'])
def manage_image_remove():
    if is_admin():
        image = request.args.get('id')
        flag = docker.rmi(image=image)
        if flag is None:
            flash('Failed to del a image. Please check the input and try again.')
        else:
            return redirect(url_for('image'))
    else:
        flash('Invalid login. Login again.')
        return redirect(url_for('index'))

@app.route("/manage/image/authorize", endpoint='manage.image.authorize', methods=['GET', 'POST'])
def manage_image_authorize():
    if is_admin():
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
            ports = request.form.get('ports')
            RepoTags = request.form.get('RepoTags')
            description = request.form.get('description')
            db.images.save({'id':image_id, 'ports':ports, 'RepoTags':RepoTags, 'description':description})
            return redirect(url_for('image'))
    else:
        flash('Invalid login. Login again.')
        return redirect(url_for('index'))

@app.route("/manage/image/revoke", endpoint='manage.image.revoke', methods=['GET'])
def manage_image_revoke():
    if is_admin():
        image_id = request.args.get('id')
        db.images.remove({'id':image_id})
        return redirect(url_for('image'))
    else:
        flash('Invalid login. Login again.')
        return redirect(url_for('index'))
