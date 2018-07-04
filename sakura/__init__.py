#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# Leann Mak, leannmak@139.com, (c) 2018.
# This is part of sakura package.
#

from __future__ import absolute_import
import os
from logging import Formatter
from logging.handlers import RotatingFileHandler
from flask import Flask, make_response, json
from flask.ext.restful import Api
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.cors import CORS
from flask.ext.cachecontrol import FlaskCacheControl
from celery import Celery, platforms
from kombu import Queue, Exchange

import config


# initialize flask object
app = Flask(__name__, instance_relative_config=True)


def make_celery(app):
    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
    exchange = Exchange('sakura')
    celery.conf.update(
        CELERY_RESULT_BACKEND='amqp',
        CELERY_IGNORE_RESULT=False,
        CELERY_TIMEZONE='Asia/Shanghai',
        CELERY_ENABLE_UTC=True,
        CELERYBEAT_SCHEDULE_FILENAME=os.path.join(
            app.config['DATA_FOLDER'], 'celerybeat-schedule'),
        DEFAULT_EXCHANGE=exchange,
        CELERY_QUEUES=(
            Queue('sakura', exchange, routing_key='sakura'),
            Queue('sakura-period', exchange, routing_key='sakura-period')),
        CELERY_DEFAULT_EXCHANGE_TYPE='direct')
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery


def config_app(app, instance_config=None):
    # config.py in folder 'instance' may cover the default config object.
    app.config.from_object(config)
    if instance_config and os.path.isfile(
            os.path.join(app.instance_path, instance_config)):
        app.config.from_pyfile(instance_config)
    # initialize folders
    if not os.path.exists(app.config['DATA_FOLDER']):
        os.makedirs(app.config['DATA_FOLDER'])
    if not os.path.exists(app.config['TMP_FOLDER']):
        os.makedirs(app.config['TMP_FOLDER'])
    if not os.path.exists(app.config['CA_FOLDER']):
        os.makedirs(app.config['CA_FOLDER'])
    if not os.path.exists(app.config['LOG_FOLDER']):
        os.makedirs(app.config['LOG_FOLDER'])
    # initialize api
    api = Api(app)
    # initialize db
    db = SQLAlchemy(app)
    # initialize logger
    handler = RotatingFileHandler(
        os.path.join(app.config['LOG_FOLDER'], app.config['LOGFILE']),
        maxBytes=102400, backupCount=1)
    handler.setFormatter(Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'
    ))
    handler.setLevel(app.config['LOGLEVEL'])
    app.logger.addHandler(handler)
    # initialize cors
    cors = CORS(app, allow_headers='*', expose_headers='Content-Disposition')
    # initialize cache control
    flask_cache_control = FlaskCacheControl()
    flask_cache_control.init_app(app)
    # initialize celery
    platforms.C_FORCE_ROOT = True
    celery = make_celery(app)
    return app, api, db, cors, celery


app, api, db, cors, celery = config_app(app, instance_config='config.py')


@api.representation('application/json')
def responseJson(data, code, headers=None):
    resp = make_response(json.dumps(data), code)
    resp.headers.extend(headers or {})
    return resp


from sakura import model, tool, task, service, resource
