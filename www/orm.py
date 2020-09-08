#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "trydying"
import asyncio, logging
import aiomysql

logging.basicConfig(level=logging.INFO)


def log(sql):
    logging.info("SQL:%s" % sql)


async def create_pool(loop, **kw):
    """
    定义连接mysql的行为
    创建全局连接池__pool
    """
    logging.info("create database connection pool...")
    global __pool
    __pool = await aiomysql.create_pool(
        host=kw.get("host", "localhost"),  # host, default=localhost
        port=kw.get("port", 3306),
        user=kw["user"],
        password=kw["password"],
        db=kw["db"],
        charset=kw.get("charset", "utf8"),
        autocommit=kw.get("autocommit", True),  #  whether autocommit, default is true
        maxsize=kw.get("maxsize", 10),  #  max connection numbers
        minsize=kw.get("minsize", 1),
        loop=loop,
    )
    return


async def select(sql, args, size=None):
    """定义select行为"""
    logging.log(sql)
    global __pool
    async with __pool.get() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(sql.replace("?", "%s"), args or ())  # ? => %s
            if size:
                res = await cur.fetchmany(size)  #  获取 size 行
            else:
                res = await cur.fetchall()

        logging.info("rows returned:%s" % len(res))
        return res


async def execute(sql, args):
    """execute INSERT, UPDATE, DELETE"""
    log(sql)
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
    """
    生成占位符
    返回 '?,?,?,?'
    """
    L = []
    for n in range(num):
        L.append("?")
    return ", ".join(L)


class Field(object):

    """
    base field
    实现column_name, column_type, primary_key的映射
    """

    def __init__(self, name, column_type, primary_key, default):
        self._name = name
        self._column_type = column_type
        self._primary_key = primary_key
        self._default = default

    def __repr__(self):
        return "<%s, %s:%s>" % (self.__class__.__name__, self._column_type, self._name)


class StringField(Field):
    """
    stringfield字段
    在base field的基础上绑定一个column_type
    """

    def __init__(self, name=None, primary_key=False, default=None, ddl="varchar(100)"):
        super().__init__(name, ddl, primary_key, default)


class BooleanField(Field):
    def __init__(self, name=None, primary_key=False, default=False):
        super().__init__(name, "boolean", primary_key, default)


class IntegerField(Field):
    def __init__(self, name=None, primary_key=False, default=0):
        super().__init__(name, "bigint", primary_key, default)


class FloatField(Field):
    def __init__(self, name=None, primary_key=False, default=0.0):
        super().__init__(name, "real", primary_key, default)


class TextField(Field):
    def __init__(self, name=None, primary_key=False, default=None):
        super().__init__(name, "text", primary_key, default)


class ModelMetaclass(type):

    """
    Model的模板，继承自type，控制创建Model的行为
    User实例的创建过程:
    继承Model -> 创建User(属性) -> 参照Metaclass修改属性 -> 根据传入参数完成__init__
    metaclass修改User中的attrs,增加__mappings__,__fields__, __table__等属性
    并在attrs中删除冗余的__mappings__映射
    """

    def __new__(cls, name, bases, attrs):
        """
        : cls class :Model or User or Blog...
        : name self.__class__.__name__: "Model" or "User" or "Field" ...
        : bases ModelMetaclass or Model or Field
        : attrs key->value
        """
        if name == "Model":  #  排除Model类,避免重复Metaclass->Model->User中的重复操作
            return type.__new__(cls, name, bases, attrs)
        tableName = attrs.get("__table__", None) or name
        mappings = dict()  # 空dict,用于保存Field映射，再赋给attrs["__mappings__"]
        fields = []
        primaryKey = None
        for k, v in attrs.items():
            if isinstance(v, Field):
                mappings[k] = v
                if v._primary_key:
                    primaryKey = k
                else:
                    fields.append(k)
        if not primaryKey:
            raise Warning("Primary key not found")

        for k in mappings.keys():
            """
            以id属性为例
            User将id绑定到Field类,而后参照Metaclass将id属性删除，增加__mappings__属性
            初始化实例u=User(id=...)时，调用Model类(dict)__init__，将id键值赋给User instance
            Model中定义了__getattr__，使得id可以用u.id直接访问，不必使用u['id']
            若在此处不删除User的id属性，u.id将访问User中的id属性，而不会调用Model中的getattr
            """
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
            ", ".join(map(lambda f: "`%s`=?" % (mappings.get(f)._name or f), fields)),
            primaryKey,
        )
        attrs["__delete__"] = "delete from `%s` where `%s`=?" % (tableName, primaryKey)
        return type.__new__(cls, name, bases, attrs)


class Model(dict, metaclass=ModelMetaclass):

    """Base Model"""

    def __init__(self, **kw):
        #  super(Model, self).__init__(**kw)
        super().__init__(**kw)

    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value

    def getValue(self, key):
        return self.__getattr__(key)

    def getValueOrDefault(self, key):
        value = getattr(self, key, None)
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                self.__setattr__(key, value)
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
