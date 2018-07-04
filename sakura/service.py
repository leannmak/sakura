#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# Leann Mak, leannmak@139.com, (c) 2018.
# This is the service module of sakura package.
#

import os
import json
import werkzeug
import traceback
from datetime import datetime
from inspect import isclass, isfunction
from flask.ext.restful import reqparse, Resource, inputs

from sakura import app
from sakura import constant as C
from sakura.model import TaskManager
from sakura.task import SakuraTask
from sakura.util import logmsg
from sakura.input import defined_dictionary, union_dictionary, ip


""" Error
"""


class SakuraAPIError(Exception):
    __abstract__ = True

    def __init__(self, prefix, content, http_code):
        self.message = '%s: %s' % (prefix, content)
        self.code = http_code

    def __str__(self):
        return repr(self.message)


class SakuraInvalidAccessError(SakuraAPIError):
    def __init__(self, content='Bad Request Data Format'):
        prefix = 'Invalid Access'
        code = 400
        super(SakuraInvalidAccessError, self).__init__(
            prefix=prefix, content=content, http_code=code)


class SakuraConstraintConflictError(SakuraAPIError):
    def __init__(self, content):
        prefix = 'Task Constraint Conflict'
        code = 403
        super(SakuraConstraintConflictError, self).__init__(
            prefix=prefix, content=content, http_code=code)


class SakuraObjectNotFoundError(SakuraAPIError):
    def __init__(self, content):
        prefix = 'Object Not Found'
        code = 404
        super(SakuraObjectNotFoundError, self).__init__(
            prefix=prefix, content=content, http_code=code)


""" Service
"""


class TaskListAPI(Resource):
    """
        TaskList Restful API.
        For GET(Readonly).
    """
    def __init__(self):
        super(TaskListAPI, self).__init__()
        self.obj = TaskManager()
        self.parser = reqparse.RequestParser(bundle_errors=True)
        # page
        self.parser.add_argument(
            'page', type=inputs.positive,
            help='Page must be a positive integer')
        # pp: number of items per page
        self.parser.add_argument(
            'pp', type=inputs.positive,
            help='PerPage must be a positive integer', dest='per_page')
        # multi-type parameters
        setattr(self, 'params', [])
        type_dict = {'String': unicode, 'Integer': int}
        for k, v in self.obj._columns().items():
            if v.type.__class__.__name__ in type_dict:
                self.parser.add_argument(
                    k, type=type_dict[v.type.__class__.__name__])
                self.params.append(k)

    def get(self):
        """ get whole list of tasks
        """
        try:
            try:
                args = self.parser.parse_args()
            except Exception as e:
                if hasattr(e, 'data'):
                    raise SakuraInvalidAccessError(e.data['message'])
                else:
                    raise SakuraInvalidAccessError()
            pages, data, kwargs = False, [], {}
            kwargs = {k: v for k, v in args.items() if k in self.params and v}
            page = args['page']
            if kwargs or not page:
                data = self.obj.get(**kwargs)
            else:
                query = []
                per_page = args['per_page']
                if per_page:
                    query = self.obj.get(page=page, per_page=per_page, **kwargs)
                else:
                    query = self.obj.get(page=page, **kwargs)
                if query:
                    data, pages = query[0], query[1]
            return {'totalpage': pages, 'data': data}, 200
        except SakuraAPIError as e:
            app.logger.error(logmsg(traceback.format_exc()))
            return {'error': e.message, 'status': 1}, e.code
        except Exception as e:
            app.logger.error(logmsg(traceback.format_exc()))
            return {'error': str(e), 'status': 1}, 500


class SakuraAPI(Resource):
    """
        Super Task Restful API.
        For both POST(Execute) and GET(Check).
    """
    __abstract__ = True

    def __init__(self, task_name, post_params=None):
        super(SakuraAPI, self).__init__()
        self.parser = reqparse.RequestParser(bundle_errors=True)
        self.task = SakuraTask()
        setattr(self, 'task_name', task_name)
        setattr(self, 'post_params', post_params if post_params else {})

    def _parse_args(self, params):
        for k, v in params.items():
            help = ''
            type_name = v['type'].__name__ if (
                isclass(v['type']) or isfunction(v['type'])) \
                else v['type'].__class__.__name__
            if 'help' in v:
                help = v.pop('help')
            elif 'choices' in v:
                help = '{} must be {} within {}'.format(
                    k, type_name, v['choices'])
            else:
                help = '{} must be {}'.format(k, type_name)
            self.parser.add_argument(name=k, help=help, **v)
        try:
            args = self.parser.parse_args(strict=True)
        except Exception as e:
            if hasattr(e, 'data'):
                raise SakuraInvalidAccessError(e.data['message'])
            else:
                raise SakuraInvalidAccessError()
        args = {k: v for k, v in args.items() if v is not None}
        return args

    def _before_task(self, args):
        return args

    def post(self):
        """ execute a task
        """
        try:
            args = self._parse_args(params=self.post_params)
            args = self._before_task(args=args)
            task = eval('self.task.%s' % self.task_name).apply_async(kwargs=args)
            return {'id': task.task_id, 'status': 0}, 201
        except SakuraAPIError as e:
            app.logger.error(logmsg(traceback.format_exc()))
            return {'error': e.message, 'status': 1}, e.code
        except Exception as e:
            app.logger.error(logmsg(traceback.format_exc()))
            return {'error': str(e), 'status': 1}, 500

    def get(self, id):
        """ check a specific task status
        """
        try:
            task = eval('self.task.%s' % self.task_name).AsyncResult(id)
            result = {
                'id': task.id,
                'state': task.result[0] if task.ready() else task.state,
                'info': task.result[1] if task.ready() else task.result
            }
            return {'result': result, 'status': 0}, 200
        except SakuraAPIError as e:
            app.logger.error(logmsg(traceback.format_exc()))
            return {'error': e.message, 'status': 1}, e.code
        except Exception as e:
            app.logger.error(logmsg(traceback.format_exc()))
            return {'error': str(e), 'status': 1}, 500


class ConfigurationUpdateAPI(SakuraAPI):
    """
        Configuration Update Restful API.
        Inherits from SakuraAPI.
    """
    def __init__(self):
        params = dict(
            service_name=dict(type=str, required=True),
            env_name=dict(type=str, required=True),
            service_version=dict(type=str, required=True),
            check_cmd=dict(type=str),
            reload_cmd=dict(type=str),
            files=dict(
                type=defined_dictionary(
                    keys=dict(
                        name=str, dir=str, mode=str,
                        owner=defined_dictionary(
                            keys=dict(name=str, group=str)),
                        template=unicode,
                        items=union_dictionary(
                            key_type=unicode, value_type=unicode))),
                action='append', required=True),
            hosts=dict(type=ip, action='append', required=True))
        super(ConfigurationUpdateAPI, self).__init__(
            task_name=C.TASK_NAME.CONFIGURATION_UPDATE.value,
            post_params=params)

    def _before_task(self, args):
        tasks = self.task.get(name=self.task_name, ack_status=None)
        tasks.extend(self.task.get(
            name=self.task_name,
            ack_status=C.CONFIGURATION_UPDATE_ACK_STATE.PENDING.value))
        # check pre task
        for x in tasks:
            kwargs = json.loads(x['kwargs'])
            if (kwargs['service_name'] == args['service_name'] and
                    kwargs['env_name'] == args['env_name'] and
                    kwargs['service_version'] == args['service_version']):
                raise SakuraConstraintConflictError(
                    'Pre Task Unconfirmed: {0}'.format(x['task_id']))
        return args


class ConfigurationCheckAPI(SakuraAPI):
    """
        Configuration Check Restful API.
        Inherits from SakuraAPI.
    """
    def __init__(self):
        params = dict(
            files=dict(
                type=defined_dictionary(
                    keys=dict(
                        name=unicode, dir=unicode, mode=str,
                        owner=defined_dictionary(
                            keys=dict(name=str, group=str)),
                        template=unicode,
                        items=union_dictionary(
                            key_type=unicode, value_type=unicode)
                        )
                    ),
                action='append', required=True),
            hosts=dict(type=ip, action='append', required=True))
        super(ConfigurationCheckAPI, self).__init__(
            task_name=C.TASK_NAME.CONFIGURATION_CHECK.value,
            post_params=params)


class ConfigurationAcknowledgeAPI(SakuraAPI):
    """
        Configuration Change Acknowledge Restful API.
        Inherits from SakuraAPI.
    """
    def __init__(self):
        params = dict(main_task_id=dict(type=str, required=True))
        super(ConfigurationAcknowledgeAPI, self).__init__(
            task_name=C.TASK_NAME.CONFIGURATION_ACKNOWLEDGE.value,
            post_params=params)

    def _before_task(self, args):
        # check main task
        main_task = self.task.getObject(task_id=args['main_task_id'])
        if main_task:
            args.pop('main_task_id')
            if main_task.name != C.TASK_NAME.CONFIGURATION_UPDATE:
                raise SakuraInvalidAccessError(
                    'Illegal Main Task Name: {0}.'.format(main_task.name))
            elif main_task.state not in (
                    C.TASK_STATE.SUCCESS.value, C.TASK_STATE.FAILURE.value):
                raise SakuraConstraintConflictError(
                    'Main Task Still Running: {0}.'.format(
                        main_task.task_id))
            elif main_task.ack_status:
                raise SakuraConstraintConflictError(
                    'Main Task Already Confirmed: {0}.'.format(
                        main_task.task_id))
            elif main_task.state == C.TASK_STATE.FAILURE:
                raise SakuraInvalidAccessError(
                    'Failure Main Task Forced to Rollback: {0}.'.format(
                        main_task.task_id))
        else:
            raise SakuraObjectNotFoundError(
                'Main Task Not Found: {0}.'.format(args['main_task_id']))
        # update main task ack_status
        self.task.update(
            task_id=main_task.task_id,
            ack_status=C.CONFIGURATION_UPDATE_ACK_STATE.PENDING.value)
        args['main_task'] = main_task
        return args


class ConfigurationRollbackAPI(SakuraAPI):
    """
        Configuration Rollback Restful API.
        Inherits from SakuraAPI.
    """
    def __init__(self):
        params = dict(main_task_id=dict(type=str, required=True))
        super(ConfigurationRollbackAPI, self).__init__(
            task_name=C.TASK_NAME.CONFIGURATION_ROLLBACK.value,
            post_params=params)

    def _before_task(self, args):
        # check main task
        main_task = self.task.getObject(task_id=args['main_task_id'])
        if main_task:
            args.pop('main_task_id')
            if main_task.name != C.TASK_NAME.CONFIGURATION_UPDATE:
                raise SakuraInvalidAccessError(
                    'Illegal Main Task Name: {0}.'.format(main_task.name))
            elif main_task.state not in (
                    C.TASK_STATE.SUCCESS.value, C.TASK_STATE.FAILURE.value):
                raise SakuraConstraintConflictError(
                    'Main Task Still Running: {0}.'.format(
                        main_task.task_id))
            elif main_task.ack_status:
                raise SakuraConstraintConflictError(
                    'Main Task Already Confirmed: {0}.'.format(
                        main_task.task_id))
        else:
            raise SakuraObjectNotFoundError(
                'Main Task Not Found: {0}.'.format(args['main_task_id']))
        # update main task ack_status
        self.task.update(
            task_id=main_task.task_id,
            ack_status=C.CONFIGURATION_UPDATE_ACK_STATE.PENDING.value)
        args['main_task'] = main_task
        return args
