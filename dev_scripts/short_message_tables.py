# _*_ coding:utf-8 _*_
# @File  : short_message_tables.py
# @Time  : 2020-09-10 16:44
# @Author: zizle

from db.mysql_z import MySqlZ

with MySqlZ() as cursor:
    # 短信通数据表
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `short_message` ("
        "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
        "`create_time` DATETIME NOT NULL DEFAULT NOW(),"
        "`creator` INT(11) NOT NULL,"
        "`content` VARCHAR(1024) NOT NULL,"
        "`is_active` BIT NOT NULL DEFAULT 1"
        ") DEFAULT CHARSET='utf8';"
    )
