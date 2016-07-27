from flask import Flask
import datetime
from dsd.ui.web.utils.basic import db, get_docker

app = Flask(__name__)
app.secret_key = '123edft654edfgY^%R#$%^&**&^'

app.jinja_env.add_extension('jinja2.ext.do')

@app.template_filter('timestamp2datetime')
def jinja2_filter_timestamp2datetime(timestamp):
    return str(datetime.datetime.fromtimestamp(timestamp))

@app.template_filter('docker_image')
def jinja2_filter_docker_image(id, fields=None, delimiter=' | '):
    docker = get_docker()
    if not docker:
        return '<no docker connection>'

    try:
        image = docker.image(id)
    except Exception as e:
        return '<%s>' % str(e)
    else:
        if not fields:
            fields = [('Image: %s', 'RepoTags'), ('Size: %s GB', 'size')]

    return delimiter.join([format % image[field] for format, field in fields if field in image])

@app.template_filter('db')
def jinja2_filter_db(oid, collection, fields=None, delimiter=' | '):
    try:
        document = db[collection].find_one({'_id':ObjectId(oid)})
    except Exception as e:
        return '<%s>' % str(e)
    else:
        if not fields:
            fields = [('ObjectId: %s', '_id')]
    return delimiter.join([format % document[field] for format, field in fields if field in document])

from dsd.ui.web import site
from dsd.ui.web import manage
from dsd.ui.web import user
