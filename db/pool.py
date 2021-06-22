# _*_ coding:utf-8 _*_
# @File  : pool.py
# @Time  : 2021-03-16 15:08
# @Author: zizle
# 数据库连接池
import sys
import MySQLdb
from MySQLdb.converters import conversions
from MySQLdb.constants import FIELD_TYPE
from dbutils.pooled_db import PooledDB

from configs import DB_CONFIGS

work_db_params = DB_CONFIGS['fa']


def get_converters():
    conversions[FIELD_TYPE.BIT] = lambda x: 1 if int.from_bytes(x, byteorder=sys.byteorder, signed=False) else 0
    return conversions


print('正在创建数据库连接池...')
# 创建连接池
fa_pool = PooledDB(
    creator=MySQLdb, mincached=5, maxcached=10,
    conv=get_converters(), charset='utf8mb4',
    blocking=True,
    **work_db_params
)
print('创建连接池完成!')
