#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# Leann Mak, leannmak@139.com, (c) 2018.
# This is the utility module of sakura package.
#

import os
import hashlib
import shutil
from enum import Enum
from flask import request


def get_folder(folder):
    """ create a folder if not exists and return
    """
    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder


def remove_folder(folder):
    """ remove a folder if exists
    """
    if os.path.exists(folder):
        shutil.rmtree(folder)
        return True
    return False


def logmsg(msg):
    """ normalize the logs.
    """
    logmsg = msg
    if request:
        logmsg = '{0}[from {1} to {2}]'.format(
            msg, request.remote_addr, request.url)
    return logmsg


class IntEnum(int, Enum):
    pass


class StrEnum(str, Enum):
    pass


def md5hex(text):
    """ use md5 encryption algorithm to generate a 32bit hex code.
    """
    if isinstance(text, unicode):
        text = text.encode('utf-8')
    elif not isinstance(text, str):
        text = str(text)
    m = hashlib.md5()
    m.update(text)
    return m.hexdigest()
