#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test
"""

__author__ = "trydying"
import asyncio

import www.orm as orm
from www.models import User, Comment
from www.config import configs

loop = asyncio.get_event_loop()


async def mycreatpool(**kw):
    await orm.create_pool(
        loop=loop,
        user=kw["user"],
        password=kw["password"],
        db=kw["db"],
        port=kw["port"],
        host=kw["host"],
    )


async def test():
    # 数据库参数
    #  await orm.create_pool(loop=loop, user="wide", password="wide123456789", db="test")
    params = configs.db
    await mycreatpool(
        #  user=params.user,
        #  password=params.password,
        #  db=params.db,
        #  port=params.port,
        #  host=params.host,
        **params,
    )
    # 传入事件循环
    await orm.create_pool(loop=loop)


loop.run_until_complete(test())
