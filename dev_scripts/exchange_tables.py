# _*_ coding:utf-8 _*_
# @File  : report_tables.py
# @Time  : 2020-09-30 09:16
# @Author: zizle
""" 交易所相关数据表 """

from db.mysql_z import MySqlZ
with MySqlZ() as cursor:
    """
    品种排名净持仓
    long_position: 前20名总买单量
    short_position: 前20名总卖单量
    """
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `exchange_rank_holding` ("
        "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
        "`date` VARCHAR(10) NOT NULL,"
        "`variety_en` VARCHAR(20) NOT NULL,"
        "`long_position` INT(11) NOT NULL DEFAULT 0,"
        "`long_position_increase` INT(11) NOT NULL DEFAULT 0,"
        "`short_position` INT(11) NOT NULL DEFAULT 0,"
        "`short_position_increase` INT(11) NOT NULL DEFAULT 0,"
        "`net_position` INT(11) NOT NULL DEFAULT 0,"
        "`net_position_increase` INT(11) NOT NULL DEFAULT 0"
        ") DEFAULT CHARSET='utf8';"
    )