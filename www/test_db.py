# coding=utf-8

__author__ = "Liu Cong"

"""
filename: www.test_db.py
create time: 2017-09-14
disc: test_db.py
"""

from models import User, Blog, Comment
from transwarp import db

db.create_engine(user='root', password='123456', database='awesome')

u = User(name='Test2', email='test2@example.com', password='987654321', image='about:blank')

u.insert()

print u

# u1 = User.find_first('where email=?', 'test1@example.com')
# print u1
#
# u1.delete()
# print u1
#
# u2 = User.find_first('where email=?', 'test2@example.com')
# print u2