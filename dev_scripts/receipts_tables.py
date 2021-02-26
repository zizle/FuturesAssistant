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
        "`date` INT NOT NULL COMMENT '日期',"
        "`variety_en` VARCHAR(32) NOT NULL COMMENT '品种',"
        "`receipt` INT NOT NULL DEFAULT 0,"
        "`increase` INT NOT NULL DEFAULT 0,"
        "UNIQUE KEY `date`(`date`,`variety_en`)"
        ") DEFAULT CHARSET='utf8';"
    )

    # 大商所仓单日报数据库
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `dce_receipt` ("
        "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
        "`date` INT NOT NULL COMMENT '日期',"
        "`variety_en` VARCHAR(32) NOT NULL COMMENT '品种',"
        "`receipt` INT NOT NULL DEFAULT 0,"
        "`increase` INT NOT NULL DEFAULT 0,"
        "UNIQUE KEY `date`(`date`,`variety_en`)"
        ") DEFAULT CHARSET='utf8';"
    )

    # 郑商所
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `czce_receipt` ("
        "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
        "`date` INT NOT NULL COMMENT '日期',"
        "`variety_en` VARCHAR(32) NOT NULL COMMENT '品种',"
        "`receipt` INT NOT NULL DEFAULT 0,"
        "`increase` INT NOT NULL DEFAULT 0,"
        "UNIQUE KEY `date`(`date`,`variety_en`)"
        ") DEFAULT CHARSET='utf8';"
    )
