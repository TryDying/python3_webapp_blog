#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
default configuration
"""

__author__ = "trydying"

configs = {
    "debug": True,
    "db": {
        "host": "127.0.0.1",
        "port": 3306,
        "user": "user",
        "password": "passwd",
        "db": "database",
    },
    "session": {"secret": "Blog"},
}

