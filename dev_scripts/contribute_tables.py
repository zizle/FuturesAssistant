# _*_ coding:utf-8 _*_
# @File  : contribute_tables.py
# @Time  : 2020-11-25 07:58
# @Author: zizle
from db.mysql_z import MySqlZ, ExchangeLibDB


""" 生成的第三方便于使用的数据表 """

def exchange_lib_tables():

    with ExchangeLibDB() as m_cursor:
        # 价格与前20名持仓量数据表
        m_cursor.execute(
            "CREATE TABLE IF NOT EXISTS `zero_price_position` ("
            "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
            "`date` INT NOT NULL COMMENT '时间戳',"
            "`variety_en` VARCHAR(2) NOT NULL COMMENT '品种',"
            "`contract` VARCHAR(6) NOT NULL COMMENT '合约编码',"
            "`close_price` DECIMAL(15,6) NOT NULL DEFAULT 0 COMMENT '收盘价',"
            "`settlement` DECIMAL(15,6) NOT NULL DEFAULT 0 COMMENT '结算价',"
            "`empty_volume` INT NOT NULL DEFAULT 0 COMMENT '持仓量',"
            "`long_position` INT NOT NULL DEFAULT 0 COMMENT '前20多头',"
            "`short_position` INT NOT NULL DEFAULT 0 COMMENT '前20空头',"
            "UNIQUE KEY `date`(`date`,contract)"
            ") DEFAULT CHARSET='utf8';"
        )

        # 价格指数数据表
        m_cursor.execute(
            "CREATE TABLE IF NOT EXISTS `zero_price_index` ("
            "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
            "`date` INT NOT NULL COMMENT '时间戳',"
            "`variety_en` VARCHAR(2) NOT NULL COMMENT '品种',"
            "`total_position` INT NOT NULL DEFAULT 0 COMMENT '总持仓量',"
            "`total_trade` INT NOT NULL DEFAULT 0 COMMENT '总成交量',"
            "`dominant_price` DECIMAL(15,6) NOT NULL DEFAULT 0 COMMENT '主力指数',"
            "`weight_price` DECIMAL(15,6) NOT NULL DEFAULT 0 COMMENT '权重指数',"
            "UNIQUE KEY `date`(`date`,variety_en)"
            ") DEFAULT CHARSET='utf8';"
        )
        """
        品种排名净持仓
        long_position: 前20名总买单量
        short_position: 前20名总卖单量
        """
        m_cursor.execute(
            "CREATE TABLE IF NOT EXISTS `zero_rank_position` ("
            "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
            "`date` VARCHAR(10) NOT NULL,"
            "`variety_en` VARCHAR(20) NOT NULL,"
            "`long_position` INT(11) NOT NULL DEFAULT 0,"
            "`long_position_increase` INT(11) NOT NULL DEFAULT 0,"
            "`short_position` INT(11) NOT NULL DEFAULT 0,"
            "`short_position_increase` INT(11) NOT NULL DEFAULT 0,"
            "`net_position` INT(11) NOT NULL DEFAULT 0,"
            "`net_position_increase` INT(11) NOT NULL DEFAULT 0,"
            "UNIQUE KEY `date`(`date`,variety_en)"
            ") DEFAULT CHARSET='utf8';"
        )
        # 品种的现货报价数据
        m_cursor.execute(
            "CREATE TABLE IF NOT EXISTS `zero_spot_price` ("
            "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
            "`date` INT NOT NULL COMMENT '日期时间戳',"
            "`variety_en` VARCHAR(2) NOT NULL COMMENT '品种代码',"
            "`price` DECIMAL(15,6) DEFAULT 0 COMMENT '现货价',"
            "`increase` DECIMAL(15,6) DEFAULT 0 COMMENT '增减',"
            "UNIQUE KEY `date`(`date`,`variety_en`)"
            ") DEFAULT CHARSET='utf8';"
        )

if __name__ == '__main__':
    exchange_lib_tables()
