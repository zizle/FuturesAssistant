# _*_ coding:utf-8 _*_
# @File  : redis_pool.py
# @Time  : 2021-04-16 16:41
# @Author: zizle

from redis import Redis, ConnectionPool
from settings import DATABASE

params = DATABASE["redis"]

conn_pool = ConnectionPool(decode_responses=True, **params)  # 利用文件导入的"单例"模式设置连接池
print('创建redis连接池:', id(conn_pool))


class RedisConnection(object):
    def __init__(self):
        print(id(conn_pool))
        self.redis_conn = Redis(connection_pool=conn_pool)

    def __enter__(self):
        return self.redis_conn

    def __exit__(self, exc, value, traceback):
        self.redis_conn.close()

    def close(self):
        self.redis_conn.close()

    def set_value(self, key, value, expires):
        # expires为秒
        self.redis_conn.set(key, value, ex=expires)
        self.redis_conn.close()

    def get_value(self, key):
        v = self.redis_conn.get(key)
        self.redis_conn.close()
        return v

