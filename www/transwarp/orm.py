# coding=utf-8

__author__ = "Liu Cong"

"""
filename: www.transwarp.orm.py
create time: 2017-09-11
disc: ORM module.
      We can use the ORM module to do something like:
        user = User.get('123')
      rather than
        u = db.select_one('select * from users where id=?', '123')
        user = User(**u)
"""

import db
import time, logging

class Field(object):
    """
    负责保存数据库表中的字段属性的基类。
    """
    _count = 0  # 字段排序编号

    def __init__(self, **kw):
        self.name = kw.get('name', None)                # 字段名
        self._default = kw.get('default', None)         # 字段默认值(可能是值，也可能是一个函数)
        self.primary_key = kw.get('primary_key', False) # 字段是否是主键，默认否
        self.nullable = kw.get('nullable', False)       # 字段是否可空，默认否
        self.updatable = kw.get('updatable', True)      # 字段是否可修改，默认是
        self.insertable = kw.get('insertable', True)    # 字段是否可插入，默认是
        self.ddl = kw.get('ddl', '')                    # 字段类型
        self._order = Field._count                      # 字段排序，_count越小，排在越前面
        Field._count = Field._count + 1

    @property
    def default(self):
        """
        构造实例属性
        :return: 返回字段默认值
        """
        d = self._default
        return d() if callable(d) else d

    def __str__(self):
        s = ['<%s:%s,%s,default(%s),' % (self.__class__.__name__, self.name, self.ddl, self._default)]
        self.nullable and s.append('N')
        self.updatable and s.append('U')
        self.insertable and s.append('I')
        s.append('>')
        return ''.join(s)

class StringField(Field):
    """
    字符串类型的Field
    """
    def __init__(self, **kw):
        if 'default' not in kw:
            kw['default'] = ''
        if 'ddl' not in kw:
            kw['ddl'] = 'varchar(255)'
        super(StringField, self).__init__(**kw)

class IntegerField(Field):
    """
    整数类型的Field
    """
    def __init__(self, **kw):
        if 'default' not in kw:
            kw['default'] = 0
        if 'ddl' not in kw:
            kw['ddl'] = 'bigint'
        super(IntegerField, self).__init__(**kw)

class FloatField(Field):
    """
    浮点类型的Field
    """
    def __init__(self, **kw):
        if 'default' not in kw:
            kw['default'] = 0.0
        if 'ddl' not in kw:
            kw['ddl'] = 'real'
        super(FloatField, self).__init__(**kw)

class BooleanField(Field):
    """
    布尔类型的Field
    """
    def __init__(self, **kw):
        if 'default' not in kw:
            kw['default'] = False
        if 'ddl' not in kw:
            kw['ddl'] = 'bool'
        super(BooleanField, self).__init__(**kw)

class TextField(Field):
    """
    文本类型的Field
    """
    def __init__(self, **kw):
        if 'default' not in kw:
            kw['default'] = ''
        if 'ddl' not in kw:
            kw['ddl'] = 'text'
        super(TextField, self).__init__(**kw)

class BlobField(Field):
    """
    Blob类型的Field
    """
    def __init__(self, **kw):
        if 'default' not in kw:
            kw['default'] = ''
        if 'ddl' not in kw:
            kw['ddl'] = 'blob'
        super(BlobField, self).__init__(**kw)

class VersionField(Field):
    def __init__(self, name=None):
        super(VersionField, self).__init__(name=name, default=0, ddl='bigint')

""" ...等等其他类型的Field """

# 触发器
_triggers = frozenset(['pre_insert', 'pre_update', 'pre_delete'])

def _gen_sql(table_name, mappings):
    """
    动态生成创建表的sql语句字符串
    :param table_name: 表名  str
    :param mappings: 表字段  {字段key1: 字段实例1, 字段key2: 字段实例2, ...}
    :return: 返回sql字符串，类似于如下：
            CREATE TABLE t1(
              id int not null,
              name char(20),
              primary key (id)
            );
    """
    pk = None  # 主键字段的名称
    sql = ['-- generating SQL for %s:' % table_name, 'create table `%s` (' % table_name]
    for f in sorted(mappings.values(), lambda x, y: cmp(x._order, y._order)):
        if not hasattr(f, 'ddl'):
            raise StandardError('no ddl in field "%s".' % f)
        ddl = f.ddl
        nullable = f.nullable
        if f.primary_key:
            pk = f.name
        sql.append(nullable and '  `%s` %s,' % (f.name, ddl) or '  `%s` %s not null,' % (f.name, ddl))
    sql.append('  primary key(`%s`)' % pk)
    sql.append(');')
    return '\n'.join(sql)

class ModelMetaclass(type):
    """
    元类(最重要的部分！！！)
    """
    def __new__(cls, name, bases, attrs):
        """
        __new__ 是在__init__之前被调用的特殊方法，
        __new__是用来创建对象(类)并返回之的方法，
        __new_()是一个类方法.
        :param cls: 类似于在普通类方法中的self参数一样：<class '__main__.ModelMetaclass'>
        :param name: 当前实例对象的类名：User或者Model
        :param bases: 类继承的父类集合：
        :param attrs: 类的属性和方法集合
        :return: 返回类修改后的定义
        """
        # 如果是创建Model类，则直接返回不做任何操作的类。
        if name == 'Model':
            return type.__new__(cls, name, bases, attrs)

        # 存储使用了该元类的类的名称。
        if not hasattr(cls, 'subclasses'):
            cls.subclasses = {}
        if name not in cls.subclasses:
            cls.subclasses[name] = name
        else:
            logging.warning('Redefine class: %s' % name)

        # 生成ORM映射关系。
        logging.info('Scan ORMapping %s...' % name)
        mappings = dict()  # 存储表字段与Field的映射关系。
        primary_key = None  # 存储表的主键字段，Field类型。
        for k, v in attrs.iteritems():
            if isinstance(v, Field):
                if not v.name:
                    v.name = k
                logging.info('Found mapping: %s => %s' % (k, v))
                # check duplicate primary key:
                if v.primary_key:
                    if primary_key:
                        raise TypeError('Cannot define more than 1 primary key in class: %s' % name)
                    if v.updatable:
                        logging.warning('NOTE: change primary key to non-updatable.')
                        v.updatable = False
                    if v.nullable:
                        logging.warning('NOTE: change primary key to non-nullable.')
                        v.nullable = False
                    primary_key = v
                mappings[k] = v

        # 检查是否存在主键：
        if not primary_key:
            raise TypeError('Primary key not defined in class: %s' % name)

        # 删掉attrs中，value是Field类型的属性，也就是代表字段的属性。
        for k in mappings.iterkeys():
            attrs.pop(k)

        # 存储表名
        if '__table__' not in attrs:
            attrs['__table__'] = name.lower()

        # 为attrs添加特殊属性
        attrs['__mappings__'] = mappings
        attrs['__primary_key__'] = primary_key
        attrs['__sql__'] = lambda self: _gen_sql(attrs['__table__'], mappings)
        for trigger in _triggers:
            if trigger not in attrs:
                attrs[trigger] = None

        return type.__new__(cls, name, bases, attrs)

class Model(dict):
    """
    所有ORM映射的基类Model:

    >>> class User(Model):
    ...     id = IntegerField(primary_key=True)
    ...     name = StringField()
    ...     email = StringField(updatable=False)
    ...     passwd = StringField(default=lambda: '******')
    ...     last_modified = FloatField()
    ...     def pre_insert(self):
    ...         self.last_modified = time.time()
    >>> u = User(id=10190, name='Michael', email='orm@db.org')
    >>> r = u.insert()
    >>> u.email
    'orm@db.org'
    >>> u.passwd
    '******'
    >>> u.last_modified > (time.time() - 2)
    True
    >>> f = User.find_by_pk(10190)
    >>> f.name
    u'Michael'
    >>> f.email
    u'orm@db.org'
    >>> f.email = 'changed@db.org'
    >>> r = f.update() # change email but email is non-updatable!
    >>> len(User.find_all())
    1
    >>> g = User.find_by_pk(10190)
    >>> g.email
    u'orm@db.org'
    >>> r = g.delete()
    >>> len(db.select('select * from user where id=10190'))
    0
    >>> print User().__sql__()
    -- generating SQL for user:
    create table `user` (
      `id` bigint not null,
      `name` varchar(255) not null,
      `email` varchar(255) not null,
      `passwd` varchar(255) not null,
      `last_modified` real not null,
      primary key(`id`)
    );
    """
    __metaclass__ = ModelMetaclass

    def __init__(self, **kw):
        super(Model, self).__init__(**kw);

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value

    @classmethod
    def find_by_pk(cls, pk):
        """
        通过主键查找
        :param pk: 主键值
        :return: Model类型的对象或者None
        """
        d = db.select_one('select * from `%s` where %s=?' % (cls.__table__, cls.__primary_key__.name), pk)
        return cls(**d) if d else None

    @classmethod
    def find_first(cls, where, *args):
        """
        通过where clause和条件args查找，并返回一个Model类型的对象。
        如果查询结果有多个，则返回第一个。如果没有查询结果，则返回None。
        :param where: where clause条例
        :return: Model类型的对象或者None
        """
        d = db.select_one('select * from `%s` %s' % (cls.__table__, where), *args)
        return cls(**d) if d else None

    @classmethod
    def find_all(cls):
        """
        查找所有的记录
        :return: list(Model)集合
        """
        l = db.select('select * from `%s`' % cls.__table__)
        return [cls(**d) for d in l]

    @classmethod
    def find_by(cls, where, *args):
        """
        通过where clause和条件args查找,返回list(Model)集合
        :param where: where clause条例
        :param args: 查询条件
        :return: list(Model)集合
        """
        l = db.select('select * from `%s` %s' % (cls.__table__, where), *args)
        return [cls(**d) for d in l]

    @classmethod
    def count_all(cls):
        """
        Find by 'select count(pk) from table' and return integer.
        :return: integer
        """
        return db.select_int('select count(`%s`) from `%s`' % (cls.__primary_key__.name, cls.__table__))

    @classmethod
    def count_by(cls, where, *args):
        """
        Find by 'select count(pk) from table where ... ' and return integer.
        :param where: where clause条例
        :param args: 查询条件
        :return: integer
        """
        return db.select_int('select count(`%s`) from `%s` %s' % (cls.__primary_key__.name, cls.__table__, where), *args)

    def update(self):
        self.pre_update and self.pre_update()
        L = []
        args = []
        for k, v in self.__mappings__.iteritems():
            if v.updatable:
                if hasattr(self, k):
                    arg = getattr(self, k)
                else:
                    arg = v.default
                    setattr(self, k, arg)
                L.append('`%s`=?' % k)
                args.append(arg)
        pk = self.__primary_key__.name
        args.append(getattr(self, pk))
        db.update('update `%s` set %s where %s=?' % (self.__table__, ','.join(L), pk), *args)
        return self

    def delete(self):
        self.pre_delete and self.pre_delete()
        pk = self.__primary_key__.name
        args = (getattr(self, pk),)
        db.update('delete from `%s` where `%s`=?' % (self.__table__, pk), *args)

    def insert(self):
        self.pre_insert and self.pre_insert()
        params = {}
        for k, v in self.__mappings__.iteritems():
            if v.insertable:
                if not hasattr(self, k):
                    setattr(self, k, v.default)
                params[v.name] = getattr(self, k)
        db.insert(self.__table__, **params)
        return self

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    db.create_engine('root', '123456', 'awesome')
    # db.update('drop table if exists user')
    # db.update('create table user (id int primary key, name text, email text, passwd text, last_modified real)')
    # import doctest
    # doctest.testmod()
    class Users(Model):
        id = IntegerField(primary_key=True)
        name = StringField()
        email = StringField(updatable=False)
        password = StringField(default=lambda: '123456')

    u = Users(id=2, name='Michael', email='orm@db.org')
    r = u.insert()
    print r


