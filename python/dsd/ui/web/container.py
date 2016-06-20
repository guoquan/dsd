from flask import Flask, request, session, redirect, url_for, render_template, flash
from dsd.ui.web import app
from dsd.ui.web.utils import *

@app.route("/container", endpoint='container.index', methods=['GET'])
def index():
    if is_login():
        return render_template('container_index.html',
                               images=docker.images(),
                               containers=docker.ps(all=True))
    else:
        return invalid_login()

@app.route("/container/run", endpoint='container.run', methods=['POST'])
def run():
    if is_login():
        # choose image
        if 'image' in request.form:
            image_id = request.form['image']
            for i in docker.images():
                if image_id == i['id']:
                    image = i
                    break
            else:
                image = None
        else:
            image = None
        if not image:
            flash('Please choose an image from the list.', 'warning')
            return redirect(url_for('container.index'))

        # get name
        if 'name' in request.form:
            name = request.form['name']
        else:
            name = None

        # run it
        container = docker.run(detach = True,
                                 image=image,
                                 name = name,
                                 ports = {},
                                 volumes = {})
        if not container:
            flash('Failed to create a container. Please check the input and try again.', 'warning')
        return redirect(url_for('container.index'))
    else:
        return invalid_login()
