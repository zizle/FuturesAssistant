# _*_ coding:utf-8 _*_
# @File  : basic_tables.py
# @Time  : 2020-08-31 9:30
# @Author: zizle

""" 初始化基本信息数据库表 """

from db.mysql_z import MySqlZ

with MySqlZ() as cursor:
    # 客户端数据表
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `basic_client` ("
        "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
        "`join_time` DATETIME NOT NULL DEFAULT NOW(),"
        "`client_name` VARCHAR(128) NOT NULL DEFAULT '',"
        "`machine_uuid` VARCHAR(36) NOT NULL,"
        "`is_manager` BIT NOT NULL,"
        "`is_active` BIT NOT NULL DEFAULT 1"
        ") DEFAULT CHARSET='utf8';"
    )
    # 客户端在线数据表
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `basic_client_online` ("
        "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
        "`client_id` INT(11) NOT NULL,"
        "`update_time` DATETIME NOT NULL DEFAULT NOW() ON UPDATE NOW(),"
        "`online_date` VARCHAR(10) NOT NULL,"
        "`total_online` INT(11) DEFAULT 0"
        ") DEFAULT CHARSET='utf8';"
    )
    # 品种数据表
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `basic_variety` ("
        "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
        "`create_time` DATETIME NOT NULL DEFAULT NOW(),"
        "`variety_name` VARCHAR(10) NOT NULL,"
        "`variety_en` VARCHAR(2) NOT NULL,"
        "`exchange_lib` ENUM('czce','dce','shfe','cffex','ine') NOT NULL,"
        "`group_name` ENUM('finance','farm','chemical','metal') NOT NULL,"
        "`sorted` INTEGER NOT NULL DEFAULT 0,"
        "`is_active` BIT NOT NULL DEFAULT 1,"
        "UNIQUE KEY `vnve`(`variety_name`,`variety_en`)"
        ") DEFAULT CHARSET='utf8';"
    )



