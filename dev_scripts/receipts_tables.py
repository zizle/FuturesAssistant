# _*_ coding:utf-8 _*_
# @File  : receipts_tables.py
# @Time  : 2020-09-29 13:33
# @Author: zizle
from db.mysql_z import ExchangeLibDB

with ExchangeLibDB() as cursor:
    # 上期所仓单日报数据库
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `shfe_receipt` ("
        "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
        "`date` VARCHAR(8) NOT NULL,"
        "`create_date` DATETIME NOT NULL DEFAULT NOW(),"
        "`variety_en` VARCHAR(32) NOT NULL,"
        "`warehouse` VARCHAR (32) NOT NULL,"
        "`receipt` INT(11) DEFAULT NULL DEFAULT 0,"
        "`receipt_increase` INT(11) DEFAULT NULL DEFAULT 0"
        ") DEFAULT CHARSET='utf8';"
    )

    # 大商所仓单日报数据库
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `dce_receipt` ("
        "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
        "`date` VARCHAR(8) NOT NULL,"
        "`create_date` DATETIME NOT NULL DEFAULT NOW(),"
        "`variety_en` VARCHAR(32) NOT NULL,"
        "`warehouse` VARCHAR (32) NOT NULL,"
        "`receipt` INT(11) DEFAULT NULL DEFAULT 0,"
        "`receipt_increase` INT(11) DEFAULT NULL DEFAULT 0"
        ") DEFAULT CHARSET='utf8';"
    )
