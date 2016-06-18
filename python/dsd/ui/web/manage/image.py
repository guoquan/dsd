from flask import Flask, request, session, redirect, url_for, abort, render_template, flash
from dsd.ui.web import app
from dsd.ui.web.utils import *

@app.route("/manage/image", endpoint='manage.image', methods=['GET'])
def manage_image():
    if is_admin():
        unauthorized_image_lst = []
        authorized_image_lst = []
        image_lst = docker().images()
        db_image_lst = list(db().images.find())
        for image in image_lst:
            unauthorized = True
            if len(db_image_lst) > 0:
                for db_image in db_image_lst:
                    if image['id'] == db_image['id']:
                        unauthorized = False
                        authorized_image = {'id':image['id'], 'RepoTags':image['RepoTags'],
                                       'ports':db_image['ports'],'description':db_image['description']}
                        authorized_image_lst.append(authorized_image)
                        break
            if unauthorized:
                unauthorized_image = {'id':image['id'], 'RepoTags':image['RepoTags']}
                unauthorized_image_lst.append(unauthorized_image)

        return render_template('manage_image.html', image_lst=image_lst,
                               unauthorized_image_lst=unauthorized_image_lst,
                               authorized_image_lst=authorized_image_lst)
    else:
        flash('Invalid login. Login again.')
        return redirect(url_for('index'))

@app.route("/manage/image/remove", endpoint='manage.image.remove', methods=['GET'])
def manage_image_remove():
    if is_admin():
        image = request.args.get('id')
        flag = docker().rmi(image=image)
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
            image_lst = docker().images()
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
            db().images.save({'id':image_id, 'ports':ports, 'RepoTags':RepoTags, 'description':description})
            return redirect(url_for('image'))
    else:
        flash('Invalid login. Login again.')
        return redirect(url_for('index'))

@app.route("/manage/image/revoke", endpoint='manage.image.revoke', methods=['GET'])
def manage_image_revoke():
    if is_admin():
        image_id = request.args.get('id')
        db().images.remove({'id':image_id})
        return redirect(url_for('image'))
    else:
        flash('Invalid login. Login again.')
        return redirect(url_for('index'))
