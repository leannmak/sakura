#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# Leann Mak, leannmak@139.com, (c) 2018.
# This is the default configuration file of sakura.
#

import os
import logging


""" LOGGING configuration
"""
LOGLEVEL = logging.DEBUG

""" DATABASE configuration
"""
SQLALCHEMY_DATABASE_URI = 'mysql://root@127.0.0.1:3306/sakura'

""" ETCD configuration
"""
ETCD_HOST = 'etcd.devops.mgmt'
ETCD_PORT = 2379
ETCD_CERT = ('client.crt', 'client-key.pem')
ETCD_CA_CERT = 'ca.crt'

""" CONFD configuration
"""
CONFD_FILE_OWNER = ('apps', 'apps')  # (name, group)

""" ANSIBLE configuration
"""
ANSIBLE_REMOTE_USER = 'maiyifan'
ANSIBLE_REMOTE_USER_PASSWORDS = dict(conn_pass='111111', become_pass='')

""" MINIO configuration
"""
MINIO_ENDPOINT = '192.168.182.2:9000'
MINIO_ACCESS_KEY = '7M3LTEM3H3MVIYAV2U3I'
MINIO_SECRET_KEY = 'LJqZRt/gL/WEjg3i6hLT1wjYcEmd7QtQ7EzlOQeZ'

""" CELERY configuration
"""
CELERY_BROKER_URL = 'amqp://promise-dev-ci:111111@192.168.182.52:5672/devci'
