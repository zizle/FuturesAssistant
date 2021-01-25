# _*_ coding:utf-8 _*_
# @File  : basic_tables.py
# @Time  : 2020-08-31 9:30
# @Author: zizle

""" 初始化基本信息数据库表 """

from db.mysql_z import MySqlZ

with MySqlZ() as cursor:
    # 客户端数据表
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `lib_exchange_rate` ("
        "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
        "`rate_timestamp` INT NOT NULL COMMENT '汇率日期',"
        "`rate_name` VARCHAR(16) NOT NULL COMMENT '汇率名称',"
        "`rate` VARCHAR(16) NOT NULL DEFAULT '' COMMENT '汇率',"
        "UNIQUE KEY `rate_timestamp`(`rate_timestamp`,`rate_name`)"
        ") DEFAULT CHARSET='utf8';"
    )


