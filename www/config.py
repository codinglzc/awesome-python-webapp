# coding=utf-8

__author__ = "Liu Cong"

"""
filename: www.config.py
create time: 2017-09-21
disc: config
    config.py作为读取配置文件的操作。
"""

import config_default

class Dict(dict):
    """
    Simple dict but support access as d.key style.
    """
    def __init__(self, names=(), values=(), **kw):
        super(Dict, self).__init__(**kw)
        for k, v in zip(names, values):
            self[k] = v

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value

def merge(defaults, override):
    r = {}
    for k, v in defaults.iteritems():
        if k in override:
            if isinstance(v, dict):
                r[k] = merge(v, override[k])
            else:
                r[k] = override[k]
        else:
            r[k] = v
    return r

def toDict(d):
    D = Dict()
    for k, v in d.iteritems():
        D[k] = toDict(v) if isinstance(v, dict) else v
    return D

configs = config_default.configs
try:
    import config_override
    configs = merge(configs, config_override.configs)
except ImportError:
    pass

configs = toDict(configs)
