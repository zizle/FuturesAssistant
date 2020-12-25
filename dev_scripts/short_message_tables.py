# _*_ coding:utf-8 _*_
# @File  : short_message_tables.py
# @Time  : 2020-09-10 16:44
# @Author: zizle

from db.mysql_z import MySqlZ

with MySqlZ() as cursor:
    # 短信通数据表
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `short_message` ("
        "`id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',"
        "`create_time` INT NOT NULL COMMENT '创建时间',"
        "`update_time` INT NOT NULL COMMENT '更新时间',"
        "`creator` INT NOT NULL COMMENT '创建者',"
        "`content` VARCHAR(1024) NOT NULL COMMENT '内容',"
        "`md5` VARCHAR(32) NOT NULL UNIQUE COMMENT '内容哈希',"
        "`is_active` BIT NOT NULL DEFAULT 1 COMMENT '有效'"
        ") DEFAULT CHARSET='utf8';"
    )
