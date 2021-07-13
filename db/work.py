# _*_ coding:utf-8 _*_
# @File  : work.py
# @Time  : 2021-03-16 15:16
# @Author: zizle

import MySQLdb
from .pool import fa_pool
from configs import logger


class FAConnection(object):
    def __init__(self, conn_name=''):
        self.conn_name = conn_name
        self.conn = fa_pool.connection()  # 从连接池取得一个连接
        self.cursor = self.conn.cursor(MySQLdb.cursors.DictCursor)  # 连接的游标

    def begin(self):
        self.conn.begin()

    def close(self):
        self.cursor.close()
        self.conn.close()

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def execute(self, sql, param=None, keep_conn=False):
        self.begin()
        is_success = True
        if param is None:
            param = []
        try:
            self.cursor.execute(sql, param)
        except Exception as e:
            self.rollback()
            is_success = False
            logger.error('业务{}操作数据库失败:{}'.format(self.conn_name, e))
        else:
            self.commit()
        finally:
            if not keep_conn:
                self.close()
            return is_success

    def execute_tasks(self, sql_list, param_list, keep_conn=False):  # 事务方式执行
        self.begin()
        is_success = True
        try:
            for sql_tuple in zip(sql_list, param_list):
                if sql_tuple[1] is None:
                    self.cursor.execute(sql_tuple[0])
                else:
                    self.cursor.execute(sql_tuple[0], sql_tuple[1])
        except Exception as e:
            self.rollback()
            logger.error('事务型操作数据库失败:{}'.format(e))
            is_success = False
        else:
            self.commit()
        finally:
            if not keep_conn:
                self.close()
            return is_success

    def insert(self, sql, param=None, many=False, keep_conn=False):
        self.begin()
        insert_id = 0
        count = 0
        if param is None:
            param = []
        try:
            if many:
                count = self.cursor.executemany(sql, param)
            else:
                count = self.cursor.execute(sql, param)
            self.cursor.execute('SELECT LAST_INSERT_ID() AS insertID;')
            insert_id = self.cursor.fetchone()['insertID']
        except Exception as e:
            self.rollback()
            logger.error('添加数据记录失败:{}'.format(e))
        else:
            self.commit()
        finally:
            if not keep_conn:
                self.close()
            return count, insert_id

    def query(self, sql, param=None, fetchone=False, keep_conn=False) -> list:
        records = []
        try:
            if param is None:  # 无参数
                self.cursor.execute(sql)
            else:
                self.cursor.execute(sql, param)
            if fetchone:
                record_obj = self.cursor.fetchone()
                if record_obj:
                    records.append(record_obj)
            else:
                records = list(self.cursor.fetchall())
        except Exception as e:
            logger.error('查询数据失败:{}'.format(e))
        finally:
            if not keep_conn:
                self.close()
            return records
