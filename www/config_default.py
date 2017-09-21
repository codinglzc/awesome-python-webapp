# coding=utf-8

__author__ = "Liu Cong"

"""
filename: www.config_default.py
create time: 2017-09-21
disc: config_default
    config_default.py作为开发环境的标准配置。
"""

configs = {
    'db': {
        'host': '127.0.0.1',
        'port': 3306,
        'user': 'root',
        'password': '123456',
        'database': 'awesome'
    },
    'session': {
        'secret': 'AwEsOmE'
    }
}
