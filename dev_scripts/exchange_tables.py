# _*_ coding:utf-8 _*_
# @File  : report_tables.py
# @Time  : 2020-09-30 09:16
# @Author: zizle
""" 交易所相关数据表 """

from db.migrate import RealExLib

with RealExLib() as ex_cursor:
    # 中金所日行情
    ex_cursor.execute(
        "CREATE TABLE IF NOT EXISTS `cffex_daily` ("
        "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',"
        "`date` INT NOT NULL COMMENT '日期',"
        "`variety_en` VARCHAR(2) NOT NULL COMMENT '品种',"
        "`contract` VARCHAR(6) NOT NULL COMMENT '合约',"
        "`pre_settlement` DECIMAL(15,6) DEFAULT 0 COMMENT '前结算',"
        "`open_price` DECIMAL(15,6) DEFAULT 0 COMMENT '开盘价',"
        "`highest` DECIMAL(15,6) DEFAULT 0 COMMENT '最高价',"
        "`lowest` DECIMAL(15,6) DEFAULT 0 COMMENT '最低价',"
        "`close_price` DECIMAL(15,6) DEFAULT 0 COMMENT '收盘价',"
        "`settlement` DECIMAL(15,6) DEFAULT 0 COMMENT '结算价',"
        "`zd_1` DECIMAL(15,6) DEFAULT 0 COMMENT '涨跌1',"
        "`zd_2` DECIMAL(15,6) DEFAULT 0 COMMENT '涨跌2',"
        "`trade_volume` INT DEFAULT 0 COMMENT '成交量',"
        "`empty_volume` INT DEFAULT 0 COMMENT '空盘量',"
        "`increase_volume` INT DEFAULT 0 COMMENT '变化量',"
        "`trade_price` DECIMAL(15,6) DEFAULT 0 COMMENT '成交额',"
        "UNIQUE KEY `date`(`date`,`contract`)"
        ") DEFAULT CHARSET='utf8';"
    )
    # 中金所排名
    ex_cursor.execute(
        "CREATE TABLE IF NOT EXISTS `cffex_rank` ("
        "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',"
        "`date` INT NOT NULL COMMENT '日期',"
        "`variety_en` VARCHAR(2) NOT NULL COMMENT '品种',"
        "`contract` VARCHAR(6) NOT NULL COMMENT '合约',"
        "`rank` INT NOT NULL COMMENT '名次',"
        "`trade_company` VARCHAR(16) DEFAULT '' COMMENT '公司1',"
        "`trade` INT DEFAULT 0 COMMENT '成交量',"
        "`trade_increase` INT DEFAULT 0 COMMENT '成交量变化',"
        "`long_position_company` VARCHAR(16) DEFAULT '' COMMENT '公司2',"
        "`long_position` INT DEFAULT 0 COMMENT '多单量',"
        "`long_position_increase` INT DEFAULT 0 COMMENT '多单变化量',"
        "`short_position_company` VARCHAR(16) DEFAULT '' COMMENT '公司3',"
        "`short_position` INT DEFAULT 0 COMMENT '空单量',"
        "`short_position_increase` INT DEFAULT 0 COMMENT '空单变化量',"
        "UNIQUE KEY `date`(`date`,`contract`,`rank`)"
        ") DEFAULT CHARSET='utf8';"
    )
    # 郑商所日行情
    ex_cursor.execute(
        "CREATE TABLE IF NOT EXISTS `czce_daily` ("
        "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',"
        "`date` INT NOT NULL COMMENT '日期',"
        "`variety_en` VARCHAR(2) NOT NULL COMMENT '品种',"
        "`contract` VARCHAR(6) NOT NULL COMMENT '合约',"
        "`pre_settlement` DECIMAL(15,6) DEFAULT 0 COMMENT '前结算',"
        "`open_price` DECIMAL(15,6) DEFAULT 0 COMMENT '开盘价',"
        "`highest` DECIMAL(15,6) DEFAULT 0 COMMENT '最高价',"
        "`lowest` DECIMAL(15,6) DEFAULT 0 COMMENT '最低价',"
        "`close_price` DECIMAL(15,6) DEFAULT 0 COMMENT '收盘价',"
        "`settlement` DECIMAL(15,6) DEFAULT 0 COMMENT '结算价',"
        "`zd_1` DECIMAL(15,6) DEFAULT 0 COMMENT '涨跌1',"
        "`zd_2` DECIMAL(15,6) DEFAULT 0 COMMENT '涨跌2',"
        "`trade_volume` INT DEFAULT 0 COMMENT '成交量',"
        "`empty_volume` INT DEFAULT 0 COMMENT '空盘量',"
        "`increase_volume` INT DEFAULT 0 COMMENT '变化量',"
        "`trade_price` DECIMAL(15,6) DEFAULT 0 COMMENT '成交额',"
        "`delivery_price` DECIMAL(15,6) DEFAULT 0 COMMENT '交割价',"
        "UNIQUE KEY `date`(`date`,`contract`)"
        ") DEFAULT CHARSET='utf8';"
    )
    # 郑商所排名
    ex_cursor.execute(
        "CREATE TABLE IF NOT EXISTS `czce_rank` ("
        "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',"
        "`date` INT NOT NULL COMMENT '日期',"
        "`variety_en` VARCHAR(2) NOT NULL COMMENT '品种',"
        "`contract` VARCHAR(6) NOT NULL COMMENT '合约',"
        "`rank` INT NOT NULL COMMENT '名次',"
        "`trade_company` VARCHAR(16) DEFAULT '' COMMENT '公司1',"
        "`trade` INT DEFAULT 0 COMMENT '成交量',"
        "`trade_increase` INT DEFAULT 0 COMMENT '成交量变化',"
        "`long_position_company` VARCHAR(16) DEFAULT '' COMMENT '公司2',"
        "`long_position` INT DEFAULT 0 COMMENT '多单量',"
        "`long_position_increase` INT DEFAULT 0 COMMENT '多单变化量',"
        "`short_position_company` VARCHAR(16) DEFAULT '' COMMENT '公司3',"
        "`short_position` INT DEFAULT 0 COMMENT '空单量',"
        "`short_position_increase` INT DEFAULT 0 COMMENT '空单变化量',"
        "UNIQUE KEY `date`(`date`,`contract`,`rank`)"
        ") DEFAULT CHARSET='utf8';"
    )

    # 大商所日行情
    ex_cursor.execute(
        "CREATE TABLE IF NOT EXISTS `dce_daily` ("
        "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',"
        "`date` INT NOT NULL COMMENT '日期',"
        "`variety_en` VARCHAR(2) NOT NULL COMMENT '品种',"
        "`contract` VARCHAR(6) NOT NULL COMMENT '合约',"
        "`pre_settlement` DECIMAL(15,6) DEFAULT 0 COMMENT '前结算',"
        "`open_price` DECIMAL(15,6) DEFAULT 0 COMMENT '开盘价',"
        "`highest` DECIMAL(15,6) DEFAULT 0 COMMENT '最高价',"
        "`lowest` DECIMAL(15,6) DEFAULT 0 COMMENT '最低价',"
        "`close_price` DECIMAL(15,6) DEFAULT 0 COMMENT '收盘价',"
        "`settlement` DECIMAL(15,6) DEFAULT 0 COMMENT '结算价',"
        "`zd_1` DECIMAL(15,6) DEFAULT 0 COMMENT '涨跌1',"
        "`zd_2` DECIMAL(15,6) DEFAULT 0 COMMENT '涨跌2',"
        "`trade_volume` INT DEFAULT 0 COMMENT '成交量',"
        "`empty_volume` INT DEFAULT 0 COMMENT '空盘量',"
        "`increase_volume` INT DEFAULT 0 COMMENT '变化量',"
        "`trade_price` DECIMAL(15,6) DEFAULT 0 COMMENT '成交额',"
        "UNIQUE KEY `date`(`date`,`contract`)"
        ") DEFAULT CHARSET='utf8';"
    )
    # 大商所排名
    ex_cursor.execute(
        "CREATE TABLE IF NOT EXISTS `dce_rank` ("
        "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',"
        "`date` INT NOT NULL COMMENT '日期',"
        "`variety_en` VARCHAR(2) NOT NULL COMMENT '品种',"
        "`contract` VARCHAR(6) NOT NULL COMMENT '合约',"
        "`rank` INT NOT NULL COMMENT '名次',"
        "`trade_company` VARCHAR(16) DEFAULT '' COMMENT '公司1',"
        "`trade` INT DEFAULT 0 COMMENT '成交量',"
        "`trade_increase` INT DEFAULT 0 COMMENT '成交量变化',"
        "`long_position_company` VARCHAR(16) DEFAULT '' COMMENT '公司2',"
        "`long_position` INT DEFAULT 0 COMMENT '多单量',"
        "`long_position_increase` INT DEFAULT 0 COMMENT '多单变化量',"
        "`short_position_company` VARCHAR(16) DEFAULT '' COMMENT '公司3',"
        "`short_position` INT DEFAULT 0 COMMENT '空单量',"
        "`short_position_increase` INT DEFAULT 0 COMMENT '空单变化量',"
        "UNIQUE KEY `date`(`date`,`contract`,`rank`)"
        ") DEFAULT CHARSET='utf8';"
    )

    # 上期所日行情
    ex_cursor.execute(
        "CREATE TABLE IF NOT EXISTS `shfe_daily` ("
        "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',"
        "`date` INT NOT NULL COMMENT '日期',"
        "`variety_en` VARCHAR(2) NOT NULL COMMENT '品种',"
        "`contract` VARCHAR(6) NOT NULL COMMENT '合约',"
        "`pre_settlement` DECIMAL(15,6) DEFAULT 0 COMMENT '前结算',"
        "`open_price` DECIMAL(15,6) DEFAULT 0 COMMENT '开盘价',"
        "`highest` DECIMAL(15,6) DEFAULT 0 COMMENT '最高价',"
        "`lowest` DECIMAL(15,6) DEFAULT 0 COMMENT '最低价',"
        "`close_price` DECIMAL(15,6) DEFAULT 0 COMMENT '收盘价',"
        "`settlement` DECIMAL(15,6) DEFAULT 0 COMMENT '结算价',"
        "`zd_1` DECIMAL(15,6) DEFAULT 0 COMMENT '涨跌1',"
        "`zd_2` DECIMAL(15,6) DEFAULT 0 COMMENT '涨跌2',"
        "`trade_volume` INT DEFAULT 0 COMMENT '成交量',"
        "`empty_volume` INT DEFAULT 0 COMMENT '空盘量',"
        "`increase_volume` INT DEFAULT 0 COMMENT '变化量',"
        "UNIQUE KEY `date`(`date`,`contract`)"
        ") DEFAULT CHARSET='utf8';"
    )
    # 上期所排名
    ex_cursor.execute(
        "CREATE TABLE IF NOT EXISTS `shfe_rank` ("
        "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',"
        "`date` INT NOT NULL COMMENT '日期',"
        "`variety_en` VARCHAR(2) NOT NULL COMMENT '品种',"
        "`contract` VARCHAR(6) NOT NULL COMMENT '合约',"
        "`rank` INT NOT NULL COMMENT '名次',"
        "`trade_company` VARCHAR(16) DEFAULT '' COMMENT '公司1',"
        "`trade` INT DEFAULT 0 COMMENT '成交量',"
        "`trade_increase` INT DEFAULT 0 COMMENT '成交量变化',"
        "`long_position_company` VARCHAR(16) DEFAULT '' COMMENT '公司2',"
        "`long_position` INT DEFAULT 0 COMMENT '多单量',"
        "`long_position_increase` INT DEFAULT 0 COMMENT '多单变化量',"
        "`short_position_company` VARCHAR(16) DEFAULT '' COMMENT '公司3',"
        "`short_position` INT DEFAULT 0 COMMENT '空单量',"
        "`short_position_increase` INT DEFAULT 0 COMMENT '空单变化量',"
        "UNIQUE KEY `date`(`date`,`contract`,`rank`)"
        ") DEFAULT CHARSET='utf8';"
    )

    # """
    # 品种排名净持仓
    # long_position: 前20名总买单量
    # short_position: 前20名总卖单量
    # """
    # ex_cursor.execute(
    #     "CREATE TABLE IF NOT EXISTS `exchange_rank_holding` ("
    #     "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
    #     "`date` VARCHAR(10) NOT NULL,"
    #     "`variety_en` VARCHAR(20) NOT NULL,"
    #     "`long_position` INT(11) NOT NULL DEFAULT 0,"
    #     "`long_position_increase` INT(11) NOT NULL DEFAULT 0,"
    #     "`short_position` INT(11) NOT NULL DEFAULT 0,"
    #     "`short_position_increase` INT(11) NOT NULL DEFAULT 0,"
    #     "`net_position` INT(11) NOT NULL DEFAULT 0,"
    #     "`net_position_increase` INT(11) NOT NULL DEFAULT 0"
    #     ") DEFAULT CHARSET='utf8';"
    # )