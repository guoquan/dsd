from flask import request, redirect, url_for, render_template, flash
from dsd.ui.web import app
from dsd.ui.web.utils import *
from bson.objectid import ObjectId

@app.route("/manage/image", endpoint='manage.image', methods=['GET'])
def manage_image():
    if is_admin():
        docker = get_docker()
        if not docker:
            return no_host_redirect()

        all_images = docker.images(inspect=True)
        authorized_images = list(db.auth_images.find())
        return render_template('manage_image.html',
                            image_lst=all_images,
                            authorized_image_lst=authorized_images)
    else:
        return invalid_login('Administrators only. Login again.')

@app.route("/manage/image/remove", endpoint='manage.image.remove', methods=['GET', 'POST'])
def manage_image_remove():
    if is_admin():
        docker = get_docker()
        if not docker:
            return no_host_redirect()

        image_id = request.values['id']
        try:
            image = docker.image(image_id)
            flag = docker.rmi(image=image_id)
        except Exception as e:
            flash(str(e), 'warning')
        else:
            flash('Image removed: %s' % image['name'], 'success')

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
            image = docker.image(id=request.args['image_id'],
                                 name=request.args['image_name'])
            return render_template('manage_image_authorize.html', image=image,
                                    name=request.args['name'],
                                    ports=request.args['ports'],
                                    description=request.args['description'],)
        elif request.method == 'POST':
            try:
                image_id = request.form['image_id']
                image_name = request.form['image_name']
                name = request.form['name']
                description = request.form['description']
                try:
                    ports = [int(p) for p in request.form['ports'].split(' ') if p]
                except ValueError:
                    raise ValueError('Something is wrong in the port list! Try again.')

                if db.auth_images.find_one({'name':name}):
                    raise ValueError('There is an authorized image with the same name! Choose a discriminative name for the new image.')

                if not docker.image(id=image_id, name=image_name):
                    raise ValueError('Could not found specific image! Try again.')

                db.auth_images.save({'image_id':image_id, 'image_name':image_name, 'name':name, 'ports':ports, 'description':description})
                return redirect(url_for('manage.image'))
            except ValueError as e:
                flash(str(e), 'warning')
                error = str(e)
                #return redirect(url_for('manage.image.authorize', **request.form))
                image = docker.image(id=request.form['image_id'],
                                     name=request.form['image_name'])
                return render_template('manage_image_authorize.html', image=image,
                                       error=error, **request.form)
            except Exception as e:
                print '-'*10, type(e), ':', str(e), e.args
    else:
        return invalid_login('Administrators only. Login again.')

@app.route("/manage/image/<oid>/revoke", endpoint='manage.image.revoke')
def manage_image_revoke(oid):
    if is_admin():
        oid = ObjectId(oid)
        try:
            image = db.auth_images.find_one({'_id':oid})
            image_name = image['name']
            db.auth_images.delete_one({'_id':oid})
        except Exception as e:
            flash(str(e), 'warning')
        else:
            flash('Authorized image revoked: %s' % image_name, 'success')
        return redirect(url_for('manage.image'))
    else:
        return invalid_login('Administrators only. Login again.')
