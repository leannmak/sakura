#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# Leann Mak, leannmak@139.com, (c) 2018.
# This is the constant module of sakura package.
#

from sakura.util import IntEnum, StrEnum


TASK_STATE = StrEnum(
    'TASK_STATE',
    dict(
        PENDING='PENDING', PROGRESS='PROGRESS', FAILURE='FAILURE',
        SUCCESS='SUCCESS'))

TASK_PERCENTAGE = IntEnum(
    'TASK_PERCENTAGE', dict(STARTPOINT=0, ENDPOINT=100))

TASK_NAME = StrEnum(
    'TASK_NAME',
    dict(
        CONFIGURATION_UPDATE='configuration_update',
        CONFIGURATION_CHECK='configuration_check',
        CONFIGURATION_ACKNOWLEDGE='configuration_acknowledge',
        CONFIGURATION_ROLLBACK='configuration_rollback'))

CONFIGURATION_UPDATE_STEP = IntEnum(
    'CONFIGURATION_UPDATE_STEP', ['INITIALIZE', 'BACKUP', 'CLEANUP', 'UPDATE'])

CONFIGURATION_UPDATE_ACK_STATE = StrEnum(
    'CONFIGURATION_UPDATE_ACK_STATE',
    {
        'PENDING': 'PENDING',
        TASK_NAME.CONFIGURATION_ACKNOWLEDGE.value: 'PASSED',
        TASK_NAME.CONFIGURATION_ROLLBACK.value: 'ROLLBACKED'})
