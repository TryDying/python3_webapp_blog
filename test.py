#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test
"""

__author__ = "trydying"
import asyncio

import www.orm as orm
from www.models import User, Comment

loop = asyncio.get_event_loop()


async def test():
    # 数据库参数
    await orm.create_pool(user="wide", password="wide123456789", db="test", loop=loop)
    # 传入事件循环
    await orm.create_pool(loop=loop)


loop.run_until_complete(test())
