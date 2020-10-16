# _*_ coding:utf-8 _*_
# @File  : redis_z.py
# @Time  : 2020-08-31 8:28
# @Author: zizle
from redis import Redis, ConnectionPool
from configs import DB_CONFIGS

params = DB_CONFIGS["redis"]

conn_pool = ConnectionPool(decode_responses=True, **params)  # 利用文件导入的"单例"模式设置连接池


class RedisZ(object):
    def __init__(self):
        self.redis_conn = Redis(connection_pool=conn_pool)

    def __enter__(self):
        return self.redis_conn

    def __exit__(self, exc, value, traceback):
        self.redis_conn.close()
