# coding=utf-8

__author__ = "Liu Cong"

"""
filename: www.models.py
create time: 2017-09-14
disc: Models
"""

import time, uuid

from transwarp.db import next_id
from transwarp.orm import Model, StringField, BooleanField, FloatField, TextField

class User(Model):
    """
    user表
    """
    __table__ = 'users'

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    email = StringField(updatable=False, ddl='varchar(50)')
    password = StringField(ddl='varchar(50)')
    admin = BooleanField()
    name = StringField(dll='varchar(50)')
    image = StringField(ddl='varchar(500)')
    created_at = FloatField(updatable=False, default=time.time)

class Blog(Model):
    """
    blog表
    """
    __table__ = 'blogs'

    id = StringField(primary_key=True, default=next_id, dll='varchar(50)')
    user_id = StringField(updatable=False, ddl='varchar(50)')
    user_name = StringField(ddl='varchar(50)')
    user_image = StringField(ddl='varchar(500)')
    name = StringField(ddl='varchar(50)')
    summary = StringField(ddl='varchar(200)')
    content = TextField()
    created_at = FloatField(updatable=False, default=time.time)

class Comment(Model):
    """
    comment表
    """
    __table__ = 'comments'

    id = StringField(primary_key=True, default=next_id(), ddl='varchar(50)')
    blog_id = StringField(updatable=False, ddl='varchar(50)')
    user_id = StringField(updatable=False, ddl='varchar(50)')
    user_name = StringField(ddl='varchar(50)')
    user_image = StringField(ddl='varchar(500)')
    content = TextField()
    created_at = FloatField(updatable=False, default=time.time)