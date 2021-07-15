# _*_ coding:utf-8 _*_
# @File  : add_administrator.py
# @Time  : 2021-06-07 09:06
# @Author: zizle
# 添加管理员

from db import FAConnection
from hutool.security import cipher_user_password


# 添加一个超级管理员
def add_administrator(username, phone, password):
    pwd = cipher_user_password(password)
    db = FAConnection()
    insert_sql = 'INSERT INTO sys_person (creator,username,account,phone,password,grouping) VALUES (%s,%s,%s,%s,%s,%s);'
    params = [0, username, phone, '', pwd, 1]
    _, count = db.insert(insert_sql, params)
    if count:
        print('添加成功!')
    else:
        print('添加失败!')


if __name__ == '__main__':
    USERNAME = 'zizlee'
    PHONE = '15759566200'
    PASSWORD = '566200'
    add_administrator(USERNAME, PHONE, PASSWORD)

