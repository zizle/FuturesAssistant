# _*_ coding:utf-8 _*_
# @File  : mysql_z.py
# @Time  : 2020-08-31 8:28
# @Author: zizle


""" 连接MySQL """
import sys
from pymysql import FIELD_TYPE, converters
from pymysql.connections import Connection
from pymysql.cursors import DictCursor
from configs import DB_CONFIGS

params = DB_CONFIGS["mysql"]                 # 系统主数据库
variety_sheet = DB_CONFIGS["variety_sheet"]  # 用户数据表数据库
exchange_lib = DB_CONFIGS["exchange_lib"]  # 交易所数据数据库

# 设置数据库查询cursor的数据类型转换
conversions = converters.conversions
# 数据库中的BIT返回0或1 (INT)
conversions[FIELD_TYPE.BIT] = lambda x: 1 if int.from_bytes(x, byteorder=sys.byteorder, signed=False) else 0

# 数据类型转换加入配置参数
params["conv"] = conversions
variety_sheet["conv"] = conversions.copy()
exchange_lib["conv"] = conversions.copy()


class ConnectError(Exception):
    """ 自定义错误 """


class MySqlZ(Connection):
    """ 系统主数据库 """
    def __init__(self):
        super(MySqlZ, self).__init__(**params)
        self.execute_cursor = self.cursor(DictCursor)
        self.execute_cursor._instance = self

    def __enter__(self):
        """Context manager that returns a Cursor"""
        if self.open:
            self.begin()
            return self.execute_cursor
        else:
            raise ConnectionError("连接Mysql失败!")

    def __exit__(self, exc, value, traceback):
        """On successful exit, commit. On exception, rollback"""
        if exc:
            self.rollback()
        else:
            self.commit()
        self.execute_cursor.close()
        self.close()


class VarietySheetDB(Connection):
    """ 用户数据表数据库 """
    def __init__(self):
        super(VarietySheetDB, self).__init__(**variety_sheet)
        self.execute_cursor = self.cursor(DictCursor)
        self.execute_cursor._instance = self

    def __enter__(self):
        """Context manager that returns a Cursor"""
        if self.open:
            self.begin()
            return self.execute_cursor
        else:
            raise ConnectionError("连接品种数据Mysql失败!")

    def __exit__(self, exc, value, traceback):
        """On successful exit, commit. On exception, rollback"""
        if exc:
            self.rollback()
        else:
            self.commit()
        self.execute_cursor.close()
        self.close()


class ExchangeLibDB(Connection):
    """ 交易所数据数据库 """
    def __init__(self):
        super(ExchangeLibDB, self).__init__(**exchange_lib)
        self.execute_cursor = self.cursor(DictCursor)
        self.execute_cursor._instance = self

    def __enter__(self):
        """Context manager that returns a Cursor"""
        if self.open:
            self.begin()
            return self.execute_cursor
        else:
            raise ConnectionError("连接交易所数据Mysql失败!")

    def __exit__(self, exc, value, traceback):
        """On successful exit, commit. On exception, rollback"""
        if exc:
            self.rollback()
        else:
            self.commit()
        self.execute_cursor.close()
        self.close()
