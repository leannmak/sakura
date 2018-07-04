#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# Leann Mak, leannmak@139.com, (c) 2018.
# This is the default configuration file of autotest.
#

import os


# folder
TEST_FOLDER = os.path.join(
    os.path.realpath(os.path.join(os.path.dirname(__file__), '..')), '.test')
TMP_FOLDER = os.path.join(TEST_FOLDER, '.tmp')
DATA_FOLDER = os.path.join(TEST_FOLDER, '.data')
# log
LOGFILE = 'test.log'
# database
SQLALCHEMY_DATABASE_URI = 'mysql://root@127.0.0.1:3306/test'
# celery
CELERY_BROKER_URL = 'amqp://guest:guest@127.0.0.1:5672/test'
