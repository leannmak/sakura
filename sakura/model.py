#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# Leann Mak, leannmak@139.com, (c) 2018.
# This is the model module of sakura package.
#

from sqlalchemy.dialects.mysql import LONGTEXT

from sakura import app, db
from sakura import constant as C
from sakura.util import logmsg


class TaskManager(db.Model):
    """
        Task Manager Model.
    """
    __tablename__ = 'task_manager'
    __DBContraintException = 'Database Contraint Exception: %s.'

    # task id
    task_id = db.Column(db.String(64), primary_key=True)
    # task name
    name = db.Column(db.String(64), nullable=False)
    # task arguments
    kwargs = db.Column(db.Text, nullable=False)
    # task creating time
    begin_time = db.Column(db.DateTime, nullable=False)
    # task ending time
    end_time = db.Column(db.DateTime)
    # task elapsed time
    delta_time = db.Column(db.Float)
    # task state (pending/failure/success)
    state = db.Column(db.String(16), default=C.TASK_STATE.PENDING.value)
    # task return information
    info = db.Column(LONGTEXT)
    # task result acknowledge status (1: pending, 2: passed, 3: rollbacked)
    ack_status = db.Column(db.String(16))
    # task current step
    step = db.Column(db.SmallInteger, default=0)
    # follow-up task id if exists
    sub_task_id = db.Column(
        db.String(64), db.ForeignKey('task_manager.task_id'))

    # constructor
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if k in self._columns():
                setattr(self, k, v)

    def insert(self, **kwargs):
        if kwargs:
            obj = self.__class__(**kwargs)
            db.session.add(obj)
            try:
                db.session.commit()
                return obj._to_dict()
            except Exception, e:
                db.session.rollback()
                msg = self.__DBContraintException % e
                app.logger.error(logmsg(msg))
                return {}
        return None

    def getObject(self, task_id):
        li = self.__class__.query.filter_by(task_id=task_id).all()
        if li:
            return li[0]
        return None

    def get(self, page=None, per_page=20, **kwargs):
        li = None
        if not kwargs:
            if page:
                li = self.__class__.query.paginate(page, per_page, False)
            else:
                li = self.__class__.query.order_by(
                    self.__class__.begin_time.desc()).all()
        else:
            li = self.__class__.query.filter_by(**kwargs).order_by(
                self.__class__.begin_time.desc()).all()
        if li:
            if not kwargs and page:
                return [x._to_dict() for x in li.items], li.pages
            return [x._to_dict() for x in li]
        return []

    def update(self, task_id, **kwargs):
        obj = self.__class__.query.filter_by(task_id=task_id).first()
        if obj:
            for k, v in kwargs.items():
                if k in self._columns():
                    setattr(obj, k, v)
            try:
                db.session.commit()
                return obj._to_dict()
            except Exception, e:
                db.session.rollback()
                msg = self.__DBContraintException % e
                app.logger.error(logmsg(msg))
                return {}
        return None

    # list of model columns
    def _columns(self):
        return self.__class__.__mapper__.columns.__dict__['_data']

    # model to dict
    def _to_dict(self):
        return {k: getattr(self, k) for k in self._columns()}

    def task_step(
            self, task, name=None, args=None,
            state=C.TASK_STATE.PROGRESS.value,
            current=C.TASK_PERCENTAGE.STARTPOINT.value,
            data=None, message=None, error=None, flag=None):
        if flag:
            msg = self.update(task_id=task.request.id, step=flag)
            app.logger.debug(logmsg(msg))
        args = args if args else {}
        meta = dict(
            current=current,
            total=C.TASK_PERCENTAGE.ENDPOINT.value,
            message=message,
            data=data)
        if error:
            meta['error'] = error
        app.logger.info(logmsg(state))
        app.logger.info(logmsg(meta))
        task.update_state(task_id=task.request.id, state=state, meta=meta)
        ret = name(**args) if name else None
        app.logger.debug(logmsg(ret))
        return ret, meta, state
