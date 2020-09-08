#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "trydying"
import time, uuid
from .orm import (
    Model,
    StringField,
    BooleanField,
    FloatField,
    TextField,
    IntegerField,
)


def next_id():
    """
    generate id
    """
    return "%015d%s000" % (int(time.time() * 1000), uuid.uuid4().hex)


class User(Model):
    __table__ = "users"  #  不定义，将使用class_name: User

    id = StringField(primary_key=True, default=next_id, ddl="varchar(50)")
    email = StringField(ddl="varchar(50)")
    passwd = StringField(ddl="varchar(50)")
    admin = BooleanField()
    name = StringField(ddl="varchar(50)")
    image = StringField(ddl="varchar(500)")
    created_at = FloatField(default=time.time)


class Blog(Model):
    __table__ = "blogs"

    id = StringField(primary_key=True, default=next_id, ddl="varchar(50)")
    user_id = StringField(ddl="varchar(50)")
    user_name = StringField(ddl="varchar(50)")
    user_image = StringField(ddl="varchar(500)")
    name = StringField(ddl="varchar(50)")
    summary = StringField(ddl="varchar(200)")
    content = TextField()
    created_at = FloatField(default=time.time)


class Comment(Model):
    __table__ = "comments"

    id = StringField(primary_key=True, default=next_id, ddl="varchar(50)")
    blog_id = StringField(ddl="varchar(50)")
    user_id = StringField(ddl="varchar(50)")
    user_name = StringField(ddl="varchar(50)")
    user_image = StringField(ddl="varchar(500)")
    content = TextField()
    created_at = FloatField(default=time.time)
