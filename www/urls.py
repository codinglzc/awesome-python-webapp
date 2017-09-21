# coding=utf-8

__author__ = 'Liu Cong'

"""
filename: www.urls.py
create time: 2017-09-21
disc: urls.py
"""

from transwarp.web import get, view
from models import User, Blog, Comment

@view('test_users.html')
@get('/')
def test_users():
    users = User.find_all()
    return dict(users=users)