# _*_ coding:utf-8 _*_
# @File  : industry_tables.py
# @Time  : 2020-09-03 16:22
# @Author: zizle
from db.mysql_z import MySqlZ

with MySqlZ() as cursor:
    # 用户品种数据分组表
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `industry_sheet_group` ("
        "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
        "`variety_en` VARCHAR(2) NOT NULL,"
        "`group_name` VARCHAR(20) NOT NULL,"
        "`suffix` INT(11) NOT NULL DEFAULT 0,"
        "`is_active` BIT NOT NULL DEFAULT 1,"
        "UNIQUE KEY `vngn`(`variety_en`,`group_name`)"
        ") DEFAULT CHARSET='utf8';"
    )

    # 用户数据更新配置表
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `industry_user_folder` ("
        "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
        "`variety_en` VARCHAR(2) NOT NULL,"
        "`group_id` INT(11) NOT NULL,"
        "`folder` VARCHAR (1024) NOT NULL,"
        "`client` VARCHAR(36) NOT NULL,"
        "`user_id` INT(11) NOT NULL"
        ") DEFAULT CHARSET='utf8';"
    )

    # 用户的品种数据表
    # creator    创建者         update_by  更新者
    # db_table   库中表名       name_md5    sheet_name的MD5值,利于where查询使用
    # min_date   最小时间       max_date    最大时间
    # update_count  最近新增的个数
    # origin     数据源         suffix      排序字段
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `industry_user_sheet` ("
        "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
        "`create_time` DATETIME NOT NULL DEFAULT NOW(),"
        "`creator` INT(11) NOT NULL,"
        "`update_time` DATETIME NOT NULL DEFAULT NOW(),"
        "`update_by` INT(11) NOT NULL,"
        "`variety_en` VARCHAR(2) NOT NULL,"
        "`group_id` INT(11) NOT NULL,"
        "`sheet_name` VARCHAR(128) NOT NULL,"
        "`name_md5` VARCHAR(32) NOT NULL,"
        "`db_table` VARCHAR(32) NOT NULL UNIQUE,"
        "`min_date` VARCHAR(10) NOT NULL DEFAULT '',"
        "`max_date` VARCHAR(10) NOT NULL DEFAULT '',"
        "`update_count` INT(11) NOT NULL DEFAULT 0,"
        "`origin` VARCHAR(128) NOT NULL DEFAULT '',"
        "`note` VARCHAR(128) NOT NULL DEFAULT '',"
        "`suffix` INT(11) NOT NULL DEFAULT 0,"
        "`is_private` BIT NOT NULL DEFAULT 0"
        ") DEFAULT CHARSET='utf8';"
    )
    # variety_en: 品种字段,方便查询      sheet_id: 相关的数据表id
    # decipherment: 图形的文字解说
    # is_principal: 主页显示的           is_petit： 品种页显示的
    # is_private: 私有化仅自己可见
    # 用户的图形表
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `industry_user_chart` ("
        "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
        "`create_time` DATETIME NOT NULL DEFAULT NOW(),"
        "`creator` INT(11) NOT NULL,"
        "`title` VARCHAR(64) NOT NULL,"
        "`variety_en` VARCHAR(2) NOT NULL,"
        "`sheet_id` INT(11) NOT NULL,"
        "`option_file` VARCHAR(128) NOT NULL,"
        "`decipherment` TEXT,"
        "`suffix` INT(11) NOT NULL DEFAULT 0,"
        "`is_principal` ENUM('0','1','2') NOT NULL DEFAULT '0',"
        "`is_petit` BIT NOT NULL DEFAULT 0,"
        "`is_private` BIT NOT NULL DEFAULT 0"
        ") DEFAULT CHARSET='utf8';"
    )

    # 品种的现货报价数据
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `industry_spot_price` ("
        "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
        "`create_time` DATETIME NOT NULL DEFAULT NOW(),"
        "`date` VARCHAR(8) NOT NULL,"
        "`variety_en` VARCHAR(2) NOT NULL,"
        "`spot_price` DECIMAL(9,2) DEFAULT 0,"
        "`price_increase` DECIMAL(9,2) DEFAULT 0"
        ") DEFAULT CHARSET='utf8';"
    )
