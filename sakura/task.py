#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# Leann Mak, leannmak@139.com, (c) 2018.
# This is the task module of sakura package.
#

import os
import re
import random
import json
import time
import traceback
from datetime import datetime
from celery.contrib.methods import task_method

from sakura import app, celery
from sakura import constant as C
from sakura.model import TaskManager
from sakura.util import logmsg
from sakura.tool import Etconf


def sakura_task_catch(success_message, failure_message):
    def _wrapper(func):
        def __wrapper(task_self, self, **kwargs):
            ret, meta, state = None, None, None
            notify = 'Task Update Notify: {0}.'
            params, main_task_id = kwargs, ''
            if 'main_task' in kwargs:
                main_task_id = kwargs['main_task'].task_id
                params = {'main_task_id': main_task_id}
            begin_time = datetime.now()
            try:
                # record task
                columns = dict(
                    task_id=task_self.request.id,
                    name=task_self.name,
                    state=C.TASK_STATE.PROGRESS.value,
                    kwargs=json.dumps(params),
                    begin_time=begin_time)
                msg = notify.format(self.insert(**columns))
                app.logger.info(logmsg(msg))
                # update main task if exists
                if main_task_id:
                    msg = notify.format(self.update(
                        task_id=main_task_id, sub_task_id=task_self.request.id))
                    app.logger.info(logmsg(msg))
                # excute task
                result = func(task_self, self, **kwargs)
                ret, meta, state = self.task_step(
                    task=task_self,
                    message=success_message.format(main_task_id),
                    data=result,
                    state=C.TASK_STATE.SUCCESS.value,
                    current=C.TASK_PERCENTAGE.ENDPOINT.value)
            except Exception as e:
                app.logger.error(logmsg(traceback.format_exc()))
                ret, meta, state = self.task_step(
                    task=task_self,
                    message=failure_message.format(main_task_id),
                    error=str(e),
                    state=C.TASK_STATE.FAILURE.value,
                    current=C.TASK_PERCENTAGE.ENDPOINT.value)
            finally:
                # record task
                end_time = datetime.now()
                columns = dict(
                    task_id=task_self.request.id,
                    info=json.dumps(meta),
                    end_time=end_time,
                    delta_time=(end_time - begin_time).total_seconds(),
                    state=state)
                msg = notify.format(self.update(**columns))
                app.logger.info(logmsg(msg))
                # update main task if exists
                if main_task_id:
                    msg = notify.format(
                        self.update(
                            task_id=main_task_id,
                            ack_status=eval(
                                'C.CONFIGURATION_UPDATE_ACK_STATE.{0}.value'.format(
                                    task_self.name))))
                    app.logger.info(logmsg(msg))
                return state, meta
        return __wrapper
    return _wrapper


class SakuraTask(TaskManager):
    """ Sakura Task Class

    Methods:
        :method configuration_update
        :method configuration_check
        :method configuration_acknowledge
        :method configuration_rollback
    """
    _task_queues = celery.conf.find_value_for_key('CELERY_QUEUES')
    _queue = _task_queues[0].name
    _routing_key = _task_queues[0].routing_key
    _cur_edge = C.TASK_PERCENTAGE.ENDPOINT.value - 1

    def __init__(self, **kwargs):
        super(SakuraTask, self).__init__(**kwargs)

    @celery.task(
        bind=True, filter=task_method, queue=_queue, routing_key=_routing_key,
        name=C.TASK_NAME.CONFIGURATION_UPDATE.value)
    @sakura_task_catch(
        success_message='Configurations have been updated completely.',
        failure_message='Error occurs while updating configurations.')
    def configuration_update(
            task_self, self, service_name, env_name, service_version, files,
            hosts, check_cmd=None, reload_cmd=None):
        """
        Parameters:
            service_name(str)   : name of the service with configurations to update
            service_version(str): version of the service with configurations to update
            env_name(str)       : environment the configurations belong to
            check_cmd(str)      : service configuration check command
            reload_cmd(str)     : service reload/restart command
            files(list)         : configuration files
                                  ex. [
                                        {
                                          'name': 'xx.cfg',
                                          'dir': '/cfg',
                                          'mode': '0755',
                                          'owner': {'name': 'xx', 'group': 'xx'},
                                          'template': 'hello {{getv "/key1"}} ...',
                                          'items': {'key1': 'value1', ...}
                                        },
                                        ...
                                      ]
            hosts(list)         : hosts in which the configurations takes effect
                                  ex. ['127.0.0.1', ...]
        """
        # 0, initialize Etconf
        etconf, meta, state = self.task_step(
            task=task_self, name=Etconf,
            args=dict(
                service_name=service_name, env_name=env_name,
                service_version=service_version, check_cmd=check_cmd,
                reload_cmd=reload_cmd, files=files, hosts=hosts),
            message='Begin to update configurations of {0}.'.format(
                service_name),
            flag=C.CONFIGURATION_UPDATE_STEP.INITIALIZE.value)
        # 1, create new template files
        ret, meta, state = self.task_step(
            task=task_self, name=etconf.create_tmpl,
            current=random.randint(meta['current'], self._cur_edge),
            message='Creating new template files ...')
        # 2, create new toml files
        ret, meta, state = self.task_step(
            task=task_self, name=etconf.create_toml,
            current=random.randint(meta['current'], self._cur_edge),
            message='Creating new toml files ...')
        # 3, backup old toml/tmpl/conf from remote/local confd to minio
        ret, meta, state = self.task_step(
            task=task_self, name=etconf.backup_files,
            current=random.randint(meta['current'], self._cur_edge),
            message='Backuping old files ...',
            flag=C.CONFIGURATION_UPDATE_STEP.BACKUP.value)
        # 4, backup items
        ret, meta, state = self.task_step(
            task=task_self, name=etconf.backup_keys,
            message='Backuping old items ...')
        # 5, stop confd client
        ret, meta, state = self.task_step(
            task=task_self, name=etconf.confd_cmd,
            args=dict(action='stop'), message='Stopping remote CONFD ...',
            current=random.randint(meta['current'], self._cur_edge),
            flag=C.CONFIGURATION_UPDATE_STEP.CLEANUP.value)
        # 6, delete old backuped toml/tmpl in remote confd client
        ret, meta, state = self.task_step(
            task=task_self, name=etconf.delete_files,
            current=random.randint(meta['current'], self._cur_edge),
            message='Deleting old template and toml files ...')
        # 7, update etcd keys
        ret, meta, state = self.task_step(
            task=task_self, name=etconf.update_keys,
            current=random.randint(meta['current'], self._cur_edge),
            message='Updating items ...',
            flag=C.CONFIGURATION_UPDATE_STEP.UPDATE.value)
        # 8, push new toml/tmpl to remote/local confd client
        ret, meta, state = self.task_step(
            task=task_self, name=etconf.push_files,
            current=random.randint(meta['current'], self._cur_edge),
            message='Pushing new template and toml files ...')
        # 9, start confd client
        ret, meta, state = self.task_step(
            task=task_self, name=etconf.confd_cmd,
            args=dict(action='start'),
            current=random.randint(meta['current'], self._cur_edge),
            message='Starting remote CONFD ...')

    @celery.task(
        bind=True, filter=task_method, queue=_queue, routing_key=_routing_key,
        name=C.TASK_NAME.CONFIGURATION_CHECK.value)
    @sakura_task_catch(
        success_message='Configurations files have been checked completely.',
        failure_message='Error occurs while checking configuration files.')
    def configuration_check(task_self, self, files, hosts):
        """
        Parameters:
            files(list)         : configuration files
                                  ex. [
                                        {
                                          'name': 'xx.cfg',
                                          'dir': '/cfg',
                                          'mode': '0755',
                                          'owner': {'name': 'xx', 'group': 'xx'},
                                          'template': 'hello {{getv "/key1"}} ...',
                                          'items': {'key1': 'value1', ...}
                                        },
                                        ...
                                      ]
            hosts(list)         : hosts in which the configurations takes effect
                                  ex. ['127.0.0.1', ...]
        """
        result, ret, meta, state = [], None, None, None
        for x in files:
            kwargs = dict(
                task=task_self, name=Etconf, args=dict(files=[x], hosts=hosts),
                message='Checking file {0} ...'.format(
                    os.path.join(x['dir'], x['name'])))
            if meta:
                kwargs['current'] = random.randint(meta['current'], self._cur_edge)
            etconf, meta, state = self.task_step(**kwargs)
            ret, meta, state = self.task_step(
                task=task_self, name=etconf.check_files,
                current=random.randint(meta['current'], self._cur_edge),
                message=meta['message'])
            result.append(ret)
        return result

    @celery.task(
        bind=True, filter=task_method, queue=_queue, routing_key=_routing_key,
        name=C.TASK_NAME.CONFIGURATION_ACKNOWLEDGE.value)
    @sakura_task_catch(
        success_message='Task <{0}> have been acknowledged.',
        failure_message='Error occurs while acknowledging task <{0}>.')
    def configuration_acknowledge(task_self, self, main_task):
        """
        Parameters:
            main_task(SakuraTask)   : the last configuration update task
        """
        # 0, initialize Etconf
        etconf, meta, state = self.task_step(
            task=task_self, name=Etconf,
            args=json.loads(main_task.kwargs),
            message='Begin to acknowledge task <{0}>.'.format(
                main_task.task_id))
        # 1, stop confd client
        ret, meta, state = self.task_step(
            task=task_self, name=etconf.confd_cmd,
            args=dict(action='stop'),
            current=random.randint(meta['current'], self._cur_edge),
            message='Stopping remote CONFD ...')
        # 2, delete expired toml/tmpl files
        ret, meta, state = self.task_step(
            task=task_self, name=etconf.delete_expired_files,
            current=random.randint(meta['current'], self._cur_edge),
            message='Deleting expired files ...')
        # 3, clean keys
        ret, meta, state = self.task_step(
            task=task_self, name=etconf.delete_expired_keys,
            current=random.randint(meta['current'], self._cur_edge),
            message='Deleting expired items ...')
        # 4, start confd client
        ret, meta, state = self.task_step(
            task=task_self, name=etconf.confd_cmd,
            current=random.randint(meta['current'], self._cur_edge),
            args=dict(action='start'), message='Starting remote CONFD ...')

    @celery.task(
        bind=True, filter=task_method, queue=_queue, routing_key=_routing_key,
        name=C.TASK_NAME.CONFIGURATION_ROLLBACK.value)
    @sakura_task_catch(
        success_message='Task <{0}> have been rolled back completely.',
        failure_message='Error occurs while rolling back task <{0}>.')
    def configuration_rollback(task_self, self, main_task):
        """
        Parameters:
            main_task(SakuraTask)   : the last configuration update task
        """
        if main_task.step > C.CONFIGURATION_UPDATE_STEP.BACKUP:
            # 0, initialize Etconf
            etconf, meta, state = self.task_step(
                task=task_self, name=Etconf,
                args=json.loads(main_task.kwargs),
                message='Begin to rollback task <{0}>.'.format(
                    main_task.task_id))
            # 1, stop confd client
            ret, meta, state = self.task_step(
                task=task_self, name=etconf.confd_cmd,
                args=dict(action='stop'),
                current=random.randint(meta['current'], self._cur_edge),
                message='Stopping remote CONFD ...')
            # 2. delete toml/tmpl
            ret, meta, state = self.task_step(
                task=task_self, name=etconf.delete_files,
                current=random.randint(meta['current'], self._cur_edge),
                message='Deleting the new files ...')
            # 3, rollback toml/tmpl/conf files
            ret, meta, state = self.task_step(
                task=task_self, name=etconf.push_files,
                args=dict(rollback=True),
                current=random.randint(meta['current'], self._cur_edge),
                message='Rolling back to the old files ...')
            # 4. rollback etcd keys
            ret, meta, state = self.task_step(
                task=task_self, name=etconf.update_keys,
                args=dict(rollback=True),
                current=random.randint(meta['current'], self._cur_edge),
                message='Rolling back the items ...')
            # 5, start confd client
            ret, meta, state = self.task_step(
                task=task_self, name=etconf.confd_cmd,
                args=dict(action='start'),
                current=random.randint(meta['current'], self._cur_edge),
                message='Starting remote CONFD ...')
