#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# Leann Mak, leannmak@139.com, (c) 2018.
# This is the api module of sakura package.
#

from sakura import api
from sakura.release import __version__
from sakura.service import (
    TaskListAPI, ConfigurationUpdateAPI, ConfigurationCheckAPI,
    ConfigurationAcknowledgeAPI, ConfigurationRollbackAPI)


def _url(identifier):
    return '/api/v{0}/sakura/{1}'.format(__version__, identifier)


def add_resource(
        identifier, many_resource=None, one_resource=None):
    url = _url(identifier)
    endpoint = 'ep_dr_{}'.format(identifier)
    if many_resource:
        api.add_resource(
            many_resource, url, endpoint='{}_list'.format(endpoint))
    if one_resource:
        api.add_resource(
            one_resource, '{}/<id>'.format(url),
            endpoint='{}_id'.format(endpoint))
        api.add_resource(one_resource, url, endpoint=endpoint)


add_resource('task', many_resource=TaskListAPI)
add_resource('cfg_upd', one_resource=ConfigurationUpdateAPI)
add_resource('cfg_chk', one_resource=ConfigurationCheckAPI)
add_resource('cfg_ack', one_resource=ConfigurationAcknowledgeAPI)
add_resource('cfg_rbk', one_resource=ConfigurationRollbackAPI)
