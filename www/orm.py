#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "trydying"
import asyncio, logging
import aiomysql


async def create_pool(loop, **kw):
    global __pool
    __pool = await aiomysql.create_pool(
        host=kw.get("host", "localhost"),
        port=kw.get("port", 3306),
        user=kw["user"],
        password=kw["password"],
        db=kw["db"],
        charset=kw.get("charset", "utf8"),
        autocommit=kw.get("autocommit", True),
        maxsize=kw.get("maxsize", 10),
        minsize=kw.get("minsize", 1),
        loop=loop,
    )
    return


async def select(sql, args, size=None):
    """orm of select"""
    global __pool
    async with __pool.get() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(sql.replace("?", "%s"), args or ())  # ? => %s
            if size:
                res = await cur.fetchmany(size)
            else:
                res = await cur.fetchall()

        return res


async def execute(sql, args):
    """execute for INSERT, UPDATE, DELETE"""
    async with __pool.get() as conn:
        if not autocommit:
            await conn.begin()
        try:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql.replace("?", "%s"), args)
                affected = cur.rowcount
            if not autocommit:
                await conn.commit()
        except BaseException as e:
            if not autocommit:
                await conn.rollback()
            raise
        return affected


def create_args_string(num):
    """return '?,?,?,?'
    """
    L = []
    for n in range(num):
        L.append("?")
    return ", ".join(L)


class Field(object):

    """Init Field"""

    def __init__(self, name, column_type, primary_key, default):
        """TODO: to be defined.

        """
        self._name = name
        self._column_type = column_type
        self._primary_key = primary_key
        self._default = default

    def __str__(self):
        return "<%s, %s:%s>" % (self.__class__.__name__, self._column_type, self._name)

    def __repr__(self):
        return "<%s, %s:%s>" % (self.__class__.__name__, self._column_type, self._name)


class StringField(Field):
    def __init__(self, name=None, primary_key=False, default=None, ddl="varchar(100)"):
        super().__init__(name, ddl, primary_key, default)


class BooleanField(Field):
    def __init__(self, name=None, primary_key=False, default=False):
        super().__init__(name, "boolean", primary_key, default)


class IntegerField(Field):
    def __init__(self, name=None, primary_key=False, default=0):
        super().__init__(name, "bigint", primary_key, default)


class FloatField(Field):

    """subclass field for float"""

    def __init__(self, name=None, primary_key=False, default=0.0):
        super().__init__(name, "real", primary_key, default)


class TextField(Field):
    def __init__(self, name=None, primary_key=False, default=None):
        super().__init__(name, "text", primary_key, default)


class ModelMetaclass(type):

    """define new type"""

    def __new__(cls, name, bases, attrs):
        if name == "Model":
            return type.__new__(cls, name, bases, attrs)
        tableName = attr.get("__table__", None) or name
        mapppings = dict()
        fields = []
        primaryKey = None
        for k, v in attrs.items():
            if isinstance(v, Field):
                mappings[k] = v
                if v._primary_key:
                    primaryKey = k
                else:
                    fields.append(k)
        for k in mappings.keys():
            attrs.pop(k)
        escaped_fields = list(map(lambda f: "`%s`" % f, fields))
        attrs["__mappings"] = mappings
        attrs["__table__"] = tableName
        attrs["__primary_key__"] = primaryKey  # primaryKey
        attrs["__fields__"] = fields  # keyname except primaryKey
        attrs["__select__"] = "selsect `%s`, %s from `%s`" % (
            primaryKey,
            ", ".join(escaped_fields),
            tableName,
        )
        attrs["__insert__"] = "insert into `%s`(%s, `%s`)values (%s)" % (
            tableName,
            ", ".join(escaped_fields),
            primaryKey,
            create_args_string(len(escaped_fields) + 1),
        )
        attrs["__update__"] = "update `%s` set %s where `%s`=?" % (
            tableName,
            ", ".join(map(lambda f: "`%s`=?" % (mappings.get(f).name or f), fields)),
            primaryKey,
        )
        attrs["__delete__"] = "delete from `%s` where `%s`=?" % (tableName, primaryKey)
        return type.__new__(cls, name, bases, attrs)


class Model(dict, metaclass=ModelMetaclass):

    """Docstring for Model. """

    def __init__(self, **kw):
        #  super(Model, self).__init__(**kw)
        super().__init__(**kw)

    def __getattr__(self, key):
        return self[key]

    def _setattr__(self, key, value):
        self[key] = value

    def getValue(self, key):
        return getattr(self, key, None)

    def getValueOrDefault(self, key):
        value = getattr(self, key, None)
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                setattr(self, key, value)
        return value

    @classmethod
    async def findAll(cls, where=None, args=None, **kw):
        """TODO: Docstring for findAll.

        :where: TODO
        :args: TODO
        :**kw: TODO
        :returns: TODO

        """
        sql = [cls.__select__]
        if where:
            sql.append("where")
            sql.append(where)
        if args is None:
            args = []
        orderBy = kw.get("orderBy", None)
        if orderBy:
            sql.append("orderby")
            sql.append(orderBy)

        limit = kw.get("limit", None)
        if limit is not None:
            sql.append("limit")
            if isinstance(limit, int):
                sql.append("?")
                args.append(limit)
            elif isinstance(limit, tuple) and len(limit) == 2:
                sql.append("?, ?")
                args.extend(limit)
            else:
                raise ValueError
        res = await select(" ".join(sql), args)
        return [cls(**r) for i in res]

    @classmethod
    async def findNumber(cls, selectField, where=None, args=None):
        """find number by select and where"""
        sql = ["select %s _num_ from `%s`" % (selectField, cls.__table__)]
        if where:
            sql.append("where")
            sql.append(where)

        res = await select(" ".join(sql), args, 1)
        if len(res) == 0:
            return None
        return res[0]["_num_"]

    @classmethod
    async def find(cls, pk):
        """find object by primaryKey

        :pk: TODO
        :returns: TODO

        """
        res = await select(
            "%s where `%s`=?" % (cls.__select__, cls.__primary_key__), [pk], 1
        )
        if len(rs) == 0:
            return None
        return cls(**rs[0])

    async def save(self):
        """TODO: Docstring for save.
        :returns: TODO

        """
        args = list(map(self.getValueOrDefault, self.__fields__))
        args.append(self.getValueOrDefault(self.__primary_key__))
        rows = await execute(self.__insert__, args)

    async def update(self):
        """TODO: Docstring for update.

        :f: TODO
        :returns: TODO

        """
        args = list(map(self.getValue, self.__fields__))
        args.append(self.getValue(self.__primary_key__))
        rows = await execute(self.__update__, args)

    async def remove(self):
        """TODO: Docstring for remove.
        :returns: TODO

        """
        args = [self.getValue(self.__primary_key__)]
        rows = await execute(self.__delete__, args)
