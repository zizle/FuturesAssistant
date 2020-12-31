# _*_ coding:utf-8 _*_
# @File  : report_tables.py
# @Time  : 2020-09-30 09:16
# @Author: zizle
""" 报告的文件信息 """

from db.mysql_z import MySqlZ

with MySqlZ() as cursor:
    # 研究报告记录表
    # date: 报告所属日期
    # filepath: 文件所在的相对路径
    # is_active: 公开
    # 废弃
    # cursor.execute(
    #     "CREATE TABLE IF NOT EXISTS `research_report` ("
    #     "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
    #     "`date` VARCHAR(10) NOT NULL,"
    #     "`creator` INT(11) NOT NULL,"
    #     "`variety_en` VARCHAR(20) NOT NULL,"
    #     "`title` VARCHAR(128) NOT NULL,"
    #     "`report_type` ENUM('daily','weekly','monthly','annual','special', 'research','others') "
    #     "NOT NULL DEFAULT 'others',"
    #     "`filepath` VARCHAR (512) NOT NULL,"
    #     "`is_active` BIT NOT NULL DEFAULT 1"
    #     ") DEFAULT CHARSET='utf8';"
    # )

    # 研究文件存储表
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `research_file` ("
        "`id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',"
        "`create_time` INT NOT NULL COMMENT '创建时间',"
        "`update_time` INT NOT NULL COMMENT '更新时间',"
        "`file_date` INT NOT NULL COMMENT '报告日期',"
        "`creator` INT NOT NULL DEFAULT 0 COMMENT '创建者',"
        "`variety_en` VARCHAR(20) DEFAULT '' COMMENT '关联品种',"
        "`title` VARCHAR(128) NOT NULL COMMENT '文件名称',"
        "`file_type` INT NOT NULL COMMENT '类型',"
        "`filepath` VARCHAR(512) NOT NULL UNIQUE COMMENT '文件URL',"
        "`is_active` BIT NOT NULL DEFAULT 1 COMMENT '有效'"
        ") DEFAULT CHARSET='utf8';"
    )
