#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# Leann Mak, leannmak@139.com, (c) 2018.
# This is the autotest cases for task module.
#

import sys
sys.path.append('.')

import os
from nose.tools import with_setup, eq_
from mock import patch, Mock
from celery import Task

from sakura import app, config_app
from sakura import constant as C
from sakura.util import get_folder, remove_folder
from sakura.tool import Etconf, MinioAPI
from sakura.task import SakuraTask


class TestTask():
    """ unit tests for tasks of sakura.
    """
    # establish db
    def setUp(self):
        app.testing = True
        config_app(app, instance_config='test_config.py')
        # mock
        MinioAPI.connect = Mock()
        MinioAPI.make_bucket = Mock()
        Task.update_state = Mock()
        SakuraTask.insert = Mock()
        SakuraTask.update = Mock()

    # clean up the garbage data
    def tearDown(self):
        remove_folder(app.config['TEST_FOLDER'])

    @with_setup(setUp, tearDown)
    def test_configuration_check(self):
        """ [task      ] configuration check test """
        kwargs = {
            "files": [
                {
                    "name": "greeting.cfg",
                    "dir": "/test",
                    "mode": "0755",
                    "owner": {"name": "leannmak", "group": "leannmak"},
                    "template": "hello world!",
                    "items": {}
                }],
            "hosts": ["127.0.0.1"]
        }
        # success
        return_value = {
            "greeting.cfg": {
                "127.0.0.1": {
                    "content": "OK",
                    "last_modify_time": "2018-05-22 10:24:10.637048142 +0800",
                    "mode": "0775 != 0755",
                    "owner": "(u'apps', u'apps') != ('leannmak', 'leannmak')"
                }
            }
        }
        Etconf.check_files = Mock(return_value=return_value)
        task = SakuraTask()
        state, meta = task.configuration_check(**kwargs)
        eq_(Etconf.check_files.call_count, 1)
        eq_(state, C.TASK_STATE.SUCCESS)
        eq_(meta['data'], [return_value])
