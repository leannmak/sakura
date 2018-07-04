#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# Leann Mak, leannmak@139.com, (c) 2018.
# This is the manager script for sakura package.
#

from flask.ext.script import Manager, Shell, prompt_bool
from flask.ext.migrate import Migrate, MigrateCommand

from sakura import app, db

manager = Manager(app, usage="manager script support for sakura")
manager.add_command('shell', Shell(make_context=dict(app=app, db=db)))
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)


@manager.command
def initdb():
    "Initialize database tables"
    db.create_all()
    print 'Database initialized, location:\r\n[%-10s] %s' % (
          'DEFAULT', app.config['SQLALCHEMY_DATABASE_URI'])


@manager.command
def dropdb(force=False):
    "Drops database tables"
    exe = (True if force or prompt_bool(
        'Are you sure you want to lose all your data?') else False)
    if exe:
        db.drop_all()
        print 'Database dropped, location:\r\n[%-10s] %s' % (
            'DEFAULT', app.config['SQLALCHEMY_DATABASE_URI'])


@manager.command
def recreatedb():
    "Recreates database tables (same as issuing 'dropdb' and 'initdb')"
    dropdb()
    initdb()


if __name__ == '__main__':
    manager.run()
