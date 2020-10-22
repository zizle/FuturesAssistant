# _*_ coding:utf-8 _*_
# @File  : delivery_tables.py
# @Time  : 2020-09-22 13:35
# @Author: zizle
""" 交割服务的数据库 """

from db.mysql_z import MySqlZ

# 交割仓库编号表
with MySqlZ() as cursor:
    # 仓库编号表
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `delivery_warehouse_number` ("
        "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
        "`name` VARCHAR(128) NOT NULL,"
        "fixed_code VARCHAR(4) NOT NULL,"
        "`create_time` DATETIME DEFAULT NOW(),"
        "`update_time` DATETIME DEFAULT NOW(),"
        "UNIQUE KEY `warecode`(`name`,`fixed_code`)"
        ") DEFAULT CHARSET='utf8';"
    )
    # 仓库信息表
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `delivery_warehouse` ("
        "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
        "fixed_code VARCHAR(4) NOT NULL DEFAULT '',"
        "`area` VARCHAR(4) NOT NULL,"
        "`name` VARCHAR(128) NOT NULL DEFAULT '',"
        "`short_name` VARCHAR(16) NOT NULL,"
        "`addr` VARCHAR(1024) NOT NULL DEFAULT '',"
        "`arrived` VARCHAR(1536) NOT NULL DEFAULT '',"
        "`create_time` DATETIME DEFAULT NOW(),"
        "`update_time` DATETIME DEFAULT NOW(),"
        "`longitude` FLOAT(10,4) NOT NULL,"
        "`latitude` FLOAT(10,4) NOT NULL,"
        "`is_active` BIT NOT NULL DEFAULT 1"
        ") DEFAULT CHARSET='utf8';"
    )

    # 仓库交割的品种表
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `delivery_warehouse_variety` ("
        "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
        "warehouse_code VARCHAR(4) NOT NULL,"
        "`variety` VARCHAR(8) NOT NULL DEFAULT '',"
        "`variety_en` VARCHAR(4) NOT NULL DEFAULT '',"
        "`linkman` VARCHAR(32) DEFAULT '' DEFAULT '',"
        "`links` VARCHAR(512) NOT NULL DEFAULT '',"
        "`premium` VARCHAR(64) NOT NULL DEFAULT '',"
        "`receipt_unit` VARCHAR(32) DEFAULT '',"
        "`create_time` DATETIME DEFAULT NOW(),"
        "`update_time` DATETIME DEFAULT NOW(),"
        "`is_active` BIT NOT NULL DEFAULT 1,"
        "UNIQUE KEY `warevariety`(`warehouse_code`,`variety_en`)"
        ") DEFAULT CHARSET='utf8';"
    )

    # 品种交割基本信息表
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `delivery_variety_message` ("
        "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
        "`variety` VARCHAR(8) NOT NULL DEFAULT '',"
        "`variety_en` VARCHAR(4) NOT NULL DEFAULT '',"
        "`last_trade` VARCHAR(32) DEFAULT '' DEFAULT '',"
        "`receipt_expire` VARCHAR(512) NOT NULL DEFAULT '',"
        "`delivery_unit` VARCHAR(32) NOT NULL DEFAULT '',"
        "`limit_holding` VARCHAR(32) DEFAULT '',"
        "UNIQUE KEY `varietyaen`(`variety`,`variety_en`)"
        ") DEFAULT CHARSET='utf8';"
    )

    # 仓单表
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `delivery_warehouse_receipt` ("
        "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
        "`warehouse_code` VARCHAR(4) DEFAULT '',"
        "`warehouse_name` VARCHAR(32) NOT NULL,"
        "`variety` VARCHAR(8) NOT NULL DEFAULT '',"
        "`variety_en` VARCHAR(4) NOT NULL DEFAULT '',"
        "`date` VARCHAR(8) NOT NULL,"
        "`receipt` INT(11) DEFAULT 0,"
        "`increase` INT(11) DEFAULT 0,"
        "`create_time` DATETIME DEFAULT NOW()"
        ") DEFAULT CHARSET='utf8';"
    )

    # 讨论交流表
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `delivery_discussion` ("
        "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
        "`author_id` INT(11) NOT NULL,"
        "`content` VARCHAR(2048) NOT NULL,"
        "`create_time` DATETIME DEFAULT NOW(),"
        "`parent_id` INT(11) DEFAULT 0"
        ") DEFAULT CHARSET='utf8';"
    )
