#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "trydying"

"url handlers"

import re, time, json, logging, hashlib, base64, asyncio

from .coroweb import get, post

from .models import User, Comment, Blog, next_id


@get("/")
async def index(request):
    summary = "Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet."
    blogs = [
        Blog(id="1", name="Blog1", summary=summary, created_at=time.time()),
        Blog(id="2", name="Blog2", summary=summary, created_at=time.time() - 3600),
    ]
    return {"__template__": "blogs.html", "blogs": blogs}
