#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# Leann Mak, leannmak@139.com, (c) 2018.
# This is the default configuration file of sakura.
#

import os
import logging

""" WORKSPACE configuration
"""
SAKURA_HOME = os.path.split(os.path.realpath(__file__))[0]
TMP_FOLDER = os.path.join(SAKURA_HOME, '.tmp')
DATA_FOLDER = os.path.join(SAKURA_HOME, '.data')
CA_FOLDER = os.path.join(SAKURA_HOME, '.ca')
LOG_FOLDER = os.path.join(SAKURA_HOME, '.log')

""" LOGGING configuration
"""
LOGFILE = 'sakura.log'
LOGLEVEL = logging.INFO

""" DATABASE configuration
"""
SQLALCHEMY_DATABASE_URI = 'mysql://root@127.0.0.1:3306/sakura'

""" ETCD configuration
"""
# if tls, default none
ETCD_CERT = ('etcd-client.crt', 'etcd-client-key.pem')
ETCD_CA_CERT = 'etcd-ca.crt'
# should be in accordance with ca if using domain name
ETCD_HOST = 'etcd.sakura.leannmak'
ETCD_PORT = 2379

""" CONFD configuration
"""
CONFD_DIR = '/apps/data/confd'
CONFD_FILE_MODE = '0775'
# (name, group)
CONFD_FILE_OWNER = ('root', 'root')
CONFD_CMD = dict(
    restart='/apps/sh/confd.sh restart',
    start='/apps/sh/confd.sh start',
    stop='/apps/sh/confd.sh stop',
    status='/apps/sh/confd.sh status')

""" ANSIBLE configuration
"""
ANSIBLE_REMOTE_USER = 'root'
# passwords of remote user and remote `root`
ANSIBLE_REMOTE_USER_PASSWORDS = dict(conn_pass='', become_pass='')
# always cover 'conn_pass'
ANSIBLE_SSH_KEY = ''

""" MINIO configuration
"""
MINIO_ENDPOINT = '127.0.0.1:9000'
MINIO_ACCESS_KEY = 'your access key'
MINIO_SECRET_KEY = 'your secret key'
MINIO_BUCKET = 'sakura'

""" CELERY configuration
"""
# should be rabbitmq
CELERY_BROKER_URL = 'amqp://guest:guest@127.0.0.1:5672/sakura'
CELERYD_TASK_TIME_LIMIT = 600
CELERYD_TASK_SOFT_TIME_LIMIT = 300
