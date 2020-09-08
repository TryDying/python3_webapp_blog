#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "trydying"

"""
JSON API
"""
import json, logging, inspect, functools


class APIError(Exception):
    """docstring for APIError """

    def __init__(self, error, data="", message=""):
        super().__init__(message)
        self._error = error
        self._data = data
        self._message = message


class APIValueError(APIError):

    """indicate input value error"""

    def __init__(self, field, message=""):
        super().__init__("value:invalid", field, message)


class APIResourceNotFoundError(APIError):
    """indicate resource error"""

    def __init__(self, field, message=""):
        super().__init__("value:not found", field, message)


class APIPermissionError(APIError):
    """api permission error"""

    def __init__(self, message=""):
        super().__init__("permission:forbidden", "permission", message)

