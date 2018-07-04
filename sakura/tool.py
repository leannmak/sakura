#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# Leann Mak, leannmak@139.com, (c) 2018.
# This is the tool module of sakura package.
#

import os
import re
import time
from datetime import datetime
from minio.error import BucketAlreadyOwnedByYou, BucketAlreadyExists

from lotus.api import Ansible2API, EtcdAPI, MinioAPI
from sakura import app
from sakura.util import get_folder, remove_folder, logmsg, md5hex


class Etconf(object):
    """ Etconf

    Using ETCD/CONFD for Configuration File Management.
    """
    def __init__(
            self, service_name=None, env_name=None, service_version=None,
            files=None, check_cmd=None, reload_cmd=None, hosts=None):
        super(Etconf, self).__init__()
        # service
        # service name
        self._service = service_name if service_name else ''
        # service version
        self._version = '_'.join(service_version.split()) if service_version else ''
        # environment name
        self._env = env_name if env_name else ''
        # hosts that the services are running on
        self._hosts = hosts if hosts else []
        # configuration files
        self._files = files if files else []
        # configuration check cmd
        self._check_cmd = check_cmd if check_cmd else ''
        # service reload cmd
        self._reload_cmd = reload_cmd if reload_cmd else ''

        # ansible
        self._ansible_kwargs = dict(
            passwords=app.config['ANSIBLE_REMOTE_USER_PASSWORDS'],
            connection='ssh',
            remote_user=app.config['ANSIBLE_REMOTE_USER'],
            verbosity=0,
            become=True,
            become_method='sudo',
            become_user='root',
            private_key_file=(
                os.path.join(
                    app.config['CA_FOLDER'], app.config['ANSIBLE_SSH_KEY'])
                if 'ANSIBLE_SSH_KEY' in app.config and
                app.config['ANSIBLE_SSH_KEY'] else None))

        # etcd
        self.etcd_kwargs = dict(
            host=app.config['ETCD_HOST'], port=app.config['ETCD_PORT'],
            per_host_pool_size=10)
        # etcd client cert/key file
        if (
                'ETCD_CERT' in app.config and app.config['ETCD_CERT'] and
                'ETCD_CA_CERT' in app.config and app.config['ETCD_CA_CERT']):
            self.etcd_kwargs['protocol'] = 'https'
            self.etcd_kwargs['cert'] = (
                os.path.join(app.config['CA_FOLDER'], app.config['ETCD_CERT'][0]),
                os.path.join(app.config['CA_FOLDER'], app.config['ETCD_CERT'][1]))
            self.etcd_kwargs['ca_cert'] = os.path.join(
                app.config['CA_FOLDER'], app.config['ETCD_CA_CERT'])
        # build connection to etcd server
        self.etcd = EtcdAPI(**self.etcd_kwargs)
        self.etcd.connect()
        # etcd key backup prefix
        self._key_bak_pre = 'bak'

        # minio
        minio_kwargs = dict(
            endpoint=app.config['MINIO_ENDPOINT'],
            access_key=app.config['MINIO_ACCESS_KEY'],
            secret_key=app.config['MINIO_SECRET_KEY'],
            secure=False)
        # minio bucket name
        self._minio_bucket = app.config['MINIO_BUCKET']
        # build connection to minio server
        self.minio = MinioAPI(**minio_kwargs)
        self.minio.connect()
        try:
            self.minio.make_bucket(self._minio_bucket)
        except (BucketAlreadyOwnedByYou, BucketAlreadyExists):
            pass
        # file name broken words using on minio
        self._broken_word_1 = 'i@mMINI0'
        self._broken_word_2 = 'iLikeKB'

        # confd
        # remote toml folder
        self._r_toml = os.path.join(app.config['CONFD_DIR'], 'conf.d')
        # remote tmpl folder
        self._r_tmpl = os.path.join(app.config['CONFD_DIR'], 'templates')
        # confd client data file permission mode
        self._confd_file_mode = app.config['CONFD_FILE_MODE']
        # confd client data file owner
        self._confd_owner = app.config['CONFD_FILE_OWNER']
        # confd client startup command
        self._confd_startup_cmd = app.config['CONFD_CMD']
        # local toml folder
        self._l_toml = os.path.join(
            app.config['TMP_FOLDER'], 'conf.d', self._folder_pre)
        # local tmpl folder
        self._l_tmpl = os.path.join(
            app.config['TMP_FOLDER'], 'templates', self._folder_pre)
        # create local toml/tmpl folder
        for x in self._hosts:
            get_folder(os.path.join(self._l_toml, x))
        get_folder(self._l_tmpl)
        # local tmpl backup folder
        self._l_toml_bak = os.path.join(
            app.config['DATA_FOLDER'], 'backup', 'conf.d', self._folder_pre)
        # local tmpl backup folder
        self._l_tmpl_bak = os.path.join(
            app.config['DATA_FOLDER'], 'backup', 'templates', self._folder_pre)
        # local conf backup folder
        self._l_conf_bak = os.path.join(
            app.config['DATA_FOLDER'], 'backup', 'conf', self._folder_pre)
        # create backup folder
        get_folder(self._l_toml_bak)
        get_folder(self._l_tmpl_bak)
        get_folder(self._l_conf_bak)

    def __del__(self):
        """remove temporary folders
        """
        remove_folder(self._l_toml)
        remove_folder(self._l_tmpl)

    @property
    def _file_pre(self):
        return '%s.%s.%s' % (self._env, self._service, self._version)

    @property
    def _folder_pre(self):
        return os.path.join(self._env, self._service, self._version)

    def get_cfg_name(self, toml_name):
        """get configuration file name from toml file name
        """
        return toml_name.split(self._file_pre)[1].split('toml')[0].strip('.')

    def get_uids(self, name, group):
        """fetch owner's uid and gid via name
        """
        aapi = Ansible2API(hosts=self._hosts, **self._ansible_kwargs)
        state, state_sum, results = aapi.run(
            module='shell',
            args="cat /etc/passwd | grep ^%s: | awk -F ':' '{print $3}';"
                 "cat /etc/passwd | grep ^%s: | awk -F ':' '{print $3}';" % (
                     name, group))
        msg = 'Uid and Gid Get: %s' % state_sum
        app.logger.debug(logmsg(msg))
        msg = 'Uid and Gid Get: %s' % results
        app.logger.info(logmsg(msg))
        results = {
            k: dict(uid=v['stdout_lines'][0], gid=v['stdout_lines'][1])
            for k, v in results.items()}
        return results

    def create_toml(self):
        """create toml files
        """
        result = {}
        for x in self._files:
            result[x['name']] = {}
            usr = self.get_uids(**x['owner'])
            for host in self._hosts:
                toml_file = os.path.join(
                    self._l_toml, host,
                    '{0}.{1}.toml'.format(self._file_pre, x['name']))
                with open(toml_file, 'w') as f:
                    content = [
                        '[template]\r\n',
                        'prefix = "/{0}"\r\n'.format(
                            os.path.join(self._folder_pre, x['name'])),
                        'keys = {0}\r\n'.format(
                            [str(k) for k in x['items'].keys()]
                            if x['items'] else []),
                        'src = "{0}.tmpl"\r\n'.format(
                            os.path.join(self._folder_pre, x['name'])),
                        'dest = "{0}"\r\n'.format(
                            os.path.join(x['dir'], x['name'])),
                        'uid = {0}\r\n'.format(usr[host]['uid']),
                        'gid = {0}\r\n'.format(usr[host]['gid']),
                        'mode = "{0}"\r\n'.format(x['mode']),
                        'check_cmd = "{0}"\r\n'.format(
                            self._check_cmd.replace('"', '\'')),
                        'reload_cmd = "{0}"\r\n'.format(
                            self._reload_cmd.replace('"', '\''))]
                    f.writelines(content)
                msg = 'Toml File Created: %s.' % toml_file
                app.logger.info(logmsg(msg))
                result[x['name']][host] = toml_file
        return result

    def create_tmpl(self):
        """create template files
        """
        result = {}
        for x in self._files:
            tmpl_file = '{0}.tmpl'.format(
                os.path.join(self._l_tmpl, x['name']))
            with open(tmpl_file, 'w') as f:
                f.write(x['template'].encode('utf-8'))
            msg = 'Tmpl File Created: %s.' % tmpl_file
            app.logger.info(logmsg(msg))
            result[x['name']] = tmpl_file
        return result

    def get_toml_content(self, cfg_name, host):
        """get toml file content from remote confd client
        """
        aapi = Ansible2API(hosts=[host], **self._ansible_kwargs)
        state, state_sum, results = aapi.run(
            module='shell',
            args='cat %s.%s.toml' % (self._file_pre, cfg_name))
        msg = 'Toml File Get: %s' % state_sum
        app.logger.debug(logmsg(msg))
        msg = 'Toml File Get: %s' % results
        app.logger.info(logmsg(msg))
        results = results[host]['stdout_lines'][1:]
        ret = dict()
        for x in results:
            key, value = x.split(' = ')
            ret[key] = value.strip('\"')
        return ret

    def get_tmpl_content(self, cfg_name, host):
        """get template file content from remote confd client
        """
        aapi = Ansible2API(hosts=[host], **self._ansible_kwargs)
        state, state_sum, results = aapi.run(
            module='shell',
            args='cat %s.tmpl' % os.path.join(self._folder_pre, cfg_name))
        msg = 'Tmpl File Get: %s' % state_sum
        app.logger.debug(logmsg(msg))
        msg = 'Tmpl File Get: %s' % results
        app.logger.info(logmsg(msg))
        return '%s\r\n' % results[host]['stdout']

    def get_tomls(self, host):
        """get toml files from remote confd client
        """
        aapi = Ansible2API(hosts=[host], **self._ansible_kwargs)
        state, state_sum, results = aapi.run(
            module='shell',
            args='ls %s | grep "^%s\..*\.toml$" | awk 1' % (
                self._r_toml, self._file_pre))
        msg = 'Toml File Check: %s' % state_sum
        app.logger.debug(logmsg(msg))
        msg = 'Toml File Check: %s' % results
        app.logger.info(logmsg(msg))
        return results[host]['stdout_lines']

    def get_tmpls(self, host):
        """get template files from remote confd client
        """
        aapi = Ansible2API(hosts=[host], **self._ansible_kwargs)
        state, state_sum, results = aapi.run(
            module='shell',
            args='ls %s | awk 1' % os.path.join(
                self._r_tmpl, self._folder_pre))
        msg = 'Tmpl File Check: %s' % state_sum
        app.logger.debug(logmsg(msg))
        msg = 'Tmpl File Check: %s' % results
        app.logger.info(logmsg(msg))
        return results[host]['stdout_lines']

    def backup_files(self):
        """backup old toml/tmpl/cfg files from remote confd client to server
        """
        for host in self._hosts:
            # local filesystem
            toml_bak = os.path.join(self._l_toml_bak, host)
            tmpl_bak = os.path.join(self._l_tmpl_bak, host)
            conf_bak = os.path.join(self._l_conf_bak, host)
            remove_folder(toml_bak)
            remove_folder(tmpl_bak)
            remove_folder(conf_bak)
            get_folder(toml_bak)
            get_folder(tmpl_bak)
            get_folder(conf_bak)
            # minio server
            toml_pre = '%s/' % os.path.join('toml', self._folder_pre, host)
            tmpl_pre = '%s/' % os.path.join('tmpl', self._folder_pre, host)
            conf_pre = '%s/' % os.path.join('conf', self._folder_pre, host)
            objs = self.minio.list_objects(
                bucket_name=self._minio_bucket, prefix=toml_pre, recursive=False)
            for x in objs:
                self.minio.remove_object(
                    bucket_name=self._minio_bucket,
                    object_name=x.object_name.encode('utf-8'))
            objs = self.minio.list_objects(
                bucket_name=self._minio_bucket, prefix=tmpl_pre, recursive=False)
            for x in objs:
                self.minio.remove_object(
                    bucket_name=self._minio_bucket,
                    object_name=x.object_name.encode('utf-8'))
            objs = self.minio.list_objects(
                bucket_name=self._minio_bucket, prefix=conf_pre, recursive=False)
            for x in objs:
                self.minio.remove_object(
                    bucket_name=self._minio_bucket,
                    object_name=x.object_name.encode('utf-8'))
            aapi = Ansible2API(hosts=[host], **self._ansible_kwargs)
            # 1. backup toml to minio server
            tomls = self.get_tomls(host=host)
            for x in tomls:
                state, state_sum, results = aapi.run(
                    module='fetch',
                    args=dict(
                        dest='%s/' % toml_bak,
                        src=os.path.join(self._r_toml, x),
                        flat='yes'))
                msg = 'Toml File Backup: %s' % state_sum
                app.logger.debug(logmsg(msg))
                msg = 'Toml File Backup: %s' % results
                app.logger.info(logmsg(msg))
                self.minio.fput_object(
                    bucket_name=self._minio_bucket,
                    object_name=os.path.join(toml_pre, x),
                    file_path=os.path.join(toml_bak, x))
            # 2. backup tmpl to minio server
            tmpls = self.get_tmpls(host=host)
            for x in tmpls:
                state, state_sum, results = aapi.run(
                    module='fetch',
                    args=dict(
                        dest='%s/' % tmpl_bak,
                        src=os.path.join(self._r_tmpl, self._folder_pre, x),
                        flat='yes'))
                msg = 'Tmpl File Backup: %s' % state_sum
                app.logger.debug(logmsg(msg))
                msg = 'Tmpl File Backup: %s' % results
                app.logger.info(logmsg(msg))
                self.minio.fput_object(
                    bucket_name=self._minio_bucket,
                    object_name=os.path.join(tmpl_pre, x),
                    file_path=os.path.join(tmpl_bak, x))
            # 3. backup conf to minio server
            # files should include (name, dir, mode, owner)
            for x in self._files:
                src = os.path.join(x['dir'], x['name'])
                file_name = '%s%s%s' % (
                    '@@'.join([x['mode'], x['owner']['name'], x['owner']['group']]),
                    self._broken_word_2,
                    src.replace('/', self._broken_word_1))
                state, state_sum, results = aapi.run(
                    module='fetch',
                    args=dict(
                        dest=os.path.join(conf_bak, file_name),
                        src=src, flat='yes'))
                msg = 'Conf File Backup: %s' % state_sum
                app.logger.debug(logmsg(msg))
                msg = 'Conf File Backup: %s' % results
                app.logger.info(logmsg(msg))
                file_path = os.path.join(conf_bak, file_name)
                if os.path.isfile(file_path):
                    self.minio.fput_object(
                        bucket_name=self._minio_bucket,
                        object_name=os.path.join(conf_pre, file_name),
                        file_path=file_path)
            # 4. check if toml/tmpl/conf have been backuped to minio server
            objs = [os.path.basename(x.object_name.encode('utf-8')) for x in
                    self.minio.list_objects(
                        bucket_name=self._minio_bucket, prefix=toml_pre,
                        recursive=False)]
            for x in tomls:
                if x not in objs:
                    raise Exception('Toml Backup Failed: %s.' % x)
            objs = [os.path.basename(x.object_name.encode('utf-8')) for x in
                    self.minio.list_objects(
                        bucket_name=self._minio_bucket, prefix=tmpl_pre,
                        recursive=False)]
            for x in tmpls:
                if x not in objs:
                    raise Exception('Tmpl Backup Failed: %s.' % x)

    def backup_keys(self):
        """backup configuration keys using etcd server
        """
        dir_pre = os.path.join('/', self._key_bak_pre, self._folder_pre)
        if dir_pre in self.etcd:
            self.etcd.delete(key=dir_pre, dir=True, recursive=True)
        for x in self._files:
            items = self.get_keys(cfg_name=x['name'])
            for k, v in items.items():
                ret = self.etcd.write(
                    key=os.path.join(dir_pre, x['name'], k), value=v)
                msg = 'Etcd Key Backup: %s.' % ret
                app.logger.info(logmsg(msg))

    def update_keys(self, rollback=False):
        """ update configuration keys stored in etcd server
            ps: when called for rollback, would delete keys totally new
        """
        for x in self._files:
            items = (self.get_keys(cfg_name=x['name'], rollback=rollback)
                     if rollback else x['items'])
            # delete keys which did not exist before update when doing rollback
            diff = set(x['items'].keys()).difference(set(items.keys()))
            for k in diff:
                key = os.path.join('/', self._folder_pre, x['name'], k)
                if key in self.etcd:
                    ret = self.etcd.delete(key=key)
                    msg = 'Etcd Key Deleted: %s.' % ret
                    app.logger.info(logmsg(msg))
            # update keys
            for k, v in items.items():
                ret = self.etcd.write(
                    key=os.path.join('/', self._folder_pre, x['name'], k),
                    value=v)
                msg = 'Etcd Key Updated: %s.' % ret
                app.logger.info(logmsg(msg))

    def get_keys(self, cfg_name, rollback=False):
        """ get configuration keys stored in the etcd server """
        key_pre = os.path.join(
            '/',
            (os.path.join(self._key_bak_pre, self._folder_pre)
             if rollback else os.path.join(self._folder_pre)),
            cfg_name)
        items = {}
        if key_pre in self.etcd:
            father = self.etcd.read(key=key_pre)
            msg = 'Etcd Key Read: %s.' % father
            app.logger.info(logmsg(msg))
            if hasattr(father, '_children'):
                for x in father._children:
                    items[x['key'].split('/')[-1]] = x['value']
        return items

    def delete_expired_keys(self):
        """delete expired configuration keys stored in etcd server
        """
        for x in self._files:
            key_pre = os.path.join('/', self._folder_pre, x['name'])
            if key_pre in self.etcd:
                father = self.etcd.read(key=key_pre)
                if hasattr(father, '_children'):
                    for y in father._children:
                        if y['key'].split('/')[-1] not in x['items'].keys():
                            ret = self.etcd.delete(key=y['key'])
                            msg = 'Etcd Key Deleted: %s.' % ret
                            app.logger.info(logmsg(msg))

    def delete_expired_files(self):
        """delete expired toml/tmpl files in remote confd client
        """
        cfg_names = [x['name'] for x in self._files]
        for host in self._hosts:
            aapi = Ansible2API(hosts=[host], **self._ansible_kwargs)
            # 1. delete expired toml file
            tomls = self.get_tomls(host=host)
            for x in tomls:
                config = x.split(self._file_pre)[1].split('toml')[0].strip('.')
                if config not in cfg_names:
                    state, state_sum, results = aapi.run(
                        module='file',
                        args=dict(
                            path=os.path.join(self._r_toml, x),
                            state='absent'))
                    msg = 'Toml File Deleted: %s' % state_sum
                    app.logger.debug(logmsg(msg))
                    msg = 'Toml File Deleted: %s' % results
                    app.logger.info(logmsg(msg))
            # 2. delete expired tmpl file
            tmpls = self.get_tmpls(host=host)
            for x in tmpls:
                config = x.split('.tmpl')[0]
                if config not in cfg_names:
                    state, state_sum, results = aapi.run(
                        module='file',
                        args=dict(
                            path=os.path.join(
                                self._r_tmpl, self._folder_pre, x),
                            state='absent'))
                    msg = 'Tmpl File Deleted: %s' % state_sum
                    app.logger.debug(logmsg(msg))
                    msg = 'Tmpl File Deleted: %s' % results
                    app.logger.info(logmsg(msg))

    def delete_files(self):
        """
            delete old toml/tmpl files in remote confd client
            ps: make sure that all these files have been backup already
        """
        for host in self._hosts:
            aapi = Ansible2API(hosts=[host], **self._ansible_kwargs)
            # 1. delete toml
            tomls = self.get_tomls(host=host)
            for x in tomls:
                state, state_sum, results = aapi.run(
                    module='file',
                    args=dict(
                        path=os.path.join(self._r_toml, x),
                        state='absent'))
                msg = 'Toml File Deleted: %s' % state_sum
                app.logger.debug(logmsg(msg))
                msg = 'Toml File Deleted: %s' % results
                app.logger.info(logmsg(msg))
            # 2. delete tmpl
            state, state_sum, results = aapi.run(
                module='file',
                args=dict(
                    path='%s/' % os.path.join(
                        self._r_tmpl, self._folder_pre),
                    state='absent'))
            msg = 'Tmpl File Deleted: %s' % state_sum
            app.logger.debug(logmsg(msg))
            msg = 'Tmpl File Deleted: %s' % results
            app.logger.info(logmsg(msg))

    def push_files(self, rollback=False):
        """ update toml/tmpl/(conf) files to remote/local confd client """
        for host in self._hosts:
            aapi = Ansible2API(hosts=[host], **self._ansible_kwargs)
            toml_folder = '%s/' % (
                os.path.join(self._l_toml_bak, host)
                if rollback else os.path.join(self._l_toml, host))
            tmpl_folder = '{}/'.format(
                os.path.join(self._l_tmpl_bak, host)
                if rollback else self._l_tmpl)
            if rollback:
                conf_folder = '%s/' % os.path.join(self._l_conf_bak, host)
                # clear folders
                remove_folder(toml_folder)
                remove_folder(tmpl_folder)
                remove_folder(conf_folder)
                get_folder(toml_folder)
                get_folder(tmpl_folder)
                get_folder(conf_folder)
                # download latest tomls/tmpls from minio
                toml_pre = '%s/' % os.path.join('toml', self._folder_pre, host)
                objs = self.minio.list_objects(
                    bucket_name=self._minio_bucket, prefix=toml_pre, recursive=False)
                for x in objs:
                    object_name = x.object_name.encode('utf-8')
                    self.minio.fget_object(
                        bucket_name=self._minio_bucket,
                        object_name=object_name,
                        file_path=os.path.join(
                            toml_folder, os.path.basename(object_name)))
                tmpl_pre = '%s/' % os.path.join('tmpl', self._folder_pre, host)
                objs = self.minio.list_objects(
                    bucket_name=self._minio_bucket, prefix=tmpl_pre, recursive=False)
                for x in objs:
                    object_name = x.object_name.encode('utf-8')
                    self.minio.fget_object(
                        bucket_name=self._minio_bucket,
                        object_name=object_name,
                        file_path=os.path.join(
                            tmpl_folder, os.path.basename(object_name)))
                conf_pre = '%s/' % os.path.join('conf', self._folder_pre, host)
                objs = self.minio.list_objects(
                    bucket_name=self._minio_bucket, prefix=conf_pre, recursive=False)
                for x in objs:
                    object_name = x.object_name.encode('utf-8')
                    self.minio.fget_object(
                        bucket_name=self._minio_bucket,
                        object_name=object_name,
                        file_path=os.path.join(
                            conf_folder, os.path.basename(object_name)))
                # push conf files to remote/local confd client
                for x in os.listdir(conf_folder):
                    config = x.split(self._broken_word_2)
                    file_path = config[1].replace(self._broken_word_1, '/')
                    info = config[0].split('@@')
                    state, state_sum, results = aapi.run(
                        module='copy',
                        args=dict(
                            mode=info[0],
                            src=os.path.join(conf_folder, x),
                            dest=file_path,
                            group=info[2],
                            owner=info[1]))
                    msg = 'Conf File Updated: %s' % state_sum
                    app.logger.debug(logmsg(msg))
                    msg = 'Conf File Updated: %s' % results
                    app.logger.info(logmsg(msg))
            # 1. push toml files to remote/local confd client
            state, state_sum, results = aapi.run(
                module='copy',
                args=dict(
                    mode=self._confd_file_mode,
                    src=toml_folder,
                    dest=self._r_toml,
                    group=self._confd_owner[1],
                    owner=self._confd_owner[0]))
            msg = 'Toml File Updated: %s' % state_sum
            app.logger.debug(logmsg(msg))
            msg = 'Toml File Updated: %s' % results
            app.logger.info(logmsg(msg))
            # 2. push tmpl files to remote/local confd client
            r_tmpl_folder = os.path.join(self._r_tmpl, self._folder_pre)
            state, state_sum, results = aapi.run(
                module='copy',
                args=dict(
                    mode=self._confd_file_mode,
                    src=tmpl_folder,
                    dest=r_tmpl_folder,
                    group=self._confd_owner[1],
                    owner=self._confd_owner[0]))
            msg = 'Tmpl File Updated: %s' % state_sum
            app.logger.debug(logmsg(msg))
            msg = 'Tmpl File Updated: %s' % results
            app.logger.info(logmsg(msg))

    def confd_cmd(self, action):
        """ confd client startup cmd """
        aapi = Ansible2API(hosts=self._hosts, **self._ansible_kwargs)
        state, state_sum, results = aapi.run(
            module='shell',
            args=self._confd_startup_cmd[action])
        msg = 'Confd %s: %s' % (action.upper(), state_sum)
        app.logger.debug(logmsg(msg))
        msg = 'Confd %s: %s' % (action.upper(), results)
        app.logger.info(logmsg(msg))

    def check_files(self):
        ret = {}
        template_regex = r'{{getv\s+"/%s"}}'
        mode_dict = {'-': 0, 'x': 1, 'w': 2, 'r': 4}
        aapi = Ansible2API(hosts=self._hosts, **self._ansible_kwargs)
        for x in self._files:
            abs_path = os.path.join(x['dir'], x['name'])
            ret[x['name']] = {host: {} for host in self._hosts}
            # 1. check md5
            # use tmpl to generate expected configuration file content
            content = x['template']
            for k, v in x['items'].items():
                content = re.sub(
                    pattern=template_regex % k, repl=v, string=content)
            # cuz ansible shell 'stdout' will ignore terminal '\r\n'
            expected_raw = content.rstrip('\r\n')
            expected_md5 = md5hex(expected_raw)
            # use ansible to fetch file content
            state, state_sum, results = aapi.run(
                module='shell', args='cat {0}'.format(abs_path))
            # compare the online to the expected using md5
            for host in self._hosts:
                actual_raw = results[host]['stdout'].rstrip('\r\n')
                actual_md5 = md5hex(actual_raw)
                if actual_md5 != expected_md5:
                    ret[x['name']][host]['content'] = '{0} != {1}'.format(
                        actual_md5, expected_md5)
                    ret[x['name']][host]['content_expected'] = expected_raw
                    ret[x['name']][host]['content_actual'] = actual_raw
                else:
                    ret[x['name']][host]['content'] = "OK"
            # 2. check mode
            state, state_sum, results = aapi.run(
                module='shell',
                args="ls -al %s|awk '{print $1}'" % abs_path)
            for host in self._hosts:
                mode = '0{0}{1}{2}'.format(
                    sum([mode_dict[y] for y in results[host]['stdout'][1:4]]),
                    sum([mode_dict[y] for y in results[host]['stdout'][4:7]]),
                    sum([mode_dict[y] for y in results[host]['stdout'][7:]]))
                ret[x['name']][host]['mode'] = (
                    '{0} != {1}'.format(mode, x['mode'])
                    if mode != x['mode'] else 'OK')
            # 3. check owner
            state, state_sum, results = aapi.run(
                module='shell',
                args="ls -al %s|awk '{print $3,$4}'" % abs_path)
            for host in self._hosts:
                owner = results[host]['stdout'].split()
                ret[x['name']][host]['owner'] = (
                    '{0} != {1}'.format(
                        tuple(owner), (x['owner']['name'], x['owner']['group']))
                    if owner[0] != x['owner']['name'] and
                    owner[1] != x['owner']['group'] else 'OK')
            # 4. check modify time
            state, state_sum, results = aapi.run(
                module='shell',
                args="ls --full-time %s|awk '{print $6,$7,$8}'" % abs_path)
            for host in self._hosts:
                ret[x['name']][host]['last_modify_time'] = results[host]['stdout']
        return ret
