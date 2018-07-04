#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# Leann Mak, leannmak@139.com, (c) 2018.
# This is the input module of sakura package.
#

import re
import json
from copy import deepcopy
from IPy import IP as ip_from_ipy


class dictionary(object):
    """
        Restrict input to a dictionary
    """
    def __call__(self, value):
        return self._get_dict(value)

    def _get_dict(self, value):
        try:
            if isinstance(value, str):
                value = json.loads(value)
            return dict(value)
        except (TypeError, ValueError):
            raise ValueError('{0} is not a valid dictionary'.format(value))

    @classmethod
    def type_desc(cls, keys):
        for x in keys:
            if isinstance(keys[x], dictionary):
                keys[x] = str(keys[x])
        return keys


class defined_dictionary(dictionary):
    """
        Restrict input to a dictionary with specific keys
    """
    def __init__(self, keys, argument='argument'):
        self.keys = keys
        self.argument = argument

    def __call__(self, value):
        value = self._get_dict(value)
        error = ('Invalid {arg}: {value}. {arg} must be a dictionary '
                 'like {type}'.format(
                     arg=self.argument, value=value, type=str(self)))
        if value and set(value.keys()) == set(self.keys.keys()):
            for k in value:
                try:
                    value[k] = self.keys[k](value[k])
                except (TypeError, ValueError):
                    raise ValueError(error)
        else:
            raise ValueError(error)
        return value

    def __str__(self):
        return "<type '{0}' {1}>".format(
            self.__class__.__name__, self.type_desc(deepcopy(self.keys)))


class union_dictionary(dictionary):
    """
        Restrict input to a dictionary with specific keys' and values' types
    """
    def __init__(self, key_type=None, value_type=None, argument='argument'):
        self.key_type = key_type
        self.value_type = value_type
        self.argument = argument

    def __call__(self, value):
        value = self._get_dict(value)
        error = ('Invalid {arg}: {value}. {arg} must be a dictionary '
                 'subjects to {type}'.format(
                     arg=self.argument, value=value, type=str(self)))
        if value:
            for k in value:
                try:
                    k = self.key_type(k)
                    value[k] = self.value_type(value[k])
                except (TypeError, ValueError, KeyError):
                    raise ValueError(error)
        return value

    def __str__(self):
        return "<type '{0}' {1}>".format(
            self.__class__.__name__, {self.key_type: (
                str(self.value_type) if isinstance(self.value_type, dictionary)
                else self.value_type)})


def ip(value):
    """ Validate a IP address.
    :param string value : the IP address to validate
    :returns            : the IP address if valid
    :raises             : ValueError
    """
    message = u"{0} is not a valid IP address".format(value)
    try:
        if re.search(r'[/\-]', value):
            raise ValueError(message)
        value = ip_from_ipy(value).strNormal()
    except (TypeError, ValueError):
        raise ValueError(message)
    return value
